from datetime import timedelta, datetime

import pytest
import time_machine
from django.core.management import call_command
from django.utils import timezone

from passage.models import ZoneZwaarVerkeer, ZwaarVerkeerHelperTable
from passage.tests.factories import PassageFactory


@pytest.mark.django_db
class TestZwaarVerkeerAggregation:
    @time_machine.travel(datetime.today() + timedelta(days=1), tick=False)
    @pytest.mark.parametrize(
        'kenteken_land,expected_kenteken_land',
        [
            ('NL', 'NL'),
            ('BE', 'buitenland'),
        ],
    )
    @pytest.mark.parametrize(
        'voertuig_soort,inrichting,expected_inrichting',
        [
            ('Personenauto', 'foobar', 'Personenauto'),
            ('Vrachtwagen', 'barbaz', 'barbaz'),
        ],
    )
    @pytest.mark.parametrize(
        'toegestane_maximum_massa_voertuig,expected_klasse_toegestaan_gewicht',
        [
            (0, 'klasse 0 <= 3500'),
            (3500, 'klasse 0 <= 3500'),
            (3501, 'klasse 1 <= 7500'),
            (7500, 'klasse 1 <= 7500'),
            (7501, 'klasse 2 <= 11250'),
            (11250, 'klasse 2 <= 11250'),
            (11251, 'klasse 3 <= 30000'),
            (30000, 'klasse 3 <= 30000'),
            (30001, 'klasse 4 <= 50000'),
            (50000, 'klasse 4 <= 50000'),
            (50001, 'klasse 5 > 50000'),
            (99999, 'klasse 5 > 50000'),
        ],
    )
    def test_aggregation(
        self,
        kenteken_land,
        expected_kenteken_land,
        voertuig_soort,
        inrichting,
        expected_inrichting,
        toegestane_maximum_massa_voertuig,
        expected_klasse_toegestaan_gewicht,
    ):
        # required to ensure partitions exist
        import make_paritions

        helper_table_row = ZwaarVerkeerHelperTable.objects.filter(
            cordon__in=['S100', 'A10']
        ).first()

        yesterday = timezone.now() - timedelta(days=1)
        # create ten passages for the correct day
        PassageFactory.create_batch(
            size=10,
            passage_at=yesterday,
            camera_naam=helper_table_row.camera_naam,
            camera_kijkrichting=helper_table_row.camera_kijkrichting,
            rijrichting=helper_table_row.rijrichting,
            kenteken_land=kenteken_land,
            voertuig_soort=voertuig_soort,
            inrichting=inrichting,
            toegestane_maximum_massa_voertuig=toegestane_maximum_massa_voertuig,
        )
        # create some more for different days
        other_days = [
            yesterday + timedelta(days=1),
            yesterday + timedelta(days=2),
            yesterday + timedelta(days=3),
        ]
        other_days = []
        for day in other_days:
            PassageFactory.create_batch(
                size=5,
                passage_at=day,
                camera_naam=helper_table_row.camera_naam,
                camera_kijkrichting=helper_table_row.camera_kijkrichting,
                rijrichting=helper_table_row.rijrichting,
            )

        assert ZoneZwaarVerkeer.objects.count() == 0
        call_command(
            'passage_zone_zwaar_verkeer',
            from_date=yesterday.date(),
        )

        if kenteken_land != 'NL':
            expected_klasse_toegestaan_gewicht = 'buitenland'

        expected_timestamp = yesterday.replace(minute=0, second=0, microsecond=0)
        expected_date = yesterday.date()
        expected_year = yesterday.year
        expected_month = yesterday.month
        expected_day = yesterday.day
        expected_week = int(yesterday.strftime("%U"))
        expected_day_of_week = self._get_expected_dow(yesterday)
        expected_hour = yesterday.hour

        # (implicitly) assert there is one result for today by using get
        result = ZoneZwaarVerkeer.objects.filter(
            passage_at_timestamp=expected_timestamp
        ).get()
        for day in other_days:
            assert ZoneZwaarVerkeer.objects.filter(
                passage_at_timestamp=day.replace(minute=0, second=0, microsecond=0)
            ).exists()

        # check extracted datetime info
        assert result.passage_at_timestamp == expected_timestamp
        assert result.passage_at_date == expected_date
        assert result.passage_at_year == expected_year
        assert result.passage_at_month == expected_month
        assert result.passage_at_day == expected_day
        assert result.passage_at_week == expected_week
        assert result.passage_at_day_of_week == expected_day_of_week
        assert result.passage_at_hour == expected_hour

        # check calculated properties based on business rules
        assert result.kenteken_land == expected_kenteken_land
        assert result.inrichting == expected_inrichting
        assert (
            result.voertuig_klasse_toegestaan_gewicht
            == expected_klasse_toegestaan_gewicht
        )

        # check helper table data
        helper_fields = [
            'order_kaart',
            'order_naam',
            'cordon',
            'richting',
            'location',
            'geom',
            'azimuth',
        ]
        for attr in helper_fields:
            assert getattr(result, attr) == getattr(helper_table_row, attr)

        # check the most important (calculated) attribute: intensity
        assert result.intensiteit == 10

    def _get_expected_dow(self, timestamp):
        """
        Get the expected day of week
        """
        dow = timestamp.weekday()
        if dow == 0:
            return '1 maandag'
        elif dow == 1:
            return '2 dinsdag'
        elif dow == 2:
            return '3 woensdag'
        elif dow == 3:
            return '4 donderdag'
        elif dow == 4:
            return '5 vrijdag'
        elif dow == 5:
            return '6 zaterdag'
        elif dow == 6:
            return '7 zondag'
        return 'onbekend'

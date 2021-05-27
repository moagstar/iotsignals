import logging
import time
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db.models import Case, F, Max, Min, Value, When
from django.db.models.functions import TruncDay, TruncYear
from passage.models import Passage

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--sleep', nargs='?', default=1, type=int)

    def handle(self, **options):
        verbosity = int(options['verbosity'])
        logger.info("message")

        sleep = options['sleep']

        dates = Passage.objects.all().aggregate(
            min=TruncDay(Min('passage_at')), max=TruncDay(Max('passage_at'))
        )

        for date in (
            dates['min'] + timedelta(n)
            for n in range((dates['max'] - dates['min']).days)
        ):
            self.stdout.write(f"Selecting data in: {self.style.SQL_KEYWORD(date)}")
            num_updated_rows = Passage.objects.filter(
                passage_at__gte=date,
                passage_at__lt=date + timedelta(days=1),
            ).exclude(privacy_check=True).update(
                datum_eerste_toelating=TruncYear('datum_eerste_toelating'),
                datum_tenaamstelling=Value(None),
                toegestane_maximum_massa_voertuig=Case(
                    When(toegestane_maximum_massa_voertuig__lte=3500, then=Value(1500)),
                    default=F('toegestane_maximum_massa_voertuig'),
                ),
                europese_voertuigcategorie_toevoeging=Case(
                    When(toegestane_maximum_massa_voertuig__lte=3500, then=Value(None)),
                    default=F('europese_voertuigcategorie_toevoeging'),
                ),
                inrichting=Case(
                    When(
                        voertuig_soort__iexact='personenauto',
                        then=Value('Personenauto'),
                    ),
                    default=F('inrichting'),
                ),
                merk=Case(
                    When(toegestane_maximum_massa_voertuig__lte=3500, then=Value(None)),
                    default=F('merk'),
                ),
                privacy_check=True,
            )
            self.stdout.write('Processed: ' + self.style.SUCCESS(num_updated_rows))
            self.stdout.write('sleeping for: ' + self.style.SUCCESS(sleep))
            time.sleep(sleep)

        self.stdout.write(self.style.SUCCESS('Finished'))

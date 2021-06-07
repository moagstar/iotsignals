import logging
import time
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import connection
from django.db.models import Case, F, Max, Min, Value, When
from django.db.models.functions import TruncDay, TruncYear
from django.db.utils import ProgrammingError
from passage.models import Passage

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--sleep', nargs='?', default=1, type=int)

    def handle(self, **options):
        verbosity = int(options['verbosity'])
        logger.info("message")

        sleep = options['sleep']

        dates = Passage.objects.aggregate(
            min=TruncDay(Min('passage_at')), max=TruncDay(Max('passage_at'))
        )

        print(dates)
        if not dates['min']:
            self.stdout.write('No data to be processed')
            return

        date_min = dates['min'] + timedelta(days=1)
        date_max = dates['max'] + timedelta(days=2)

        for date in (
            date_min + timedelta(n) for n in range((date_max - date_min).days)
        ):
            self.stdout.write(f"Selecting data in: {self.style.SQL_KEYWORD(date)}")
            num_updated_rows = Passage.objects.filter(
                passage_at__gte=date,
                passage_at__lt=date + timedelta(days=1),
            ).update(
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
            )
            self.stdout.write(f'Processed: {self.style.SUCCESS(num_updated_rows)}')

            if num_updated_rows > 0:
                self.stdout.write(f'sleeping for: {self.style.SUCCESS(sleep)}')
                time.sleep(sleep)
            else:
                self.stdout.write(f'sleeping for: {self.style.SUCCESS(0.1)}')
                time.sleep(0.1)

            partition_name = f'passage_passage_{date:%Y%m%d}'
            vacuum_query = f'VACUUM FULL ANALYZE {partition_name}'
            self.stdout.write(f'Starting vacuum: {vacuum_query}')
            try:
                with connection.cursor() as cursor:
                    cursor.execute(vacuum_query)
            except ProgrammingError as e:
                self.stderr.write(f'Error vacuuming: {e}')
            self.stdout.write(f'sleeping for: {self.style.SUCCESS(sleep)}')
            time.sleep(sleep)

        self.stdout.write(self.style.SUCCESS('Finished'))

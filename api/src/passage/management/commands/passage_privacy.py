import logging
import time

from django.core.management.base import BaseCommand
from django.db.models import Case, F, Value, When
from django.db.models.functions import Greatest, TruncYear
from django.forms import model_to_dict
from passage.models import Passage

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--batch-size', nargs='?', default=1000, type=int)
        parser.add_argument('--sleep', nargs='?', default=1, type=int)

    def handle(self, **options):
        verbosity = int(options['verbosity'])
        logger.info("message")

        batch_size = options['batch_size']
        sleep = options['sleep']

        while batch := self.get_batch(batch_size):
            qs = Passage.objects.filter(pk__in=batch).update(
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
                privacy_check=True
            )
            self.stdout.write('Processed: ' + self.style.SUCCESS(qs))
            self.stdout.write('sleeping for: ' + self.style.SUCCESS(sleep))
            time.sleep(sleep)

        self.stdout.write(self.style.SUCCESS('Finished'))

    def get_batch(self, size):
        return Passage.objects.filter(privacy_check=False).values('pk')[0:size]

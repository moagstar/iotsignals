import logging
from datetime import date

from datapunt_api.rest import DisplayField, HALSerializer
from django.db import IntegrityError
from rest_framework import serializers

from .errors import DuplicateIdError
from .models import Passage

log = logging.getLogger(__name__)


class PassageSerializer(HALSerializer):

    _display = DisplayField()

    class Meta:
        model = Passage
        fields = [
            '_display',
            '_links',
            'id',
            'versie',
            'merk',
            'created_at',
            'passage_at',
        ]


class PassageDetailSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(
        validators=[]
    )  # Disable the validators for the id, which improves performance (rps) by over 200%

    class Meta:
        model = Passage
        fields = '__all__'

    def create(self, validated_data):
        try:
            return super().create(validated_data)
        except IntegrityError as e:
            log.info(f"DuplicateIdError for id {validated_data['id']}")
            raise DuplicateIdError(str(e))

    def validate_datum_eerste_toelating(self, value):
        return date(year=value.year, month=1, day=1)

    def validate_datum_tenaamstelling(self, value):
        return None

    def validate_toegestane_maximum_massa_voertuig(self, value):
        if value <= 3500:
            return 1500
        return value

    def validate(self, data):
        if 'toegestane_maximum_massa_voertuig' in data:
            if data['toegestane_maximum_massa_voertuig'] <= 3500:
                data['europese_voertuigcategorie_toevoeging'] = None
                data['merk'] = None

        if 'voertuig_soort' in data:
            if data['voertuig_soort'].lower() == 'personenauto':
                data['inrichting'] = 'Personenauto'

        return data

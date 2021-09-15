import logging
from datetime import date

from datapunt_api.rest import DisplayField, HALSerializer
from django.db import IntegrityError
from rest_framework import serializers

from .errors import DuplicateIdError
from .models import Passage, PassageCamera, PassageVehicle

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


class PassageCameraSerializer(serializers.ModelSerializer):
    class Meta:
        model = PassageCamera
        exclude = 'id',


class PassageVehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = PassageVehicle
        exclude = 'id',

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


class PassageDetailSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(
        validators=[]
    )  # Disable the validators for the id, which improves performance (rps) by over 200%

    class Meta:
        model = Passage
        fields = '__all__'

    def create_related(self, validated_data, serializer):
        """

        """
        fields = {x.name for x in serializer.Meta.model._meta.fields}
        data = {k: v for k, v in validated_data.items() if k in fields}
        s = serializer(data=data)
        s.is_valid(raise_exception=True)
        return s.save()

    def create(self, validated_data):
        try:
            passage_camera = self.create_related(validated_data, PassageCameraSerializer)
            passage_vehicle = self.create_related(validated_data, PassageVehicleSerializer)
            validated_data = dict(
                validated_data,
                passage_camera=passage_camera,
                passage_vehicle=passage_vehicle,
            )
            return super().create(validated_data)
        except IntegrityError as e:
            log.info(f"DuplicateIdError for id {validated_data['id']}")
            raise DuplicateIdError(str(e))
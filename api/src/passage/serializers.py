import logging
from datetime import date

from datapunt_api.rest import DisplayField, HALSerializer
from django.db import IntegrityError
from django.db.transaction import atomic
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
        exclude = 'id', 'hash',


class PassageVehicleSerializer(serializers.ModelSerializer):

    class Meta:
        model = PassageVehicle
        exclude = 'id', 'hash',

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

    def _create_related(self, serializer_cls):
        # need to use ``intitial_data`` since ``validated_data`` only contains
        # fields from the Passage model
        s = serializer_cls(data=self.initial_data)
        s.is_valid(raise_exception=True)
        return s.save()

    def create(self, validated_data):
        try:
            with atomic():

                passage_camera = self._create_related(PassageCameraSerializer)
                passage_vehicle = self._create_related(PassageVehicleSerializer)

                validated_data = dict(
                    validated_data,
                    passage_camera_id=passage_camera.id,
                    passage_vehicle_id=passage_vehicle.id,
                )

            return super().create(validated_data)
        except IntegrityError as e:
            log.info(f"DuplicateIdError for id {validated_data['id']}")
            raise DuplicateIdError(str(e))
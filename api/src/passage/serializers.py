import logging

from datapunt_api.rest import DisplayField, HALSerializer
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from rest_framework import serializers

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
    id = serializers.UUIDField(validators=[])  # Disable the validators for the id, which improves performance (rps) by over 200%

    class Meta:
        model = Passage
        fields = '__all__'

    def create(self, validated_data):
        try:
            return super().create(validated_data)
        except IntegrityError as e:
            log.error(f"ValidationError for id {validated_data['id']}")
            raise ValidationError(str(e))

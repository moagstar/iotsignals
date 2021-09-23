import json
import logging
from datetime import date
from hashlib import sha1, md5

from datapunt_api.rest import DisplayField, HALSerializer
from django.core.cache import cache
from django.db import IntegrityError
from django.db.transaction import atomic
from rest_framework import serializers
from rest_framework.renderers import JSONRenderer

from .errors import DuplicateIdError
from .models import Passage, PassageCamera, PassageVehicle
from .util import profile

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


class AppendOnlyModelSerializer(serializers.ModelSerializer):

    class Meta:
        exclude = 'id', 'hash',

    @classmethod
    def _data_for_hash(cls, data):
        return {
            key: value
            for key, value in data.items()
            if key in {field.name for field in cls.Meta.model._meta.fields}
            if key not in cls.Meta.exclude
        }

    @classmethod
    def hash(cls, data):
        data_for_hash = cls._data_for_hash(data)
        rendered = json.dumps(data_for_hash, sort_keys=True, separators=(',', ':')).encode()
        return md5(rendered).hexdigest()


class PassageCameraSerializer(AppendOnlyModelSerializer):
    class Meta(AppendOnlyModelSerializer.Meta):
        model = PassageCamera

    @classmethod
    def _data_for_hash(cls, data):
        return {
            **super()._data_for_hash(data),
            'camera_locatie': None,
        }


class PassageVehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = PassageVehicle


class PassageDetailSerializer(serializers.ModelSerializer):

    id = serializers.UUIDField(
        validators=[]
    )  # Disable the validators for the id, which improves performance (rps) by over 200%

    class Meta:
        model = Passage
        fields = '__all__'

    def _get_or_create_related_id(self, serializer_cls):
        """
        Get the id of a related object (camera or vehicle).

        :param serializer_cls: The class which should be used to serialize the
                               object (only used when the object does not yet
        """
        model = serializer_cls.Meta.model

        # Calculate a hash of the data so we can determine if this object
        # already exists in the database. We can use the hash as a cache key
        # so that most of the time we don't even need to hit the database to
        # determine if the object exists or not.

        # Check first the cache, then the database to see if the object exists,
        # only when a camera / vehicle without these properties has not already
        # been added do we need to perform a save.
        if True:#(id := cache.get(hash)) is None:
            id = next(iter(model.objects.filter(hash=hash).values_list('id', flat=True)), None)
            if id is None:
                s = serializer_cls(data=self.initial_data)
                s.is_valid(raise_exception=True)
                id = s.save(hash=hash).id
            #cache.set(hash, id)

        return id

    def create(self, validated_data):
        try:
            validated_data = dict(
                validated_data,
                passage_camera_id=self._get_or_create_related_id(PassageCameraSerializer),
                passage_vehicle_id=self._get_or_create_related_id(PassageVehicleSerializer),
            )
            return super().create(validated_data)
        except IntegrityError as e:
            log.info(f"DuplicateIdError for id {validated_data['id']}")
            raise DuplicateIdError(str(e))

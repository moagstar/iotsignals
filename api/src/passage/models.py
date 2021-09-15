# std
import json
from functools import partial
from hashlib import sha1
# 3rd party
from typing import Type, Callable, TypeVar

from datetimeutc.fields import DateTimeUTCField
from django.contrib.postgres.fields import JSONField
from django.core.validators import MaxValueValidator, MinValueValidator
from django.contrib.gis.db import models
from rest_framework.renderers import JSONRenderer
from unittest.mock import patch

from rest_framework.serializers import Serializer


C = TypeVar('C')


class AppendOnlyModel(models.Model):
    """
    Append only model, the primary key consists of a sha1 hash digest of the
    contents. It is therefore not possible to update exist records. Care must
    be taken with migrations which add or remove fields
    """

    id = models.CharField(max_length=40, primary_key=True, unique=True)

    def _do_insert(self, manager, using, fields, update_pk, raw):
        # override _do_insert to ensure we ignore any conflicts which would
        # occur when this entity already exists in the database - we don't
        # get much control over this, it would be nice to specify that it is
        # only the pk conflict which we should ignore (this should be possible
        # in postgres, but is not exposed by django).
        return manager._insert([self], fields=fields, return_id=update_pk,
                               using=using, raw=raw, ignore_conflicts=True)

    def save(self, *args, **kwargs):

        serializer_factory = self._get_serializer_factory()
        serializer = serializer_factory(self)

        # rest_framework JSONRenderer does not support the sort_keys argument
        # for json.dumps (see https://github.com/encode/django-rest-framework/pull/8166)
        # but we want a stable serialisation, regardless of the key order. Once
        # sort_keys is supported we could remove this nasty patching
        with patch('rest_framework.renderers.json.dumps', partial(json.dumps, sort_keys=True)):
            serialized = JSONRenderer().render(serializer.data)
            self.id = sha1(serialized).hexdigest()

        return super().save(*args, **kwargs)

    class Meta:
        abstract = True

    @classmethod
    def _get_serializer_factory(cls: C) -> Callable[[Type[C]], Serializer]:
        """
        Return the factory for generating a serialiser for serializing instances
        of `cls`

        In order to generate the id (which is calculated based on the content)
        we need to be able to serialize instances of `cls`.
        """
        raise NotImplementedError()


class PassageCamera(AppendOnlyModel):
    """
    Fields relating to the camera that made a measurement.
    """
    straat = models.CharField(max_length=255, null=True)
    rijrichting = models.SmallIntegerField()
    rijstrook = models.SmallIntegerField()
    # not the primary key - but a unique identifier of the camera equipment itself
    camera_id = models.CharField(max_length=255)
    camera_naam = models.CharField(max_length=255)
    camera_kijkrichting = models.FloatField()
    camera_locatie = models.PointField(srid=4326)

    @classmethod
    def _get_serializer_factory(cls: C) -> Callable[[Type[C]], Serializer]:
        # prevent circular import
        from passage.serializers import PassageCameraSerializer
        return PassageCameraSerializer


class PassageVehicle(AppendOnlyModel):
    """
    Fields relating to the vehicle from a measurement.
    """
    kenteken_land = models.CharField(max_length=2)
    voertuig_soort = models.CharField(max_length=25, null=True)
    merk = models.CharField(max_length=255, null=True)
    inrichting = models.CharField(max_length=255, null=True)
    datum_eerste_toelating = models.DateField(null=True)
    datum_tenaamstelling = models.DateField(null=True)
    toegestane_maximum_massa_voertuig = models.IntegerField(null=True)
    europese_voertuigcategorie = models.CharField(max_length=2, null=True)
    europese_voertuigcategorie_toevoeging = models.CharField(max_length=1, null=True)
    taxi_indicator = models.NullBooleanField()
    maximale_constructie_snelheid_bromsnorfiets = models.SmallIntegerField(null=True)

    # fuel properties
    brandstoffen = JSONField(null=True)
    extra_data = JSONField(null=True)
    diesel = models.SmallIntegerField(null=True)
    gasoline = models.SmallIntegerField(null=True)
    electric = models.SmallIntegerField(null=True)

    # TNO Versit klasse.
    # Zie ook: https://www.tno.nl/media/2451/lowres_tno_versit.pdf
    versit_klasse = models.CharField(null=True, max_length=255)

    @classmethod
    def _get_serializer_factory(cls: C) -> Callable[[Type[C]], Serializer]:
        # prevent circular import
        from passage.serializers import PassageVehicleSerializer
        return PassageVehicleSerializer


class Passage(models.Model):
    """Passage measurement.

    Each passing of a vehicle with a license plate passes into
    an environment zone which passes an environment camera
    should result in a record here.
    """
    id = models.UUIDField(primary_key=True, unique=True)
    passage_at = DateTimeUTCField(db_index=True, null=False)
    created_at = DateTimeUTCField(db_index=True, auto_now_add=True, editable=False)

    version = models.CharField(max_length=20)

    kenteken_nummer_betrouwbaarheid = models.SmallIntegerField(
        validators=[MaxValueValidator(1000), MinValueValidator(0)]
    )
    kenteken_land_betrouwbaarheid = models.SmallIntegerField(
        validators=[MaxValueValidator(1000), MinValueValidator(0)]
    )
    kenteken_karakters_betrouwbaarheid = JSONField(null=True)
    indicatie_snelheid = models.FloatField(null=True)
    automatisch_verwerkbaar = models.NullBooleanField()

    passage_camera = models.ForeignKey(PassageCamera, on_delete=models.PROTECT, null=True)
    passage_vehicle = models.ForeignKey(PassageVehicle, on_delete=models.PROTECT, null=True)


class PassageHourAggregation(models.Model):
    date = models.DateField()
    year = models.IntegerField()
    month = models.IntegerField()
    day = models.IntegerField()
    week = models.IntegerField()
    dow = models.IntegerField()  # day of week
    hour = models.IntegerField()
    camera_id = models.CharField(max_length=255)
    camera_naam = models.CharField(max_length=255)
    rijrichting = models.IntegerField()
    camera_kijkrichting = models.FloatField()
    kenteken_land = models.TextField()
    voertuig_soort = models.CharField(max_length=25, null=True)
    europese_voertuigcategorie = models.CharField(max_length=2, null=True)
    taxi_indicator = models.NullBooleanField()
    diesel = models.IntegerField(null=True)
    gasoline = models.IntegerField(null=True)
    electric = models.IntegerField(null=True)
    toegestane_maximum_massa_voertuig = models.TextField()
    count = models.IntegerField()


class Camera(models.Model):
    camera_naam = models.CharField(max_length=255, db_index=True)
    rijrichting = models.IntegerField(null=True, blank=True, db_index=True)
    camera_kijkrichting = models.FloatField(null=True, blank=True, db_index=True)

    order_kaart = models.IntegerField(null=True, blank=True)     # in sheet: volgorde
    order_naam = models.CharField(max_length=255, null=True, blank=True)      # in sheet: straatnaam
    cordon = models.CharField(max_length=255, db_index=True, null=True, blank=True)
    richting = models.CharField(max_length=10, null=True, blank=True)
    location = models.PointField(srid=4326, null=True, blank=True)
    geom = models.CharField(max_length=255, null=True, blank=True)
    azimuth = models.FloatField(null=True, blank=True)


class HeavyTrafficHourAggregation(models.Model):
    passage_at_timestamp = DateTimeUTCField()
    passage_at_date = models.DateField()
    passage_at_year = models.IntegerField()
    passage_at_month = models.IntegerField()
    passage_at_day = models.IntegerField()
    passage_at_week = models.IntegerField()
    passage_at_day_of_week = models.CharField(max_length=20)  # day of week
    passage_at_hour = models.IntegerField()

    order_kaart = models.IntegerField(null=True, blank=True)  # in sheet: volgorde
    order_naam = models.CharField(max_length=255, null=True, blank=True)  # in sheet: straatnaam
    cordon = models.CharField(max_length=255, db_index=True, null=True, blank=True)
    richting = models.CharField(max_length=3, null=True, blank=True)
    location = models.PointField(srid=4326, null=True, blank=True)
    geom = models.CharField(max_length=255, null=True, blank=True)
    azimuth = models.FloatField()

    kenteken_land = models.TextField()
    voertuig_soort = models.CharField(max_length=25, null=True)
    inrichting = models.CharField(max_length=255, null=True)
    voertuig_klasse_toegestaan_gewicht = models.CharField(max_length=255, null=True, blank=True)
    intensiteit = models.IntegerField(null=True, blank=True)

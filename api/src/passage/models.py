# std
import json
from collections import OrderedDict, defaultdict
from hashlib import sha1
# 3rd party
from typing import Type, Callable
from datetimeutc.fields import DateTimeUTCField
from django.contrib.postgres.fields import JSONField, ArrayField
from django.core.validators import MaxValueValidator, MinValueValidator
from django.contrib.gis.db import models
from rest_framework.renderers import JSONRenderer
from django.core.cache import cache


class AppendOnlyModel(models.Model):
    """
    Append only model, the primary key consists of a sha1 hash digest of the
    contents. It is therefore not possible to update exist records. Care must
    be taken with migrations which add or remove fields
    """
    hash = models.CharField(max_length=40, unique=True)

    class Meta:
        abstract = True

    @classmethod
    def _get_serializer_factory(cls):
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
    def _get_serializer_factory(cls):
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
    automatisch_verwerkbaar = models.NullBooleanField()

    # fuel properties
    brandstoffen = JSONField(null=True)
    extra_data = JSONField(null=True)
    diesel = models.SmallIntegerField(null=True)
    gasoline = models.SmallIntegerField(null=True)
    electric = models.SmallIntegerField(null=True)

    # TNO Versit klasse.
    # Zie ook: https://www.tno.nl/media/2451/lowres_tno_versit.pdf
    versit_klasse = models.CharField(null=True, max_length=255)

    # new fields
    pseudokenteken = models.CharField(max_length=255, null=True)
    vervaldatum_apk = models.DateField(null=True)
    wam_verzekerd = models.NullBooleanField()
    massa_ledig_voertuig = models.SmallIntegerField(null=True)
    aantal_assen = models.SmallIntegerField(null=True)
    aantal_staanplaatsen = models.SmallIntegerField(null=True)
    aantal_wielen = models.SmallIntegerField(null=True)
    aantal_zitplaatsen = models.SmallIntegerField(null=True)
    handelsbenaming = models.CharField(max_length=255, null=True)
    lengte = models.SmallIntegerField(null=True)
    breedte = models.SmallIntegerField(null=True)
    maximum_massa_trekken_ongeremd = models.FloatField(null=True)
    maximum_massa_trekken_geremd = models.FloatField(null=True)
    co2_uitstoot_gecombineerd = models.FloatField(null=True)
    co2_uitstoot_gewogen = models.FloatField(null=True)
    milieuklasse_eg_goedkeuring_zwaar = models.CharField(max_length=255, null=True)

    @classmethod
    def _get_serializer_factory(cls):
        # prevent circular import
        from passage.serializers import PassageVehicleSerializer
        return PassageVehicleSerializer


class BetrouwbaarheidField(models.SmallIntegerField):
    def __init__(self, *args, **kwargs):
        kwargs['validators'] = [MaxValueValidator(1000), MinValueValidator(0)]
        super().__init__(*args, **kwargs)


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

    kenteken_nummer_betrouwbaarheid = BetrouwbaarheidField()
    kenteken_land_betrouwbaarheid = BetrouwbaarheidField()
    kenteken_karakters_betrouwbaarheid = ArrayField(BetrouwbaarheidField(), null=True)
    indicatie_snelheid = models.FloatField(null=True)

    passage_camera = models.ForeignKey(PassageCamera, null=True, on_delete=models.PROTECT)
    passage_vehicle = models.ForeignKey(PassageVehicle, null=True, on_delete=models.PROTECT)


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

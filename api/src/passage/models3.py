import json
from hashlib import sha1

from datetimeutc.fields import DateTimeUTCField
from django.contrib.postgres.fields import JSONField
from django.core.validators import MaxValueValidator, MinValueValidator
from django.contrib.gis.db import models


# Step 1: Introduce foreign keys for camera and vehicle, let the API fill those
# Step 2: Back fill old foreign key values
# Step 3: Make the API + aggregation script use foreign keys
# Step 4: Remove camera + vehicle properties from Passage model
# Step 5: Expose new POST API, this just maps the new values to the old ones
# Step 6: Introduce new fields


class AppendOnlyModel(models.Model):

class Test(models.Model):
    id = models.IntegerField(primary_key=True, unique=True)
    hash = models.IntegerField(unique=True)

    class Meta:
        managed = False
        db_table = 'test'

class PassageEntity(models.Model):

    id = models.UUIDField(primary_key=True, unique=True)
    hash_digest = models.CharField(max_length=40, unique=True)

    @classmethod
    def get_or_create(cls, *args, **kwargs):
        """
        Create an instance of this model in the database, and return the
        database id. When a conflict occurs because the object already exists,
        ignore the conflict (i.e. upsert behaviour).

        :return: instance of ``cls``
        """
        instance = cls(
            *args,
            **kwargs,
            hash_digest=sha1(json.dumps(kwargs, sort_keys=True).encode()).hexdigest(),
        )
        return cls.objects.bulk_create([instance], ignore_conflicts=True)[0]

    class Meta:
        abstract = True


class PassageCamera(PassageEntity):
    """

    """
    straat = models.CharField(max_length=255, null=True)
    rijrichting = models.SmallIntegerField()
    rijstrook = models.SmallIntegerField()
    # not the primary key - but a unique identifier of the camera equipment itself
    identifier = models.CharField(max_length=255)
    naam = models.CharField(max_length=255)
    kijkrichting = models.FloatField()
    locatie = models.PointField(srid=4326)


class PassageVehicle(PassageEntity):
    """

    """
    kenteken_land = models.CharField(max_length=2)
    automatisch_verwerkbaar = models.NullBooleanField()
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

    # camera properties
    straat = models.CharField(max_length=255, null=True)
    rijrichting = models.SmallIntegerField()
    rijstrook = models.SmallIntegerField()
    camera_id = models.CharField(max_length=255)
    camera_naam = models.CharField(max_length=255)
    camera_kijkrichting = models.FloatField()
    camera_locatie = models.PointField(srid=4326)

    # car properties
    kenteken_land = models.CharField(max_length=2)
    kenteken_nummer_betrouwbaarheid = models.SmallIntegerField(
        validators=[MaxValueValidator(1000), MinValueValidator(0)]
    )
    kenteken_land_betrouwbaarheid = models.SmallIntegerField(
        validators=[MaxValueValidator(1000), MinValueValidator(0)]
    )
    kenteken_karakters_betrouwbaarheid = JSONField(null=True)
    indicatie_snelheid = models.FloatField(null=True)
    automatisch_verwerkbaar = models.NullBooleanField()
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

    # camera + vehicle properties
    camera = models.ForeignKey(PassageCamera, on_delete=models.DO_NOTHING, null=True)
    vehicle = models.ForeignKey(PassageVehicle, on_delete=models.DO_NOTHING, null=True)


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

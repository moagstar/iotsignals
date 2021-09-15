from datetimeutc.fields import DateTimeUTCField
from django.contrib.gis.db.models import PointField
from django.contrib.postgres.fields import JSONField
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


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

    # camera properties (from /camera)
    straat = models.CharField(max_length=255, null=True)
    rijrichting = models.SmallIntegerField(choices=[(1, 'VAN'), (2, 'NAAR')])  # add choices (VAN, NAAR) old value was integer, which is correct?
    rijstrook = models.SmallIntegerField()
    camera_id = models.CharField(max_length=255)  # needs "camera" prefix
    camera_naam = models.CharField(max_length=255)  # needs "camera" prefix
    camera_kijkrichting = models.FloatField()  # needs "camera" prefix
    camera_locatie = PointField(srid=4326)  # longitude + latitude need to be retrieved from "locatie"

    # car properties - kenteken (from /voertuig/kenteken)
    # pseudokenteken - slaan we nu niet op, privacy?
    kenteken_land = models.CharField(max_length=2)  # from "/voertuig/kenteken/landcode"
    kenteken_nummer_betrouwbaarheid = models.SmallIntegerField(
        validators=[MaxValueValidator(1000), MinValueValidator(0)]
    )  # from /voertuig/kenteken/kentekenBetrouwbaarheid
    kenteken_land_betrouwbaarheid = models.SmallIntegerField(
        validators=[MaxValueValidator(1000), MinValueValidator(0)]
    )  # from /voertuig/kenteken/landcodeBetrouwbaarheid
    kenteken_karakters_betrouwbaarheid = JSONField(null=True)  # from /voertuig/kenteken/karaktersBetrouwbaarheid

    # car properties - vehicle (new fields)
    jaar_eerste_toelating = models.PositiveIntegerField()  # see comment datum_eerste_toelating
    vervaldatum_apk = models.DateField()
    wam_verzekerd = models.BooleanField()
    massa_ledig_voertuig = models.PositiveIntegerField()
    aantal_assen = models.PositiveSmallIntegerField()
    aantal_staanplaatsen = models.PositiveSmallIntegerField()
    aantal_wielen = models.PositiveSmallIntegerField()
    aantal_zitplaatsen = models.PositiveSmallIntegerField()
    handelsbenaming = models.CharField(max_length=255, null=True)
    lengte = models.PositiveIntegerField(null=True)
    breede = models.PositiveIntegerField(null=True)
    maximum_massa_trekken_ongeremd = models.PositiveIntegerField(null=True)
    maximum_massa_trekken_geremd = models.PositiveIntegerField(null=True)

    # car properties - vehicle
    automatisch_verwerkbaar = models.NullBooleanField()
    voertuig_soort = models.CharField(max_length=25, null=True)
    merk = models.CharField(max_length=255, null=True)
    inrichting = models.CharField(max_length=255, null=True)
    datum_eerste_toelating = models.DateField(null=True)  # this has become jaar_eerste_toelating (can we keep this fiela and just use 01-01-year?)
    datum_tenaamstelling = models.DateField(null=True)    # field is removed
    toegestane_maximum_massa_voertuig = models.IntegerField(null=True)
    europese_voertuigcategorie = models.CharField(max_length=2, null=True)
    europese_voertuigcategorie_toevoeging = models.CharField(max_length=1, null=True)
    taxi_indicator = models.NullBooleanField()
    maximale_constructie_snelheid_bromsnorfiets = models.SmallIntegerField(null=True)

    # car properties - fuel
    brandstoffen = JSONField(null=True)
    extra_data = JSONField(null=True)  # field no longer present
    diesel = models.SmallIntegerField(null=True)  # field no longer present
    gasoline = models.SmallIntegerField(null=True)  # field no longer present
    electric = models.SmallIntegerField(null=True)  # field no longer present

    # car properties - new fields
    co2_uitstoot_gecombineerd = models.PositiveIntegerField(null=True)
    co2_uitstoot_gewogen = models.PositiveIntegerField(null=True)
    milieuklasse_eg_goedkeuring_zwaar = models.CharField(max_length=255, null=True)

    # passage properties
    indicatie_snelheid = models.FloatField(null=True)

    # TNO Versit klasse.
    # Zie ook: https://www.tno.nl/media/2451/lowres_tno_versit.pdf
    versit_klasse = models.CharField(null=True, max_length=255)


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

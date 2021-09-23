# std
from functools import partial
from typing import Tuple, Type
# 3rd party
import pytest
from django.contrib.gis.geos import Point
from hypothesis import given, strategies as st
from rest_framework.serializers import ModelSerializer
# iotsignals
from passage.serializers import PassageCameraSerializer, PassageVehicleSerializer


st_optional = partial(st.one_of, st.none())
st_small_integers = partial(st.integers, min_value=-32768, max_value=32767)
st_ams_longitudes = partial(st.floats, 4.58565, 5.31360)
st_ams_latitudes = partial(st.floats, 52.03560, 52.48769)


@st.composite
def camera(draw, version=1):
    """
    Strategy which generates data pertaining to the Vehicle model.

    :param draw: Callable for drawing examples from other strategies.
    :param version: The version of the vehicle data to generate.

    :return: Dictionary containing vehicle information.
    """
    mapping = {
        'straat': st_optional(st.text(min_size=1, max_size=255)),
        'rijrichting': st_small_integers(),
        'rijstrook': st_small_integers(),
        'camera_id': st.uuids().map(str),
        'camera_naam': st.text(min_size=1, max_size=255),
        'camera_kijkrichting': st.floats(),
    }

    point_in_ams = st_ams_latitudes(),  st_ams_longitudes()
    if version == 1:
        camera_locatie_mapping = dict(zip(('latitude', 'longitude'), point_in_ams))
        mapping['camera_locatie'] = st.fixed_dictionaries(camera_locatie_mapping)
    else:
        mapping['camera_locatie'] = st.builds(Point, *point_in_ams)

    return draw(st.fixed_dictionaries(mapping))


@st.composite
def vehicle(draw, version=1):
    """
    Strategy which generates data pertaining to the Vehicle model.

    :param draw: Callable for drawing examples from other strategies.
    :param version: The version of the vehicle data to generate.

    :return: Dictionary containing vehicle information.
    """
    mapping = {
        'kenteken_land': st.text(min_size=1, max_size=2),
        'voertuig_soort': st_optional(st.text(min_size=1, max_size=25)),
        'merk': st_optional(st.text(min_size=1, max_size=255)),
        'inrichting': st_optional(st.text(min_size=1, max_size=255)),
        'datum_eerste_toelating': st_optional(st.dates()),
        'datum_tenaamstelling': st_optional(st.dates()),
        'toegestane_maximum_massa_voertuig': st_optional(st.integers()),
        'europese_voertuigcategorie': st_optional(st.text(min_size=1, max_size=2)),
        'europese_voertuigcategorie_toevoeging': st_optional(st.text(min_size=1, max_size=1)),
        'taxi_indicator': st_optional(st.booleans()),
        'maximale_constructie_snelheid_bromsnorfiets': st_optional(st_small_integers()),
        'automatisch_verwerkbaar': st_optional(st.booleans()),
        'brandstoffen': st_optional(st.lists(st.fixed_dictionaries({
            'volgnr': st_small_integers(),
            'brandstof': st.sampled_from(('Diesel', 'Electric', 'Gasoline')),
        }))),
        'extra_data': st.none(),
        'diesel': st_optional(st_small_integers()),
        'gasoline': st_optional(st_small_integers()),
        'electric': st_optional(st_small_integers()),
        'versit_klasse': st_optional(st.text(min_size=1, max_size=255)),
    }

    if version > 1:
        mapping.update(**{
            'pseudokenteken': st.text(min_size=1, max_size=255),
            'vervaldatum_apk': st.dates(),
            'wam_verzekerd': st.booleans(),
            'massa_ledig_voertuig': st_small_integers(),
            'aantal_assen': st_small_integers(),
            'aantal_staanplaatsen': st_small_integers(),
            'aantal_wielen': st_small_integers(),
            'aantal_zitplaatsen': st_small_integers(),
            'handelsbenaming': st.text(min_size=1, max_size=255),
            'lengte': st_small_integers(),
            'breedte': st_small_integers(),
            'maximum_massa_trekken_ongeremd': st.floats(),
            'maximum_massa_trekken_geremd': st.floats(),
            'co2_uitstoot_gecombineerd': st.floats(),
            'co2_uitstoot_gewogen': st.floats(),
            'milieuklasse_eg_goedkeuring_zwaar': st.text(min_size=1, max_size=255),
        })

    return draw(st.fixed_dictionaries(mapping))


@st.composite
def message(draw, version=1):
    pass


@given(st.one_of(
    st.tuples(vehicle(), st.just(PassageVehicleSerializer)),
    st.tuples(camera(), st.just(PassageCameraSerializer)),
))
@pytest.mark.django_db
def test_sql_produces_same_hash_as_python(test_data: Tuple[dict, Type[ModelSerializer]]):
    data, serializer_cls = test_data
    serializer = serializer_cls(data=data)
    serializer.is_valid(raise_exception=True)
    serializer_cls.Meta.model.objects.all().delete()
    try:
        serializer.save()
    except Exception as e:
        raise

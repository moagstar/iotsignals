import json
from functools import partial
from typing import Tuple, Type

import pytest
from hypothesis import given, strategies as st
from hypothesis.extra.django import from_model
from rest_framework.serializers import ModelSerializer

from passage.models import PassageCamera, PassageVehicle
from passage.serializers import PassageCameraSerializer, PassageVehicleSerializer


st_optional = partial(st.one_of, st.none())
st_small_integers = partial(st.integers, min_value=-32768, max_value=32767)


@st.composite
def camera(draw):
    return draw(st.fixed_dictionaries({
        'straat': st_optional(st.text(max_size=255)),
        'rijrichting': st_small_integers(),
        'rijstrook': st_small_integers(),
        'camera_id': st.uuids().map(str),
        'camera_naam': st.text(max_size=255),
        'camera_kijkrichting': st.floats(),
        #'camera_locatie': st_points(),
    }))


@st.composite
def vehicle(draw):
    return draw(st.fixed_dictionaries({
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
    }))


@given(st.one_of(
    st.tuples(vehicle(), st.just(PassageVehicleSerializer)),
    st.tuples(camera(), st.just(PassageCameraSerializer)),
))
@pytest.mark.django_db
def test_sql_produces_same_hash_as_python(test_data: Tuple[dict, Type[ModelSerializer]]):
    data, serializer_cls = test_data
    serializer = serializer_cls(data=data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    print(data)

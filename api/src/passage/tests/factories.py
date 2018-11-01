import random
import json
import datetime
import factory
from django.contrib.gis.geos import Point
from factory import fuzzy
from ..models import Passage

# Amsterdam.
BBOX = [52.03560, 4.58565, 52.48769, 5.31360]


def get_puntje():
    lat = fuzzy.FuzzyFloat(BBOX[0], BBOX[2]).fuzz()
    lon = fuzzy.FuzzyFloat(BBOX[1], BBOX[3]).fuzz()
    return Point(float(lat), float(lon)).__str__()


def get_data():
    return DataFactory()


def get_kenteken_karakter_betrouwbaarheid():
    char_list = []
    for n in range(6):
        char_list.append({
            'betrouwbaarheid': random.randint(1, 1000),
            'positie': n
        })
    return char_list


def get_brandstoffen():
    return [{
        'brandstof': 'Benzine',
        'volgnr': 1
    }]


class DataFactory(factory.DictFactory):
    datum_tijd = fuzzy.FuzzyDate(datetime.date(2008, 1, 1)).__str__()
    straat = factory.Faker('name')
    rijstrook = fuzzy.FuzzyInteger(1, 10)
    rijrichting = fuzzy.FuzzyInteger(-1, 1)
    camera_id = factory.Faker('uuid4')
    camera_naam = factory.Faker('name')
    camera_kijkrichting = fuzzy.FuzzyInteger(0, 400)
    camera_locatie = get_puntje()


class PassageFactory(factory.DjangoModelFactory):

    class Meta:
        model = Passage

    id = factory.Faker('uuid4')
    versie = "passage-v1"
    data = get_data()
    kenteken_land = fuzzy.FuzzyText(length=2)
    kenteken_nummer_betrouwbaarheid = fuzzy.FuzzyInteger(1, 1000)
    kenteken_land_betrouwbaarheid = fuzzy.FuzzyInteger(1.0, 1000.0, 1)
    kenteken_karakters_betrouwbaarheid = get_kenteken_karakter_betrouwbaarheid()
    indicatie_snelheid = fuzzy.FuzzyDecimal(0, 500)
    automatisch_verwerkbaar = factory.Faker('boolean', chance_of_getting_true=50)
    voertuig_soort = random.choice(['Personenauto', 'Bromfiets', 'Bedrijfsauto', 'Bus'])
    merk = factory.Faker('first_name')
    inrichting = factory.Faker('first_name')
    datum_eerste_toelating = fuzzy.FuzzyDate(datetime.date(2008, 1, 1))
    datum_tenaamstelling = fuzzy.FuzzyDate(datetime.date(2008, 1, 1))
    toegestane_maximum_massa_voertuig = fuzzy.FuzzyInteger(1, 32000)
    europese_voertuig_categorie = fuzzy.FuzzyText(length=2)
    europese_voertuig_categorie_toevoeging = fuzzy.FuzzyText(length=1)
    tax_indicator = factory.Faker('boolean', chance_of_getting_true=50)
    maximale_constructie_snelheid_bromsnorfiets = fuzzy.FuzzyInteger(0, 500)
    brandstoffen = get_brandstoffen()

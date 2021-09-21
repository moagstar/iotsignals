import requests
from uuid import uuid4
from locustfile import get_dt_with_tz_info

requests.post(
    'http://localhost:8001/v0/milieuzone/passage/',
    json={
        'id': str(uuid4()),
        'passage_at': get_dt_with_tz_info(),
        'created_at': get_dt_with_tz_info(),
        'version': '1',
        'kenteken_nummer_betrouwbaarheid': 516,
        'kenteken_land_betrouwbaarheid': 142,
        'kenteken_karakters_betrouwbaarheid': [
            {
                'positie': 0,
                'betrouwbaarheid': 288
            },
            {
                'positie': 1,
                'betrouwbaarheid': 143
            },
            {
                'positie': 2,
                'betrouwbaarheid': 773
            },
            {
                'positie': 3,
                'betrouwbaarheid': 97
            },
            {
                'positie': 4,
                'betrouwbaarheid': 633
            },
            {
                'positie': 5,
                'betrouwbaarheid': 818
            }
        ],
        'indicatie_snelheid': 32,
        'automatisch_verwerkbaar': False,
        'straat': 'JanvanGalenstraat',
        'rijrichting': '-1',
        'rijstrook': '-2',
        'camera_id': 'c7470af5-3e9f-49ed-b520-ad086b38aadc',
        'camera_naam': 'ANPR-01006-B - Rijstrook -2',
        'camera_kijkrichting': '270.0',
        'camera_locatie': '0101000020E6100000C093162EAB601340BA6B09F9A02F4A40',
        'kenteken_land': 'NL',
        'voertuig_soort': 'Personenauto',
        'inrichting': 'Personenauto',
        'datum_eerste_toelating': '2005-01-01',
        'toegestane_maximum_massa_voertuig': '1500',
        'europese_voertuigcategorie': 'M1',
        'taxi_indicator': False,
        'brandstoffen': [
            {
                'volgnr': 1,
                'brandstof': 'Diesel'
            }
        ],
        'versit_klasse': 'LPADEUR4'
    }
)

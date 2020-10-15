import csv
import logging
from datetime import datetime, timedelta
from itertools import cycle
from random import randint
from unittest import mock

from django.db import connection
from django.urls import reverse
from model_bakery import baker
from model_bakery.recipe import seq
from passage.case_converters import to_camelcase
from rest_framework.test import APITestCase

from .factories import PassageFactory

log = logging.getLogger(__name__)


TEST_POST = {
    "version": "passage-v1",
    "id": "cbbd2efc-78f4-4d41-bf5b-4cbdf1e87269",
    "passage_at": "2018-10-16T12:13:44+02:00",
    "straat": "Spaarndammerdijk",
    "rijstrook": 1,
    "rijrichting": 1,
    "camera_id": "ddddffff-4444-aaaa-7777-aaaaeeee1111",
    "camera_naam": "Spaarndammerdijk [Z]",
    "camera_kijkrichting": 0,
    "camera_locatie": {"type": "Point", "coordinates": [4.845423, 52.386831]},
    "kenteken_land": "NL",
    "kenteken_nummer_betrouwbaarheid": 640,
    "kenteken_land_betrouwbaarheid": 690,
    "kenteken_karakters_betrouwbaarheid": [
        {"betrouwbaarheid": 650, "positie": 1},
        {"betrouwbaarheid": 630, "positie": 2},
        {"betrouwbaarheid": 640, "positie": 3},
        {"betrouwbaarheid": 660, "positie": 4},
        {"betrouwbaarheid": 620, "positie": 5},
        {"betrouwbaarheid": 640, "positie": 6},
    ],
    "indicatie_snelheid": 23,
    "automatisch_verwerkbaar": True,
    "voertuig_soort": "Bromfiets",
    "merk": "SYM",
    "inrichting": "N.V.t.",
    "datum_eerste_toelating": "2015-03-06",
    "datum_tenaamstelling": "2015-03-06",
    "toegestane_maximum_massa_voertuig": 249,
    "europese_voertuigcategorie": "L1",
    "europese_voertuigcategorie_toevoeging": "e",
    "taxi_indicator": True,
    "maximale_constructie_snelheid_bromsnorfiets": 25,
    "brandstoffen": [{"brandstof": "Benzine", "volgnr": 1}],
    "versit_klasse": "test klasse",
}


def get_records_in_partition():
    with connection.cursor() as cursor:
        cursor.execute('select count(*) from passage_passage_20181016')
        row = cursor.fetchone()
        if len(row) > 0:
            return row[0]
        return 0


class PassageAPITestV0(APITestCase):
    """Test the passage endpoint."""

    def setUp(self):
        self.URL = '/v0/milieuzone/passage/'
        self.p = PassageFactory()

    def valid_response(self, url, response, content_type):
        """Check common status/json."""
        self.assertEqual(
            200, response.status_code, "Wrong response code for {}".format(url)
        )

        self.assertEqual(
            f"{content_type}",
            response["Content-Type"],
            "Wrong Content-Type for {}".format(url),
        )

    def test_post_new_passage_camelcase(self):
        """ Test posting a new camelcase passage """
        before = get_records_in_partition()

        # convert keys to camelcase for test
        camel_case = {to_camelcase(k): v for k, v in TEST_POST.items()}
        res = self.client.post(self.URL, camel_case, format='json')

        # check if the record was stored in the correct partition
        self.assertEqual(before + 1, get_records_in_partition())

        self.assertEqual(res.status_code, 201, res.data)
        for k, v in TEST_POST.items():
            self.assertEqual(res.data[k], v)

    def test_post_new_passage(self):
        """ Test posting a new passage """
        before = get_records_in_partition()

        res = self.client.post(self.URL, TEST_POST, format='json')

        # check if the record was stored in the correct partition
        self.assertEqual(before + 1, get_records_in_partition())

        self.assertEqual(res.status_code, 201, res.data)
        for k, v in TEST_POST.items():
            self.assertEqual(res.data[k], v)

    def test_post_new_passage_missing_attr(self):
        """Test posting a new passage with missing fields"""
        before = get_records_in_partition()
        NEW_TEST = dict(TEST_POST)
        NEW_TEST.pop('voertuig_soort')
        NEW_TEST.pop('europese_voertuigcategorie_toevoeging')
        res = self.client.post(self.URL, NEW_TEST, format='json')

        # check if the record was stored in the correct partition
        self.assertEqual(before + 1, get_records_in_partition())

        self.assertEqual(res.status_code, 201, res.data)
        for k, v in NEW_TEST.items():
            self.assertEqual(res.data[k], v)

    def test_post_range_betrouwbaarheid(self):
        """Test posting a invalid range betrouwbaarheid"""
        before = get_records_in_partition()
        NEW_TEST = dict(TEST_POST)
        NEW_TEST["kenteken_nummer_betrouwbaarheid"] = -1
        res = self.client.post(self.URL, NEW_TEST, format='json')

        # check if the record was NOT stored in the correct partition
        self.assertEqual(before, get_records_in_partition())
        self.assertEqual(res.status_code, 400, res.data)

    def test_post_duplicate_key(self):
        """ Test posting a new passage with a duplicate key """
        before = get_records_in_partition()

        res = self.client.post(self.URL, TEST_POST, format='json')
        self.assertEqual(res.status_code, 201, res.data)

        # # Post the same message again
        res = self.client.post(self.URL, TEST_POST, format='json')
        self.assertEqual(res.status_code, 409, res.data)

    def test_get_passages_not_allowed(self):
        PassageFactory.create()
        response = self.client.get(self.URL)
        self.assertEqual(response.status_code, 405)

    def test_update_passages_not_allowed(self):
        # first post a record
        self.client.post(self.URL, TEST_POST, format='json')

        # Then check if I cannot update it
        response = self.client.put(
            f'{self.URL}{TEST_POST["id"]}/', TEST_POST, format='json'
        )
        self.assertEqual(response.status_code, 404)

    def test_delete_passages_not_allowed(self):
        # first post a record
        self.client.post(self.URL, TEST_POST, format='json')

        # Then check if I cannot update it
        response = self.client.delete(f'{self.URL}{TEST_POST["id"]}/')
        self.assertEqual(response.status_code, 404)

    def test_passage_taxi_export(self):

        baker.make(
            'passage.PassageHourAggregation',
            count=2,
            taxi_indicator=True,
            _quantity=500,
        )

        # first post a record
        url = reverse('v0:passage-export-taxi')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        date = datetime.now().strftime("%Y-%m-%d")
        lines = [line for line in response.streaming_content]
        assert lines == [b'datum,aantal_taxi_passages\r\n', f'{date},1000\r\n'.encode()]

    def test_passage_export_no_filters(self):

        reading_count = 4
        camera_count = 3
        readings_per_camera = 2

        now = datetime.now()
        today = datetime(now.year, now.month, now.day)

        # Get the first day of the week; 2 weeks ago
        start_date = today - timedelta(days=now.weekday(), weeks=2)

        # Fill 3 weeks of data to ensure our export will only get the
        # previous week
        for day in range(7 * 3):
            # Generate 24 hours of data
            for hour in range(24):
                date = start_date + timedelta(days=day, hours=hour)

                # Generate multiple records per camera
                for i in range(camera_count):
                    num = i % camera_count + 1
                    baker.make(
                        'passage.PassageHourAggregation',
                        camera_id=num,
                        camera_naam=f'Camera: {num}',
                        count=reading_count,
                        date=date,
                        year=date.year,
                        week=date.isocalendar()[1],
                        hour=date.hour,
                        taxi_indicator=True,
                        _quantity=readings_per_camera,
                    )

        # first post a record
        url = reverse('v0:passage-export')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        lines = [line.decode() for line in response.streaming_content]
        content = list(csv.reader(lines))
        header = content.pop(0)
        assert header == ['camera_id', 'camera_naam', 'bucket', 'sum']
        assert len(content) == 7 * 24 * camera_count

        i = 0
        expected_content = []
        previous_week = today - timedelta(days=now.weekday(), weeks=1)
        for day in range(7):
            for hour in range(24):
                expected_datetime = previous_week + timedelta(days=day, hours=hour)
                for camera in range(camera_count):
                    camera += 1
                    expected_row = [
                        str(camera),
                        f'Camera: {camera}',
                        expected_datetime.strftime('%Y-%m-%d %H:%M:%S'),
                        str(reading_count * readings_per_camera),
                    ]
                    expected_content.append(tuple(expected_row))

        content = set(map(tuple, content))
        expected_content = set(map(tuple, expected_content))
        assert set(expected_content) == set(content)

    def test_passage_export_filters(self):
        date = datetime.fromisocalendar(2019, 11, 1)
        # create data for 3 cameras
        row = baker.make(
            'passage.PassageHourAggregation',
            camera_id=cycle(range(1, 4)),
            camera_naam=cycle(f'Camera: {i}' for i in range(1, 4)),
            date=date,
            year=date.year,
            week=date.isocalendar()[1],
            hour=1,
            _quantity=100,
        )
        url = reverse('v0:passage-export')
        response = self.client.get(url, dict(year=2019, week=12))
        self.assertEqual(response.status_code, 200)
        lines = [x for x in response.streaming_content]
        assert len(lines) == 0

        response = self.client.get(url, dict(year=2019, week=11))
        self.assertEqual(response.status_code, 200)
        lines = [x for x in response.streaming_content]

        # Expect the header and 3 lines
        assert len(lines) == 4

        response = self.client.get(url, dict(year=2019))
        self.assertEqual(response.status_code, 200)
        lines = [x for x in response.streaming_content]

        # Expect the header and 3 lines
        assert len(lines) == 4

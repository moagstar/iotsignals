import copy
import csv
import json
import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from itertools import cycle

import pytest
from django.contrib.gis.geos import Point
from django.db import connection
from django.test import override_settings
from django.urls import reverse
from model_bakery import baker
from passage.case_converters import to_camelcase
from passage.models import Passage
from rest_framework import status

from .factories import PassageFactory

log = logging.getLogger(__name__)


@pytest.fixture
def passage():
    return PassageFactory()


@pytest.fixture
def passage_payload():

    stub = PassageFactory.stub()
    data = stub.__dict__

    for k, v in data.items():
        if isinstance(v, date):
            data[k] = v.isoformat()

        if isinstance(v, datetime):
            data[k] = v.astimezone().isoformat()

        if isinstance(v, Point):
            data[k] = json.loads(v.json)

    return data


def get_records_in_partition():
    with connection.cursor() as cursor:
        cursor.execute('select count(*) from passage_passage_20181016')
        row = cursor.fetchone()
        if len(row) > 0:
            return row[0]
        return 0


def assert_response(response, payload):
    data = response.data
    expected = copy.deepcopy(payload)

    # Check for privacy changes
    if payload['toegestane_maximum_massa_voertuig'] <= 3500:
        expected['toegestane_maximum_massa_voertuig'] = 1500
        expected['europese_voertuigcategorie_toevoeging'] = None
        expected['merk'] = None

    if payload['voertuig_soort'].lower() == 'personenauto':
        expected['inrichting'] = 'Personenauto'

    expected[
        'datum_eerste_toelating'
    ] = f"{expected['datum_eerste_toelating'][:4]}-01-01"

    expected['datum_tenaamstelling'] = None

    for k, v in expected.items():
        assert data[k] == v, (k, data[k])


@pytest.mark.django_db
class TestPassageAPI:
    """Test the passage endpoint."""

    def setup(self):
        self.URL = '/v0/milieuzone/passage/'

    @pytest.fixture(autouse=True)
    def inject_api_client(self, api_client):
        self.client = api_client

    def valid_response(self, url, response, content_type):
        """Check common status/json."""
        assert 200 == response.status_code, "Wrong response code for {}".format(url)

        assert (
            f"{content_type}" == response["Content-Type"]
        ), "Wrong Content-Type for {}".format(url)

    def test_post_new_passage_camelcase(self, passage_payload):
        """ Test posting a new camelcase passage """
        # convert keys to camelcase for test

        assert Passage.objects.count() == 0
        camel_case = {to_camelcase(k): v for k, v in passage_payload.items()}
        res = self.client.post(self.URL, camel_case, format='json')
        assert res.status_code == 201, res.data
        assert Passage.objects.get(id=passage_payload['id'])
        assert_response(res, passage_payload)

    def test_post_new_passage(self, passage_payload):
        """ Test posting a new passage """
        assert Passage.objects.count() == 0
        res = self.client.post(self.URL, passage_payload, format='json')
        assert res.status_code == 201, res.data
        assert Passage.objects.get(id=passage_payload['id'])
        assert_response(res, passage_payload)

    def test_post_new_passage_missing_attr(self, passage_payload):
        """Test posting a new passage with missing fields"""
        assert Passage.objects.count() == 0
        passage_payload.pop('merk')
        passage_payload.pop('europese_voertuigcategorie_toevoeging')
        res = self.client.post(self.URL, passage_payload, format='json')
        assert res.status_code == 201, res.data
        assert Passage.objects.get(id=passage_payload['id'])
        assert_response(res, passage_payload)

    def test_post_range_betrouwbaarheid(self, passage_payload):
        """Test posting a invalid range betrouwbaarheid"""
        before = get_records_in_partition()
        passage_payload["kenteken_nummer_betrouwbaarheid"] = -1
        res = self.client.post(self.URL, passage_payload, format='json')

        # check if the record was NOT stored in the correct partition
        assert before == get_records_in_partition()
        assert res.status_code == 400, res.data

    def test_post_duplicate_key(self, passage_payload):
        """ Test posting a new passage with a duplicate key """
        before = get_records_in_partition()

        res = self.client.post(self.URL, passage_payload, format='json')
        assert res.status_code == 201, res.data

        # # Post the same message again
        res = self.client.post(self.URL, passage_payload, format='json')
        assert res.status_code == 409, res.data

    def test_get_passages_not_allowed(self, passage_payload):
        PassageFactory.create()
        response = self.client.get(self.URL)
        assert response.status_code == 405

    def test_update_passages_not_allowed(self, passage_payload):
        # first post a record
        self.client.post(self.URL, passage_payload, format='json')

        # Then check if I cannot update it
        response = self.client.put(
            f'{self.URL}{passage_payload["id"]}/', passage_payload, format='json'
        )
        assert response.status_code == 404

    def test_delete_passages_not_allowed(self, passage_payload):
        # first post a record
        self.client.post(self.URL, passage_payload, format='json')

        # Then check if I cannot update it
        response = self.client.delete(f'{self.URL}{passage_payload["id"]}/')
        assert response.status_code == 404

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
        assert response.status_code == 200

        date = datetime.now().strftime("%Y-%m-%d")
        lines = [line for line in response.streaming_content]
        assert lines == [b'datum,aantal_taxi_passages\r\n', f'{date},1000\r\n'.encode()]

    @override_settings(AUTHORIZATION_TOKEN='foo')
    def test_passage_export_no_auth(self):
        url = reverse('v0:passage-export')
        response = self.client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @override_settings(AUTHORIZATION_TOKEN='foo')
    def test_passage_export_wrong_auth(self):
        url = reverse('v0:passage-export')
        response = self.client.get(url, HTTP_AUTHORIZATION='Token bar')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @override_settings(AUTHORIZATION_TOKEN='foo')
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
        response = self.client.get(url, HTTP_AUTHORIZATION='Token foo')
        assert response.status_code == 200

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

    @override_settings(AUTHORIZATION_TOKEN='foo')
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
        response = self.client.get(
            url, dict(year=2019, week=12), HTTP_AUTHORIZATION='Token foo'
        )
        assert response.status_code == 200
        lines = [x for x in response.streaming_content]
        assert len(lines) == 0

        response = self.client.get(
            url, dict(year=2019, week=11), HTTP_AUTHORIZATION='Token foo'
        )
        assert response.status_code == 200
        lines = [x for x in response.streaming_content]

        # Expect the header and 3 lines
        assert len(lines) == 4

        response = self.client.get(url, dict(year=2019), HTTP_AUTHORIZATION='Token foo')
        assert response.status_code == 200
        lines = [x for x in response.streaming_content]

        # Expect the header and 3 lines
        assert len(lines) == 4

    def test_privacy_maximum_massa(self, api_client, passage_payload):
        passage_payload['toegestane_maximum_massa_voertuig'] = 3000

        res = self.client.post(self.URL, passage_payload, format='json')
        assert res.status_code == 201, res.data
        assert Passage.objects.get(id=passage_payload['id'])
        assert_response(res, passage_payload)

    def test_privacy_voertuig_soort(self, api_client, passage_payload):
        passage_payload['voertuig_soort'] = 'PeRsonEnaUto'

        res = self.client.post(self.URL, passage_payload, format='json')
        assert res.status_code == 201, res.data
        assert Passage.objects.get(id=passage_payload['id'])
        assert_response(res, passage_payload)

    def test_privacy_tenaamstelling(self, api_client, passage_payload):
        passage_payload['datum_tenaamstelling'] = '2020-02-02'

        res = self.client.post(self.URL, passage_payload, format='json')
        assert res.status_code == 201, res.data
        assert Passage.objects.get(id=passage_payload['id'])
        assert_response(res, passage_payload)

    def test_privacy_datum_eerste_toelating(self, api_client, passage_payload):
        passage_payload['datum_eerste_toelating'] = '2020-02-02'

        res = self.client.post(self.URL, passage_payload, format='json')
        assert res.status_code == 201, res.data
        assert Passage.objects.get(id=passage_payload['id'])
        assert_response(res, passage_payload)

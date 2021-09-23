"""
This is a (much needed) load test for this repo. These are some example usages:

locust --host=http://127.0.0.1:8001 --headless --users 250 --spawn-rate 25 --run-time 30s
"""

# std
import csv
import datetime
import json
import os
import random
import time
from pathlib import Path
from uuid import uuid4
# 3rd party
from locust import HttpUser, task, between


PASSAGE_ENDPOINT_URL = "/v0/milieuzone/passage/"


def get_dt_with_tz_info():
    # Calculate the offset taking into account daylight saving time
    utc_offset_sec = time.altzone if time.localtime().tm_isdst else time.timezone
    utc_offset = datetime.timedelta(seconds=-utc_offset_sec)
    return datetime.datetime.now().replace(tzinfo=datetime.timezone(offset=utc_offset)).isoformat()


def load_data(filename):

    def postprocess(row):

        del row['count']

        # '' -> undefined
        for key in [key for key, value in row.items() if not value]:
            del row[key]

        # parse bool
        if 'taxi_indicator' in row:
            row['taxi_indicator'] = {'TRUE': True, 'FALSE': False}.get(row['taxi_indicator'], None)

        # parse json fields
        if 'brandstoffen' in row:
            row['brandstoffen'] = json.loads(row['brandstoffen'].replace("'", '"'))

        return row

    with open(filename) as f:
        # this will be our "pool" of values to choose from, multiply each
        # item by the number of times it occurred to make it more likely that
        # we will choose those.
        return [
            postprocess(dict(row))
            for row in csv.DictReader(f)
            for _ in range(int(row['count']))
        ]


# allow caller to provide camera / vehicle data, or default to unique camera
# and vehicle data selected from 2021-09-01
__dir__ = Path(__file__).parent
cameras = load_data(__dir__/'api'/'data'/'camera.csv')
vehicles = load_data(__dir__/'api'/'data'/'vehicle.csv')


# make sure sampling is reproducible
random.seed(0)


def vehicle(version=1):
    result = random.sample(vehicles, 1)[0]

    # TODO: select this in vehicle.sql and store in vehicle.csv
    result["automatisch_verwerkbaar"] = True

    if version == 2:
        # extra fields in version 2, just make a simple model whereby the other
        # data is enough to make vehicles unique, which means we can just use
        # constant values here. It's almost certainly not the case, but let's
        # just keep it simple for now.
        result.update({
            "pseudokenteken": "11AA11",
            "vervaldatum_apk": "2017-01-01",
            "wam_verzekerd": True,
            "massa_ledig_voertuig": 1280,
            "aantal_assen": 2,
            "aantal_staan_plaatsen": 10,
            "aantal_wielen": 6,
            "aantal_zit_plaatsen": 50,
            "handelsbenaming": "S40",
            "lengte": 507,
            "breedte": 203,
            "maximum_massa_trekken_ongeremd": 1280,
            "maximum_massa_trekken_geremd": 1300,
            "co2_uitstoot_gecombineerd": 7.30,
            "co2_uitstoot_gewogen": 7.50,
            "milieuklasse_eg_goedkeuring_zwaar": "595/2009*2018/932D",
        })

    return result


def create_message(version):
    message = {
        "id": str(uuid4()),
        "passage_at": get_dt_with_tz_info(),
        "created_at": get_dt_with_tz_info(),
        "version": str(version),
        "kenteken_nummer_betrouwbaarheid": random.randint(0, 1000),
        "kenteken_land_betrouwbaarheid": random.randint(0, 1000),
        "kenteken_karakters_betrouwbaarheid": [
            {
                "positie": positie,
                "betrouwbaarheid": random.randint(0, 1000),
            }
            for positie in range(6)
        ],
        "indicatie_snelheid": random.randrange(0, 100),
        **random.sample(cameras, 1)[0],
        **vehicle(version),
    }
    return message


class CarsBehaviour(HttpUser):
    weight = 1
    wait_time = between(0, 1)

    @task(1)
    def post_cars(self):
        self.client.post(PASSAGE_ENDPOINT_URL, json=create_message(2))

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

    def postprocess(d):

        del d['count']

        # '' -> undefined
        for key in [k for k, v in d.items() if not v]:
            del d[key]

        # parse bool
        if 'taxi_indicator' in d:
            d['taxi_indicator'] = {'TRUE': True, 'FALSE': False}.get(d['taxi_indicator'], None)

        # parse json fields
        if 'brandstoffen' in d:
            d['brandstoffen'] = json.loads(d['brandstoffen'].replace("'", '"'))

        return d

    with open(filename) as f:
        # this will be our "pool" of values to choose from, multiply each
        # item by the number of times it occurred to make it more likely that
        # we will choose those.
        return [
            postprocess(dict(x))
            for x in csv.DictReader(f)
            for _ in range(int(x['count']))
        ]


# allow caller to provide camera / vehicle data, or default to unique camera
# and vehicle data selected from 2021-09-01
cameras = load_data(os.environ.get('CAMERA_CSV', '/opt/src/api/data/camera.csv'))
vehicles = load_data(os.environ.get('VEHICLE_CSV', '/opt/src/api/data/vehicle.csv'))


# make sure sampling is reproducible
random.seed(0)


def create_message():
    message = {
        "id": str(uuid4()),
        "passage_at": get_dt_with_tz_info(),
        "created_at": get_dt_with_tz_info(),
        "version": "1",
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
        "automatisch_verwerkbaar": random.sample((None, True, False), 1)[0],
        **random.sample(cameras, 1)[0],
        **random.sample(vehicles, 1)[0],
    }
    return message


class CarsBehaviour(HttpUser):
    weight = 1
    wait_time = between(0, 1)

    @task(1)
    def post_cars(self):
        self.client.post(PASSAGE_ENDPOINT_URL, json=create_message())

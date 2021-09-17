# 3rd party
import csv

import pytest
# iotsignals
from passage.models import PassageCamera
from passage.tests.factories import PassageCameraFactory


@pytest.mark.django_db
class TestAppendOnlyModel:

    def test_save_should_create_first_instance(self):
        PassageCameraFactory.create()
        assert PassageCamera.objects.count() == 1

    def test_save_with_same_values_should_not_create_second_instance(self):
        stub = PassageCameraFactory.stub()
        instance1 = PassageCamera(**stub.__dict__)
        instance1.save()
        instance2 = PassageCamera(**stub.__dict__)
        instance2.save()
        assert PassageCamera.objects.filter(id=instance1.id)._existing_ids()
        assert PassageCamera.objects.count() == 1
        assert instance1.id == instance2.id

    def test_save_with_different_values_should_create_second_instance(self):
        stub1 = PassageCameraFactory.stub()
        instance1 = PassageCamera(**stub1.__dict__)
        instance1.save()
        stub2 = PassageCameraFactory.stub()
        instance2 = PassageCamera(**stub2.__dict__)
        instance2.save()
        assert PassageCamera.objects.filter(id=instance1.id)._existing_ids()
        assert PassageCamera.objects.filter(id=instance2.id)._existing_ids()
        assert PassageCamera.objects.count() == 2
        assert instance1.id != instance2.id

    def test_thing(self):

        def delcount(d):
            del d['count']
            return d

        with open('../../../data/vehicle.csv') as f:
            vehicles = [
                delcount(vehicle)
                for vehicle in csv.DictReader(f)
                for _ in range(vehicle['count'])
            ]

        with open('../../../data/camera.csv') as f:
            cameras = [
                delcount(camera)
                for camera in csv.DictReader(f)
                for _ in range(camera['count'])
            ]

        print()
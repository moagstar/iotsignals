# iotsignals

Naming conventions:
    - iotsignals: Umbrella term for this repository since the data is retrieved through IoT devices (e.g: cameras)
    - Passages: Monitoring cars. Measured with cameras that keep count of passing cars.

Receive IOT data from various systems and store it for later analysis.


Start the docker database and run the download en upload scripts.

    docker-compose build
    docker-compose up database api


Now you should be able to access http://127.0.0.1:8001/iotsignals/


#### Local development ####

Create a local environment and activate it:

    virtualenv --python=$(which python3) venv
    source venv/bin/activate


Start development database

	docker-compose up database
	
Fill test data in database.

    docker-compose run api python manage.py migrate

TIP: add database to your /etc/hosts pointing at 127.0.0.1 so that you can run the same 
settings both in docker and locally

Please schedule api/deploy/docker-migrate.sh script to run once a day. It will create the database partitions.

Then add the requirements:

    pip install -r requirements.txt


# Stress testing with locust
We've got a simple locust test script which fires a bunch of requests. It is automatically started by the locust 
container.

It can also be run manually from the root folder using:

    locust --host=http://127.0.0.1:8001

and starting it from the browser http://127.0.0.1:8089. 

Or run it headless:

    locust --host=http://127.0.0.1:8001 --headless --users 250 --spawn-rate 25 --run-time 30s

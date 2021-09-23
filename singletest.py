import requests
from locustfile import PASSAGE_ENDPOINT_URL, create_message

requests.post(f'http://localhost:8001{PASSAGE_ENDPOINT_URL}', json=create_message(2))

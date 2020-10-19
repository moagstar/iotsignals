from unittest.mock import MagicMock

from django.test import RequestFactory, TestCase
from middleware.gzip import UWSGIGZipMiddleware


class TestTestUWSGIGzipMiddlewareTest(TestCase):
    def test_middleware(self):
        request = RequestFactory()
        middleware = UWSGIGZipMiddleware(lambda request: {})
        response = middleware(request)
        assert response['uWSGI-Encoding'] == 'gzip'

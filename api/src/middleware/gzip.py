class UWSGIGZipMiddleware:
    """
    Let uWSGI do the gzip encoding.
    With the UWSGI http-auto-gzip (UWSGI_HTTP_AUTO_GZIP=1) setting
    enabled we can instruct it using the uWSGI-Encoding header
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response['uWSGI-Encoding'] = 'gzip'
        return response

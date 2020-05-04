from rest_framework import status
from rest_framework.exceptions import APIException


class DuplicateIdError(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = 'Duplicate id supplied.'
    default_code = 'parse_error'

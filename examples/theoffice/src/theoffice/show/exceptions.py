from typing import ClassVar
from starlette import status as http_status


class BaseHTTPException(Exception):
    status: ClassVar[int] = http_status.HTTP_500_INTERNAL_SERVER_ERROR


class SeasonNotFound(BaseHTTPException):
    status = http_status.HTTP_404_NOT_FOUND


class SeasonMedataCorrupted(BaseHTTPException):
    status = http_status.HTTP_500_INTERNAL_SERVER_ERROR


class EpisodeNotFound(BaseHTTPException):
    status = http_status.HTTP_404_NOT_FOUND

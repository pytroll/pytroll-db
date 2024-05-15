"""TODO."""

from typing import Any
from urllib.parse import urljoin

from pydantic import AnyUrl
from urllib3 import BaseHTTPResponse, request

from trolldb.config.config import APIServerConfig, AppConfig, DatabaseConfig

test_app_config = AppConfig(
    api_server=APIServerConfig(url=AnyUrl("http://localhost:8080"), title="Test API Server", version="0.1"),
    database=DatabaseConfig(
        main_database_name="mock_database",
        main_collection_name="mock_collection",
        url=AnyUrl("mongodb://localhost:28017"),
        timeout=1000)
)


def http_get(route: str = "") -> BaseHTTPResponse:
    """An auxiliary function to make a GET request using :func:`urllib.request`.

    Args:
        route:
            The desired route (excluding the root URL) which can include a query string as well.

    Returns:
        The response from the GET request.
    """
    return request("GET", urljoin(test_app_config.api_server.url.unicode_string(), route))


def assert_equal(test, expected) -> None:
    """An auxiliary function to assert the equality of two objects using the ``==`` operator.

    In case an input is a list or a tuple, it will be first converted to a set so that the order of items there in does
    not affect the assertion outcome.

    Warning:
        In case of a list or tuple of items as inputs, do not use this function if the order of items matters.

    Args:
        test:
            The object to be tested.
        expected:
            The object to test against.
    """

    def _setify(obj: Any) -> Any:
        """An auxiliary function to convert an object to a set if it is a tuple or a list."""
        return set(obj) if isinstance(obj, list | tuple) else obj

    if not _setify(test) == _setify(expected):
        raise AssertionError(f"{test} and {expected} are not equal.")

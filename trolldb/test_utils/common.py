"""Common functionalities for testing, shared between tests and other test utility modules."""

from collections import OrderedDict
from typing import Any
from urllib.parse import urljoin

from pydantic import AnyUrl
from urllib3 import BaseHTTPResponse, request

from trolldb.config.config import APIServerConfig, AppConfig, DatabaseConfig

test_app_config = AppConfig(
    api_server=APIServerConfig(url=AnyUrl("http://localhost:8080")),
    database=DatabaseConfig(
        main_database_name="mock_database",
        main_collection_name="mock_collection",
        url=AnyUrl("mongodb://localhost:28017"),
        timeout=1000),
    subscriber_config=dict()
)
"""The app configuration when used in testing."""


def http_get(route: str = "") -> BaseHTTPResponse:
    """An auxiliary function to make a GET request using :func:`urllib.request`.

    Args:
        route:
            The desired route (excluding the root URL) which can include a query string as well.

    Returns:
        The response from the GET request.
    """
    return request("GET", urljoin(test_app_config.api_server.url.unicode_string(), route))


def assert_equal(test: Any, expected: Any, ordered: bool = False) -> None:
    """An auxiliary function to assert the equality of two objects using the ``==`` operator.

    Examples:
      - If ``ordered=False`` and the input is a list or a tuple, it will be first converted to a set
        so that the order of items therein does not affect the assertion outcome.
      - If ``ordered=True`` and the input is a dictionary, it will be first converted to an ``OrderedDict``.

    Note:
        The rationale behind choosing ``ordered=False`` as the default behaviour is that this function is often used
        in combination with API calls and/or querying the database. In such cases, the order of items which are returned
        often does not matter. In addition, if the order really matters, one might as well simply use the built-in
        ``assert`` statement.

    Note:
        Dictionaries by default are unordered objects.

    Warning:
        For the purpose of this function, the concept of ordered vs unordered only applies to lists, tuples, and
        dictionaries. An object of any other type is assumed as-is, i.e. the default behaviour of Python applies.
        For example, conceptually, two strings can be converted to two sets of characters and then be compared with
        each other. However, this is not what we do for strings.

    Args:
        test:
            The object to be tested.
        expected:
            The object to test against.
        ordered (Optional, default ``False``):
            A flag to determine whether the order of items matters in case of a list, a tuple, or a dictionary.
    """

    def _ordered(obj: Any) -> Any:
        """An auxiliary function to convert an object to ordered depending on its type and the ``ordered`` flag."""
        match obj:
            case list() | tuple():
                return set(obj) if not ordered else obj
            case dict():
                return OrderedDict(obj) if ordered else obj
            case _:
                return obj

    if not _ordered(test) == _ordered(expected):
        raise AssertionError(f"{test} and {expected} are not equal. The flag `ordered` is set to `{ordered}`.")

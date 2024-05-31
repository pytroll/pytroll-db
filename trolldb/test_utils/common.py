"""Common functionalities for testing, shared between tests and other test utility modules."""

from typing import Any, Optional
from urllib.parse import urljoin

import yaml
from pydantic import AnyUrl, FilePath
from urllib3 import BaseHTTPResponse, request

from trolldb.config.config import AppConfig


def make_test_app_config(subscriber_address: Optional[FilePath] = None) -> dict[str, dict]:
    """Makes the app configuration when used in testing.

    Args:
        subscriber_address:
            The address of the subscriber if it is of type ``FilePath``. Otherwise, if it is ``None`` the ``subscriber``
            config will be an empty dictionary.

    Returns:
        A dictionary which resembles an object of type :obj:`~trolldb.config.config.AppConfig`.
    """
    app_config = dict(
        api_server=dict(
            url="http://localhost:8080"
        ),
        database=dict(
            main_database_name="test_database",
            main_collection_name="test_collection",
            url="mongodb://localhost:28017",
            timeout=1
        ),
        subscriber=dict(
            nameserver=False,
            addresses=[f"ipc://{subscriber_address}/in.ipc"] if subscriber_address is not None else [""],
            port=3000
        )
    )

    return app_config


test_app_config = AppConfig(**make_test_app_config())
"""The app configs for testing purposes assuming an empty configuration for the subscriber."""


def create_config_file(config_path: FilePath) -> FilePath:
    """Creates a config file for tests."""
    config_file = config_path / "config.yaml"
    with open(config_file, "w") as f:
        yaml.safe_dump(make_test_app_config(config_path), f)
    return config_file


def http_get(route: str = "", root: AnyUrl = test_app_config.api_server.url) -> BaseHTTPResponse:
    """An auxiliary function to make a GET request using :func:`urllib.request`.

    Args:
        route:
            The desired route (excluding the root URL) which can include a query string as well.
        root (Optional, default :obj:`test_app_config.api_server.url`):
            The root to which the given route will be added to make the complete URL.

    Returns:
        The response from the GET request.
    """
    return request("GET", urljoin(root.unicode_string(), route))


def compare_by_operator_name(operator: str, left: Any, right: Any) -> Any:
    """Compares two operands given the binary operator name in a string format.

    Args:
        operator:
            Any of ``["$gte", "$gt", "$lte", "$lt", "$eq"]``.
            These match the MongoDB comparison operators described
            `here <https://www.mongodb.com/docs/v6.2/reference/operator/aggregation/#comparison-expression-operators>`_.
        left:
            The left operand
        right:
            The right operand

    Returns:
        The result of the comparison operation, i.e. ``<left> <operator> <right>``.

    Raises:
         ValueError:
            If the operator name is not valid.
    """
    match operator:
        case "$gte":
            return left >= right
        case "$gt":
            return left > right
        case "$lte":
            return left <= right
        case "$lt":
            return left < right
        case "$eq":
            return left == right
        case _:
            raise ValueError(f"Unknown operator: {operator}")

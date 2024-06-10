"""Common functionalities for testing, shared between tests and other test utility modules."""

import time
from contextlib import contextmanager
from multiprocessing import Process
from typing import Any, Generator, Optional
from urllib.parse import urljoin

import yaml
from pydantic import AnyUrl, FilePath
from urllib3 import BaseHTTPResponse, request

from trolldb.api.api import run_server
from trolldb.config.config import AppConfig, Timeout


def make_test_app_config_as_dict(subscriber_address: Optional[FilePath] = None) -> dict[str, dict]:
    """Makes the app configuration (as a dictionary) when used in testing.

    Args:
        subscriber_address:
            The address of the subscriber if it is of type ``FilePath``. Otherwise, if it is ``None`` the ``subscriber``
            config will be an empty dictionary.

    Returns:
        A dictionary with a structure similar to that of an :obj:`~trolldb.config.config.AppConfig` object.

    Warning:
        The return value of this function is a dictionary and not accepted as a valid input argument for
        :func:`trolldb.database.mongodb.MongoDB.initialize`. As a result, one must cast it to the valid type by e.g.
        ``AppConfig(**make_test_app_config_as_dict())``.
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


test_app_config = AppConfig(**make_test_app_config_as_dict())
"""The app configs for testing purposes assuming an empty configuration for the subscriber."""


def create_config_file(config_path: FilePath) -> FilePath:
    """Creates a config file for tests."""
    config_file = config_path / "config.yaml"
    with open(config_file, "w") as f:
        yaml.safe_dump(make_test_app_config_as_dict(config_path), f)
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


@contextmanager
def api_server_process_context(
        config: AppConfig = test_app_config, startup_time: Timeout = 2) -> Generator[Process, Any, None]:
    """A synchronous context manager to run the API server in a separate process (non-blocking).

    It uses the `multiprocessing <https://docs.python.org/3/library/multiprocessing.html>`_ package. The main use case
    is envisaged to be in `TESTING` environments.

    Args:
        config:
            Same as ``config`` argument for :func:`run_server`.

        startup_time:
            The overall time in seconds that is expected for the server and the database connections to be established
            before actual requests can be sent to the server. For testing purposes ensure that this is sufficiently
            large so that the tests will not time out.
    """
    process = Process(target=run_server, args=(config,))
    try:
        process.start()
        time.sleep(startup_time)
        yield process
    finally:
        process.terminate()
        process.join()

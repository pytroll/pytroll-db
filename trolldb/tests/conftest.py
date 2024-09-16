"""Pytest config for database tests.

This module provides fixtures for running a Mongo DB instance in test mode and filling the database with test data.
"""

from typing import Callable

import pytest
import pytest_asyncio
from _pytest.logging import LogCaptureFixture
from loguru import logger

from trolldb.database.mongodb import mongodb_context
from trolldb.test_utils.common import test_app_config
from trolldb.test_utils.mongodb_database import TestDatabase
from trolldb.test_utils.mongodb_instance import running_prepared_database_context


@pytest.fixture
def caplog(caplog: LogCaptureFixture):
    """This overrides the actual pytest ``caplog`` fixture.

    Reason:
        We are using ``loguru`` instead of the Python built-in logging package. More information at:
        https://loguru.readthedocs.io/en/latest/resources/migration.html#replacing-caplog-fixture-from-pytest-library
    """
    handler_id = logger.add(
        caplog.handler,
        format="{message}",
        level=0,
        filter=lambda record: record["level"].no >= caplog.handler.level,
        enqueue=False,  # Set to 'True' if your test is spawning child processes.
    )
    yield caplog
    logger.remove(handler_id)


@pytest.fixture(scope="session")
def _run_mongodb_server_instance():
    """Encloses all tests (session scope) in a context manager of a running MongoDB instance (in a separate process)."""
    with running_prepared_database_context():
        yield


@pytest_asyncio.fixture()
async def mongodb_fixture(_run_mongodb_server_instance):
    """Fills the database with test data and then enclose each test in a mongodb context manager."""
    TestDatabase.prepare()
    async with mongodb_context(test_app_config.database):
        yield


@pytest.fixture
def check_log(caplog) -> Callable:
    """A fixture to check the logs. It relies on the ``caplog`` fixture.

    Returns:
        A function which can be called to check the log level and message.
    """

    def check_log_message_at_level(level: str, message: str) -> bool:
        """An auxiliary function to check the log level and message."""
        for rec in caplog.records:
            if rec.levelname == level and (message in rec.message):
                return True
        return False

    return check_log_message_at_level

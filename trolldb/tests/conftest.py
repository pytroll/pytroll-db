"""Pytest config for database tests.

This module provides fixtures for running a Mongo DB instance in test mode and filling the database with test data.
"""

import pytest
import pytest_asyncio

from trolldb.api.api import api_server_process_context
from trolldb.database.mongodb import mongodb_context
from trolldb.test_utils.common import test_app_config
from trolldb.test_utils.mongodb_database import TestDatabase
from trolldb.test_utils.mongodb_instance import running_prepared_database_context


@pytest.fixture(scope="session")
def _run_mongodb_server_instance():
    """Encloses all tests (session scope) in a context manager of a running MongoDB instance (in a separate process)."""
    with running_prepared_database_context():
        yield


@pytest.fixture(scope="session")
def _test_server_fixture(_run_mongodb_server_instance):
    """Encloses all tests (session scope) in a context manager of a running API server (in a separate process)."""
    with api_server_process_context(test_app_config, startup_time=2):
        yield


@pytest_asyncio.fixture()
async def mongodb_fixture(_run_mongodb_server_instance):
    """Fills the database with test data and then enclose each test in a mongodb context manager."""
    TestDatabase.prepare()
    async with mongodb_context(test_app_config.database):
        yield

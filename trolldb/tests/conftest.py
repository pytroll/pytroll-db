"""Pytest config for database tests.

This module provides fixtures for running a Mongo DB instance in test mode and filling the database with test data.
"""

import pytest
import pytest_asyncio

from trolldb.api.api import server_process_context
from trolldb.database.mongodb import mongodb_context
from trolldb.test_utils.common import test_app_config
from trolldb.test_utils.mongodb_database import TestDatabase
from trolldb.test_utils.mongodb_instance import mongodb_instance_server_process_context


@pytest.fixture(scope="session")
def _run_mongodb_server_instance():
    """Encloses all tests (session scope) in a context manager of a running MongoDB instance (in a separate process)."""
    with mongodb_instance_server_process_context():
        yield


@pytest.fixture(scope="session")
def _test_server_fixture(_run_mongodb_server_instance):
    """Encloses all tests (session scope) in a context manager of a running API server (in a separate process)."""
    TestDatabase.prepare()
    with server_process_context(test_app_config, startup_time=2000):
        yield


@pytest_asyncio.fixture()
async def mongodb_fixture(_run_mongodb_server_instance):
    """Fills the database with test data and then enclose each test in a mongodb context manager."""
    TestDatabase.prepare()
    async with mongodb_context(test_app_config.database):
        yield


@pytest.fixture()
def tmp_data_filename(tmp_path):
    """Create a filename for the messages."""
    filename = "20191103_153936-s1b-ew-hh.tiff"
    return tmp_path / filename

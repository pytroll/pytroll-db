"""TODO."""

import pytest

from trolldb.api.api import server_process_context
from trolldb.test_utils.common import test_app_config
from trolldb.test_utils.mongodb_database import TestDatabase
from trolldb.test_utils.mongodb_instance import mongodb_instance_server_process_context


@pytest.fixture(scope="session")
def _run_mongodb_server_instance():
    """TODO."""
    with mongodb_instance_server_process_context():
        yield


@pytest.fixture(scope="session")
def _test_server_fixture(_run_mongodb_server_instance):
    """TODO."""
    TestDatabase.prepare()
    with server_process_context(test_app_config, startup_time=2000):
        yield

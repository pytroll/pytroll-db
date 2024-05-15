import pytest

from trolldb.api.api import server_process_context
from trolldb.test_utils.common import test_app_config
from trolldb.test_utils.mongodb_database import TestDatabase
from trolldb.test_utils.mongodb_instance import mongodb_instance_server_process_context


@pytest.fixture(scope="session")
def run_mongodb_server_instance():
    with mongodb_instance_server_process_context():
        yield


@pytest.fixture(scope="session", autouse=True)
def test_server_fixture(run_mongodb_server_instance):
    TestDatabase.prepare()
    with server_process_context(test_app_config, startup_time=2000):
        yield

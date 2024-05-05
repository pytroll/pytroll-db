import pytest
import pytest_asyncio

from test_utils.mock_mongodb_instance import mongodb_instance_server_process_context
from test_utils.common import test_app_config
from test_utils.mock_mongodb_database import TestDatabase
from trolldb.database.mongodb import mongodb_context


@pytest.fixture(scope="session")
def run_mongodb_server_instance():
    with mongodb_instance_server_process_context():
        yield


@pytest_asyncio.fixture(autouse=True)
async def mongodb_fixture(run_mongodb_server_instance):
    TestDatabase.prepare()
    async with mongodb_context(test_app_config.database):
        yield

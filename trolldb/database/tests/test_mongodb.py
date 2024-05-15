import errno
import time

import pytest
from pydantic import AnyUrl
from pymongo.errors import InvalidOperation

from trolldb.database.mongodb import DatabaseConfig, MongoDB, mongodb_context
from trolldb.test_utils.common import test_app_config


async def test_connection_timeout_negative():
    """Expect to see the connection attempt times out since the MongoDB URL is invalid."""
    timeout = 3000
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        t1 = time.time()
        async with mongodb_context(
                DatabaseConfig(url=AnyUrl("mongodb://invalid_url_that_does_not_exist:8000"),
                               timeout=timeout, main_database_name=" ", main_collection_name=" ")):
            pass
    t2 = time.time()
    assert pytest_wrapped_e.value.code == errno.EIO
    assert t2 - t1 >= timeout / 1000


async def test_main_database_negative(run_mongodb_server_instance):
    """Expect to fail when giving an invalid name for the main database, given a valid collection name."""
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        async with mongodb_context(DatabaseConfig(
                timeout=1000,
                url=test_app_config.database.url,
                main_database_name=" ",
                main_collection_name=test_app_config.database.main_collection_name)):
            pass
    assert pytest_wrapped_e.value.code == errno.ENODATA


async def test_main_collection_negative(run_mongodb_server_instance):
    """Expect to fail when giving an invalid name for the main collection, given a valid database name."""
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        async with mongodb_context(DatabaseConfig(
                timeout=1000,
                url=test_app_config.database.url,
                main_database_name=test_app_config.database.main_database_name,
                main_collection_name=" ")):
            pass
    assert pytest_wrapped_e.value.code == errno.ENODATA


async def test_get_client(mongodb_fixture):
    """This is our way of testing that MongoDB.client() returns the valid client object.

    Expect:
        - The `close` method can be called on the client and leads to the closure of the client
        - Further attempts to access the database after closing the client fails.
    """
    MongoDB.close()
    with pytest.raises(InvalidOperation):
        await MongoDB.list_database_names()


async def test_main_collection(mongodb_fixture):
    """Expect:
    - The retrieved main collection is not `None`
    - It has the correct name
    - It is the same object that can be accessed via the `client` object of the MongoDB.
    """
    assert MongoDB.main_collection() is not None
    assert MongoDB.main_collection().name == test_app_config.database.main_collection_name
    assert MongoDB.main_collection() == \
           (await MongoDB.get_database(test_app_config.database.main_database_name))[
               test_app_config.database.main_collection_name]


async def test_main_database(mongodb_fixture):
    """Same as test_main_collection but for the main database."""
    assert MongoDB.main_database() is not None
    assert MongoDB.main_database().name == test_app_config.database.main_database_name
    assert MongoDB.main_database() == await MongoDB.get_database(test_app_config.database.main_database_name)

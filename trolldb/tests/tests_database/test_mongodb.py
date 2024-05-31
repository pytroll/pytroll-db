"""Direct tests for :obj:`trolldb.database.mongodb` module without an API server connection.

Note:
    The functionalities of the MongoDB client is not mocked! For the tests herein an actual MongoDB instance will be
    run. It includes databases which are pre-filled with random data having similar characteristics to the real data.
    Actual calls will be made to the running MongoDB instance via the client.
"""

import errno
import time
from collections import Counter

import pytest
from bson import ObjectId
from pydantic import AnyUrl
from pymongo.errors import InvalidOperation

from trolldb.database.mongodb import DatabaseConfig, MongoDB, get_id, get_ids, mongodb_context
from trolldb.test_utils.common import test_app_config
from trolldb.test_utils.mongodb_database import TestDatabase


async def test_connection_timeout_negative():
    """Expect to see the connection attempt times out since the MongoDB URL is invalid."""
    timeout = 3
    t1 = time.time()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        async with mongodb_context(
                DatabaseConfig(url=AnyUrl("mongodb://invalid_url_that_does_not_exist:8000"),
                               timeout=timeout, main_database_name=" ", main_collection_name=" ")):
            pass
    t2 = time.time()
    assert pytest_wrapped_e.value.code == errno.EIO
    assert t2 - t1 >= timeout


@pytest.mark.usefixtures("_run_mongodb_server_instance")
async def test_main_database_negative():
    """Expect to fail when giving an invalid name for the main database, given a valid collection name."""
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        async with mongodb_context(DatabaseConfig(
                timeout=1,
                url=test_app_config.database.url,
                main_database_name=" ",
                main_collection_name=test_app_config.database.main_collection_name)):
            pass
    assert pytest_wrapped_e.value.code == errno.ENODATA


@pytest.mark.usefixtures("_run_mongodb_server_instance")
async def test_main_collection_negative():
    """Expect to fail when giving an invalid name for the main collection, given a valid database name."""
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        async with mongodb_context(DatabaseConfig(
                timeout=1,
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
    """Tests the properties of the main collection.

    Expect:
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


async def test_get_id(mongodb_fixture):
    """Tests :func:`trolldb.database.mongodb.get_id` using all documents (one at a time)."""
    for _id in TestDatabase.get_document_ids_from_database():
        doc = MongoDB.main_collection().find_one({"_id": ObjectId(_id)})
        assert await get_id(doc) == _id


async def test_get_ids(mongodb_fixture):
    """Tests :func:`trolldb.database.mongodb.get_ids` using all documents in one pass."""
    docs = MongoDB.main_collection().find({})
    assert Counter(await get_ids(docs)) == Counter(TestDatabase.get_document_ids_from_database())

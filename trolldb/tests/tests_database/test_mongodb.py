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
from pydantic import AnyUrl, ValidationError
from pymongo.errors import InvalidOperation

from trolldb.database.errors import Client
from trolldb.database.mongodb import DatabaseConfig, MongoDB, get_id, get_ids, mongodb_context
from trolldb.errors.errors import ResponseError
from trolldb.test_utils.common import make_test_app_config_as_dict, test_app_config
from trolldb.test_utils.mongodb_database import TestDatabase


async def test_connection_timeout_negative(caplog):
    """Tests that the connection attempt times out after the expected time, since the MongoDB URL is invalid."""
    invalid_config = DatabaseConfig(
        url=AnyUrl("mongodb://invalid_url_that_does_not_exist:8000"),
        timeout=3,
        main_database_name=test_app_config.database.main_database_name,
        main_collection_name=test_app_config.database.main_collection_name,
    )

    t1 = time.time()
    with pytest.raises(SystemExit) as exc:
        async with mongodb_context(invalid_config):
            pass
    t2 = time.time()

    assert exc.value.code == errno.EIO
    assert check_log(caplog, "ERROR", Client.ConnectionError)
    assert t2 - t1 >= invalid_config.timeout


@pytest.mark.parametrize("invalid_config", [
    dict(main_database_name=test_app_config.database.main_database_name, main_collection_name=" "),
    dict(main_database_name=" ", main_collection_name=test_app_config.database.main_collection_name)
])
@pytest.mark.usefixtures("_run_mongodb_server_instance")
async def test_main_database_and_collection_negative(invalid_config):
    """Tests that we fail when the name of the main database/collection is invalid, given a valid name for the other."""
    config = dict(timeout=1, url=test_app_config.database.url) | invalid_config
    with pytest.raises(SystemExit) as exc:
        async with mongodb_context(DatabaseConfig(**config)):
            pass
    assert exc.value.code == errno.ENODATA


@pytest.mark.usefixtures("_run_mongodb_server_instance")
async def test_reinitialize_different_config_negative(caplog):
    """Tests that we fail when trying to reinitialize with a different configuration."""
    different_config = DatabaseConfig(**(make_test_app_config_as_dict()["database"] | {"timeout": 0.1}))
    with pytest.raises(SystemExit) as exc:
        async with mongodb_context(test_app_config.database):
            await MongoDB.initialize(different_config)

    assert exc.value.code == errno.EIO
    assert check_log(caplog, "ERROR", Client.ReinitializeConfigError)


@pytest.mark.parametrize("config_with_wrong_type", [
    1, "1", 1.0, {}, None, [], (), make_test_app_config_as_dict()
])
@pytest.mark.usefixtures("_run_mongodb_server_instance")
async def test_invalid_config_type(caplog, config_with_wrong_type):
    """Tests that we fail when trying to initialize with a configuration of wrong type."""
    with pytest.raises(ValidationError):
        async with mongodb_context(config_with_wrong_type):
            pass


def check_log(caplog, level: str, response_error: ResponseError) -> bool:
    """An auxiliary function to check the log message."""
    for rec in caplog.records:
        if rec.levelname == level and (response_error.get_error_details()[1] in rec.message):
            return True
    return False


@pytest.mark.usefixtures("_run_mongodb_server_instance")
async def test_reinitialize_same_config_warning(caplog):
    """Tests the log (warning) when trying to reinitialize with the same configuration."""
    async with mongodb_context(test_app_config.database):
        await MongoDB.initialize(test_app_config.database)

    assert check_log(caplog, "WARNING", Client.AlreadyOpenError)


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

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
from pydantic import MongoDsn, ValidationError

from trolldb.database.errors import Client, Collections, Databases
from trolldb.database.mongodb import DatabaseConfig, MongoDB, get_id, get_ids, mongodb_context
from trolldb.test_utils.common import make_test_app_config_as_dict, test_app_config
from trolldb.test_utils.mongodb_database import TestDatabase


async def test_connection_timeout_negative(check_log):
    """Tests that the connection attempt times out after the expected time, since the MongoDB URL is invalid."""
    invalid_config = DatabaseConfig(
        url=MongoDsn("mongodb://invalid_url_that_does_not_exist:8000"),
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
    assert check_log("ERROR", Client.ConnectionError.get_error_details()[1])
    assert t2 - t1 >= invalid_config.timeout


@pytest.mark.parametrize(("error", "invalid_config"), [(
        Collections.NotFoundError,
        dict(main_database_name=test_app_config.database.main_database_name, main_collection_name=" ")),
    (
            Databases.NotFoundError,
            dict(main_database_name=" ", main_collection_name=test_app_config.database.main_collection_name))
])
@pytest.mark.usefixtures("_run_mongodb_server_instance")
async def test_main_database_and_collection_negative(check_log, error, invalid_config):
    """Tests that we fail when the name of the main database/collection is invalid, given a valid name for the other."""
    config = dict(timeout=1, url=test_app_config.database.url) | invalid_config
    with pytest.raises(SystemExit) as exc:
        async with mongodb_context(DatabaseConfig(**config)):
            pass
    assert exc.value.code == errno.ENODATA
    assert check_log("ERROR", error.get_error_details()[1])


@pytest.mark.usefixtures("mongodb_fixture")
async def test_reinitialize_different_config_negative(check_log):
    """Tests that we fail when trying to reinitialize with a different configuration."""
    different_config = DatabaseConfig(**(make_test_app_config_as_dict()["database"] | {"timeout": 0.1}))
    with pytest.raises(SystemExit) as exc:
        await MongoDB.initialize(different_config)
    assert exc.value.code == errno.EIO
    assert check_log("ERROR", Client.ReinitializeConfigError.get_error_details()[1])


@pytest.mark.parametrize("config_with_wrong_type", [
    1, "1", 1.0, {}, None, [], (), make_test_app_config_as_dict()
])
@pytest.mark.usefixtures("mongodb_fixture")
async def test_invalid_config_type(check_log, config_with_wrong_type):
    """Tests that we fail when trying to initialize with a configuration of wrong type."""
    with pytest.raises(ValidationError):
        async with mongodb_context(config_with_wrong_type):
            pass


@pytest.mark.usefixtures("mongodb_fixture")
async def test_reinitialize_same_config_warning(check_log):
    """Tests the log (warning) when trying to reinitialize with the same configuration."""
    await MongoDB.initialize(test_app_config.database)
    assert check_log("WARNING", Client.AlreadyOpenError.get_error_details()[1])


async def test_close_client_negative(check_log):
    """Tests that we fail to close a MongoDB client which has not been initialized."""
    with pytest.raises(SystemExit) as exc:
        MongoDB.close()
    assert exc.value.code == errno.EIO
    assert check_log("ERROR", Client.CloseNotAllowedError.get_error_details()[1])


@pytest.mark.usefixtures("mongodb_fixture")
async def test_client_close():
    """This is our way of testing :func:`trolldb.database.mongodb.MongoDB.close()`.

    Expect:
        - The `close` method can be called on the client and leads to the closure of the client
        - Further attempts to access the database after closing the client fails.
    """
    MongoDB.close()
    with pytest.raises(AttributeError):
        await MongoDB.list_database_names()


@pytest.mark.usefixtures("mongodb_fixture")
async def test_main_collection():
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


@pytest.mark.usefixtures("mongodb_fixture")
async def test_main_database():
    """Same as ``test_main_collection()`` but for the main database."""
    assert MongoDB.main_database() is not None
    assert MongoDB.main_database().name == test_app_config.database.main_database_name
    assert MongoDB.main_database() == await MongoDB.get_database(test_app_config.database.main_database_name)


@pytest.mark.usefixtures("mongodb_fixture")
async def test_get_database(check_log):
    """Tests the ``get_database()`` method given different inputs."""
    assert await MongoDB.get_database(None) == MongoDB.main_database()
    assert await MongoDB.get_database() == MongoDB.main_database()
    assert await MongoDB.get_database(test_app_config.database.main_database_name) == MongoDB.main_database()


@pytest.mark.usefixtures("mongodb_fixture")
async def test_get_collection(check_log):
    """Same as ``test_get_database()`` but for the ``get_collection()``."""
    assert await MongoDB.get_collection(None, None) == MongoDB.main_collection()
    assert await MongoDB.get_collection() == MongoDB.main_collection()

    collection = await MongoDB.get_collection(
        test_app_config.database.main_database_name,
        test_app_config.database.main_collection_name
    )
    assert collection == MongoDB.main_collection()


@pytest.mark.usefixtures("mongodb_fixture")
async def test_get_id():
    """Tests :func:`trolldb.database.mongodb.get_id` using all documents (one at a time)."""
    for _id in TestDatabase.get_document_ids_from_database():
        doc = MongoDB.main_collection().find_one({"_id": ObjectId(_id)})
        assert await get_id(doc) == _id


@pytest.mark.usefixtures("mongodb_fixture")
async def test_get_ids():
    """Tests :func:`trolldb.database.mongodb.get_ids` using all documents in one pass."""
    docs = MongoDB.main_collection().find({})
    assert Counter(await get_ids(docs)) == Counter(TestDatabase.get_document_ids_from_database())

"""Tests for the API server.

Note:
    The functionalities of the API server is not mocked! For the tests herein an actual API server will be running in a
    separate process. Moreover, a MongoDB instance is run with databases which are pre-filled with random data having
    similar characteristics to the real data. Actual requests will be sent to the API and the results will be asserted
    against expectations.
"""

import pytest
from fastapi import status

from trolldb.test_utils.common import assert_equal, http_get
from trolldb.test_utils.mongodb_database import TestDatabase, test_mongodb_context


@pytest.mark.usefixtures("_test_server_fixture")
def test_root():
    """Checks that the server is up and running, i.e. the root routes responds with 200."""
    assert_equal(http_get().status, status.HTTP_200_OK)


@pytest.mark.usefixtures("_test_server_fixture")
def test_platforms():
    """Checks that the retrieved platform names match the expected names."""
    assert_equal(http_get("platforms").json(), TestDatabase.platform_names)


@pytest.mark.usefixtures("_test_server_fixture")
def test_sensors():
    """Checks that the retrieved sensor names match the expected names."""
    assert_equal(http_get("sensors").json(), TestDatabase.sensors)


@pytest.mark.usefixtures("_test_server_fixture")
def test_database_names():
    """Checks that the retrieved database names match the expected names."""
    assert_equal(http_get("databases").json(), TestDatabase.database_names)
    assert_equal(http_get("databases?exclude_defaults=True").json(), TestDatabase.database_names)
    assert_equal(http_get("databases?exclude_defaults=False").json(), TestDatabase.all_database_names)


@pytest.mark.usefixtures("_test_server_fixture")
def test_database_names_negative():
    """Checks that the non-existing databases cannot be found."""
    assert_equal(http_get("databases/non_existing_database").status, status.HTTP_404_NOT_FOUND)


@pytest.mark.usefixtures("_test_server_fixture")
def test_collections():
    """Checks the presence of existing collections and that the ids of documents therein can be correctly retrieved."""
    with test_mongodb_context() as client:
        for database_name, collection_name in zip(TestDatabase.database_names, TestDatabase.collection_names,
                                                  strict=False):
            # Collections exist
            assert_equal(
                http_get(f"databases/{database_name}").json(),
                [collection_name]
            )

            # Document ids are correct
            assert_equal(
                http_get(f"databases/{database_name}/{collection_name}").json(),
                {str(doc["_id"]) for doc in client[database_name][collection_name].find({})}
            )


@pytest.mark.usefixtures("_test_server_fixture")
def test_collections_negative():
    """Checks that the non-existing collections cannot be found."""
    for database_name in TestDatabase.database_names:
        assert_equal(
            http_get(f"databases/{database_name}/non_existing_collection").status,
            status.HTTP_404_NOT_FOUND
        )

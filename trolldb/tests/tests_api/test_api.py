"""Tests for the API server.

Note:
    The functionalities of the API server is not mocked! For the tests herein an actual API server will be running in a
    separate process. Moreover, a MongoDB instance is run with databases which are pre-filled with random data having
    similar characteristics to the real data. Actual requests will be sent to the API and the results will be asserted
    against expectations.
"""

from collections import Counter

import pytest
from fastapi import status

from trolldb.test_utils.common import http_get
from trolldb.test_utils.mongodb_database import TestDatabase, mongodb_for_test_context


def collections_exists(test_collection_names: list[str], expected_collection_name: list[str]) -> bool:
    """Checks if the test and expected list of collection names match."""
    return Counter(test_collection_names) == Counter(expected_collection_name)


def document_ids_are_correct(test_ids: list[str], expected_ids: list[str]) -> bool:
    """Checks if the test (retrieved from the API) and expected list of (document) ids match."""
    return Counter(test_ids) == Counter(expected_ids)


@pytest.mark.usefixtures("_test_server_fixture")
def test_root():
    """Checks that the server is up and running, i.e. the root routes responds with 200."""
    assert http_get().status == status.HTTP_200_OK


@pytest.mark.usefixtures("_test_server_fixture")
def test_platforms():
    """Checks that the retrieved platform names match the expected names."""
    assert set(http_get("platforms").json()) == set(TestDatabase.platform_names)


@pytest.mark.usefixtures("_test_server_fixture")
def test_sensors():
    """Checks that the retrieved sensor names match the expected names."""
    assert set(http_get("sensors").json()) == set(TestDatabase.sensors)


@pytest.mark.usefixtures("_test_server_fixture")
def test_database_names():
    """Checks that the retrieved database names match the expected names."""
    assert Counter(http_get("databases").json()) == Counter(TestDatabase.database_names)
    assert Counter(http_get("databases?exclude_defaults=True").json()) == Counter(TestDatabase.database_names)
    assert Counter(http_get("databases?exclude_defaults=False").json()) == Counter(TestDatabase.all_database_names)


@pytest.mark.usefixtures("_test_server_fixture")
def test_database_names_negative():
    """Checks that the non-existing databases cannot be found."""
    assert http_get("databases/non_existing_database").status == status.HTTP_404_NOT_FOUND


@pytest.mark.usefixtures("_test_server_fixture")
def test_collections():
    """Checks the presence of existing collections and that the ids of documents therein can be correctly retrieved."""
    with mongodb_for_test_context() as client:
        for database_name, collection_name in zip(TestDatabase.database_names, TestDatabase.collection_names,
                                                  strict=False):
            assert collections_exists(
                http_get(f"databases/{database_name}").json(),
                [collection_name]
            )
            assert document_ids_are_correct(
                http_get(f"databases/{database_name}/{collection_name}").json(),
                [str(doc["_id"]) for doc in client[database_name][collection_name].find({})]
            )


@pytest.mark.usefixtures("_test_server_fixture")
def test_collections_negative():
    """Checks that the non-existing collections cannot be found."""
    for database_name in TestDatabase.database_names:
        assert http_get(f"databases/{database_name}/non_existing_collection").status == status.HTTP_404_NOT_FOUND

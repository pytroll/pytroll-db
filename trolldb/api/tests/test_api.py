from fastapi import status

from test_utils.common import assert_equal, http_get
from test_utils.mock_mongodb_database import test_mongodb_context, TestDatabase


def test_root():
    """
    Checks that the server is up and running, i.e. the root routes responds with 200.
    """
    assert_equal(http_get().status, status.HTTP_200_OK)


def test_platforms():
    """
    Checks that the retrieved platform names match the expected names.
    """
    assert_equal(http_get("platforms").json(), TestDatabase.platform_names)


def test_sensors():
    """
    Checks that the retrieved sensor names match the expected names.
    """
    assert_equal(http_get("sensors").json(), TestDatabase.sensors)


def test_database_names():
    """
    Checks that the retrieved database names match the expected names.
    """
    assert_equal(http_get("databases").json(), TestDatabase.database_names)
    assert_equal(http_get("databases?exclude_defaults=True").json(), TestDatabase.database_names)
    assert_equal(http_get("databases?exclude_defaults=False").json(), TestDatabase.all_database_names)


def test_database_names_negative():
    """
    Checks that the non-existing databases cannot be found.
    """
    assert_equal(http_get(f"databases/non_existing_database").status, status.HTTP_404_NOT_FOUND)


def test_collections():
    """
    Check the presence of existing collections and that the ids of documents therein can be correctly retrieved.
    """
    with test_mongodb_context() as client:
        for database_name, collection_name in zip(TestDatabase.database_names, TestDatabase.collection_names):
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


def test_collections_negative():
    """
    Checks that the non-existing collections cannot be found.
    """
    for database_name, collection_name in zip(TestDatabase.database_names, TestDatabase.collection_names):
        assert_equal(
            http_get(f"databases/{database_name}/non_existing_collection").status,
            status.HTTP_404_NOT_FOUND
        )

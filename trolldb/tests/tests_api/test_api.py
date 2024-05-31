"""Tests for the API server.

Note:
    The functionalities of the API server is not mocked! For the tests herein an actual API server will be running in a
    separate process. Moreover, a MongoDB instance is run with databases which are pre-filled with random data having
    similar characteristics to the real data. Actual requests will be sent to the API and the results will be asserted
    against expectations.
"""

from collections import Counter
from datetime import datetime

import pytest
from fastapi import status

from trolldb.test_utils.common import http_get, test_app_config
from trolldb.test_utils.mongodb_database import TestDatabase, mongodb_for_test_context

main_database_name = test_app_config.database.main_database_name
main_collection_name = test_app_config.database.main_collection_name


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


def collections_exists(test_collection_names: list[str], expected_collection_name: list[str]) -> bool:
    """Checks if the test and expected list of collection names match."""
    return Counter(test_collection_names) == Counter(expected_collection_name)


def document_ids_are_correct(test_ids: list[str], expected_ids: list[str]) -> bool:
    """Checks if the test (retrieved from the API) and expected list of (document) ids match."""
    return Counter(test_ids) == Counter(expected_ids)


@pytest.mark.usefixtures("_test_server_fixture")
def test_collections_negative():
    """Checks that the non-existing collections cannot be found."""
    for database_name in TestDatabase.database_names:
        assert http_get(f"databases/{database_name}/non_existing_collection").status == status.HTTP_404_NOT_FOUND


@pytest.mark.usefixtures("_test_server_fixture")
def test_datetime():
    """Checks that the datetime route works properly."""
    assert http_get("datetime").json() == TestDatabase.find_min_max_datetime()


@pytest.mark.usefixtures("_test_server_fixture")
def test_queries_all():
    """Tests that the queries route returns all documents when no actual queries are given."""
    assert document_ids_are_correct(
        http_get("queries").json(),
        [str(doc["_id"]) for doc in TestDatabase.get_all_documents_from_database()]
    )


@pytest.mark.usefixtures("_test_server_fixture")
@pytest.mark.parametrize(("key", "values"), [
    ("platform", TestDatabase.unique_platform_names),
    ("sensor", TestDatabase.unique_sensors)
])
def test_queries_platform_or_sensor(key: str, values: list[str]):
    """Tests the platform and sensor queries, one at a time.

    There is only a single key in the query, but it has multiple corresponding values.
    """
    for i in range(len(values)):
        assert query_results_are_correct(
            [key],
            [values[:i]]
        )


def make_query_string(keys: list[str], values_list: list[list[str] | datetime]) -> str:
    """Makes a single query string for all the given queries."""
    query_buffer = []
    for key, value_list in zip(keys, values_list, strict=True):
        query_buffer += [f"{key}={value}" for value in value_list]
    return "&".join(query_buffer)


def query_results_are_correct(keys: list[str], values_list: list[list[str] | datetime]) -> bool:
    """Checks if the retrieved result from querying the database via the API matches the expected result.

    There can be more than one query `key/value` pair.

    Args:
        keys:
            A list of all query keys, e.g. ``keys=["platform", "sensor"]``

        values_list:
            A list in which each element is a list of values itself. The `nth` element corresponds to the `nth` key in
            the ``keys``.

    Returns:
        A boolean flag indicating whether the retrieved result matches the expected result.
    """
    query_string = make_query_string(keys, values_list)

    return (
            Counter(http_get(f"queries?{query_string}").json()) ==
            Counter(TestDatabase.match_query(
                **{label: value_list for label, value_list in zip(keys, values_list, strict=True)}
            ))
    )


@pytest.mark.usefixtures("_test_server_fixture")
def test_queries_mix_platform_sensor():
    """Tests a mix of platform and sensor queries."""
    for n_plt, n_sns in zip([1, 1, 2, 3, 3], [1, 3, 2, 1, 3], strict=False):
        assert query_results_are_correct(
            ["platform", "sensor"],
            [TestDatabase.unique_platform_names[:n_plt], TestDatabase.unique_sensors[:n_sns]]
        )


@pytest.mark.usefixtures("_test_server_fixture")
def test_queries_time():
    """Checks that a single time query works properly."""
    res = http_get("datetime").json()
    time_min = datetime.fromisoformat(res["start_time"]["_min"]["_time"])
    time_max = datetime.fromisoformat(res["end_time"]["_max"]["_time"])

    assert single_query_is_correct(
        "time_min",
        time_min
    )

    assert single_query_is_correct(
        "time_max",
        time_max
    )


def single_query_is_correct(key: str, value: str | datetime) -> bool:
    """Checks if the given single query, denoted by ``key`` matches correctly against the ``value``."""
    return (
            Counter(http_get(f"queries?{key}={value}").json()) ==
            Counter(TestDatabase.match_query(**{key: value}))
    )

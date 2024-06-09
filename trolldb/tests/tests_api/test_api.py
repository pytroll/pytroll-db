"""Tests for the API server.

Note:
    The functionalities of the API server is not mocked! For the tests herein an actual MongoDB instance is run with
    databases which are pre-filled with random data having similar characteristics to the real data. Actual requests
    will be sent to the API and the results will be asserted against expectations.
"""

from collections import Counter
from datetime import datetime

import pytest
import pytest_asyncio
from fastapi import status
from httpx import ASGITransport, AsyncClient

from trolldb.api.fastapi_app import fastapi_app
from trolldb.database.mongodb import mongodb_context
from trolldb.test_utils.common import test_app_config
from trolldb.test_utils.mongodb_database import TestDatabase, mongodb_for_test_context
from trolldb.test_utils.mongodb_instance import running_prepared_database_context

main_database_name = test_app_config.database.main_database_name
main_collection_name = test_app_config.database.main_collection_name


@pytest_asyncio.fixture()
async def server_client():
    """A fixture to enclose the server async client context manager and start a prepared database.

    TODO: this needs to be optimized so that the database is not closed and reopened for each test!
    """
    with running_prepared_database_context():
        async with mongodb_context(test_app_config.database):
            async with AsyncClient(transport=ASGITransport(app=fastapi_app), base_url="http://localhost") as ac:
                yield ac


async def test_root(server_client):
    """Checks that the server is up and running, i.e. the root routes responds with 200."""
    assert (await server_client.get("")).status_code == status.HTTP_200_OK


async def test_platforms(server_client):
    """Checks that the retrieved platform names match the expected names."""
    assert set((await server_client.get("/platforms")).json()) == set(TestDatabase.platform_names)


async def test_sensors(server_client):
    """Checks that the retrieved sensor names match the expected names."""
    assert set((await server_client.get("/sensors")).json()) == set(TestDatabase.sensors)


async def test_database_names(server_client):
    """Checks that the retrieved database names match the expected names."""
    assert Counter((await server_client.get("/databases")).json()) == Counter(TestDatabase.database_names)
    assert Counter((await server_client.get("/databases?exclude_defaults=True")).json()) == Counter(
        TestDatabase.database_names)
    assert Counter((await server_client.get("/databases?exclude_defaults=False")).json()) == Counter(
        TestDatabase.all_database_names)


async def test_database_names_negative(server_client):
    """Checks that the non-existing databases cannot be found."""
    assert (await server_client.get("/databases/non_existing_database")).status_code == status.HTTP_404_NOT_FOUND


async def test_collections(server_client):
    """Checks the presence of existing collections and that the ids of documents therein can be correctly retrieved."""
    with mongodb_for_test_context() as client:
        for database_name, collection_name in zip(TestDatabase.database_names, TestDatabase.collection_names,
                                                  strict=False):
            assert collections_exists(
                (await server_client.get(f"databases/{database_name}")).json(),
                [collection_name]
            )
            assert document_ids_are_correct(
                (await server_client.get(f"databases/{database_name}/{collection_name}")).json(),
                [str(doc["_id"]) for doc in client[database_name][collection_name].find({})]
            )


def collections_exists(test_collection_names: list[str], expected_collection_name: list[str]) -> bool:
    """Checks if the test and expected list of collection names match."""
    return Counter(test_collection_names) == Counter(expected_collection_name)


def document_ids_are_correct(test_ids: list[str], expected_ids: list[str]) -> bool:
    """Checks if the test (retrieved from the API) and expected list of (document) ids match."""
    return Counter(test_ids) == Counter(expected_ids)


async def test_collections_negative(server_client):
    """Checks that the non-existing collections cannot be found."""
    for database_name in TestDatabase.database_names:
        assert (await server_client.get(
            f"databases/{database_name}/non_existing_collection")).status_code == status.HTTP_404_NOT_FOUND


async def test_datetime(server_client):
    """Checks that the datetime route works properly."""
    assert (await server_client.get("datetime")).json() == TestDatabase.find_min_max_datetime()


async def test_queries_all(server_client):
    """Tests that the queries route returns all documents when no actual queries are given."""
    assert document_ids_are_correct(
        (await server_client.get("queries")).json(),
        TestDatabase.get_document_ids_from_database()
    )


@pytest.mark.parametrize(("key", "values"), [
    ("platform", TestDatabase.unique_platform_names),
    ("sensor", TestDatabase.unique_sensors)
])
async def test_queries_platform_or_sensor(server_client, key: str, values: list[str]):
    """Tests the platform and sensor queries, one at a time.

    There is only a single key in the query, but it has multiple corresponding values.
    """
    for i in range(len(values)):
        assert await query_results_are_correct(
            server_client,
            [key],
            [values[:i]]
        )


def make_query_string(keys: list[str], values_list: list[list[str] | datetime]) -> str:
    """Makes a single query string for all the given queries."""
    query_buffer = []
    for key, value_list in zip(keys, values_list, strict=True):
        query_buffer += [f"{key}={value}" for value in value_list]
    return "&".join(query_buffer)


async def query_results_are_correct(server_client: AsyncClient, keys: list[str],
                                    values_list: list[list[str] | datetime]) -> bool:
    """Checks if the retrieved result from querying the database via the API matches the expected result.

    There can be more than one query `key/value` pair.

    Args:
        server_client:
            The async client object to make API calls.

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
            Counter((await server_client.get(f"queries?{query_string}")).json()) ==
            Counter(TestDatabase.match_query(
                **{label: value_list for label, value_list in zip(keys, values_list, strict=True)}
            ))
    )


async def test_queries_mix_platform_sensor(server_client):
    """Tests a mix of platform and sensor queries."""
    for n_plt, n_sns in zip([1, 1, 2, 3, 3], [1, 3, 2, 1, 3], strict=False):
        assert await query_results_are_correct(
            server_client,
            ["platform", "sensor"],
            [TestDatabase.unique_platform_names[:n_plt], TestDatabase.unique_sensors[:n_sns]]
        )


async def test_queries_time(server_client):
    """Checks that a single time query works properly."""
    res = (await server_client.get("/datetime")).json()
    time_min = datetime.fromisoformat(res["start_time"]["_min"]["_time"])
    time_max = datetime.fromisoformat(res["end_time"]["_max"]["_time"])

    assert await single_query_is_correct(
        server_client,
        "time_min",
        time_min
    )

    assert await single_query_is_correct(
        server_client,
        "time_max",
        time_max
    )


async def single_query_is_correct(server_client: AsyncClient, key: str, value: str | datetime) -> bool:
    """Checks if the given single query, denoted by ``key`` matches correctly against the ``value``."""
    return (
            Counter((await server_client.get(f"queries?{key}={value}")).json()) ==
            Counter(TestDatabase.match_query(**{key: value}))
    )

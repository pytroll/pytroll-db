"""The module which provides testing utilities to make MongoDB databases/collections and fill them with test data."""
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timedelta
from random import choices, randint, shuffle
from typing import Any, ClassVar, Generator

from pymongo import MongoClient

from trolldb.config.config import DatabaseConfig
from trolldb.test_utils.common import test_app_config


@contextmanager
def mongodb_for_test_context(
        database_config: DatabaseConfig = test_app_config.database) -> Generator[MongoClient, Any, None]:
    """A context manager for the MongoDB client given test configurations.

    Note:
        This is based on `Pymongo` and not the `motor` async driver. For testing purposes this is sufficient, and we
        do not need async capabilities.

    Args:
        database_config (Optional, default :obj:`test_app_config.database`):
            The configuration object for the database.

    Yields:
        MongoClient:
            The MongoDB client object (from `Pymongo`)
    """
    client = None
    try:
        client = MongoClient(database_config.url.unicode_string(), connectTimeoutMS=database_config.timeout * 1000)
        yield client
    finally:
        if client is not None:
            client.close()


class Time:
    """A static class to enclose functionalities for generating random timestamps."""

    min_start_time: ClassVar[datetime] = datetime(2019, 1, 1, 0, 0, 0)
    """The minimum timestamp which is allowed to appear in our data."""

    max_end_time: ClassVar[datetime] = datetime(2024, 1, 1, 0, 0, 0)
    """The maximum timestamp which is allowed to appear in our data."""

    delta_time: ClassVar[int] = int((max_end_time - min_start_time).total_seconds())
    """The difference between the maximum and minimum timestamps in seconds."""

    @staticmethod
    def random_interval_secs(max_interval_secs: int) -> timedelta:
        """Generates a random time interval between zero and the given max interval in seconds."""
        # We suppress ruff (S311) here as we are not generating anything cryptographic here!
        return timedelta(seconds=randint(0, max_interval_secs))  # noqa: S311

    @staticmethod
    def random_start_time() -> datetime:
        """Generates a random start time.

        The start time has a lower bound which is specified by :obj:`~Time.min_start_time` and an upper bound given by
        :obj:`~Time.max_end_time`.
        """
        return Time.min_start_time + Time.random_interval_secs(Time.delta_time)

    @staticmethod
    def random_end_time(start_time: datetime, max_interval_secs: int = 300) -> datetime:
        """Generates a random end time.

        The end time is within ``max_interval_secs`` seconds from the given ``start_time``. By default, the interval
        is set to 300 seconds (5 minutes).
        """
        return start_time + Time.random_interval_secs(max_interval_secs)


class Document:
    """A class which defines functionalities to generate database documents/data which are similar to real data."""

    def __init__(self, platform_name: str, sensor: str) -> None:
        """Initializes the document given its platform and sensor names."""
        self.platform_name = platform_name
        self.sensor = sensor
        self.start_time = Time.random_start_time()
        self.end_time = Time.random_end_time(self.start_time)

    def generate_dataset(self, max_count: int) -> list[dict]:
        """Generates the dataset for a given document.

        This corresponds to the list of files which are stored in each document. The number of items in a dataset is
        randomly chosen from 1 to ``max_count`` for each document.
        """
        dataset = []
        # We suppress ruff (S311) here as we are not generating anything cryptographic here!
        n = randint(1, max_count)  # noqa: S311
        for i in range(n):
            txt = f"{self.platform_name}_{self.sensor}_{self.start_time}_{self.end_time}_{i}"
            dataset.append({
                "uri": f"/pytroll/{txt}",
                "uid": f"{txt}.EXT1",
                "path": f"{txt}.EXT1.EXT2"
            })
        return dataset

    def like_mongodb_document(self) -> dict:
        """Returns a dictionary which resembles the format we have for our real data when saving them to MongoDB."""
        return {
            "platform_name": self.platform_name,
            "sensor": self.sensor,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "dataset": self.generate_dataset(30)
        }


class TestDatabase:
    """A static class which encloses functionalities to prepare and fill the test database with test data."""

    unique_platform_names: ClassVar[list[str]] = ["PA", "PB", "PC"]
    """The unique platform names that will be used to generate the sample of all platform names."""

    # We suppress ruff (S311) here as we are not generating anything cryptographic here!
    platform_names: ClassVar[list[str]] = choices(["PA", "PB", "PC"], k=20)  # noqa: S311
    """Example platform names.

    Warning:
        The value of this variable changes randomly every time. What you see above is just an example which has been
        generated as a result of building the documentation!
    """

    unique_sensors: ClassVar[list[str]] = ["SA", "SB", "SC"]
    """The unique sensor names that will be used to generate the sample of all sensor names."""

    # We suppress ruff (S311) here as we are not generating anything cryptographic here!
    sensors: ClassVar[list[str]] = choices(["SA", "SB", "SC"], k=20)  # noqa: S311
    """Example sensor names.

    Warning:
        The value of this variable changes randomly every time. What you see above is just an example which has been
        generated as a result of building the documentation!
    """

    database_names: ClassVar[list[str]] = [test_app_config.database.main_database_name, "another_test_database"]
    """List of all database names.

    The first element is the main database that will be queried by the API and includes the test data. The second
    database is for testing scenarios when one attempts to access another existing database or collection.
    """

    collection_names: ClassVar[list[str]] = [test_app_config.database.main_collection_name, "another_test_collection"]
    """List of all collection names.

    The first element is the main collection that will be queried by the API and includes the test data. The second
    collection is for testing scenarios when one attempts to access another existing collection.
    """

    all_database_names: ClassVar[list[str]] = ["admin", "config", "local", *database_names]
    """All database names including the default ones which are automatically created by MongoDB."""

    documents: ClassVar[list[dict]] = []
    """The list of documents which include test data."""

    @classmethod
    def generate_documents(cls, random_shuffle: bool = True) -> None:
        """Generates test documents which for practical purposes resemble real data.

        Warning:
            This method is not pure! The side effect is that the :obj:`TestDatabase.documents` is reset to new values.
        """
        cls.documents = [
            Document(p, s).like_mongodb_document() for p, s in zip(cls.platform_names, cls.sensors, strict=False)
        ]
        if random_shuffle:
            shuffle(cls.documents)

    @classmethod
    def reset(cls) -> None:
        """Resets all the databases/collections.

        This is done by deleting all documents in the collections and then inserting a single empty document, i.e.
        ``{}``, in them.
        """
        with mongodb_for_test_context() as client:
            for db_name, coll_name in zip(cls.database_names, cls.collection_names, strict=False):
                db = client[db_name]
                collection = db[coll_name]
                collection.delete_many({})
                collection.insert_one({})

    @classmethod
    def write_test_data(cls) -> None:
        """Fills databases/collections with test data."""
        with mongodb_for_test_context() as client:
            # The following function call has side effects!
            cls.generate_documents()
            collection = client[
                test_app_config.database.main_database_name
            ][
                test_app_config.database.main_collection_name
            ]
            collection.delete_many({})
            collection.insert_many(cls.documents)

    @classmethod
    def get_documents_from_database(cls) -> list[dict]:
        """Retrieves all the documents from the database.

        Returns:
            A list of all documents from the database. This matches the content of :obj:`~TestDatabase.documents` with
            the addition of `IDs` which are assigned by the MongoDB.
        """
        with mongodb_for_test_context() as client:
            collection = client[
                test_app_config.database.main_database_name
            ][
                test_app_config.database.main_collection_name
            ]
            documents = list(collection.find({}))
        return documents

    @classmethod
    def get_document_ids_from_database(cls) -> list[str]:
        """Retrieves all the document IDs from the database."""
        return [str(doc["_id"]) for doc in cls.get_documents_from_database()]

    @classmethod
    def find_min_max_datetime(cls) -> dict[str, dict]:
        """Finds the minimum and the maximum for both the ``start_time`` and the ``end_time``.

        We use `brute force` for this purpose. We set the minimum to a large value (year 2100) and the maximum to a
        small value (year 1900). We then iterate through all documents and update the extrema.

        Returns:
            A dictionary whose schema matches the response returned by the ``/datetime`` route of the API.
        """
        result = dict(
            start_time=dict(
                _min=dict(_id=None, _time="2100-01-01T00:00:00"),
                _max=dict(_id=None, _time="1900-01-01T00:00:00")
            ),
            end_time=dict(
                _min=dict(_id=None, _time="2100-01-01T00:00:00"),
                _max=dict(_id=None, _time="1900-01-01T00:00:00"))
        )

        documents = cls.get_documents_from_database()

        for document in documents:
            for k in ["start_time", "end_time"]:
                dt = document[k].isoformat()
                if dt > result[k]["_max"]["_time"]:
                    result[k]["_max"]["_time"] = dt
                    result[k]["_max"]["_id"] = str(document["_id"])

                if dt < result[k]["_min"]["_time"]:
                    result[k]["_min"]["_time"] = dt
                    result[k]["_min"]["_id"] = str(document["_id"])

        return result

    @classmethod
    def _query_platform_sensor(cls, document, platform=None, sensor=None) -> bool:
        """An auxiliary method to the :func:`TestDatabase.match_query`."""
        should_remove = False

        if platform:
            should_remove = platform and document["platform_name"] not in platform

        if sensor and not should_remove:
            should_remove = document["sensor"] not in sensor

        return should_remove

    @classmethod
    def _query_time(cls, document, time_min=None, time_max=None) -> bool:
        """An auxiliary method to the :func:`TestDatabase.match_query`."""
        should_remove = False

        if time_min and time_max and not should_remove:
            should_remove = document["end_time"] < time_min or document["start_time"] > time_max

        if time_min and not time_max and not should_remove:
            should_remove = document["end_time"] < time_min

        if time_max and not time_min and not should_remove:
            should_remove = document["end_time"] > time_max

        return should_remove

    @classmethod
    def match_query(cls, platform=None, sensor=None, time_min=None, time_max=None) -> list[str]:
        """Matches the given query.

        We first take all the documents and then progressively remove all that do not match the given queries until
        we end up with those that match. When a query is ``None``, it does not have any effect on the results.
        This method will be used in testing the ``/queries`` route of the API.
        """
        documents = cls.get_documents_from_database()

        buffer = deepcopy(documents)
        for document in documents:
            should_remove = cls._query_platform_sensor(document, platform, sensor)
            if not should_remove:
                should_remove = cls._query_time(document, time_min, time_max)
            if should_remove and document in buffer:
                buffer.remove(document)

        return [str(item["_id"]) for item in buffer]

    @classmethod
    def prepare(cls) -> None:
        """Prepares the MongoDB instance by first resetting the database and filling it with generated test data."""
        cls.reset()
        cls.write_test_data()

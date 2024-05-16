"""The module which provides testing utilities to make MongoDB databases/collections and fill them with test data."""

from contextlib import contextmanager
from datetime import datetime, timedelta
from random import randint, shuffle
from typing import Any, Iterator

from pymongo import MongoClient

from trolldb.config.config import DatabaseConfig
from trolldb.test_utils.common import test_app_config


@contextmanager
def test_mongodb_context(database_config: DatabaseConfig = test_app_config.database) -> Iterator[MongoClient]:
    """A context manager for the MongoDB client given test configurations.

    Note:
        This is based on `pymongo` and not the `motor` async driver. For testing purposes this is sufficient and we
        do not need async capabilities.
    """
    client = None
    try:
        client = MongoClient(database_config.url.unicode_string(), connectTimeoutMS=database_config.timeout)
        yield client
    finally:
        if client is not None:
            client.close()


def random_sample(items: list[Any], size: int = 10) -> list[Any]:
    """Generates a random sample of ``size`` elements, using the given list of items."""
    last_index = len(items) - 1
    # We suppress ruff here as we are not generating anything cryptographic here!
    indices = [randint(0, last_index) for _ in range(size)]  # noqa: S311
    return [items[i] for i in indices]


class Time:
    """A static class to enclose functionalities for generating random time stamps."""

    min_start_time = datetime(2019, 1, 1, 0, 0, 0)
    """The minimum timestamp."""

    max_end_time = datetime(2024, 1, 1, 0, 0, 0)
    """The maximum timestamp."""

    delta_time = int((max_end_time - min_start_time).total_seconds())
    """The difference between the maximum and minimum timestamps in seconds."""

    @staticmethod
    def random_interval_secs(max_interval_secs: int) -> timedelta:
        """Generates a random time interval between zero and the given max interval."""
        # We suppress ruff here as we are not generating anything cryptographic here!
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

        The end time is within ``max_interval_secs`` seconds from the given ``start_time``.
        """
        return start_time + Time.random_interval_secs(max_interval_secs)


class Document:
    """A class which defines functionalities to generate documents data which are similar to real data."""

    def __init__(self, platform_name: str, sensor: str) -> None:
        """Initializes the document given its platform and sensor names."""
        self.platform_name = platform_name
        self.sensor = sensor
        self.start_time = Time.random_start_time()
        self.end_time = Time.random_end_time(self.start_time)

    def generate_dataset(self, max_count: int) -> list[dict]:
        """Generates the dataset for a given document.

        This corresponds to the list of files which are stored in each document. The number of datasets is randomly
        chosen from 1 to ``max_count`` for each document.
        """
        dataset = []
        # We suppress ruff here as we are not generating anything cryptographic here!
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
    """The class which encloses functionalities to prepare and fill the test database with mock data."""

    platform_names = random_sample(["PA", "PB", "PC"])
    """Example platform names."""

    sensors = random_sample(["SA", "SB", "SC"])
    """Example sensor names."""

    database_names = [test_app_config.database.main_database_name, "another_mock_database"]
    """List of all database names.

    The first element is the main database that will be queried by the API and includes the mock data. The second
    database is for testing scenarios when one attempts to access another existing database or collection.
    """

    collection_names = [test_app_config.database.main_collection_name, "another_mock_collection"]
    """List of all collection names.

    The first element is the main collection that will be queried by the API and includes the mock data. The second
    collection is for testing scenarios when one attempts to access another existing collection.
    """

    all_database_names = ["admin", "config", "local", *database_names]
    """All database names including the default ones which are automatically created by MongoDB."""

    documents = []
    """The list of documents which include mock data."""

    @classmethod
    def generate_documents(cls, random_shuffle: bool = True) -> list:
        """Generates test documents which for practical purposes resemble real data."""
        documents = [Document(p, s).like_mongodb_document() for p, s in zip(cls.platform_names, cls.sensors,
                                                                            strict=False)]
        if random_shuffle:
            shuffle(documents)
        return documents

    @classmethod
    def reset(cls):
        """Resets all the databases/collections."""
        with test_mongodb_context() as client:
            for db_name, coll_name in zip(cls.database_names, cls.collection_names, strict=False):
                db = client[db_name]
                collection = db[coll_name]
                collection.delete_many({})
                collection.insert_one({})

    @classmethod
    def write_mock_date(cls):
        """Fills databases/collections with mock data."""
        with test_mongodb_context() as client:
            cls.documents = cls.generate_documents()
            collection = client[test_app_config.database.main_database_name][
                test_app_config.database.main_collection_name]
            collection.insert_many(cls.documents)

    @classmethod
    def prepare(cls):
        """Prepares the instance by first resetting all databases/collections and filling them with mock data."""
        cls.reset()
        cls.write_mock_date()

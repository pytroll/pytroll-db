from contextlib import contextmanager
from datetime import datetime, timedelta
from random import randint, shuffle
from typing import Any

from pymongo import MongoClient

from trolldb.config.config import DatabaseConfig
from trolldb.test_utils.common import test_app_config


@contextmanager
def test_mongodb_context(database_config: DatabaseConfig = test_app_config.database):
    client = None
    try:
        client = MongoClient(database_config.url.unicode_string(), connectTimeoutMS=database_config.timeout)
        yield client
    finally:
        if client is not None:
            client.close()


def random_sample(items: list[Any], size=10):
    last_index = len(items) - 1
    indices = [randint(0, last_index) for _ in range(size)]
    return [items[i] for i in indices]


class Time:
    min_start_time = datetime(2019, 1, 1, 0, 0, 0)
    max_end_time = datetime(2024, 1, 1, 0, 0, 0)
    delta_time = int((max_end_time - min_start_time).total_seconds())

    @staticmethod
    def random_interval_secs(max_interval_secs):
        return timedelta(seconds=randint(0, max_interval_secs))

    @staticmethod
    def random_start_time():
        return Time.min_start_time + Time.random_interval_secs(Time.delta_time)

    @staticmethod
    def random_end_time(start_time: datetime, max_interval_secs: int = 300):
        return start_time + Time.random_interval_secs(max_interval_secs)


class Document:
    def __init__(self, platform_name: str, sensor: str):
        self.platform_name = platform_name
        self.sensor = sensor
        self.start_time = Time.random_start_time()
        self.end_time = Time.random_end_time(self.start_time)

    def generate_dataset(self, max_count: int):
        dataset = []
        n = randint(1, max_count)
        for i in range(n):
            txt = f"{self.platform_name}_{self.sensor}_{self.start_time}_{self.end_time}_{i}"
            dataset.append({
                "uri": f"/pytroll/{txt}",
                "uid": f"{txt}.EXT1",
                "path": f"{txt}.EXT1.EXT2"
            })
        return dataset

    def like_mongodb_document(self):
        return {
            "platform_name": self.platform_name,
            "sensor": self.sensor,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "dataset": self.generate_dataset(30)
        }


class TestDatabase:
    platform_names = random_sample(["PA", "PB", "PC"])
    sensors = random_sample(["SA", "SB", "SC"])

    database_names = [test_app_config.database.main_database_name, "another_mock_database"]
    collection_names = [test_app_config.database.main_collection_name, "another_mock_collection"]
    all_database_names = ["admin", "config", "local", *database_names]

    documents = []

    @classmethod
    def generate_documents(cls, random_shuffle=True) -> list:
        documents = [Document(p, s).like_mongodb_document() for p, s in zip(cls.platform_names, cls.sensors)]
        if random_shuffle:
            shuffle(documents)
        return documents

    @classmethod
    def reset(cls):
        with test_mongodb_context() as client:
            for db_name, coll_name in zip(cls.database_names, cls.collection_names):
                db = client[db_name]
                collection = db[coll_name]
                collection.delete_many({})
                collection.insert_one({})

    @classmethod
    def write_mock_date(cls):
        with test_mongodb_context() as client:
            cls.documents = cls.generate_documents()
            collection = client[test_app_config.database.main_database_name][
                test_app_config.database.main_collection_name]
            collection.insert_many(cls.documents)

    @classmethod
    def prepare(cls):
        cls.reset()
        cls.write_mock_date()

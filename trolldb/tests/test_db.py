"""Tests for the message recording into database."""

from contextlib import contextmanager

import pytest
import yaml
from posttroll.message import Message
from posttroll.testing import patched_subscriber_recv

from trolldb.cli import record_messages, record_messages_from_command_line, record_messages_from_config
from trolldb.database.mongodb import MongoDB, mongodb_context
from trolldb.test_utils.common import test_app_config
from trolldb.test_utils.mongodb_database import TestDatabase
from trolldb.test_utils.mongodb_instance import mongodb_instance_server_process_context

FILENAME = "20191103_153936-s1b-ew-hh.tiff"

@pytest.fixture()
def tmp_filename(tmp_path):
    """Create a filename for the messages."""
    return tmp_path / FILENAME

@pytest.fixture()
def file_message(tmp_filename):
    """Create a string for a file message."""
    return ('pytroll://segment/raster/L2/SAR file a001673@c20969.ad.smhi.se 2019-11-05T13:00:10.366023 v1.01 '
            'application/json {"platform_name": "S1B", "scan_mode": "EW", "type": "GRDM", "data_source": "1SDH", '
            '"start_time": "2019-11-03T15:39:36.543000", "end_time": "2019-11-03T15:40:40.821000", "orbit_number": '
            '18765, "random_string1": "0235EA", "random_string2": "747D", "uri": '
            f'"{str(tmp_filename)}", "uid": "20191103_153936-s1b-ew-hh.tiff", '
            '"polarization": "hh", "sensor": "sar-c", "format": "GeoTIFF", "pass_direction": "ASCENDING"}')


@pytest.fixture()
def del_message(tmp_filename):
    """Create a string for a delete message."""
    return ('pytroll://segment/raster/L2/SAR delete a001673@c20969.ad.smhi.se 2019-11-05T13:00:10.366023 v1.01 '
            'application/json {"platform_name": "S1B", "scan_mode": "EW", "type": "GRDM", "data_source": "1SDH", '
            '"start_time": "2019-11-03T15:39:36.543000", "end_time": "2019-11-03T15:40:40.821000", "orbit_number": '
            '18765, "random_string1": "0235EA", "random_string2": "747D", "uri": '
            f'"{str(tmp_filename)}", "uid": "20191103_153936-s1b-ew-hh.tiff", '
            '"polarization": "hh", "sensor": "sar-c", "format": "GeoTIFF", "pass_direction": "ASCENDING"}')


@contextmanager
def running_prepared_database():
    """Starts and prepares a database instance for tests."""
    with mongodb_instance_server_process_context():
        TestDatabase.prepare()
        yield


async def test_record_adds_message(tmp_path, file_message, tmp_filename):
    """Test that message recording adds a message to the database."""
    msg = Message.decode(file_message)

    subscriber_config = dict(nameserver=False, addresses=[f"ipc://{str(tmp_path)}/in.ipc"], port=3000)

    with running_prepared_database():
        with patched_subscriber_recv([file_message]):

            await record_messages(subscriber_config)

            async with mongodb_context(test_app_config.database):
                collection = await MongoDB.get_collection("mock_database", "mock_collection")

                result = await collection.find_one(dict(scan_mode="EW"))
                result.pop("_id")
                assert result == msg.data

                deletion_result = await collection.delete_many({"uri": str(tmp_filename)})

                assert deletion_result.deleted_count == 1


async def test_record_deletes_message(tmp_path, file_message, del_message):
    """Test that message recording can delete a record in the database."""
    subscriber_config = dict(nameserver=False, addresses=[f"ipc://{str(tmp_path)}/in.ipc"], port=3000)

    with running_prepared_database():

        with patched_subscriber_recv([file_message, del_message]):

            await record_messages(subscriber_config)

            async with mongodb_context(test_app_config.database):
                collection = await MongoDB.get_collection("mock_database", "mock_collection")
                result = await collection.find_one(dict(scan_mode="EW"))
                assert result is None


async def test_record_from_config(tmp_path, file_message, tmp_filename):
    """Test that we can record when passed a config file."""
    config_file = create_config_file(tmp_path)

    msg = Message.decode(file_message)

    with running_prepared_database():

        with patched_subscriber_recv([file_message]):

            await record_messages_from_config(config_file)

            async with mongodb_context(test_app_config.database):
                collection = await MongoDB.get_collection("mock_database", "mock_collection")

                result = await collection.find_one(dict(scan_mode="EW"))
                result.pop("_id")
                assert result == msg.data

                deletion_result = await collection.delete_many({"uri": str(tmp_filename)})

                assert deletion_result.deleted_count == 1


def create_config_file(tmp_path):
    """Create a config file for tests."""
    config_file = tmp_path / "config.yaml"
    subscriber_config = dict(nameserver=False, addresses=[f"ipc://{str(tmp_path)}/in.ipc"], port=3000)
    db_config = {"main_database_name": "sat_db",
                 "main_collection_name": "files",
                 "url": "mongodb://localhost:27017",
                 "timeout": 1000}
    api_server_config = {"url": "http://localhost:8000"}

    config_dict = dict(subscriber_config=subscriber_config,
                       database = db_config,
                       api_server = api_server_config)
    with open(config_file, "w") as fd:
        fd.write(yaml.dump(config_dict))

    return config_file

async def test_record_cli(tmp_path, file_message, tmp_filename):
    """Test that we can record when passed a config file."""
    config_file = create_config_file(tmp_path)

    msg = Message.decode(file_message)

    with running_prepared_database():

        with patched_subscriber_recv([file_message]):
            await record_messages_from_command_line([str(config_file)])

            async with mongodb_context(test_app_config.database):
                collection = await MongoDB.get_collection("mock_database", "mock_collection")

                result = await collection.find_one(dict(scan_mode="EW"))
                result.pop("_id")
                assert result == msg.data

                deletion_result = await collection.delete_many({"uri": str(tmp_filename)})

                assert deletion_result.deleted_count == 1

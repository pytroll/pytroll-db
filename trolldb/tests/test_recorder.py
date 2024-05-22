"""Tests for the message recording into database."""

import pytest
from posttroll.message import Message
from posttroll.testing import patched_subscriber_recv
from pytest_lazy_fixtures import lf

from trolldb.cli import record_messages, record_messages_from_command_line, record_messages_from_config
from trolldb.database.mongodb import MongoDB, mongodb_context
from trolldb.test_utils.common import AppConfig, create_config_file, make_test_app_config, test_app_config
from trolldb.test_utils.mongodb_instance import running_prepared_database_context


@pytest.fixture()
def file_message(tmp_data_filename):
    """Create a string for a file message."""
    return ('pytroll://segment/raster/L2/SAR file a001673@c20969.ad.smhi.se 2019-11-05T13:00:10.366023 v1.01 '
            'application/json {"platform_name": "S1B", "scan_mode": "EW", "type": "GRDM", "data_source": "1SDH", '
            '"start_time": "2019-11-03T15:39:36.543000", "end_time": "2019-11-03T15:40:40.821000", "orbit_number": '
            '18765, "random_string1": "0235EA", "random_string2": "747D", "uri": '
            f'"{str(tmp_data_filename)}", "uid": "20191103_153936-s1b-ew-hh.tiff", '
            '"polarization": "hh", "sensor": "sar-c", "format": "GeoTIFF", "pass_direction": "ASCENDING"}')


@pytest.fixture()
def del_message(tmp_data_filename):
    """Create a string for a delete message."""
    return ('pytroll://deletion del a001673@c20969.ad.smhi.se 2019-11-05T13:00:10.366023 v1.01 '
            'application/json {"platform_name": "S1B", "scan_mode": "EW", "type": "GRDM", "data_source": "1SDH", '
            '"start_time": "2019-11-03T15:39:36.543000", "end_time": "2019-11-03T15:40:40.821000", "orbit_number": '
            '18765, "random_string1": "0235EA", "random_string2": "747D", "uri": '
            f'"{str(tmp_data_filename)}", "uid": "20191103_153936-s1b-ew-hh.tiff", '
            '"polarization": "hh", "sensor": "sar-c", "format": "GeoTIFF", "pass_direction": "ASCENDING"}')


@pytest.fixture()
def tmp_data_filename(tmp_path):
    """Create a filename for the messages."""
    filename = "20191103_153936-s1b-ew-hh.tiff"
    return tmp_path / filename


@pytest.fixture()
def config_file(tmp_path):
    """A fixture to create a config file for the tests."""
    return create_config_file(tmp_path)


async def message_in_database_and_delete_count_is_one(msg) -> bool:
    """Checks if there is exactly one item in the database which matches the data of the message."""
    async with mongodb_context(test_app_config.database):
        collection = await MongoDB.get_collection("mock_database", "mock_collection")
        result = await collection.find_one(dict(scan_mode="EW"))
        result.pop("_id")
        deletion_result = await collection.delete_many({"uri": msg.data["uri"]})
        return result == msg.data and deletion_result.deleted_count == 1


@pytest.mark.parametrize(("function", "args"), [
    (record_messages_from_config, lf("config_file")),
    (record_messages_from_command_line, [lf("config_file")])
])
async def test_record_from_cli_and_config(tmp_path, file_message, tmp_data_filename, function, args):
    """Tests that message recording adds a message to the database either via configs from a file or the CLI."""
    msg = Message.decode(file_message)
    with running_prepared_database_context():
        with patched_subscriber_recv([file_message]):
            await function(args)
            assert await message_in_database_and_delete_count_is_one(msg)


async def test_record_messages(config_file, tmp_path, file_message, tmp_data_filename):
    """Tests that message recording adds a message to the database."""
    config = AppConfig(**make_test_app_config(tmp_path))
    msg = Message.decode(file_message)
    with running_prepared_database_context():
        with patched_subscriber_recv([file_message]):
            await record_messages(config)
            assert await message_in_database_and_delete_count_is_one(msg)


async def test_record_deletes_message(tmp_path, file_message, del_message):
    """Tests that message recording can delete a record in the database."""
    config = AppConfig(**make_test_app_config(tmp_path))
    with running_prepared_database_context():
        with patched_subscriber_recv([file_message, del_message]):
            await record_messages(config)
            async with mongodb_context(config.database):
                collection = await MongoDB.get_collection("mock_database", "mock_collection")
                result = await collection.find_one(dict(scan_mode="EW"))
                assert result is None

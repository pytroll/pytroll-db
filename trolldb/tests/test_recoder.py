"""Tests for the message recording into database."""

from typing import Any

import pytest
from posttroll.message import Message
from posttroll.testing import patched_subscriber_recv
from pydantic import FilePath

from trolldb.cli import record_messages, record_messages_from_command_line, record_messages_from_config
from trolldb.database.mongodb import MongoDB, mongodb_context
from trolldb.test_utils.common import assert_equal, create_config_file, make_test_app_config, test_app_config
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


async def assert_message(msg, data_filename):
    """Documentation to be added."""
    async with mongodb_context(test_app_config.database):
        collection = await MongoDB.get_collection("mock_database", "mock_collection")
        result = await collection.find_one(dict(scan_mode="EW"))
        result.pop("_id")
        assert_equal(result, msg.data)

        deletion_result = await collection.delete_many({"uri": str(data_filename)})
        assert_equal(deletion_result.deleted_count, 1)


async def _record_from_somewhere(config_path: FilePath, message: Any, data_filename, record_from_func, f=False):
    """Test that we can record when passed a config file."""
    config_file = create_config_file(config_path)
    msg = Message.decode(message)
    with running_prepared_database_context():
        with patched_subscriber_recv([message]):
            await record_from_func(config_file if not f else [str(config_file)])
            await assert_message(msg, data_filename)


async def test_record_adds_message(tmp_path, file_message, tmp_data_filename):
    """Test that message recording adds a message to the database."""
    await _record_from_somewhere(
        tmp_path, file_message, tmp_data_filename, record_messages_from_config
    )


async def test_record_from_config(tmp_path, file_message, tmp_data_filename):
    """Test that we can record when passed a config file."""
    await _record_from_somewhere(
        tmp_path, file_message, tmp_data_filename, record_messages_from_config
    )


async def test_record_cli(tmp_path, file_message, tmp_data_filename):
    """Test that we can record when passed a config file."""
    await _record_from_somewhere(
        tmp_path, file_message, tmp_data_filename, record_messages_from_command_line, True
    )


async def test_record_deletes_message(tmp_path, file_message, del_message):
    """Test that message recording can delete a record in the database."""
    config = make_test_app_config(tmp_path)
    with running_prepared_database_context():
        with patched_subscriber_recv([file_message, del_message]):
            await record_messages(config)

            async with mongodb_context(config.database):
                collection = await MongoDB.get_collection("mock_database", "mock_collection")
                result = await collection.find_one(dict(scan_mode="EW"))
                assert result is None

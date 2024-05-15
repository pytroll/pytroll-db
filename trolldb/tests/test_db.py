"""Tests for the message recording into database."""

import pytest
from posttroll.message import Message
from posttroll.testing import patched_subscriber_recv

from trolldb.cli import record_messages
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


async def test_record_adds_message(tmp_path, file_message, tmp_filename):
    """Test that message recording adds a message to the database."""
    msg = Message.decode(file_message)

    subscriber_config = dict(nameserver=False, addresses=[f"ipc://{str(tmp_path)}/in.ipc"], port=3000)

    with mongodb_instance_server_process_context():
        TestDatabase.prepare()
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

    with mongodb_instance_server_process_context():
        TestDatabase.prepare()

        with patched_subscriber_recv([file_message, del_message]):

            await record_messages(subscriber_config)

            async with mongodb_context(test_app_config.database):
                collection = await MongoDB.get_collection("mock_database", "mock_collection")
                result = await collection.find_one(dict(scan_mode="EW"))
                assert result is None

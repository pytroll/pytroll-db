"""Main interface."""

import argparse
import asyncio

from posttroll.message import Message
from posttroll.subscriber import create_subscriber_from_dict_config
from pydantic import FilePath

from trolldb.config.config import AppConfig, from_yaml
from trolldb.database.mongodb import MongoDB, mongodb_context


async def record_messages(config: AppConfig):
    """Record the metadata of messages into the database."""
    async with mongodb_context(config.database):
        sub = create_subscriber_from_dict_config(config.subscriber)
        collection = await MongoDB.get_collection("mock_database", "mock_collection")
        for m in sub.recv():
            msg = Message.decode(m)
            match msg.type:
                case "file":
                    await collection.insert_one(msg.data)
                case "del":
                    deletion_result = await collection.delete_many({"uri": msg.data["uri"]})
                    if deletion_result.deleted_count != 1:
                        raise ValueError("Multiple deletions!")  # Replace with logging
                case _:
                    raise KeyError(f"Don't know what to do with {msg.type} message.")  # Replace with logging


async def record_messages_from_config(config_file: FilePath):
    """Record messages into the database, getting the configuration from a file."""
    config = from_yaml(config_file)
    await record_messages(config)


async def record_messages_from_command_line(args=None):
    """Record messages into the database, command-line interface."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "configuration_file",
        help="Path to the configuration file")
    cmd_args = parser.parse_args(args)

    await record_messages_from_config(cmd_args.configuration_file)


def run_sync():
    """Runs the interface synchronously."""
    asyncio.run(record_messages_from_command_line())

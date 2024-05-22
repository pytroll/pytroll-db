"""Main interface."""

import argparse
import asyncio

from loguru import logger
from posttroll.message import Message
from posttroll.subscriber import create_subscriber_from_dict_config
from pydantic import FilePath

from trolldb.config.config import AppConfig, parse_config_yaml_file
from trolldb.database.mongodb import MongoDB, mongodb_context


async def record_messages(config: AppConfig):
    """Record the metadata of messages into the database."""
    async with mongodb_context(config.database):
        collection = await MongoDB.get_collection(
            config.database.main_database_name, config.database.main_collection_name
        )
        for m in create_subscriber_from_dict_config(config.subscriber).recv():
            msg = Message.decode(str(m))
            match msg.type:
                case "file":
                    await collection.insert_one(msg.data)
                case "del":
                    deletion_result = await collection.delete_many({"uri": msg.data["uri"]})
                    if deletion_result.deleted_count != 1:
                        logger.error("Recorder found multiple deletions!")  # TODO: Log some data related to the msg
                case _:
                    logger.debug(f"Don't know what to do with {msg.type} message.")


async def record_messages_from_config(config_file: FilePath):
    """Record messages into the database, getting the configuration from a file."""
    config = parse_config_yaml_file(config_file)
    await record_messages(config)


async def record_messages_from_command_line(args=None):
    """Record messages into the database, command-line interface."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "configuration_file",
        help="Path to the configuration file")
    cmd_args = parser.parse_args(None if args is None else [str(i) for i in args])

    await record_messages_from_config(cmd_args.configuration_file)


def run_sync():
    """Runs the interface synchronously."""
    asyncio.run(record_messages_from_command_line())

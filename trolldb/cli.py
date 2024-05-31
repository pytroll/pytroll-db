"""Main interface."""

import argparse
import asyncio

from loguru import logger
from motor.motor_asyncio import AsyncIOMotorCollection
from posttroll.message import Message
from posttroll.subscriber import create_subscriber_from_dict_config
from pydantic import FilePath

from trolldb.config.config import AppConfig, parse_config
from trolldb.database.mongodb import MongoDB, mongodb_context


async def delete_uri_from_collection(collection: AsyncIOMotorCollection, uri: str) -> int:
    """Deletes a document from collection and logs the deletion.

    Args:
        collection:
            The collection object which includes the document to delete.
        uri:
            The URI used to query the collection. It can be either a URI of a previously recorded file message or
            a dataset message.

    Returns:
         Number of deleted documents.
    """
    del_result_file = await collection.delete_many({"uri": uri})
    if del_result_file.deleted_count == 1:
        logger.info(f"Deleted one document (file) with uri: {uri}")

    del_result_dataset = await collection.delete_many({"dataset.uri": uri})
    if del_result_dataset.deleted_count == 1:
        logger.info(f"Deleted one document (dataset) with uri: {uri}")

    return del_result_file.deleted_count + del_result_dataset.deleted_count


async def record_messages(config: AppConfig) -> None:
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
                    logger.info(f"Inserted file with uri: {msg.data["uri"]}")
                case "dataset":
                    await collection.insert_one(msg.data)
                    logger.info(f"Inserted dataset with {len(msg.data["dataset"])} elements: {msg.data["dataset"]}")
                case "del":
                    deletion_count = await delete_uri_from_collection(collection, msg.data["uri"])
                    if deletion_count > 1:
                        logger.error(f"Recorder found multiple deletions for uri: {msg.data["uri"]}!")
                case _:
                    logger.debug(f"Don't know what to do with {msg.type} message.")


async def record_messages_from_config(config_file: FilePath) -> None:
    """Record messages into the database, getting the configuration from a file."""
    await record_messages(parse_config(config_file))


async def record_messages_from_command_line(args=None) -> None:
    """Record messages into the database, command-line interface."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "configuration_file",
        help="Path to the configuration file")
    cmd_args = parser.parse_args(None if args is None else [str(i) for i in args])

    await record_messages_from_config(cmd_args.configuration_file)


def run_sync() -> None:
    """Runs the interface synchronously."""
    asyncio.run(record_messages_from_command_line())

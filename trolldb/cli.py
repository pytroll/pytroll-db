"""Main interface."""

from posttroll.message import Message
from posttroll.subscriber import create_subscriber_from_dict_config

from trolldb.database.mongodb import MongoDB, mongodb_context
from trolldb.test_utils.common import test_app_config


async def record_messages(subscriber_config):
    """Record the metadata of messages into the database."""
    async with mongodb_context(test_app_config.database):
        sub = create_subscriber_from_dict_config(subscriber_config)
        collection = await MongoDB.get_collection("mock_database", "mock_collection")
        for m in sub.recv():
            msg = Message.decode(m)
            match msg.type:
                case "file":
                    collection.insert_one(msg.data)
                case "delete":
                    deletion_result = await collection.delete_many({"uri": msg.data["uri"]})
                    if deletion_result.deleted_count != 1:
                        raise ValueError("Multiple deletions!")  # Replace with logging
                case _:
                    raise KeyError(f"Don't know what to do with {msg.type} message.")  # Replace with logging

"""
The module which handles database CRUD operations for MongoDB. It is based on
`PyMongo <https://github.com/mongodb/mongo-python-driver>`_ and `motor <https://github.com/mongodb/motor>`_.
"""

import errno
import sys
from contextlib import asynccontextmanager
from typing import Any, Coroutine

from loguru import logger
from motor.motor_asyncio import (
    AsyncIOMotorClient,
    AsyncIOMotorDatabase,
    AsyncIOMotorCollection,
    AsyncIOMotorCommandCursor,
    AsyncIOMotorCursor
)
from pydantic import validate_call
from pymongo.collection import _DocumentType
from pymongo.errors import (
    ConnectionFailure,
    ServerSelectionTimeoutError)

from config.config import DatabaseConfig


class MongoDB:
    """
    A wrapper class around the `motor async driver <https://www.mongodb.com/docs/drivers/motor/>`_ for Mongo DB with
    convenience methods tailored to our specific needs. As such, most of the methods return coroutines whose results
    need to be awaited.

    Note:
        This class is not meant to be instantiated! That's why all the methods in this class are decorated with
        ``@classmethods``. This choice has been made to guarantee optimal performance, i.e. for each running process
        there must be only a single motor client to handle all database operations. Having different clients which are
        constantly opened/closed degrades the performance. The expected usage is that we open a client in the beginning
        of the program and keep it open until the program finishes. It is okay to reopen/close the client for testing
        purposes when isolation is needed.

    Note:
        The main difference between this wrapper class and the original motor driver class is that we attempt to access
        the database and collections during the initialization to see if we succeed or fail. This is contrary to the
        behaviour of the motor driver which simply creates a client object and does not attempt to access the database
        until some time later when an actual operation is performed on the database. This behaviour is not desired for
        us, we would like to fail early!
    """

    __client: AsyncIOMotorClient | None = None
    __main_collection: AsyncIOMotorCollection = None
    __main_database: AsyncIOMotorDatabase = None

    default_database_names = ["admin", "config", "local"]
    """
    MongoDB creates these databases by default for self usage. 
    """

    @classmethod
    async def initialize(cls, database_config: DatabaseConfig):
        """
        Initializes the motor client. Note that this method has to be awaited!

        Args:
            database_config:
                 A named tuple which includes the database configurations.

        Raises :obj:`~SystemExit(errno.EIO)`:
            If connection is not established (``ConnectionFailure``) or if the attempt times out
            (``ServerSelectionTimeoutError``)

        Raises :obj:`~SystemExit(errno.ENODATA)`:
            If either ``database_config.main_database`` or ``database_config.main_collection`` does not exist.

        Returns:
            On success ``None``.
        """

        # This only makes the reference and does not establish an actual connection until the first attempt is made
        # to access the database.
        cls.__client = AsyncIOMotorClient(
            database_config.url.unicode_string(),
            serverSelectionTimeoutMS=database_config.timeout)

        try:
            # Here we attempt to access the database
            __database_names = await cls.__client.list_database_names()
        except (ConnectionFailure, ServerSelectionTimeoutError):
            logger.error(f"Could not connect to the database with URL: {database_config.url.unicode_string()}")
            sys.exit(errno.EIO)

        if database_config.main_database_name not in __database_names:
            logger.error(f"Could not find any database with the given name: {database_config.main_database_name}")
            sys.exit(errno.ENODATA)
        cls.__main_database = cls.__client.get_database(database_config.main_database_name)

        if database_config.main_collection_name not in await cls.__main_database.list_collection_names():
            logger.error(f"Could not find any collection in database `{database_config.main_database_name}` with the "
                         f"given name: {database_config.main_database_name}")
            sys.exit(errno.ENODATA)
        cls.__main_collection = cls.__main_database.get_collection(database_config.main_collection_name)

    @classmethod
    def client(cls) -> AsyncIOMotorClient:
        """
        Returns:
            The actual motor client so that it can be used to perform database CRUD operations.
        """
        return cls.__client

    @classmethod
    def main_collection(cls) -> AsyncIOMotorCollection:
        """
        A convenience method to get the main collection.

        Returns:
            The main collection which resides inside the main database.
            Equivalent to ``MongoDB.client()[<main_database_name>][<main_collection_name>]``.
        """
        return cls.__main_collection

    @classmethod
    def main_database(cls) -> AsyncIOMotorDatabase:
        """
        A convenience method to get the main database.

        Returns:
            The main database which includes the main collection, which in turn includes the desired documents.
            Equivalent to ``MongoDB.client()[<main_database_name>]``.
        """
        return cls.__main_database

    @staticmethod
    async def get_id(doc: Coroutine[Any, Any, _DocumentType | None] | _DocumentType) -> str:
        """
        Retrieves the ID of a document as a simple flat string.

        Note:
            The rationale behind this method is as follows. In MongoDB, each document has a unique ID which is of type
            :class:`~bson.objectid.ObjectId`. This is not suitable for purposes when a simple string is needed, hence
            the need for this method.

        Args:
            doc:
                A MongoDB document as a :class:`_DocumentType` object or in the coroutine form. The latter could be e.g.
                the result of applying the standard ``find_one`` method from MongoDB on a collection given a ``filter``.

        Returns:
            The ID of a document as a simple string. For example, when applied on a document with
            ``_id: ObjectId('000000000000000000000000')``, the method returns ``'000000000000000000000000'``.
        """
        match doc:
            case _DocumentType():
                return str(doc["_id"])
            case Coroutine():
                return str((await doc)["_id"])
            case _:
                raise TypeError("The type of `doc` must be either `_DocumentType` or "
                                "`Coroutine[Any, Any, _DocumentType | None] `.")

    @staticmethod
    async def get_ids(docs: AsyncIOMotorCommandCursor | AsyncIOMotorCursor | list[_DocumentType]) -> list[str]:
        """
        Similar to :func:`~MongoDB.get_id` but for a list of documents.

        Args:
            docs:
                A list of MongoDB documents each as a :class:`DocumentType`, or all as an
                :obj:`~AsyncIOMotorCommandCursor`. The latter could be e.g. the result of applying the
                standard ``aggregate`` method from MongoDB on a collection given a ``pipeline``.

        Returns:
            The list of all IDs, each as a simple string.
        """
        match docs:
            case list():
                return [str(doc["_id"]) for doc in docs]
            case AsyncIOMotorCommandCursor() | AsyncIOMotorCursor():
                return [str(doc["_id"]) async for doc in docs]
            case _:
                raise TypeError("The type of `docs` must be either `list[_DocumentType]` or "
                                "`AsyncIOMotorCommandCursor`.")


@asynccontextmanager
@validate_call
async def mongodb_context(database_config: DatabaseConfig):
    """
    An asynchronous context manager to connect to the MongoDB client.
    It can be either used in production or in testing environments.

    Args:
        database_config:
            The configuration of the database.
    """
    try:
        await MongoDB.initialize(database_config)
        yield
    finally:
        if MongoDB.client() is not None:
            MongoDB.client().close()

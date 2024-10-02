"""The module which handles database CRUD operations for MongoDB.

It is based on the following libraries:
  - `PyMongo <https://github.com/mongodb/mongo-python-driver>`_
  - `motor <https://github.com/mongodb/motor>`_.

Note:
    Some functions/methods in this module are decorated with the Pydantic
    `@validate_call <https://docs.pydantic.dev/latest/api/validate_call/>`_ which checks the arguments during the
    function calls.
"""

import errno
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, ClassVar, Coroutine, Optional, TypeVar, Union

from loguru import logger
from motor.motor_asyncio import (
    AsyncIOMotorClient,
    AsyncIOMotorCollection,
    AsyncIOMotorCommandCursor,
    AsyncIOMotorCursor,
    AsyncIOMotorDatabase,
)
from pydantic import validate_call
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from pymongo.typings import _DocumentType

from trolldb.config.config import DatabaseConfig
from trolldb.database.errors import Client, Collections, Databases

T = TypeVar("T")
CoroutineLike = Coroutine[Any, Any, T]
"""A simple type hint for a coroutine of any type."""

CoroutineDocument = CoroutineLike[_DocumentType | None]
"""Coroutine type hint for document like objects."""

CoroutineStrList = CoroutineLike[list[str]]
"""Coroutine type hint for a list of strings."""


async def get_id(doc: CoroutineDocument) -> str:
    """Retrieves the ID of a document as a simple flat string.

    Note:
        The rationale behind this method is as follows. In MongoDB, each document has a unique ID which is of type
        :class:`bson.objectid.ObjectId`. This is not suitable for purposes when a simple string is needed, hence
        the need for this method.

    Args:
        doc:
            A MongoDB document in the coroutine form. This could be e.g. the result of applying the standard
            ``find_one`` method from MongoDB on a collection given a ``filter``.

    Returns:
        The ID of a document as a simple string. For example, when applied on a document with
        ``_id: ObjectId('000000000000000000000000')``, the method returns ``'000000000000000000000000'``.
    """
    return str((await doc)["_id"])


async def get_ids(docs: Union[AsyncIOMotorCommandCursor, AsyncIOMotorCursor]) -> list[str]:
    """Similar to :func:`~MongoDB.get_id` but for a list of documents.

    Args:
        docs:
            A list of MongoDB documents as :obj:`~AsyncIOMotorCommandCursor` or :obj:`~AsyncIOMotorCursor`.
            This could be e.g. the result of applying the standard ``aggregate`` method from MongoDB on a
            collection given a ``pipeline``.

    Returns:
        The list of all IDs, each as a simple string.
    """
    return [str(doc["_id"]) async for doc in docs]


class MongoDB:
    """A wrapper class around the `motor async driver <https://www.mongodb.com/docs/drivers/motor/>`_ for Mongo DB.

    It includes convenience methods tailored to our specific needs. As such, the :func:`~MongoDB.initialize()` method
    returns a coroutine which needs to be awaited.

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

    __client: ClassVar[Optional[AsyncIOMotorClient]] = None
    __database_config: ClassVar[Optional[DatabaseConfig]] = None
    __main_collection: ClassVar[Optional[AsyncIOMotorCollection]] = None
    __main_database: ClassVar[Optional[AsyncIOMotorDatabase]] = None

    default_database_names: ClassVar[list[str]] = ["admin", "config", "local"]
    """MongoDB creates these databases by default for self usage."""

    @classmethod
    @validate_call
    async def initialize(cls, database_config: DatabaseConfig):
        """Initializes the motor client. Note that this method has to be awaited!

        Args:
            database_config:
                 An object of type :class:`~trolldb.config.config.DatabaseConfig` which includes the database
                 configurations.

        Warning:
            The timeout is given in seconds in the configurations, while the MongoDB uses milliseconds.

        Returns:
            On success ``None``.

        Raises:
            ValidationError:
                If the method is not called with arguments of valid type.

            SystemExit(errno.EIO):
                If connection is not established, i.e. ``ConnectionFailure``.
            SystemExit(errno.EIO):
                If the attempt times out, i.e. ``ServerSelectionTimeoutError``.
            SystemExit(errno.EIO):
                If one attempts reinitializing the class with new (different) database configurations without calling
                :func:`~close()` first.
            SystemExit(errno.EIO):
                If the state is not consistent, i.e. the client is closed or ``None`` but the internal database
                configurations still exist and are different from the new ones which have been just provided.
            SystemExit(errno.ENODATA):
                If either ``database_config.main_database_name`` or ``database_config.main_collection_name`` does not
                exist.
        """
        logger.info("Attempt to initialize the MongoDB client ...")
        logger.info("Checking the database configs ...")
        if cls.__database_config:
            if database_config == cls.__database_config:
                if cls.__client:
                    return Client.AlreadyOpenError.log_as_warning()
                Client.InconsistencyError.sys_exit_log(errno.EIO)
            else:
                Client.ReinitializeConfigError.sys_exit_log(errno.EIO)
        logger.info("Database configs are OK.")

        # This only makes the reference and does not establish an actual connection until the first attempt is made
        # to access the database.
        cls.__client = AsyncIOMotorClient(
            database_config.url.unicode_string(),
            serverSelectionTimeoutMS=database_config.timeout * 1000)

        __database_names = []
        try:
            logger.info("Attempt to access list of databases ...")
            __database_names = await cls.__client.list_database_names()
        except (ConnectionFailure, ServerSelectionTimeoutError):
            Client.ConnectionError.sys_exit_log(
                errno.EIO, {"url": database_config.url.unicode_string()}
            )
        logger.info("Accessing the list of databases is successful.")

        err_extra_information = {"database_name": database_config.main_database_name}

        logger.info("Checking if the main database name exists ...")
        if database_config.main_database_name not in __database_names:
            Databases.NotFoundError.sys_exit_log(errno.ENODATA, err_extra_information)
        cls.__main_database = cls.__client.get_database(database_config.main_database_name)
        logger.info("The main database name exists.")

        err_extra_information |= {"collection_name": database_config.main_collection_name}

        logger.info("Checking if the main collection name exists ...")
        if database_config.main_collection_name not in await cls.__main_database.list_collection_names():
            Collections.NotFoundError.sys_exit_log(errno.ENODATA, err_extra_information)
        logger.info("The main collection name exists.")

        cls.__main_collection = cls.__main_database.get_collection(database_config.main_collection_name)
        cls.__database_config = database_config
        logger.info("MongoDB is successfully initialized.")

    @classmethod
    def is_initialized(cls) -> bool:
        """Checks if the motor client is initialized."""
        return cls.__client is not None

    @classmethod
    def close(cls) -> None:
        """Closes the motor client."""
        logger.info("Attempt to close the MongoDB client ...")
        if cls.__client:
            cls.__client.close()
            cls.__client = None
            cls.__database_config = None
            logger.info("The MongoDB client is closed successfully.")
            return
        Client.CloseNotAllowedError.sys_exit_log(errno.EIO)

    @classmethod
    def list_database_names(cls) -> CoroutineStrList:
        """Lists all the database names."""
        return cls.__client.list_database_names()

    @classmethod
    def main_collection(cls) -> AsyncIOMotorCollection:
        """A convenience method to get the main collection.

        Returns:
            The main collection which resides inside the main database.
            Equivalent to ``MongoDB.client()[<main_database_name>][<main_collection_name>]``.
        """
        return cls.__main_collection

    @classmethod
    def main_database(cls) -> AsyncIOMotorDatabase:
        """A convenience method to get the main database.

        Returns:
            The main database which includes the main collection, which in turn includes the desired documents.

            This is equivalent to ``MongoDB.client()[<main_database_name>]``.
        """
        return cls.__main_database

    @classmethod
    @validate_call
    async def get_collection(
            cls,
            database_name: str | None = None,
            collection_name: str | None = None) -> AsyncIOMotorCollection:
        """Gets the collection object given its name and the database name in which it resides.

        Args:
            database_name:
                The name of the parent database which includes the collection.
            collection_name:
                The name of the collection which resides inside the parent database labelled by ``database_name``.

        Returns:
            The database object. In case of ``None`` for both the database name and collection name, the main collection
            will be returned.

        Raises:
            ValidationError:
                If the method is not called with arguments of valid type.

            KeyError:
                If the database name exists, but it does not include any collection with the given name.

            TypeError:
                If only one of the database or collection names are ``None``.

            ...:
                This method relies on :func:`get_database` to check for the existence of the database which can raise
                exceptions. Check its documentation for more information.
        """
        match database_name, collection_name:
            case None, None:
                return cls.main_collection()

            case str(), str():
                db = await cls.get_database(database_name)
                if collection_name in await db.list_collection_names():
                    return db[collection_name]
                raise Collections.NotFoundError
            case _:
                raise Collections.WrongTypeError

    @classmethod
    @validate_call
    async def get_database(cls, database_name: str | None = None) -> AsyncIOMotorDatabase:
        """Gets the database object given its name.

        Args:
            database_name:
                The name of the database to retrieve.

        Returns:
            The database object.

        Raises:
            ValidationError:
                If the method is not called with arguments of valid type.

            KeyError:
                If the database name does not exist in the list of database names.
        """
        match database_name:
            case None:
                return cls.main_database()
            case _ if database_name in await cls.list_database_names():
                return cls.__client[database_name]
            case _:
                raise Databases.NotFoundError


@asynccontextmanager
async def mongodb_context(database_config: DatabaseConfig) -> AsyncGenerator:
    """An asynchronous context manager to connect to the MongoDB client.

    It can be either used in `PRODUCTION` or in `TESTING` environments.

    Note:
        Since the :class:`MongoDB` is supposed to be used statically, this context manager does not yield anything!
        One can simply use :class:`MongoDB` inside the context manager.

    Args:
        database_config:
            The configuration of the database.
    """
    logger.info("Attempt to open the MongoDB context manager ...")
    try:
        await MongoDB.initialize(database_config)
        yield
    finally:
        if MongoDB.is_initialized():
            MongoDB.close()
        else:
            logger.info("The MongoDB client was not initialized!")
        logger.info("The MongoDB context manager is successfully closed.")

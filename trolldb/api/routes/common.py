"""The module with common functions to be used in handling requests related to `databases` and `collections`."""

from typing import Annotated, Union

from fastapi import Depends, Response
from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase

from trolldb.database.mongodb import MongoDB


async def check_database(database_name: str | None = None) -> AsyncIOMotorDatabase:
    """A dependency for route handlers to check for the existence of a database given its name.

    Args:
        database_name (Optional, default ``None``):
            The name of the database to check. In case of ``None``, the main database will be picked.

    Returns:
        The database object if it exists.

    Raises:
        :class:`~trolldb.errors.errors.ResponseError`:
            Check :func:`~trolldb.database.mongodb.MongoDB.get_database` for more information.
    """
    return await MongoDB.get_database(database_name)


async def check_collection(
        database_name: str | None = None,
        collection_name: str | None = None) -> AsyncIOMotorCollection:
    """A dependency for route handlers to check for the existence of a collection.

    It performs the check given the collection name and the name of the database it resides in. It first checks for the
    existence of the database.

    Args:
        database_name (Optional, default ``None``):
            The name of the database to check. In case of ``None``, the main database will be picked.
        collection_name (Optional, default ``None``):
            The name of the collection to check. In case of ``None``, the main collection will be picked.

    Warning:
        Both of ``database_name`` and ``collection_name`` must be ``None`` so that the main database and collection
        will be picked. In case only one of them is ``None``, this is treated as an unacceptable request.

    Returns:
      - The collection object if it exists in the designated database.

    Raises:
        :class:`~trolldb.errors.errors.ResponseError`:
            Check :func:`~trolldb.database.mongodb.MongoDB.get_collection` for more information.
    """
    return await MongoDB.get_collection(database_name, collection_name)


async def get_distinct_items_in_collection(
        response_or_collection: Union[Response, AsyncIOMotorCollection],
        field_name: str) -> Union[Response, list[str]]:
    """An auxiliary function to either return the given response; or return a list of distinct (unique) values.

    Given the ``field_name`` it conducts a search in all documents of the given collection. The latter behaviour is
    equivalent to the ``distinct`` function from MongoDB. The former is the behaviour of an identity function.

    Args:
        response_or_collection:
            Either a response object, or a collection in which documents will be queried for the ``field_name``.

        field_name:
            The name of the target field in the documents

    Returns:
      - In case of a response object as input, the same response will be returned as-is.
      - In case of a collection as input, all the documents of the collection will be searched for ``field_name``,
        and the corresponding values will be retrieved. Finally, a list of all the distinct values is returned.
    """
    if isinstance(response_or_collection, Response):
        return response_or_collection

    return await response_or_collection.distinct(field_name)


CheckCollectionDependency = Annotated[AsyncIOMotorCollection, Depends(check_collection)]
"""Type annotation for the FastAPI dependency injection of checking a collection (function)."""

CheckDataBaseDependency = Annotated[AsyncIOMotorDatabase, Depends(check_database)]
"""Type annotation for the FastAPI dependency injection of checking a database (function)."""

"""
The module which defines common functions to be used in handling requests related to `databases` and `collections`.
"""

from typing import Annotated

from fastapi import Response, Query, Depends
from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase

from api.errors.errors import CollectionFail, DatabaseFail, Database_Collection_Fail, FailureResponse
from database.mongodb import MongoDB

exclude_defaults_query = Query(
    True,
    title="Query string",
    description="A boolean to exclude default databases from a MongoDB instance. Refer to "
                "`trolldb.database.mongodb.MongoDB.default_database_names` for more information.")


async def check_database(database_name: str | None = None) -> Response | AsyncIOMotorDatabase:
    """
    A dependency for route handlers to check for the existence of a database given
    its name.

    Args:
        database_name (Optional, default ``None``):
            The name of the database to check. In case of ``None``, the main database will be picked.

    Returns:
        -- The database object if it exists.

        -- :obj:`api.errors.errors.DatabaseFail.NOT_FOUND`, if the database does not exist.

        -- :obj:`api.errors.errors.DatabaseFail.WRONG_TYPE`, if the type of the database name is not ``str`` or
        ``None``.
    """

    match database_name:
        case None:
            return MongoDB.main_database()

        case str():
            if database_name in await MongoDB.client().list_database_names():
                return MongoDB.client()[database_name]
            return DatabaseFail.NOT_FOUND.fastapi_response()

        case _:
            return DatabaseFail.WRONG_TYPE.fastapi_response()


async def check_collection(
        database_name: str | None = None,
        collection_name: str | None = None) -> Response | AsyncIOMotorCollection:
    """
    A dependency for route handlers to check for the existence of a collection given
    its name and the name of the database it resides in. It first checks for the existence of the database using
    :func:`check_database`.

    Args:
        database_name (Optional, default ``None``):
            The name of the database to check. In case of ``None``, the main database will be picked.
        collection_name (Optional, default ``None``):
            The name of the collection to check. In case of ``None``, the main collection will be picked.

    Warning:
        Both of ``database_name`` and ``collection_name`` must be ``None`` so that the main database and collection
        will be picked. In case only one of them is ``None``, this is treated as an unacceptable request.

    Returns:
        -- The collection object if it exists in the designated database.

        -- A response from :func:`check_database`, if the database does not exist or the type of ``database_name`` is
        not valid.

        -- :obj:`api.errors.errors.CollectionFail.NOT_FOUND`, if the parent database exists but the collection does not.

        -- :obj:`api.errors.errors.CollectionFail.WRONG_TYPE`, if only one of ``database_name`` or ``collection_name``
        is ``None``; or if the type of ``collection_name`` is not ``str``.
    """

    res = await check_database(database_name)
    if isinstance(res, Response):
        return res

    match database_name, collection_name:
        case None, None:
            return MongoDB.main_collection()

        case str(), str():
            if collection_name in await MongoDB.client()[database_name].list_collection_names():
                return MongoDB.client()[database_name][collection_name]
            return CollectionFail.NOT_FOUND.fastapi_response()

        case _:
            return CollectionFail.WRONG_TYPE.fastapi_response()


async def get_distinct_items_in_collection(
        res_coll: Response | AsyncIOMotorCollection,
        field_name: str) -> Response | list[str]:
    """
    An auxiliary function to either return (verbatim echo) the given response; or return a list of distinct (unique)
    values for the given ``field_name`` via a search which is conducted in all documents of the given collection. The
    latter behaviour is equivalent to the ``distinct`` function from MongoDB. The former is the behaviour of an
    identity function

    Args:
        res_coll:
            Either a response object, or a collection in which documents will be queried for the ``field_name``.

        field_name:
            The name of the target field in the documents

    Returns:
        -- In case of a response as input, the same response will be returned.

        -- In case of a collection as input, all the documents of the collection will be searched for ``field_name``,
        and the corresponding values will be retrieved. Finally, a list of all the distinct values is returned.
    """

    if isinstance(res_coll, Response):
        return res_coll

    return await res_coll.distinct(field_name)


CheckCollectionDependency = Annotated[FailureResponse | AsyncIOMotorCollection, Depends(check_collection)]
CheckDataBaseDependency = Annotated[FailureResponse | AsyncIOMotorDatabase, Depends(check_database)]
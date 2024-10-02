"""The module which handles all requests related to getting the list of `databases` and `collections`.

Note:
    For more information on the API server, see the automatically generated documentation by FastAPI.
"""

from typing import Annotated

from fastapi import APIRouter, Query
from pymongo.typings import _DocumentType

from trolldb.api.routes.common import CheckCollectionDependency, CheckDataBaseDependency
from trolldb.config.config import MongoObjectId
from trolldb.database.errors import (
    Databases,
    Documents,
    database_collection_document_error_descriptor,
    database_collection_error_descriptor,
)
from trolldb.database.mongodb import MongoDB, get_ids

router = APIRouter()


@router.get("",
            response_model=list[str],
            summary="Gets the list of all database names")
async def database_names(
        exclude_defaults: Annotated[bool, Query(
            title="Query parameter",
            description="A boolean to exclude default databases from a MongoDB instance. Refer to "
                        "`trolldb.database.mongodb.MongoDB.default_database_names` for more information."
        )] = True) -> list[str]:
    """Please consult the auto-generated documentation by FastAPI."""
    db_names = await MongoDB.list_database_names()

    if not exclude_defaults:
        return db_names

    return [db for db in db_names if db not in MongoDB.default_database_names]


@router.get("/{database_name}",
            response_model=list[str],
            responses=Databases.union().fastapi_descriptor,
            summary="Gets the list of all collection names for the given database name")
async def collection_names(db: CheckDataBaseDependency) -> list[str]:
    """Please consult the auto-generated documentation by FastAPI."""
    return await db.list_collection_names()


@router.get("/{database_name}/{collection_name}",
            response_model=list[str],
            responses=database_collection_error_descriptor,
            summary="Gets the object ids of all documents for the given database and collection name")
async def documents(collection: CheckCollectionDependency) -> list[str]:
    """Please consult the auto-generated documentation by FastAPI."""
    return await get_ids(collection.find({}))


@router.get("/{database_name}/{collection_name}/{_id}",
            response_model=_DocumentType,
            responses=database_collection_document_error_descriptor,
            summary="Gets the document content in json format given its object id, database, and collection name")
async def document_by_id(collection: CheckCollectionDependency, _id: MongoObjectId) -> _DocumentType:
    """Please consult the auto-generated documentation by FastAPI."""
    if document := await collection.find_one({"_id": _id}):
        return dict(document) | {"_id": str(_id)}

    raise Documents.NotFound

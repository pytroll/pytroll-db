"""
The module which handles all requests related to getting the list of `databases` and `collections`.

Note:
    For more information on the API server, see the automatically generated documentation by FastAPI.
"""

from fastapi import APIRouter
from pymongo.collection import _DocumentType

from api.routes.common import (
    exclude_defaults_query, CheckCollectionDependency, CheckDataBaseDependency)
from config.config import MongoObjectId
from database.errors import (
    DatabaseFail,
    DocumentsFail,
    database_collection_fail_descriptor,
    database_collection_document_fail_descriptor)
from database.mongodb import MongoDB, get_ids

router = APIRouter()


@router.get("/",
            response_model=list[str],
            summary="Gets the list of all database names")
async def database_names(exclude_defaults: bool = exclude_defaults_query) -> list[str]:
    db_names = await MongoDB.list_database_names()

    if not exclude_defaults:
        return db_names

    return [db for db in db_names if db not in MongoDB.default_database_names]


@router.get("/{database_name}",
            response_model=list[str],
            responses=DatabaseFail.union().fastapi_descriptor,
            summary="Gets the list of all collection names for the given database name")
async def collection_names(db: CheckDataBaseDependency) -> list[str]:
    return await db.list_collection_names()


@router.get("/{database_name}/{collection_name}",
            response_model=list[str],
            responses=database_collection_fail_descriptor,
            summary="Gets the object ids of all documents for the given database and collection name")
async def documents(collection: CheckCollectionDependency) -> list[str]:
    return await get_ids(collection.find({}))


@router.get("/{database_name}/{collection_name}/{_id}",
            response_model=_DocumentType,
            responses=database_collection_document_fail_descriptor,
            summary="Gets the document content in json format given its object id, database, and collection name")
async def document_by_id(collection: CheckCollectionDependency, _id: MongoObjectId) -> _DocumentType:
    if document := await collection.find_one({"_id": _id}):
        return dict(document) | {"_id": str(_id)}

    raise DocumentsFail.NotFound

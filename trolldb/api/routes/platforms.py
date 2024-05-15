"""
The module which handles all requests regarding `platforms`.

Note:
    For more information on the API server, see the automatically generated documentation by FastAPI.
"""

from fastapi import APIRouter

from api.routes.common import get_distinct_items_in_collection, CheckCollectionDependency
from database.errors import database_collection_error_descriptor

router = APIRouter()


@router.get("",
            response_model=list[str],
            responses=database_collection_error_descriptor,
            summary="Gets the list of all platform names")
async def platform_names(collection: CheckCollectionDependency) -> list[str]:
    return await get_distinct_items_in_collection(collection, "platform_name")

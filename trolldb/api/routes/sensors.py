"""
The module which handles all requests regarding `sensors`.

Note:
    For more information on the API server, see the automatically generated documentation by FastAPI.
"""

from fastapi import APIRouter, Response

from api.errors.errors import database_collection_fail_descriptor
from api.routes.common import get_distinct_items_in_collection, CheckCollectionDependency

router = APIRouter()


@router.get("",
            response_model=list[str],
            responses=database_collection_fail_descriptor,
            summary="Gets the list of all sensor names")
async def sensor_names(res_coll: CheckCollectionDependency) -> Response | list[str]:
    return await get_distinct_items_in_collection(res_coll, "sensor")

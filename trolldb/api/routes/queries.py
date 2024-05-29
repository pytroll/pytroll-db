"""The module which handles all requests to the queries route.

Note:
    For more information on the API server, see the automatically generated documentation by FastAPI.
"""

import datetime
from typing import Annotated

from fastapi import APIRouter, Query

from trolldb.api.routes.common import CheckCollectionDependency
from trolldb.database.errors import database_collection_error_descriptor
from trolldb.database.mongodb import get_ids
from trolldb.database.pipelines import PipelineAttribute, Pipelines

router = APIRouter()


@router.get("",
            response_model=list[str],
            responses=database_collection_error_descriptor,
            summary="Gets the database UUIDs of the documents that match specifications determined by the query string")
async def queries(
        collection: CheckCollectionDependency,
        platform: Annotated[list[str] | None, Query()] = None,
        sensor: Annotated[list[str] | None, Query()] = None,
        time_min: Annotated[datetime.datetime, Query()] = None,
        time_max: Annotated[datetime.datetime, Query()] = None) -> list[str]:
    """Please consult the auto-generated documentation by FastAPI."""
    pipelines = Pipelines()

    if platform:
        pipelines += PipelineAttribute("platform_name") == platform

    if sensor:
        pipelines += PipelineAttribute("sensor") == sensor

    if [time_min, time_max] != [None, None]:
        start_time = PipelineAttribute("start_time")
        end_time = PipelineAttribute("end_time")
        pipelines += (
                ((start_time >= time_min) & (start_time <= time_max)) |
                ((end_time >= time_min) & (end_time <= time_max))
        )
    return await get_ids(collection.aggregate(pipelines))

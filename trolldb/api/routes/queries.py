"""The module which handles all requests to the queries route.

Note:
    For more information on the API server, see the automatically generated documentation by FastAPI.
"""

import datetime

from fastapi import APIRouter, Query

from trolldb.api.routes.common import CheckCollectionDependency
from trolldb.database.errors import database_collection_error_descriptor
from trolldb.database.mongodb import get_ids
from trolldb.database.piplines import PipelineAttribute, Pipelines

router = APIRouter()


@router.get("",
            response_model=list[str],
            responses=database_collection_error_descriptor,
            summary="Gets the database UUIDs of the documents that match specifications determined by the query string")
async def queries(
        collection: CheckCollectionDependency,
        # We suppress ruff for the following four lines with `Query(default=None)`.
        # Reason: This is the FastAPI way of defining optional queries and ruff is not happy about it!
        platform: list[str] = Query(default=None),  # noqa: B008
        sensor: list[str] = Query(default=None),  # noqa: B008
        time_min: datetime.datetime = Query(default=None),  # noqa: B008
        time_max: datetime.datetime = Query(default=None)) -> list[str]:  # noqa: B008
    """Please consult the auto-generated documentation by FastAPI."""
    # We
    pipelines = Pipelines()

    if platform:
        pipelines += PipelineAttribute("platform_name") == platform

    if sensor:
        pipelines += PipelineAttribute("sensor") == sensor

    if [time_min, time_max] != [None, None]:
        start_time = PipelineAttribute("start_time")
        end_time = PipelineAttribute("end_time")
        pipelines += (
                (start_time >= time_min) |
                (start_time <= time_max) |
                (end_time >= time_min) |
                (end_time <= time_max)
        )

    return await get_ids(collection.aggregate(pipelines))

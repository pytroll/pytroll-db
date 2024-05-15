"""The module which handles all requests related to `datetime`.

Note:
    For more information on the API server, see the automatically generated documentation by FastAPI.
"""

from datetime import datetime
from typing import TypedDict

from fastapi import APIRouter
from pydantic import BaseModel

from trolldb.api.routes.common import CheckCollectionDependency
from trolldb.database.errors import database_collection_error_descriptor
from trolldb.database.mongodb import get_id


class TimeModel(TypedDict):
    """Documentation to be added!"""
    _id: str
    _time: datetime


class TimeEntry(TypedDict):
    """Documentation to be added!"""
    _min: TimeModel
    _max: TimeModel


class ResponseModel(BaseModel):
    """Documentation to be added!"""
    start_time: TimeEntry
    end_time: TimeEntry


router = APIRouter()


@router.get("",
            response_model=ResponseModel,
            responses=database_collection_error_descriptor,
            summary="Gets the the minimum and maximum values for the start and end times")
async def datetime(collection: CheckCollectionDependency) -> ResponseModel:
    """Documentation to be added!"""
    agg_result = await collection.aggregate([{
        "$group": {
            "_id": None,
            "min_start_time": {"$min": "$start_time"},
            "max_start_time": {"$max": "$start_time"},
            "min_end_time": {"$min": "$end_time"},
            "max_end_time": {"$max": "$end_time"}
        }}]).next()

    def _aux(query):
        """Documentation to be added!"""
        return get_id(collection.find_one(query))

    return ResponseModel(
        start_time=TimeEntry(
            _min=TimeModel(
                _id=await _aux({"start_time": agg_result["min_start_time"]}),
                _time=agg_result["min_start_time"]),
            _max=TimeModel(
                _id=await _aux({"start_time": agg_result["max_start_time"]}),
                _time=agg_result["max_start_time"])
        ),
        end_time=TimeEntry(
            _min=TimeModel(
                _id=await _aux({"end_time": agg_result["min_end_time"]}),
                _time=agg_result["min_end_time"]),
            _max=TimeModel(
                _id=await _aux({"end_time": agg_result["max_end_time"]}),
                _time=agg_result["max_end_time"])
        )
    )

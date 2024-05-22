"""The module which defines all the routes with their corresponding tags.

Note:
    For more information on the API server, see the automatically generated documentation by FastAPI.
"""

from fastapi import APIRouter

from trolldb.api.routes import databases, datetime_, platforms, queries, root, sensors

api_router = APIRouter()
api_router.include_router(root.router, tags=["root"])
api_router.include_router(databases.router, tags=["databases"], prefix="/databases")
api_router.include_router(datetime_.router, tags=["datetime"], prefix="/datetime")
api_router.include_router(platforms.router, tags=["platforms"], prefix="/platforms")
api_router.include_router(queries.router, tags=["queries"], prefix="/queries")
api_router.include_router(sensors.router, tags=["sensors"], prefix="/sensors")

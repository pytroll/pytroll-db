"""The module which handles all requests to the root route, i.e. "/".

Note:
    For more information on the API server, see the automatically generated documentation by FastAPI.
"""

from fastapi import APIRouter, Response, status

router = APIRouter()


@router.get("/",
            summary="The root route which is mainly used to check the status of connection")
async def root() -> Response:
    """Please consult the auto-generated documentation by FastAPI."""
    return Response(status_code=status.HTTP_200_OK)

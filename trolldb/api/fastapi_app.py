"""The module which creates the main FastAPI app which will be used when running the API server."""

from fastapi import FastAPI, status
from fastapi.responses import PlainTextResponse
from loguru import logger
from pydantic import ValidationError

from trolldb.api.routes import api_router
from trolldb.errors.errors import ResponseError

API_INFO = dict(
    title="pytroll-db",
    summary="The database API of Pytroll",
    description=
    "The API allows you to perform CRUD operations as well as querying the database"
    "At the moment only MongoDB is supported. It is based on the following Python packages"
    "\n * **PyMongo** (https://github.com/mongodb/mongo-python-driver)"
    "\n * **motor** (https://github.com/mongodb/motor)",
    license_info=dict(
        name="The GNU General Public License v3.0",
        url="https://www.gnu.org/licenses/gpl-3.0.en.html"
    )
)
"""These will appear in the auto-generated documentation and are passed to the ``FastAPI`` class as keyword args."""

logger.info("Attempt to create the FastAPI app ...")
fastapi_app = FastAPI()

fastapi_app.include_router(api_router)


@fastapi_app.exception_handler(ResponseError)
async def auto_handler_response_errors(_, exc: ResponseError) -> PlainTextResponse:
    """Catches all the exceptions raised as a ResponseError, e.g. accessing non-existing databases/collections."""
    status_code, message = exc.get_error_details()
    info = dict(
        status_code=status_code if status_code else status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=message if message else "Generic Error [This is not okay, check why we have the generic error!]",
    )
    logger.error(f"Response error caught by the API auto exception handler: {info}")
    return PlainTextResponse(**info)


@fastapi_app.exception_handler(ValidationError)
async def auto_handler_pydantic_validation_errors(_, exc: ValidationError) -> PlainTextResponse:
    """Catches all the exceptions raised as a Pydantic ValidationError."""
    logger.error(f"Response error caught by the API auto exception handler: {exc}")
    return PlainTextResponse(str(exc), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


logger.info("FastAPI app created successfully.")

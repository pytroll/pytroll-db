"""The module which includes the main functionalities of the API package.

This is the main module which is supposed to be imported by the users of the package.

Note:
    The following applies to the :obj:`api` package and all its subpackages/modules.

    To avoid redundant documentation and inconsistencies, only non-FastAPI components are documented via the docstrings.
    For the documentation related to the FastAPI components, check out the auto-generated documentation by FastAPI.
    Assuming that the API server is running on `<http://localhost:8000>`_ (example) the auto-generated documentation can
    be accessed via either `<http://localhost:8000/redoc>`_ or  `<http://localhost:8000/docs>`_.

    Read more at `FastAPI automatics docs <https://fastapi.tiangolo.com/features/#automatic-docs>`_.
"""

import asyncio
import sys
import time
from contextlib import contextmanager
from multiprocessing import Process
from typing import Any, Generator, NoReturn

import uvicorn
from fastapi import FastAPI, status
from fastapi.responses import PlainTextResponse
from loguru import logger
from pydantic import ValidationError

from trolldb.api.routes import api_router
from trolldb.config.config import AppConfig, Timeout
from trolldb.database.mongodb import mongodb_context
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


@logger.catch(onerror=lambda _: sys.exit(1))
def run_server(config: AppConfig, **kwargs) -> None:
    """Runs the API server with all the routes and connection to the database.

    It first creates a FastAPI application and runs it using `uvicorn <https://www.uvicorn.org/>`_ which is
    ASGI (Asynchronous Server Gateway Interface) compliant. This function runs the event loop using
    `asyncio <https://docs.python.org/3/library/asyncio.html>`_ and does not yield!

    Args:
        config:
            The configuration of the application which includes both the server and database configurations.

        **kwargs:
            The keyword arguments are the same as those accepted by the
            `FastAPI class <https://fastapi.tiangolo.com/reference/fastapi/#fastapi.FastAPI>`_ and are directly passed
            to it. These keyword arguments will be first concatenated with the configurations of the API server which
            are read from the ``config`` argument. The keyword arguments which are passed explicitly to the function
            take precedence over ``config``. Finally, :obj:`API_INFO`, which are hard-coded information for the API
            server, will be concatenated and takes precedence over all.

    Example:
        .. code-block:: python

            from trolldb.api.api import run_server
            from trolldb.config.config import parse_config

            if __name__ == "__main__":
                run_server(parse_config("config.yaml"))
    """
    logger.info("Attempt to run the API server ...")

    # Concatenate the keyword arguments for the API server in the order of precedence (lower to higher).
    app = FastAPI(**(config.api_server._asdict() | kwargs | API_INFO))

    app.include_router(api_router)

    @app.exception_handler(ResponseError)
    async def auto_handler_response_errors(_, exc: ResponseError) -> PlainTextResponse:
        """Catches all the exceptions raised as a ResponseError, e.g. accessing non-existing databases/collections."""
        status_code, message = exc.get_error_details()
        info = dict(
            status_code=status_code if status_code else status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=message if message else "Generic Error [This is not okay, check why we have the generic error!]",
        )
        logger.error(f"Response error caught by the API auto exception handler: {info}")
        return PlainTextResponse(**info)

    @app.exception_handler(ValidationError)
    async def auto_handler_pydantic_validation_errors(_, exc: ValidationError) -> PlainTextResponse:
        """Catches all the exceptions raised as a Pydantic ValidationError."""
        logger.error(f"Response error caught by the API auto exception handler: {exc}")
        return PlainTextResponse(str(exc), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    async def _serve() -> NoReturn:
        """An auxiliary coroutine to be used in the asynchronous execution of the FastAPI application."""
        async with mongodb_context(config.database):
            logger.info("Attempt to start the uvicorn server ...")
            await uvicorn.Server(
                config=uvicorn.Config(
                    host=config.api_server.url.host,
                    port=config.api_server.url.port,
                    app=app
                )
            ).serve()

    logger.info("Attempt to run the asyncio loop for the API server ...")
    asyncio.run(_serve())


@contextmanager
def api_server_process_context(config: AppConfig, startup_time: Timeout = 2) -> Generator[Process, Any, None]:
    """A synchronous context manager to run the API server in a separate process (non-blocking).

    It uses the `multiprocessing <https://docs.python.org/3/library/multiprocessing.html>`_ package. The main use case
    is envisaged to be in `TESTING` environments.

    Args:
        config:
            Same as ``config`` argument for :func:`run_server`.

        startup_time:
            The overall time in seconds that is expected for the server and the database connections to be established
            before actual requests can be sent to the server. For testing purposes ensure that this is sufficiently
            large so that the tests will not time out.
    """
    logger.info("Attempt to run the API server process in a context manager ...")
    process = Process(target=run_server, args=(config,))
    try:
        process.start()
        time.sleep(startup_time)
        yield process
    finally:
        logger.info("Attempt to terminate the API server process in the context manager ...")
        process.terminate()
        process.join()
        logger.info("The API server process has terminated successfully.")

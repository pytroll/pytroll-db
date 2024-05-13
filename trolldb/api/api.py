"""
The module which includes the main functionalities of the API package. This is the main module which is supposed to be
imported by the users of the package.

Note:
    Functions in this module are decorated with
    `pydantic.validate_call <https://docs.pydantic.dev/latest/api/validate_call/#pydantic.validate_call_decorator.validate_call>`_
    so that their arguments can be validated using the corresponding type hints, when calling the function at runtime.

Note:
    The following applies to the :obj:`trolldb.api` package and all its subpackages/modules.

    To avoid redundant documentation and inconsistencies, only non-FastAPI components are documented via the docstrings.
    For the documentation related to the FastAPI components, check out the auto-generated documentation by FastAPI.
    Assuming that the API server is running on `<http://localhost:8000>`_ (example) the auto-generated documentation can
    be accessed via either `<http://localhost:8000/redoc>`_ or  `<http://localhost:8000/docs>`_.

    Read more at `FastAPI automatics docs <https://fastapi.tiangolo.com/features/#automatic-docs>`_.
"""

import asyncio
import time
from contextlib import contextmanager
from multiprocessing import Process

import uvicorn
from fastapi import FastAPI, status
from fastapi.responses import PlainTextResponse
from pydantic import FilePath, validate_call

from api.routes import api_router
from config.config import AppConfig, parse, Timeout
from database.mongodb import mongodb_context
from errors.errors import ResponseError


@validate_call
def run_server(config: AppConfig | FilePath, **kwargs) -> None:
    """
    Runs the API server with all the routes and connection to the database. It first creates a FastAPI
    application and runs it using `uvicorn <https://www.uvicorn.org/>`_ which is
    ASGI (Asynchronous Server Gateway Interface) compliant. This function runs the event loop using
    `asyncio <https://docs.python.org/3/library/asyncio.html>`_ and does not yield!

    Args:
        config:
            The configuration of the application which includes both the server and database configurations. In case of
            a :class:`FilePath`, it should be a valid path to an existing config file which will parsed as a ``.YAML``
            file.

        **kwargs:
            The keyword arguments are the same as those accepted by the
            `FastAPI class <https://fastapi.tiangolo.com/reference/fastapi/#fastapi.FastAPI>`_ and are directly passed
            to it. These keyword arguments will be first concatenated with the configurations of the API server which
            are read from the ``config`` argument. The keyword arguments which are passed
            explicitly to the function take precedence over ``config``.
    """

    config = parse(config)
    app = FastAPI(**(config.api_server._asdict() | kwargs))
    app.include_router(api_router)

    @app.exception_handler(ResponseError)
    async def unicorn_exception_handler(_, exc: ResponseError):
        status_code, message = exc.get_error_info()
        return PlainTextResponse(
            status_code=status_code if status_code else status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=message if message else "Generic Error [This is not okay, check why we have the generic error!]",
        )

    async def _serve():
        """
        An auxiliary coroutine to be used in the asynchronous execution of the FastAPI application.
        """
        async with mongodb_context(config.database):
            await uvicorn.Server(
                config=uvicorn.Config(
                    host=config.api_server.url.host,
                    port=config.api_server.url.port,
                    app=app
                )
            ).serve()

    asyncio.run(_serve())


@contextmanager
@validate_call
def server_process_context(config: AppConfig | FilePath, startup_time: Timeout = 2000):
    """
    A synchronous context manager to run the API server in a separate process (non-blocking) using the
    `multiprocessing <https://docs.python.org/3/library/multiprocessing.html>`_ package. The main use case is envisaged
    to be in testing environments.

    Args:
        config:
            Same as ``config`` argument for :func:`run_server`.

        startup_time:
            The overall time that is expected for the server and the database connections to be established before
            actual requests can be sent to the server. For testing purposes ensure that this is sufficiently large so
            that the tests will not time out.
    """
    config = parse(config)
    process = Process(target=run_server, args=(config,))
    process.start()
    try:
        time.sleep(startup_time / 1000)  # `time.sleep()` expects an argument in seconds, hence the division by 1000.
        yield process
    finally:
        process.terminate()

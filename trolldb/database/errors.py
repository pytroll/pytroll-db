"""The modules which defines the error responses that might occur while working with the MongoDB database.

Note:
    The error responses are grouped into classes, with each class representing the major
    category (context) in which the errors occur. As such, the attributes of the top classes
    are (expected to be) self-explanatory and require no additional documentation.
"""

from typing import ClassVar

from fastapi import status

from trolldb.errors.errors import ResponseError, ResponsesErrorGroup


class Client(ResponsesErrorGroup):
    """Database client error responses, e.g. if something goes wrong with initialization or closing the client."""
    CloseNotAllowedError: ClassVar[ResponseError] = ResponseError({
        status.HTTP_405_METHOD_NOT_ALLOWED:
            "Calling `close()` on a client which has not been initialized is not allowed!"
    })

    ReinitializeConfigError: ClassVar[ResponseError] = ResponseError({
        status.HTTP_405_METHOD_NOT_ALLOWED:
            "The client is already initialized with a different database configuration!"
    })

    AlreadyOpenError: ClassVar[ResponseError] = ResponseError({
        status.HTTP_100_CONTINUE:
            "The client has been already initialized with the same configuration."
    })

    InconsistencyError: ClassVar[ResponseError] = ResponseError({
        status.HTTP_405_METHOD_NOT_ALLOWED:
            "Something must have been wrong as we are in an inconsistent state. "
            "The internal database configuration is not empty and is the same as what we just "
            "received but the client is `None` or has been already closed!"
    })

    ConnectionError: ClassVar[ResponseError] = ResponseError({
        status.HTTP_400_BAD_REQUEST:
            "Could not connect to the database with the given URL."
    })


class Collections(ResponsesErrorGroup):
    """Collections error responses, e.g. if the requested collection cannot be found."""
    NotFoundError: ClassVar[ResponseError] = ResponseError({
        status.HTTP_404_NOT_FOUND:
            "Could not find the given collection name inside the specified database."
    })

    WrongTypeError: ClassVar[ResponseError] = ResponseError({
        status.HTTP_422_UNPROCESSABLE_ENTITY:
            "Both the database and collection name must be `None` if either one is `None`."
    })


class Databases(ResponsesErrorGroup):
    """Databases error responses, e.g. if the requested database cannot be found."""
    NotFoundError: ClassVar[ResponseError] = ResponseError({
        status.HTTP_404_NOT_FOUND:
            "Could not find the given database name."
    })

    WrongTypeError: ClassVar[ResponseError] = ResponseError({
        status.HTTP_422_UNPROCESSABLE_ENTITY:
            "Database name must be either of type `str` or `None.`"
    })


class Documents(ResponsesErrorGroup):
    """Documents error responses, e.g. if the requested document cannot be found."""
    NotFound: ClassVar[ResponseError] = ResponseError({
        status.HTTP_404_NOT_FOUND:
            "Could not find any document with the given object id."
    })


database_collection_error_descriptor = (
        Databases.union() | Collections.union()
).fastapi_descriptor
"""A response descriptor for the Fast API routes.

This combines all the error messages that might occur as result of working with databases and collections. See the
FastAPI documentation for `additional responses <https://fastapi.tiangolo.com/advanced/additional-responses/>`_.
"""

database_collection_document_error_descriptor = (
        Databases.union() | Collections.union() | Documents.union()
).fastapi_descriptor
"""Same as :obj:`database_collection_error_descriptor` but including documents as well."""

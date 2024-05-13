from fastapi import status

from errors.errors import ResponsesErrorGroup, ResponseError


class ClientFail(ResponsesErrorGroup):
    CloseNotAllowedError = ResponseError({
        status.HTTP_405_METHOD_NOT_ALLOWED:
            "Calling `close()` on a client which has not been initialized is not allowed!"
    })

    ReinitializeConfigError = ResponseError({
        status.HTTP_405_METHOD_NOT_ALLOWED:
            "The client is already initialized with a different database configuration!"
    })

    AlreadyOpenError = ResponseError({
        status.HTTP_100_CONTINUE:
            "The client has been already initialized with the same configuration."
    })

    InconsistencyError = ResponseError({
        status.HTTP_405_METHOD_NOT_ALLOWED:
            "Something must have been wrong as we are in an inconsistent state. "
            "The internal database configuration is not empty and is the same as what we just "
            "received but the client is `None` or has been already closed!"
    })

    ConnectionError = ResponseError({
        status.HTTP_400_BAD_REQUEST:
            "Could not connect to the database with URL."
    })


class CollectionFail(ResponsesErrorGroup):
    NotFoundError = ResponseError({
        status.HTTP_404_NOT_FOUND:
            "Could not find the given collection name inside the specified database."
    })

    WrongTypeError = ResponseError({
        status.HTTP_422_UNPROCESSABLE_ENTITY:
            "Both the Database and collection name must be `None` if one of them is `None`."
    })


class DatabaseFail(ResponsesErrorGroup):
    NotFoundError = ResponseError({
        status.HTTP_404_NOT_FOUND:
            "Could not find the given database name."
    })

    WrongTypeError = ResponseError({
        status.HTTP_422_UNPROCESSABLE_ENTITY:
            "Database name must be either of type `str` or `None.`"
    })


class DocumentsFail(ResponsesErrorGroup):
    NotFound = ResponseError({
        status.HTTP_404_NOT_FOUND:
            "Could not find any document with the given object id."
    })


Database_Collection_Fail = DatabaseFail | CollectionFail
Database_Collection_Document_Fail = DatabaseFail | CollectionFail | DocumentsFail
database_collection_fail_descriptor = (
        DatabaseFail.union() | CollectionFail.union()
).fastapi_descriptor
database_collection_document_fail_descriptor = (
        DatabaseFail.union() | CollectionFail.union() | DocumentsFail.union()
).fastapi_descriptor

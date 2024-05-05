"""
The module which defines error responses that will be returned by the API.
"""

from collections import OrderedDict
from typing import Self

from fastapi import status
from fastapi.responses import PlainTextResponse


class FailureResponse:
    descriptor_delimiter = " |OR| "
    defaultResponseClass = PlainTextResponse

    def __init__(self, args_dict: dict):
        self.__dict = OrderedDict(args_dict)

    def __or__(self, other: Self):
        buff = OrderedDict(self.__dict)
        for key, value in other.__dict.items():
            buff[key] = FailureResponse.listify(buff.get(key, []))
            buff[key].extend(FailureResponse.listify(value))
        return FailureResponse(buff)

    def __str__(self):
        return str(self.__dict)

    def fastapi_response(self, status_code: int | None = None):
        if status_code is None and len(self.__dict) > 1:
            raise ValueError("In case of multiple response status codes, please provide one.")
        status_code, content = [(k, v) for k, v in self.__dict.items()][0]
        try:
            return FailureResponse.defaultResponseClass(
                content=FailureResponse.stringify(content),
                status_code=status_code)
        except KeyError:
            raise KeyError(f"No default response found for the given status code: {status_code}")

    @property
    def fastapi_descriptor(self):
        return {k: {"description": FailureResponse.stringify(v)} for k, v in self.__dict.items()}

    @staticmethod
    def listify(item: str | list[str]) -> list[str]:
        return item if isinstance(item, list) else [item]

    @staticmethod
    def stringify(item: str | list[str]) -> str:
        return FailureResponse.descriptor_delimiter.join(FailureResponse.listify(item))


class BaseFailureResponses:

    @classmethod
    def fields(cls):
        return {k: v for k, v in cls.__dict__.items() if isinstance(v, FailureResponse)}

    @classmethod
    def union(cls):
        buff = FailureResponse({})
        for k, v in cls.fields().items():
            buff |= v
        return buff


class CollectionFail(BaseFailureResponses):
    NOT_FOUND = FailureResponse({
        status.HTTP_404_NOT_FOUND:
            "Collection name does not exist."
    })

    WRONG_TYPE = FailureResponse({
        status.HTTP_422_UNPROCESSABLE_ENTITY:
            "Collection name must be either a string or None; or both database name and collection name must be None."
    })


class DatabaseFail(BaseFailureResponses):
    NOT_FOUND = FailureResponse({
        status.HTTP_404_NOT_FOUND:
            "Database name does not exist."
    })

    WRONG_TYPE = FailureResponse({
        status.HTTP_422_UNPROCESSABLE_ENTITY:
            "Database name must be either a string or None."
    })


class DocumentsFail(BaseFailureResponses):
    NOT_FOUND = FailureResponse({
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

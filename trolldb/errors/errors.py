"""
The module which defines the base functionality for error responses that will be returned by the API.
This module only includes the generic utilities using which each module should define its own error responses
specifically. See :obj:`trolldb.database.errors` as an example on how this module is used.
"""

from collections import OrderedDict
from sys import exit
from typing import Literal, Self

from fastapi import Response
from fastapi.responses import PlainTextResponse
from loguru import logger

StatusCode = int


class ResponseError(Exception):
    """
    The base class for all error responses. This is derivative of the ``Exception`` class.
    """

    descriptor_delimiter: str = " |OR| "
    """
    A delimiter to combine the message part of several error responses into a single one. This will be shown in textual 
    format  for the response descriptors of the Fast API routes. For example:
    
        ``ErrorA |OR| ErrorB``
    """

    defaultResponseClass: Response = PlainTextResponse
    """
    The default type of the response which will be returned when an error occurs.
    """

    def __init__(self, args_dict: OrderedDict[StatusCode, str | list[str]] | dict) -> None:
        self.__dict: OrderedDict = OrderedDict(args_dict)
        self.extra_information: dict | None = None

    def __or__(self, other: Self):
        """
        Combines the error responses into a single error response.
        Args:
            other:
                Another error response of the same base type to combine with.

        Returns:
            A new error response which includes the combined error response. In case of different http status codes,
            the returned response includes the `{status-code: message}` pairs for both ``self`` and the ``other``.
            In case of the same status codes, the messages will be appended to a list and saved as a list.

        Example:
              ErrorA = ResponseError({200: "OK"})
              ErrorB = ResponseError({400: "Bad Request"})
              ErrorC = ResponseError({200: "Still Okay"})

              ErrorCombined = ErrorA | ErrorB | ErrorC

        """
        buff = OrderedDict(self.__dict)
        for key, msg in other.__dict.items():
            self_msg = buff.get(key, None)
            buff[key] = ResponseError.__listify(self_msg) if self_msg else []
            buff[key].extend(ResponseError.__listify(msg))
        return ResponseError(buff)

    def __assert_existence_multiple_response_codes(
            self,
            status_code: StatusCode | None = None) -> (StatusCode, str):
        match status_code, len(self.__dict):
            case None, n if n > 1:
                raise ValueError("In case of multiple response status codes, the status code must be specified.")
            case StatusCode(), n if n > 1:
                if status_code in self.__dict.keys():
                    return status_code, self.__dict[status_code]
                raise KeyError(f"Status code {status_code} cannot be found.")
            case _, 1:
                return [(k, v) for k, v in self.__dict.items()][0]
            case _:
                return 500, "Generic Response Error"

    def get_error_details(
            self,
            extra_information: dict | None = None,
            status_code: int | None = None) -> (StatusCode, str):
        status_code, msg = self.__assert_existence_multiple_response_codes(status_code)
        return (
            status_code,
            ResponseError.__stringify(msg) + (f" :=> {extra_information}" if extra_information else "")
        )

    def sys_exit_log(
            self,
            exit_code: int = -1,
            extra_information: dict | None = None,
            status_code: int | None = None) -> None:
        msg, _ = self.get_error_details(extra_information, status_code)
        logger.error(msg)
        exit(exit_code)

    def log_as_warning(
            self,
            extra_information: dict | None = None,
            status_code: int | None = None):
        msg, _ = self.get_error_details(extra_information, status_code)
        logger.warning(msg)

    @property
    def fastapi_descriptor(self) -> dict[StatusCode, dict[Literal["description"], str]]:
        return {status: {Literal["description"]: ResponseError.__stringify(msg)} for status, msg in self.__dict.items()}

    @staticmethod
    def __listify(item: str | list[str]) -> list[str]:
        return item if isinstance(item, list) else [item]

    @staticmethod
    def __stringify(item: str | list[str]) -> str:
        return ResponseError.descriptor_delimiter.join(ResponseError.__listify(item))


class ResponsesErrorGroup:

    @classmethod
    def fields(cls):
        return {k: v for k, v in cls.__dict__.items() if isinstance(v, ResponseError)}

    @classmethod
    def union(cls):
        buff = None
        for k, v in cls.fields().items():
            if buff is None:
                buff = v
            else:
                buff |= v
        return buff

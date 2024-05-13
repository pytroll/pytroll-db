"""
The module which defines error responses that will be returned by the API.
"""

from collections import OrderedDict
from sys import exit
from typing import Literal, Self

from fastapi import Response
from fastapi.responses import PlainTextResponse
from loguru import logger

StatusCode = int


class ResponseError(Exception):
    descriptor_delimiter: str = " |OR| "
    defaultResponseClass: Response = PlainTextResponse

    def __init__(self, args_dict: OrderedDict[StatusCode, str | list[str]] | dict) -> None:
        self.__dict: OrderedDict = OrderedDict(args_dict)
        self.extra_information: dict | None = None

    def __or__(self, other: Self):
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

    def get_error_info(
            self,
            extra_information: dict | None = None,
            status_code: int | None = None) -> (StatusCode, str):
        status_code, msg = self.__assert_existence_multiple_response_codes(status_code)
        return (
            status_code,
            ResponseError.__stringify(msg) + (f" :=> {extra_information}" if extra_information else "")
        )

    def fastapi_response(
            self,
            extra_information: dict | None = None,
            status_code: StatusCode | None = None) -> defaultResponseClass:
        try:
            msg, _ = self.get_error_info(extra_information, status_code)
            return ResponseError.defaultResponseClass(content=msg, status_code=status_code)
        except KeyError:
            raise KeyError(f"No default response found for the given status code: {status_code}")

    def raise_error_log_and_exit(
            self,
            exit_code: int = -1,
            extra_information: dict | None = None,
            status_code: int | None = None) -> None:
        msg, _ = self.get_error_info(extra_information, status_code)
        logger.error(msg)
        exit(exit_code)

    def log_warning(
            self,
            extra_information: dict | None = None,
            status_code: int | None = None):
        msg, _ = self.get_error_info(extra_information, status_code)
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

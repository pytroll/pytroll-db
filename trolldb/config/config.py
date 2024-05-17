"""The module which handles parsing and validating the config (YAML) file.

The validation is performed using `Pydantic <https://docs.pydantic.dev/latest/>`_.

Note:
    Functions in this module are decorated with
    `pydantic.validate_call <https://docs.pydantic.dev/latest/api/validate_call/#pydantic.validate_call_decorator.validate_call>`_
    so that their arguments can be validated using the corresponding type hints, when calling the function at runtime.
"""

import errno
import sys
from typing import Any, NamedTuple

from bson import ObjectId
from bson.errors import InvalidId
from loguru import logger
from pydantic import AnyUrl, BaseModel, Field, FilePath, MongoDsn, ValidationError, validate_call
from pydantic.functional_validators import AfterValidator
from typing_extensions import Annotated
from yaml import safe_load

Timeout = Annotated[int, Field(ge=0)]
"""A type hint for the timeout in milliseconds (non-negative int)."""


def id_must_be_valid(id_like_string: str) -> ObjectId:
    """Checks that the given string can be converted to a valid MongoDB ObjectId.

    Args:
        id_like_string:
            The string to be converted to an ObjectId.

    Returns:
       The ObjectId object if successfully.

    Raises:
        ValueError:
            If the given string cannot be converted to a valid ObjectId. This will ultimately turn into a pydantic
            validation error.
    """
    try:
        return ObjectId(id_like_string)
    except InvalidId as e:
        raise ValueError from e


MongoObjectId = Annotated[str, AfterValidator(id_must_be_valid)]
"""Type hint validator for object IDs."""


class MongoDocument(BaseModel):
    """Pydantic model for a MongoDB document."""
    _id: MongoObjectId


class APIServerConfig(NamedTuple):
    """A named tuple to hold all the configurations of the API server (excluding the database).

    Note:
        The attributes herein are a subset of the keyword arguments accepted by
        `FastAPI class <https://fastapi.tiangolo.com/reference/fastapi/#fastapi.FastAPI>`_ and are directly passed
        to the FastAPI class.
    """

    url: AnyUrl
    """The URL of the API server including the port, e.g. ``mongodb://localhost:8000``."""


class DatabaseConfig(NamedTuple):
    """A named tuple to hold all the configurations of the Database which will be used by the MongoDB instance."""

    main_database_name: str
    """The name of the main database which includes the ``main_collection``, e.g. ``"satellite_database"``."""

    main_collection_name: str
    """The name of the main collection which resides inside the ``main_database`` and includes the actual data for the
    files, e.g. ``"files"``
    """

    url: MongoDsn
    """The URL of the MongoDB server excluding the port part, e.g. ``"mongodb://localhost:27017"``"""

    timeout: Timeout
    """The timeout in milliseconds (non-negative int), after which an exception is raised if a connection with the
    MongoDB instance is not established successfully, e.g. ``1000``.
    """


SubscriberConfig = dict[Any, Any]
"""A dictionary to hold all the configurations of the subscriber.

TODO: This has to be moved to the `posttroll` package.
"""


class AppConfig(BaseModel):
    """A model to hold all the configurations of the application including both the API server and the database.

    This will be used by Pydantic to validate the parsed YAML file.
    """
    api_server: APIServerConfig
    database: DatabaseConfig
    subscriber_config: SubscriberConfig


@validate_call
def from_yaml(filename: FilePath) -> AppConfig:
    """Parses and validates the configurations from a YAML file.

    Args:
        filename:
            The filename of a valid YAML file which holds the configurations.

    Returns:
        An instance of :class:`AppConfig`.

    Raises:
        ParserError:
            If the file cannot be properly parsed

        ValidationError:
            If the successfully parsed file fails the validation, i.e. its schema or the content does not conform to
            :class:`AppConfig`.
    """
    with open(filename, "r") as file:
        config = safe_load(file)
    try:
        return AppConfig(**config)
    except ValidationError as e:
        logger.error(e)
        sys.exit(errno.EIO)


@validate_call
def parse(config: AppConfig | FilePath) -> AppConfig:
    """Tries to return a valid object of type :class:`AppConfig`.

    Args:
        config:
            Either an object of type :class:`AppConfig` or :class:`FilePath`.

    Returns:
      - In case of an object of type :class:`AppConfig` as input, the same object will be returned as-is.
      - An input object of type ``str`` will be interpreted as a YAML filename, in which case the function returns
        the result of parsing the file.
    """
    match config:
        case AppConfig():
            return config
        case _:
            return from_yaml(config)

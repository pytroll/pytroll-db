"""The module which handles parsing and validating the config (YAML) file.

The validation is performed using `Pydantic <https://docs.pydantic.dev/latest/>`_.

Note:
    Functions in this module are decorated with
    `pydantic.validate_call <https://docs.pydantic.dev/latest/api/validate_call/#pydantic.validate_call_decorator.validate_call>`_
    so that their arguments can be validated using the corresponding type hints, when calling the function at runtime.
"""

import errno
import sys
from typing import NamedTuple, Optional, TypedDict

from bson import ObjectId
from bson.errors import InvalidId
from loguru import logger
from pydantic import AnyUrl, BaseModel, Field, FilePath, MongoDsn, ValidationError, validate_call
from pydantic.functional_validators import AfterValidator
from typing_extensions import Annotated
from yaml import safe_load

Timeout = Annotated[int, Field(gt=0)]


def id_must_be_valid(v: str) -> ObjectId:
    """Checks that the given string can be converted to a valid MongoDB ObjectId."""
    try:
        return ObjectId(v)
    except InvalidId as e:
        raise ValueError from e


MongoObjectId = Annotated[str, AfterValidator(id_must_be_valid)]


class MongoDocument(BaseModel):
    """Pydantic model for a MongoDB document."""
    _id: MongoObjectId


class LicenseInfo(TypedDict):
    """A dictionary type to hold the summary of the license information.

    Warning:
        One has to always consult the included `LICENSE` file for more information.
    """

    name: str
    """The full name of the license including the exact variant and the version (if any), e.g.
    ``"The GNU General Public License v3.0"``
    """

    url: AnyUrl
    """The URL to access the license, e.g. ``"https://www.gnu.org/licenses/gpl-3.0.en.html"``"""


class APIServerConfig(NamedTuple):
    """A named tuple to hold all the configurations of the API server (excluding the database).

    Note:
        Except for the ``url``, the attributes herein are a subset of the keyword arguments accepted by
        `FastAPI class <https://fastapi.tiangolo.com/reference/fastapi/#fastapi.FastAPI>`_ and are directly passed
        to the FastAPI class.
    """

    url: AnyUrl
    """The URL of the API server including the port, e.g. ``mongodb://localhost:8000``. This will not be passed to the
    FastAPI class. Instead, it will be used by the `uvicorn` to determine the URL of the server.
    """

    title: str
    """The title of the API server, as appears in the automatically generated documentation by the FastAPI."""

    version: str
    """The version of the API server as appears in the automatically generated documentation by the FastAPI."""

    summary: Optional[str] = None
    """The summary of the API server, as appears in the automatically generated documentation by the FastAPI."""

    description: Optional[str] = None
    """The more comprehensive description (extended summary) of the API server, as appears in the automatically
    generated documentation by the FastAPI.
    """

    license_info: Optional[LicenseInfo] = None
    """The license information of the API server, as appears in the automatically generated documentation by the
    FastAPI.
    """


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

    timeout: Annotated[int, Field(gt=-1)]
    """The timeout in milliseconds (non-negative integer), after which an exception is raised if a connection with the
    MongoDB instance is not established successfully, e.g. ``1000``.
    """


class AppConfig(BaseModel):
    """A model to hold all the configurations of the application including both the API server and the database.

    This will be used by Pydantic to validate the parsed YAML file.
    """
    api_server: APIServerConfig
    database: DatabaseConfig


@validate_call
def from_yaml(filename: FilePath) -> AppConfig:
    """Parses and validates the configurations from a YAML file.

    Args:
        filename:
            The filename of a valid YAML file which holds the configurations.

    Raises:
        -- ParserError:
            If the file cannot be properly parsed.

        -- ValidationError:
            If the successfully parsed file fails the validation, i.e. its schema or the content does not conform to
            :class:`AppConfig`.

    Returns:
        An instance of :class:`AppConfig`.
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
        -- In case of an object of type :class:`AppConfig` as input, the same object will be returned.

        -- An input object of type ``str`` will be interpreted as a YAML filename, in which case the function returns
        the result of parsing the file.
    """
    match config:
        case AppConfig():
            return config
        case _:
            return from_yaml(config)
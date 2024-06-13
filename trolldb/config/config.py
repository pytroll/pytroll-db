"""The module which handles parsing and validating the config (YAML) file.

The validation is performed using `Pydantic <https://docs.pydantic.dev/latest/>`_.

Note:
    Some functions/methods in this module are decorated with the Pydantic
    `@validate_call <https://docs.pydantic.dev/latest/api/validate_call/>`_ which checks the arguments during the
    function calls.
"""

import errno
import sys
from typing import Any, NamedTuple

from bson import ObjectId
from bson.errors import InvalidId
from loguru import logger
from pydantic import AnyUrl, BaseModel, MongoDsn, PositiveFloat, ValidationError, validate_call
from pydantic.functional_validators import AfterValidator
from typing_extensions import Annotated
from yaml import safe_load

Timeout = PositiveFloat
"""A type hint for the timeout in seconds (non-negative float)."""


@validate_call
def id_must_be_valid(id_like_string: str) -> ObjectId:
    """Checks that the given string can be converted to a valid MongoDB ObjectId.

    Args:
        id_like_string:
            The string to be converted to an ObjectId.

    Returns:
       The ObjectId object if successful.

    Raises:
        ValidationError:
            If the given argument is not of type ``str``.

        ValueError:
            If the given string cannot be converted to a valid ObjectId. This will ultimately turn into a pydantic
            validation error.

    Note:
        The reason that we change the type of the raised error is the following. As per the requirements of Pydantic,
        one can either raise a ``ValueError`` or ``AssertionError`` in a custom validator. Here we have defined a custom
        validator for a MongoDB object ID. When it fails it raises ``InvalidId`` which is not a valid exception to
        signify validation failure in Pydantic, hence the need to catch the error and raise a different one.

        Reference:
            https://docs.pydantic.dev/latest/concepts/validators/#handling-errors-in-validators

    """
    try:
        return ObjectId(id_like_string)
    except InvalidId as e:
        raise ValueError(f"{id_like_string} is not a valid value for an ID.") from e


MongoObjectId = Annotated[str, AfterValidator(id_must_be_valid)]
"""The type hint validator for object IDs."""


class APIServerConfig(NamedTuple):
    """A named tuple to hold all the configurations of the API server (excluding the database).

    Note:
        The attributes herein are a subset of the keyword arguments accepted by
        `FastAPI class <https://fastapi.tiangolo.com/reference/fastapi/#fastapi.FastAPI>`_ and are directly passed
        to the FastAPI class. Consult :func:`trolldb.api.api.run_server` on how these configurations are treated.
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
    """The URL of the MongoDB server including the port part, e.g. ``"mongodb://localhost:27017"``"""

    timeout: Timeout
    """The timeout in seconds (non-negative float), after which an exception is raised if a connection with the
    MongoDB instance is not established successfully, e.g. ``1.5``.
    """


SubscriberConfig = dict[Any, Any]
"""A dictionary to hold all the configurations of the subscriber.

TODO: This has to be moved to the `posttroll` package.
"""


class AppConfig(BaseModel):
    """A model to hold all the configurations of the application, i.e. the API server, the database, and the subscriber.

    This will be used by Pydantic to validate the parsed YAML file.
    """
    api_server: APIServerConfig
    database: DatabaseConfig
    subscriber: SubscriberConfig


@logger.catch(onerror=lambda _: sys.exit(1))
def parse_config(file) -> AppConfig:
    """Parses and validates the configurations from a YAML file (descriptor).

    Args:
        file:
            A `path-like object <https://docs.python.org/3/glossary.html#term-path-like-object>`_ or an integer file
            descriptor. This will be directly passed to the ``open()`` function. For example, it can be the filename
            (absolute or relative) of a valid YAML file which holds the configurations.

    Returns:
        An instance of :class:`AppConfig`.
    """
    logger.info("Attempt to parse the YAML file ...")
    with open(file, "r") as f:
        config = safe_load(f)
    logger.info("Parsing YAML file is successful.")

    try:
        logger.info("Attempt to validate the parsed YAML file ...")
        config = AppConfig(**config)
    except ValidationError as e:
        logger.error(e)
        sys.exit(errno.EIO)

    logger.info("Validation of the parsed YAML file is successful.")
    return config

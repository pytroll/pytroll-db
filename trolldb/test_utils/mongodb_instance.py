"""The module which defines functionalities to run a MongoDB instance which is to be used in the testing environment."""
import errno
import subprocess
import sys
import tempfile
import time
from contextlib import contextmanager
from os import mkdir, path
from shutil import rmtree

from loguru import logger

from trolldb.config.config import DatabaseConfig
from trolldb.test_utils.common import test_app_config


class TestMongoInstance:
    """A static class to enclose functionalities for running a MongoDB instance."""

    log_dir: str = tempfile.mkdtemp("__pytroll_db_temp_test_log")
    """Temp directory for logging messages by the MongoDB instance."""

    storage_dir: str = tempfile.mkdtemp("__pytroll_db_temp_test_storage")
    """Temp directory for storing database files by the MongoDB instance."""

    port: int = 28017
    """The port on which the instance will run."""

    process: subprocess.Popen | None = None
    """The (sub-)process which will be used to run the MongoDB instance."""

    @classmethod
    def __prepare_dir(cls, directory: str):
        """Auxiliary function to prepare a single directory.

        That is making a directory if it does not exist, or removing it if it does and then remaking it.
        """
        cls.__remove_dir(directory)
        mkdir(directory)

    @classmethod
    def __remove_dir(cls, directory: str):
        """Auxiliary function to remove temporary directories."""
        if path.exists(directory) and path.isdir(directory):
            rmtree(directory)

    @classmethod
    def run_subprocess(cls, args: list[str], wait=True):
        """Runs the subprocess in shell given its arguments."""
        # We suppress ruff here as we are not receiving any args from outside, e.g. port is hard-coded. Therefore,
        # sanitization of ``args`` is not required.
        cls.process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)  # noqa: S603
        if wait:
            outs, errs = cls.process.communicate()
            return outs, errs
        return None

    @classmethod
    def mongodb_exists(cls) -> bool:
        """Checks if ``mongod`` command exists."""
        outs, errs = cls.run_subprocess(["which", "mongod"])
        if outs and not errs:
            return True
        return False

    @classmethod
    def prepare_dirs(cls) -> None:
        """Prepares the temp directories."""
        cls.__prepare_dir(cls.log_dir)
        cls.__prepare_dir(cls.storage_dir)

    @classmethod
    def run_instance(cls):
        """Runs the MongoDB instance and does not wait for it, i.e. the process runs in the background."""
        cls.run_subprocess(
            ["mongod", "--dbpath", cls.storage_dir, "--logpath", f"{cls.log_dir}/mongod.log", "--port", f"{cls.port}"]
            , wait=False)

    @classmethod
    def shutdown_instance(cls):
        """Shuts down the MongoDB instance by terminating its process."""
        cls.process.terminate()
        cls.process.wait()
        for d in [cls.log_dir, cls.storage_dir]:
            cls.__remove_dir(d)


@contextmanager
def mongodb_instance_server_process_context(
        database_config: DatabaseConfig = test_app_config.database,
        startup_time=2000):
    """A synchronous context manager to run the MongoDB instance in a separate process (non-blocking).

     It uses the `subprocess <https://docs.python.org/3/library/subprocess.html>`_ package. The main use case is
     envisaged to be in testing environments.

    Args:
        database_config:
            The configuration of the database.

        startup_time:
            The overall time that is expected for the MongoDB server instance to run before the database content can be
            accessed.
    """
    TestMongoInstance.port = database_config.url.hosts()[0]["port"]
    TestMongoInstance.prepare_dirs()

    if not TestMongoInstance.mongodb_exists():
        logger.error("`mongod` is not available!")
        sys.exit(errno.EIO)

    try:
        TestMongoInstance.run_instance()
        time.sleep(startup_time / 1000)
        yield
    finally:
        TestMongoInstance.shutdown_instance()

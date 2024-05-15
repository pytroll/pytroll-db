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
    """TODO."""
    log_dir: str = tempfile.mkdtemp("__pytroll_db_temp_test_log")
    storage_dir: str = tempfile.mkdtemp("__pytroll_db_temp_test_storage")
    port: int = 28017
    process: subprocess.Popen | None = None

    @classmethod
    def prepare_dir(cls, directory: str):
        """TODO."""
        cls.remove_dir(directory)
        mkdir(directory)

    @classmethod
    def remove_dir(cls, directory: str):
        """TODO."""
        if path.exists(directory) and path.isdir(directory):
            rmtree(directory)

    @classmethod
    def run_subprocess(cls, args: list[str], wait=True):
        """TODO."""
        cls.process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)  # noqa: S603
        if wait:
            outs, errs = cls.process.communicate()
            return outs, errs
        return None

    @classmethod
    def mongodb_exists(cls) -> bool:
        """TODO."""
        outs, errs = cls.run_subprocess(["which", "mongod"])
        if outs and not errs:
            return True
        return False

    @classmethod
    def prepare_dirs(cls) -> None:
        """TODO."""
        cls.prepare_dir(cls.log_dir)
        cls.prepare_dir(cls.storage_dir)

    @classmethod
    def run_instance(cls):
        """TODO."""
        cls.run_subprocess(
            ["mongod", "--dbpath", cls.storage_dir, "--logpath", f"{cls.log_dir}/mongod.log", "--port", f"{cls.port}"]
            , wait=False)

    @classmethod
    def shutdown_instance(cls):
        """TODO."""
        cls.process.kill()
        for d in [cls.log_dir, cls.storage_dir]:
            cls.remove_dir(d)


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

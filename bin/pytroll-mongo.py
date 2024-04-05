#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os
from threading import Thread

import yaml
from posttroll.subscriber import Subscribe
from pymongo import MongoClient

logger = logging.getLogger(__name__)


class MongoRecorder:
    """A recorder for posttroll file messages."""

    def __init__(self,
                 mongo_uri="mongodb://localhost:27017",
                 db_name='sat_db'):
        """Init the recorder."""
        self.db = MongoClient(mongo_uri)[db_name]
        self.loop = True
        self._recorder = Thread(target=self.record)

    def start(self):
        """Start the recording."""
        self._recorder.start()

    def insert_files(self, msg):
        """Insert files in the database."""
        self.db.files.insert_one(msg.data)

    def record(self):
        """Log stuff."""
        try:
            with Subscribe("", addr_listener=True) as sub:
                for msg in sub.recv(timeout=1):
                    if msg:
                        logger.debug("got msg %s", str(msg))
                        if msg.type in ['collection', 'file', 'dataset']:
                            self.insert_files(msg)
                    if not self.loop:
                        logger.info("Stop recording")
                        break
        except Exception:
            logger.exception("Something went wrong in record")
            raise

    def stop(self):
        """Stop the machine."""
        self.loop = False


log_levels = {
    0: logging.WARN,
    1: logging.INFO,
    2: logging.DEBUG,
}


def setup_logging(cmd_args):
    """Set up logging."""
    if cmd_args.log_config is not None:
        with open(cmd_args.log_config) as fd:
            log_dict = yaml.safe_load(fd.read())
            logging.config.dictConfig(log_dict)
            return

    root = logging.getLogger('')
    root.setLevel(log_levels[cmd_args.verbosity])

    if cmd_args.log:
        fh_ = logging.handlers.TimedRotatingFileHandler(
            os.path.join(cmd_args.log),
            "midnight",
            backupCount=7)
    else:
        fh_ = logging.StreamHandler()

    formatter = logging.Formatter(LOG_FORMAT)
    fh_.setFormatter(formatter)

    root.addHandler(fh_)


LOG_FORMAT = "[%(asctime)s %(name)s %(levelname)s] %(message)s"

if __name__ == '__main__':
    import time
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--database",
                        help="URI to the mongo database (default mongodb://localhost:27017 ).",
                        default="mongodb://localhost:27017")
    parser.add_argument("-l", "--log",
                        help="The file to log to. stdout otherwise.")
    parser.add_argument("-c", "--log-config",
                        help="Log config file to use instead of the standard logging.")
    parser.add_argument("-v", "--verbose", dest="verbosity", action="count", default=0,
                        help="Verbosity (between 1 and 2 occurrences with more leading to more "
                             "verbose logging). WARN=0, INFO=1, "
                             "DEBUG=2. This is overridden by the log config file if specified.")
    cmd_args = parser.parse_args()

    logger = logging.getLogger("mongo_recorder")
    logger.setLevel(logging.DEBUG)
    setup_logging(cmd_args)
    logger.info("Starting up.")

    try:
        recorder = MongoRecorder(cmd_args.database)
        recorder.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        recorder.stop()
        print("Thanks for using pytroll/mongo_recorder. See you soon on www.pytroll.org!")

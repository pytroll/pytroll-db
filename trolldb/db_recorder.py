#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2012, 2013, 2014, 2015 Martin Raspaud

# Author(s):

#   Martin Raspaud <martin.raspaud@smhi.se>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Records new files into the database system.
"""

from posttroll.subscriber import Subscribe
from posttroll.message import Message
from trolldb.pytroll_db import DCManager
from trolldb.hl_file import File
from pyorbital.orbital import Orbital
from datetime import timedelta
from pyresample.utils import get_area_def
from sqlalchemy.orm.exc import NoResultFound
from threading import Thread
import os
import yaml

import logging
import logging.handlers
logger = logging.getLogger(__name__)

sat_lookup = {"Suomi-NPP": "SUOMI NPP",
              "Metop-A": "METOP-A",
              "Metop-B": "METOP-B",
              "NOAA-15": "NOAA 15",
              "NOAA-18": "NOAA 18",
              "NOAA-19": "NOAA 19",
              "EOS-Terra": "TERRA",
              "EOS-Aqua": "AQUA"
              }


class DBRecorder(object):

    """The database recording machine.

    Contains a thread listening to incomming messages, and a thread recording
    to the database.
    """

    def __init__(self,
                 nameserver_address='localhost',
                 nameserver_port=16543,
                 config_file="db.yaml"):
        self.db_thread = Thread(target=self.record)
        self.dbm = None
        self.loop = True
        self._config_file = config_file

    def init_db(self):
        with open(self._config_file) as cf:
            config = yaml.safe_load(cf.read())
        self.dbm = DCManager(config.get("uri"))

    def start(self):
        """Starts the logging.
        """
        self.init_db()
        self.db_thread.start()

    def insert_line(self, msg):
        """Insert the line corresponding to *msg* in the database.
        """
        if msg.type == "dataset":

            new_msg = Message(rawstr=str(msg))
            new_msg.type = "file"
            del new_msg.data["dataset"]

            if 'uid' not in new_msg.data:
                for item in msg.data["dataset"]:
                    new_msg.data.update(item)
                    self.insert_line(new_msg)
            else:
                self.insert_line(new_msg)

        elif msg.type == "file":

            if (("start_time" not in msg.data.keys() or
                 "end_time" not in msg.data.keys()) and
                    "area" not in msg.data.keys()):
                logger.warning("Missing field, not creating record from "
                               + str(msg))
                return
            #required_fields = ["start_time", "end_time"]
            # for field in required_fields:
            #     if field not in msg.data.keys():
            #         logger.warning("Missing required " + field
            #                     + ", not creating record from "
            #                     + str(msg))
            #         return

            try:
                import ipdb; ipdb.set_trace()
                file_obj = File(msg.data["uid"], self.dbm,
                                filetype=msg.data.get("type", None),
                                fileformat=msg.data.get("format", None))
            except NoResultFound:
                logger.warning("Cannot process: " + str(msg))
                return

            logger.debug("adding :" + str(msg))

            for key, val in msg.data.items():
                if key in ["uid", "type", "area"]:
                    continue
                if key == "uri":
                    file_obj["URIs"] += [val]
                    continue
                try:
                    file_obj[key] = val
                except NoResultFound:
                    logger.warning("Cannot add: " + str((key, val)))

            if ("start_time" in msg.data.keys() and
                    "end_time" in msg.data.keys()):
                # compute sub_satellite_track
                satname = msg.data["platform_name"]
                sat = Orbital(sat_lookup.get(satname, satname))
                dt_ = timedelta(seconds=10)
                current_time = msg.data["start_time"]
                lonlat_list = []
                while current_time < msg.data["end_time"]:
                    pos = sat.get_lonlatalt(current_time)
                    lonlat_list.append(pos[:2])
                    current_time += dt_
                pos = sat.get_lonlatalt(msg.data["end_time"])
                lonlat_list.append(pos[:2])

                logger.debug("Computed sub-satellite track")

                if len(lonlat_list) < 2:
                    logger.info("Sub satellite track to short, skipping it.")
                else:
                    file_obj["sub_satellite_track"] = lonlat_list
                    logger.debug("Added sub-satellite track")

            if "area" in msg.data.keys():
                logger.debug("Add area definition to the data")
                area_def = get_area_def(str(msg.data["area"]["id"]),
                                        str(msg.data["area"]["name"]),
                                        str(msg.data["area"]["proj_id"]),
                                        str(msg.data["area"]["proj4"]),
                                        msg.data["area"]["shape"][0],
                                        msg.data["area"]["shape"][1],
                                        msg.data["area"]["area_extent"])
                logger.debug("Adding boundary...")
                file_obj["area"] = area_def
                logger.debug("Boundary added.")

    def record(self):
        """Log stuff."""
        try:
            with Subscribe("", addr_listener=True) as sub:
                for msg in sub.recv(timeout=1):
                    if msg:
                        logger.debug("got msg %s", str(msg))
                        self.insert_line(msg)
                    if not self.loop:
                        logger.info("Stop recording")
                        break
        except:
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
    # parser.add_argument("config_file",
    #                     help="The configuration file to run on.")
    parser.add_argument("-l", "--log",
                        help="The file to log to. stdout otherwise.")
    parser.add_argument("-c", "--log-config",
                        help="Log config file to use instead of the standard logging.")
    parser.add_argument("-v", "--verbose", dest="verbosity", action="count", default=0,
                        help="Verbosity (between 1 and 2 occurrences with more leading to more "
                        "verbose logging). WARN=0, INFO=1, "
                        "DEBUG=2. This is overridden by the log config file if specified.")
    cmd_args = parser.parse_args()

    logger = logging.getLogger("db_recorder")
    logger.setLevel(logging.DEBUG)
    setup_logging(cmd_args)
    logger.info("Starting up.")

    try:
        recorder = DBRecorder()
        recorder.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        recorder.stop()
        print("Thanks for using pytroll/db_recorder. See you soon on www.pytroll.org!")


# insert a line

# pytroll://oper/polar/direct_readout/norrköping file
# safusr.u@lxserv248.smhi.se 2013-01-15T14:19:19.135161 {u'satellite':
# u'NOAA 15', u'format': u'HRPT', u'start_time': 2013-01-15T14:03:55,
# u'level': u'0', u'orbit_number': 76310, u'uri':
# u'ssh://pps.smhi.se//san1/polar_in/direct_readout/hrpt/20130115140355_NOAA_15.hmf',
# u'uid': u'20130115140355_NOAA_15.hmf', u'end_time':
# 2013-01-15T14:19:07), u'type': u'binary'}

# from db_recorder import DBRecorder
# rec = DBRecorder()
# rec.start()


# mystr = """pytroll://oper/polar/direct_readout/norrköping file safusr.u@lxserv248.smhi.se 2013-01-15T14:19:19.135161 v1.01 application/json "{'satellite': 'NOAA 15', 'format': 'HRPT', 'start_time': datetime.datetime(2013, 1, 15, 14, 3, 55), 'level': '0', 'orbit_number': 76310, 'uri': 'ssh://pps.smhi.se//san1/polar_in/direct_readout/hrpt/20130115140355_NOAA_15.hmf', 'uid': '20130115140355_NOAA_15.hmf', 'end_time': datetime.datetime(2013, 1, 15, 14, 19, 7), 'type': 'binary'}" """

# from posttroll.message import Message
# m = Message(rawstr=mystr)
# m.data = eval(m.data)

# rec.insert_line(m)

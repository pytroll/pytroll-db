#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2011, 2012, 2014, 2015.

# Author(s):

#   The pytroll team:
#   Martin Raspaud <martin.raspaud@smhi.se>

# This file is part of pytroll.

# This is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.

# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.

# You should have received a copy of the GNU General Public License along with
# this program.  If not, see <http://www.gnu.org/licenses/>.

from setuptools import setup
import imp

version = imp.load_source('doobie.version', 'doobie/version.py')


requirements = ['geoalchemy2', 'sqlalchemy==0.8.4', 'pyorbital',
                'posttroll', 'shapely', 'psycopg2', 'paramiko']

setup(name="pytroll-dibby",
      version=version.__version__,
      description='Messaging system for pytroll',
      author='The pytroll team',
      author_email='martin.raspaud@smhi.se',
      url="http://github.com/mraspaud/doobie",
      packages=['doobie'],
      zip_safe=False,
      license="GPLv3",
      install_requires=requirements,
      classifiers=[
          'Development Status :: 4 - Beta',
          'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
          'Programming Language :: Python',
          'Operating System :: OS Independent',
          'Intended Audience :: Science/Research',
          'Topic :: Scientific/Engineering',
          'Topic :: Database'
      ],
      )

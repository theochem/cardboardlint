#!/usr/bin/env python3
# Cardboardlint is a cheap lint solution for pull requests.
# Copyright (C) 2011-2017 The Cardboardlint Development Team
#
# This file is part of Cardboardlint.
#
# Cardboardlint is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# Cardboardlint is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>
# --
"""Package build and install script."""

from __future__ import print_function

import os

from setuptools import setup


NAME = 'cardboardlint'


def get_version_info():
    """Read __version__ and DEV_CLASSIFIER from version.py, using exec, not import."""
    with open(os.path.join(NAME, 'version.py'), 'r') as f:
        myglobals = {"__name__": f"{NAME}.version"}
        exec(f.read(), myglobals)  # pylint: disable=exec-used
    return myglobals['__version__'], myglobals['DEV_CLASSIFIER']


VERSION, DEV_CLASSIFIER = get_version_info()


def load_readme():
    """Load README for display on PyPI."""
    with open('README.rst') as f:
        return f.read()


setup(
    name=NAME,
    version=VERSION,
    package_dir={NAME: NAME},
    packages=[NAME, NAME + '.test'],
    description='Cheap lint solution for PRs.',
    long_description=load_readme(),
    install_requires=['pyyaml'],
    entry_points={
        'console_scripts': ['cardboardlinter = cardboardlint.__main__:main']
    },
    classifiers=[
        DEV_CLASSIFIER,
        'Environment :: Console',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ]
)

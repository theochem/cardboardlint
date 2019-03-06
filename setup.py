#!/usr/bin/env python
# -*- coding: utf-8 -*-
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

from setuptools import setup

setup(
    name='cardboardlint',
    version='0.0.0',
    description='Cheap lint solution for PRs.',
    scripts=['scripts/cardboardlinter'],
    package_dir={'cardboardlint': 'cardboardlint'},
    packages=['cardboardlint', 'cardboardlint.tests'],
    install_requires=['pyyaml'],
    zip_safe=False,
    classifiers=[
        'Environment :: Console',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
)

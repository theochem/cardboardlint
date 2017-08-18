#!/usr/bin/env python
"""Package build and install script."""

from __future__ import print_function

from glob import glob

from setuptools import setup

if __name__ == '__main__':
    setup(
        name='cardboardlint',
        version='0.0.0',
        description='Cheap lint solution for PRs.',
        scripts=glob("scripts/*"),
        classifiers=[
            'Environment :: Console',
            'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
            'Operating System :: POSIX :: Linux',
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3',
        ],
    )

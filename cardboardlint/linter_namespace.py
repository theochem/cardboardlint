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
"""Linter for namespace collisions.

This script imports every module in the packages and checks for overlapping name spaces.
It also checks if __all__ is missing and if some forbidden names are present in the
public namespace of a module.
"""

import os
import sys
import importlib

from .linter import Linter
from .report import Report


__all__ = []


DEFAULT_CONFIG = {
    # Filename filter rules
    'filefilter': ['- */tests/__init__.py', '- */test_*.py', '- *setup.py', '+ *.py', '+ *.pyx'],
    # Names that are not allowed in the public namespace.
    'forbidden': ['numpy', 'scipy', 'h5py', 'pyplot', 'np', 'h5', 'plt'],
}


def lint(config: dict, report: Report, _numproc: int = 1, _fixit: bool = False):
    """Lint Python namespace collisions.

    Parameters
    ----------
    config
        Dictionary that contains the configuration for the linter.
    report
        Collection of filenames and corresponding messages.
    _numproc
        The number of processors to use.
    _fixit
        When True, the linter will try to fix (a part of) the problems in each
        file.

    """
    print('CHECKING FILES     : {0}'.format(' '.join(report.filenames)))

    # Make sure we test the source tree and not some locally installed copy.
    sys.path.insert(0, '.')

    # Find all module names and load namespaces
    namespace = {}
    for filename in report.filenames:
        # remove extension and replace / by .
        modulename = os.path.splitext(filename)[0].replace('/', '.')

        # Check all public names of the module.
        module = importlib.import_module(modulename)
        names = dir(module)
        if '__all__' in names:
            for name in names:
                if name in module.__all__:
                    namespace.setdefault(name, []).append(filename)
                    if name in config['forbidden']:
                        report(filename, None, None,
                               'Invalid name in namespace: {0}'.format(name))
        else:
            report(filename, None, None, 'Missing __all__')

    # Fix sys.path
    del sys.path[0]

    # Detect collisions
    for name, sourcefiles in namespace.items():
        if len(sourcefiles) > 1:
            text = "Name '{0}' found in more than one module: {1}".format(
                name, ' '.join(sourcefiles))
            report(sourcefiles[0], None, None, text)


LINTER = Linter('namespace', lint, DEFAULT_CONFIG, style='dynamic', language='python')

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
"""Linter for namespace collisions.

This script imports every module in the packages and checks for overlapping name spaces.
It also checks if __all__ is missing and if some forbidden names are present in the
public namespace of a module.
"""
from __future__ import print_function

import os
import sys
import importlib

from cardboardlint.common import Message, filter_filenames, static


__all__ = ['linter_namespace']


DEFAULT_CONFIG = {
    # Filename patterns to be considered for the namespace linter.
    'include': ['*.py', '*.pyx'],
    # Optionally, exclusion rules that override the 'include' config above.
    'exclude': ['*/tests/__init__.py', '*/test_*.py', '*setup.py'],
    # Names that are not allowed in the public namespace.
    'forbidden': ['numpy', 'scipy', 'h5py', 'pyplot', 'np', 'h5', 'plt'],
}


@static
def linter_namespace(linter_config, files_lines):
    """Linter for checking namespace Python namespace collisions.

    Parameters
    ----------
    linter_config : dict
        Dictionary that contains the configuration for the linter
    files_lines : dict
        Dictionary of filename to the set of line numbers (that have been modified).
        See `run_diff` function in `carboardlinter`.
    """
    config = DEFAULT_CONFIG.copy()
    config.update(linter_config)

    # Get all relevant filenames
    filenames = filter_filenames(files_lines.keys(), config['include'], config['exclude'])

    # Make sure we test the source tree and not some locally installed copy of HORTON.
    sys.path.insert(0, '.')

    # Find all module names and load namespaces
    namespace = {}
    messages = []
    for filename in filenames:
        # remove extension and replace / by .
        modulename = os.path.splitext(filename)[0].replace('/', '.')

        # Check all public names of the module.
        module = importlib.import_module(modulename)
        names = dir(module)
        if '__all__' in names:
            for name in names:
                if name in module.__all__:
                    namespace.setdefault(name, []).append(modulename)
                    if name in config['forbidden']:
                        messages.append(Message(
                            filename, None, None,
                            'Invalid name in namespace: {0}'.format(name)))
        else:
            messages.append(Message(filename, None, None, 'Missing __all__'))

    # Fix sys.path
    del sys.path[0]

    # Detect collisions
    for name, modules in namespace.items():
        if len(modules) > 1:
            text = "Name '{0}' found in more than one module: {1}".format(name, ' '.join(modules))
            messages.append(Message(None, None, None, text))
    return messages

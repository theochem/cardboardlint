"""Linter for namespace collisions.

This script imports every module in the packages and checks for overlapping name spaces
"""
from __future__ import print_function

import os
import sys
import importlib

from cardboardlint.common import Message, filter_filenames


__all__ = ['linter_namespace']


DEFAULT_CONFIG = {
    'include': ['*.py', '*.pyx'],
    'exclude': ['test_*.py', 'setup.py'],
    'forbidden': ['numpy', 'scipy', 'h5py', 'pyplot', 'np', 'h5', 'plt'],
}


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

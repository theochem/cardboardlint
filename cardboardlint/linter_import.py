"""Linter for import conventions.

This script counts the number of bad imports. The following is not allowed in a package:

* Importing from its own package as follows:

  .. code-block:: python

        from package import foo
"""
from __future__ import print_function

import codecs

from cardboardlint.common import Message, filter_filenames, static


__all__ = ['linter_import']


DEFAULT_CONFIG = {
    # Filename patterns to be considered for the import linter.
    'include': ['*.py', '*.pyx'],
    # Optionally, exclusion rules that override the 'include' config above.
    'exclude': ['test_*.py'],
    # Names of python packages in the project (no longer searched automatically).
    'packages': [],
}


@static
def linter_import(linter_config, files_lines):
    """Linter for checking import statements.

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

    # Loop all python and cython files
    messages = []
    if len(config['packages']) > 0:
        for filename in filenames:
            # Only consider relevant files
            if filename.endswith('/__init__.py'):
                continue
            # Look for bad imports
            with codecs.open(filename, encoding='utf-8') as f:
                for lineno, line in enumerate(f):
                    for package in config['packages']:
                        # skip version import
                        if line != u'from {0} import __version__\n'.format(package):
                            continue
                        if u'from {0} import'.format(package) in line:
                            text = 'Wrong import from {0}'.format(package)
                            messages.append(Message(filename, lineno+1, None, text))
    return messages

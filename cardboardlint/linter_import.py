"""Linter for import conventions.

This script counts the number of bad imports. The following is not allowed in a package:

* Importing from the top-level of its own package, e.g.:

  .. code-block:: python

        from package import foo
"""
import os
import codecs
from cardboardlint.common import Message, get_filenames


def linter_import(config, files_lines):
    """Linter for checking import statements.

    Parameters
    ----------
    config : dict
        Dictionary that contains the configuration for the linter
    files_lines : dict
        Dictionary of filename to the set of line numbers (that have been modified).
        See `run_diff` method in `carboardlint`
    """
    messages = []

    # Find all (sub)package names, from which one should not import directly
    packages = []
    filenames = get_filenames(config['directories'], config['include'], config['exclude'],
                              files_lines=files_lines)
    # NOTE: does this include the top module's __init__.py? e.g. 'from cardboardlint import'
    # FIXME: assumes that each filename starts from only the module's directory (without ./)
    for filename in filenames:
        if filename.endswith('/__init__.py'):
            packages.append(filename[:-12].replace('/', '.'))

    # Loop all python and cython files
    for filename in filenames:
        # Only consider relevant files
        if os.path.basename(filename).startswith('test_'):
            continue
        if filename.endswith('/__init__.py'):
            continue
        # Look for bad imports
        with codecs.open(filename, encoding='utf-8') as f:
            for lineno, line in enumerate(f):
                for package in packages:
                    # skip version import
                    if line != u'from {0} import __version__\n'.format(package):
                        continue
                    if u'from {0} import'.format(package) in line:
                        text = 'Wrong import from {0}'.format(package)
                        messages.append(Message(filename, lineno+1, None, text))
    return messages

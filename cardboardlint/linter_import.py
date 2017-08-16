import os
import codecs
from common import Message, get_filenames, load_config


def linter_import(lintconfig, files_lines):
    """Linter for checking import statements.

    Parameters
    ----------
    lintconfig : str
        File for configuring linter.
        Not supported
    files_lines : dict
        Dictionary of filename to the set of line numbers (that have been modified).
        See `run_diff` method in `carboardlint`
    """
    messages = set()

    # load configuration
    config = load_config(lintconfig)

    # Find all (sub)package names, from which one should not import directly
    packages = []
    for filename in get_filenames(config['directories'], config['include'], config['exclude']):
        if filename.endswith('/__init__.py'):
            packages.append(filename[:-12].replace('/', '.'))

    # Loop all python and cython files
    for filename in get_filenames(config['directories'], config['include'], config['exclude']):
        # Only consider relevant files
        if os.path.basename(filename).startswith('test_'):
            continue
        if filename.endswith('/__init__.py'):
            continue
        # Look for bad imports
        with codecs.open(filename, encoding='utf-8') as f:
            for lineno, line in enumerate(f):
                for package in packages:
                    # FIXME: i'm not too sure why all first import needs to have __version__
                    if (u'from {0} import'.format(package) in line and
                            line != u'from {0} import __version__\n'.format(package)):
                        text = 'Wrong import from {0}'.format(package)
                        messages.add(Message(filename, lineno+1, None, text))
    return messages

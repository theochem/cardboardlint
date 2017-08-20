"""Linter using pylint.

This test calls the pylint program, see http://docs.pylint.org/index.html.
"""
from __future__ import print_function

import json

from cardboardlint.common import Message, run_command, filter_filenames, dynamic


__all__ = ['linter_pylint']


DEFAULT_CONFIG = {
    # Filename patterns to be considered for Pylint.
    'include': ['*.py', 'scripts/*'],
    # Optionally, exclusion rules that override the 'include' config above.
    'exclude': ['test_*.py'],
    # Location of the Pylint config file.
    'pylintrc': '.pylintrc',
}


@dynamic
def linter_pylint(linter_config, files_lines):
    """Linter for checking pylint results.

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

    # get Pylint version
    command = ['pylint', '--version', '--rcfile={0}'.format(config['pylintrc'])]
    version_info = ''.join(run_command(command, verbose=False)[0].split('\n')[:2])
    print('USING              : {0}'.format(version_info))

    # Get all relevant filenames
    filenames = filter_filenames(files_lines.keys(), config['include'], config['exclude'])

    messages = []
    if len(filenames) > 0:
        command = ['pylint'] + filenames
        command += ['--rcfile={0}'.format(config['pylintrc']), '--jobs=2',
                    '--output-format=json']
        has_failed = lambda returncode, stdout, stderr: not 0 <= returncode < 32
        output = run_command(command, has_failed=has_failed)[0]
        if len(output) > 0:
            for plmap in json.loads(output):
                charno = plmap['column']
                if charno == 0:
                    charno = None
                messages.append(Message(
                    plmap['path'], plmap['line'], charno,
                    '{0} {1}'.format(plmap['symbol'], plmap['message'])))
    return messages

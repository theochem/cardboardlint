"""Linter using pylint.

This test calls the pylint program, see http://docs.pylint.org/index.html.

* `config_file` is a configuration file.
* `include` is the unix shell-style wildcard search keywords that specify the files that will be
  tested using.
* `exclude` is the unix shell-style wildcard search keywords that specify the files that will not
  be tested using.
"""
from __future__ import print_function

import json

from cardboardlint.common import Message, run_command, filter_filenames


__all__ = ['linter_pylint']


DEFAULT_CONFIG = {
    'include': ['*.py', 'scripts/*'],
    'exclude': ['test_*.py'],
    'pylintrc': '.pylintrc',
}


def linter_pylint(linter_config, files_lines):
    """Linter for checking pylint results.

    Parameters
    ----------
    linter_config : dict
        Dictionary that contains the configuration for the linter
    files_lines : dict
        Dictionary of filename to the set of line numbers (that have been modified).
        See `run_diff` method in `carboardlint`
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

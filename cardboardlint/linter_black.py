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
"""Linter using black.

This test calls the black program, see https://black.readthedocs.io/en/stable/
"""

from .diff import parse_unified_diff
from .linter import Linter, process_patch
from .report import Report
from .utils import run_command


__all__ = []


DEFAULT_CONFIG = {
    # Filename filter rules
    'filefilter': ['+ *.py', '+ bin/*'],
    # Optional path to the config file.
    'config': None,
    # The python version of interest
    'target_version': 'py37',
}


def lint(config: dict, report: Report, _numproc: int = 1, fixit: bool = False):
    """Lint with black.

    Parameters
    ----------
    config
        Dictionary that contains the configuration for the linter.
    report
        Collection of filenames and corresponding messages.
    _numproc
        The number of processors to use.
    fixit
        When True, the linter will try to fix (a part of) the problems in each
        file.

    """
    # get black version
    command = ['black', '--version']
    version_info = run_command(command, verbose=False)[0]
    print('USING              : {0}'.format(version_info))

    if len(report.filenames) > 0:
        command = ['black', '--diff', '--target-version', config['target_version']]
        command += report.filenames
        if config['config'] is not None:
            command += ['--config={}'.format(config['config'])]
        output = run_command(command)[0]
        if len(output) > 0:
            patch = parse_unified_diff(output, '', '')
            process_patch(patch, report, fixit)


LINTER = Linter('black', lint, DEFAULT_CONFIG, language='python', can_fix=True)

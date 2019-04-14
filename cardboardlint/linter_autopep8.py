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
"""Linter using autopep8.

This test calls the autopep8 program, see https://github.com/hhatto/autopep8
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
    # Line range sets a range of line lengths that are tollerated. This
    # should be a tuple of two integers.
    'line-range': None,

}


def lint(config: dict, report: Report, _numproc: int = 1, fixit: bool = False):
    """Lint with autopep8.

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
    # get autopep8 version
    command = ['autopep8', '--version']
    version_info = run_command(command, verbose=False)[0]
    print('USING              : {0}'.format(version_info))

    if len(report.filenames) > 0:
        command = ['autopep8', '-d'] + report.filenames
        if config['config'] is not None:
            command += ['--global-config={}'.format(config['config']),
                        '--ignore-local-config']
        if config['line-range'] is not None:
            low, high = config['line-range']
            command += ['--line-range', str(low), str(high)]
        output = run_command(command)[0]
        if len(output) > 0:
            patch = parse_unified_diff(output, 'original/', 'fixed/')
            process_patch(patch, report, fixit)


LINTER = Linter('autopep8', lint, DEFAULT_CONFIG, language='python', can_fix=True)

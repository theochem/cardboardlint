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
"""Linter using pylint.

This test calls the pylint program, see http://docs.pylint.org/index.html.
"""

import json

from .linter import Linter
from .report import Report
from .utils import run_command


__all__ = []


DEFAULT_CONFIG = {
    # Filename filter rules
    'filefilter': ['+ *.py', '+ bin/*'],
    # Optional path to the config file.
    'config': None
}


def lint(config: dict, report: Report, numproc: int = 1, _fixit: bool = False):
    """Lint with pylint.

    Parameters
    ----------
    config
        Dictionary that contains the configuration for the linter.
    report
        Collection of filenames and corresponding messages.
    numproc
        The number of processors to use.
    _fixit
        When True, the linter will try to fix (a part of) the problems in each
        file.

    """
    # get Pylint version
    command = ['pylint', '--version']
    version_info = ' '.join(run_command(command, verbose=False)[0].split('\n')[:-3])
    print('USING              : {0}'.format(version_info))

    def has_failed(returncode, _stdout, _stderr):
        """Determine if pylint ran correctly."""
        return not 0 <= returncode < 32

    if len(report.filenames) > 0:
        command = ['pylint'] + report.filenames
        command += ['--jobs={}'.format(numproc), '--output-format=json']
        if config['config'] is not None:
            command += ['--rcfile={0}'.format(config['config'])]
        output = run_command(command, has_failed=has_failed)[0]
        if len(output) > 0:
            for plmap in json.loads(output):
                charno = plmap['column']
                if charno in [0, -1]:
                    charno = None
                report(plmap['path'], plmap['line'], charno,
                       '{0} {1}'.format(plmap['symbol'], plmap['message']))


# Pylint should be considered dynamic, which is in practice only true for projects with
# extension modules.
LINTER = Linter('pylint', lint, DEFAULT_CONFIG, style='dynamic', language='python')

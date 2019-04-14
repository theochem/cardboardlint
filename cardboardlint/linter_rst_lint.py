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
"""Linter using restructuredtext-lint.

This test calls the restructuredtext-lint program,
see https://github.com/twolfson/restructuredtext-lint
"""

import json

from .linter import Linter
from .report import Report
from .utils import run_command


__all__ = []


DEFAULT_CONFIG = {
    # Filename filter rules
    'filefilter': ['+ *.rst'],
}


def lint(_config: dict, report: Report, _numproc: int = 1, _fixit: bool = False):
    """Lint with restructuredtext-lint.

    Parameters
    ----------
    _config
        Dictionary that contains the configuration for the linter.
    report
        Collection of filenames and corresponding messages.
    _numproc
        The number of processors to use.
    _fixit
        When True, the linter will try to fix (a part of) the problems in each
        file.

    """
    command = ['rst-lint', '--version']
    version_info = ''.join(run_command(command, verbose=False)[0].split('\n')[:2])
    print('USING              : {0}'.format(version_info))

    def has_failed(returncode, _stdout, _stderr):
        """Determine if rst-lint ran correctly."""
        return returncode == 1

    if len(report.filenames) > 0:
        command = ['rst-lint', '--format', 'json'] + report.filenames
        output = run_command(command, has_failed=has_failed)[0]
        if len(output) > 0:
            for rlmap in json.loads(output):
                report(rlmap['source'], rlmap['line'], None,
                       '{0} {1}'.format(rlmap['type'], rlmap['message']))


LINTER = Linter('rst-lint', lint, DEFAULT_CONFIG, style='static', language='rst')

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
"""Linter using pydocstyle.

This test calls the flake program, see http://pydocstyle.pycqa.org
"""

from .linter import Linter
from .report import Report
from .utils import run_command


__all__ = []


DEFAULT_CONFIG = {
    # Filename filter rules
    'filefilter': ['+ *.py', '+ *.pyx', '+ *.pxd', '+ bin/*'],
    # Optional path to the config file.
    'config': None
}


def lint(config: dict, report: Report, _numproc: int = 1, _fixit: bool = False):
    """Linter for checking pydocstyle results.

    Parameters
    ----------
    config
        Dictionary that contains the configuration for the linter.
    report
        Collection of filenames and corresponding messages.
    _numproc
        The number of processors to use.
    _fixit
        When True, the linter will try to fix (a part of) the problems in each
        file.

    """
    # get pydocstyle version
    command = ['pydocstyle', '--version']
    version_info = run_command(command, verbose=False)[0]
    print('USING              : {0}'.format(version_info))

    def has_failed(returncode, _stdout, _stderr):
        """Determine if pydocstyle ran correctly."""
        return not 0 <= returncode < 2

    if len(report.filenames) > 0:
        command = ['pydocstyle'] + report.filenames
        if config['config'] is not None:
            command += ['--config={0}'.format(config['config'])]
        output = run_command(command, has_failed=has_failed)[0]
        lines = output.split('\n')[:-1]
        while len(lines) > 0:
            if 'WARNING: ' in lines[0]:
                lines.pop(0)
            else:
                words = lines.pop(0).split()
                filename, lineno = words[0].split(':')
                code, description = lines.pop(0).split(':', 1)
                code = code.strip()
                description = description.strip()
                report(filename, int(lineno), None, '%s %s' % (code, description))


LINTER = Linter('pydocstyle', lint, DEFAULT_CONFIG, language='python')

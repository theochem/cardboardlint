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
"""Linter using CPPLint.

This test calls the cpplint.py program, see https://github.com/google/styleguide
"""

from .linter import Linter
from .report import Report
from .utils import run_command


__all__ = []


DEFAULT_CONFIG = {
    # Filename filter rules
    'filefilter': ['+ *.h', '+ *.h.in', '+ *.cpp', '+ *.c'],
    # Location of the file
    'script': 'cpplint',
    # CPPLint rules to include or exclude
    'filter': '',
    # Max line length
    'linelength': 100,
}


def _has_failed(_returncode, stdout, _stderr):
    """Determine if cpplint.py has failed."""
    return 'FATAL' in stdout


def lint(config: dict, report: Report, _numproc: int = 1, _fixit: bool = False):
    """Lint with cpplint.

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
    if len(report.filenames) > 0:
        # Call cpplint
        command = [config['script'], '--linelength={}'.format(config['linelength'])]
        if config['filter'] != '':
            command.append('--filter={}'.format(config['filter']))
        command.extend(report.filenames)
        output = run_command(command, has_failed=_has_failed)[1]

        # Parse the output of cpplint into standard return values
        for line in output.split('\n')[:-1]:
            words = line.split()
            if len(words) == 0 or words[0].count(':') != 2:
                continue
            filename, lineno = words[0].split(':')[:2]
            description = ' '.join(words[1:-2])
            tag = words[-2]
            priority = words[-1]
            lineno = int(lineno)
            if lineno == 0:
                lineno = None
            report(filename, lineno, None, '{} {} {}'.format(priority, tag, description))


LINTER = Linter('cpplint', lint, DEFAULT_CONFIG, language='cpp')

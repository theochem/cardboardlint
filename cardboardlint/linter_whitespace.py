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
"""Linter for whitespace conventions.

This script checks for three ugly things: tabs, trailing whitespace and trailing newlines.
"""

import codecs

from .linter import Linter
from .report import Report


__all__ = []


DEFAULT_CONFIG = {
    # Filename filter rules
    'filefilter': ['+ *'],
    # The preferred tab width. Tabs will be replaced by the tabwidth number of
    # spaces by the fixer.
    'tabwidth': 4,
}


def lint(config: dict, report: Report, _numproc: int = 1, fixit: bool = False):
    """Lint whitespace conventions.

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
    print('CHECKING FILES     : {0}'.format(' '.join(report.filenames)))

    # Loop over all files and check whitespace in each file.
    for filename in report.filenames:
        try:
            _check_file(filename, config, report, fixit)
        except UnicodeDecodeError as err:
            report(filename, None, None, str(err))


def _check_file(filename: str, config: dict, report: Report, fixit: bool = False):
    """Look for white-space issues.

    Parameters
    ----------
    filename
        File to be checked
    config
        Dictionary that contains the configuration for the linter.
    report
        Collection of filenames and corresponding messages.
    fixit
        When True, whitespace issues in the file are fixed. The file is only
        rewritten if changes are needed.

    """
    # Load all lines from the file.
    with codecs.open(filename, encoding='utf-8') as f:
        lines = list(f)

    # Check and optionally fix line by line.
    changed = False
    lineno = len(lines) - 1
    while lineno > 0:
        line = lines[lineno]
        if lineno == len(lines) - 1:
            if line.strip() == "":
                if report(filename, lineno + 1, None, 'trailing empty line') and fixit:
                    del lines[lineno]
                    changed = True
                    lineno -= 1
                    continue
            if not line.endswith('\n'):
                line = _check_line(filename, lineno, 'last linit missing \\n',
                                   line, line + '\n', report)
        line = _check_line(filename, lineno, 'tab', line,
                           line.replace('\t', ' '*config['tabwidth']), report)
        line = _check_line(filename, lineno, 'carriage return', line,
                           line.replace('\r', ''), report)
        line = _check_line(filename, lineno, 'trailing whitespace', line,
                           line.rstrip() + '\n', report)
        # Replace the line by its cleaned version. Only matters when fixit=True
        if fixit and line != lines[lineno]:
            lines[lineno] = line
            changed = True
        lineno -= 1

    # Fix the file if requested.
    if changed:
        assert fixit  # Internal consistenct check
        with codecs.open(filename, 'w', encoding='utf-8') as f:
            f.write(''.join(lines))


def _check_line(filename: str, lineno: int, msg: str, oldline: str,
                fixedline: str, report: Report) -> str:
    """Look for issues on one line.

    Parameters
    ----------
    filename
        File to be checked
    lienno
        The line number of the line being checked
    msg
        The message for this check.
    oldline
        The line before fixing.
    fixedline
        The line after fixing.
    report
        Collection of filenames and corresponding messages.

    """
    # Bail out early when there are no differences
    if oldline == fixedline:
        return oldline
    # Find the first charachter where oldline and fixedline differ.
    charno = 0
    charno_end = min(len(oldline), len(fixedline))
    while charno < charno_end and oldline[charno] == fixedline[charno]:
        charno += 1
    if report(filename, lineno + 1, charno + 1, msg):
        return fixedline
    else:
        return oldline


LINTER = Linter('whitespace', lint, DEFAULT_CONFIG, can_fix=True)

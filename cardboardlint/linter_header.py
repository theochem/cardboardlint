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
"""Linter for source file headers.

This linter checks if the headers of source files are correctly formatted. The header
is read in from some file and it is expected that the source files contain this header
as a comment at the start of the file. Options can be used to allow other lines to be
present, such as a shebang line or a mode line.
"""

import codecs
from typing import List

from .linter import Linter
from .report import Report


__all__ = []


DEFAULT_CONFIG = {
    # Filename filter rules
    'filefilter': ['+ *.py', '+ *.pyx', '+ *.pxd', '+ bin/*'],
    # The path to the header file'
    'header': 'HEADER',
    # Comments start with:
    'comment': '# ',
    # Format of the shebang line, only checked if a shebang line is present
    'shebang': '#!/usr/bin/env python',
    # Some extra lines that should be inserted above the header (but under the shebang if
    # present)
    'extra': ['-*- coding: utf-8 -*-'],
}


def lint(config: dict, report: Report, _numproc: int = 1, fixit: bool = False):
    """Lint and optionally fix source file headers.

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
    print('HEADER             : {0}'.format(config['header']))
    print('CHECKING FILES     : {0}'.format(' '.join(report.filenames)))

    # Load the header file as a set of lines
    with codecs.open(config['header'], encoding='utf-8') as f:
        header_lines = list(f)

    # Loop all files and check in the header each file.
    for filename in report.filenames:
        try:
            _check_file(filename, config, header_lines, report, fixit)
        except UnicodeDecodeError as err:
            report(filename, None, None, str(err))


def _check_file(filename: str, config: dict, header_lines: List[str],
                report: Report, fixit: bool = False):
    """Look for bad filename headers.

    Parameters
    ----------
    filename
        File to be checked
    config
        Dictionary with configuration of the linters.
    header_lines
        The expected header.
    report
        Collection of filenames and corresponding messages.
    fixit
        When True, header issues in the file are fixed. The file is only
        rewritten if changes are needed.

    """
    # Load all lines from the file.
    with codecs.open(filename, encoding='utf-8') as f:
        lines = list(f)

    # Build the list with expected lines
    expected_lines = []
    if lines and lines[0].startswith('#!') and config['shebang'] is not None:
        expected_lines.append(config['shebang'] + '\n')
    comment = config['comment']
    for extra_line in config['extra']:
        expected_lines.append((comment + extra_line).rstrip() + '\n')
    for header_line in header_lines:
        expected_lines.append((comment + header_line).rstrip() + '\n')
    expected_lines.append(comment + '--\n')

    # Compare expected with actual
    needs_fixing = False
    for lineno, (expected_line, line) in enumerate(zip(expected_lines, lines)):
        if expected_line != line:
            if report(filename, lineno + 1, None,
                      'Line should be: {}'.format(expected_line[:-1])):
                needs_fixing = True

    # Fix if requested
    if fixit and needs_fixing:
        try:
            first_keep = lines.index(expected_lines[-1]) + 1
        except ValueError:
            if lines and lines[0].startswith('#!'):
                first_keep = 1
            else:
                first_keep = 0
        lines = lines[first_keep:]
        lines = expected_lines + lines
        with codecs.open(filename, 'w', encoding='utf-8') as f:
            f.write(''.join(lines))


LINTER = Linter('header', lint, DEFAULT_CONFIG, can_fix=True)

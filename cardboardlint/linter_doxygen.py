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
"""Trapdoor test using doxygen to find undocumented C++ code.

This linter uses doxygen, see http://www.doxygen.org.
"""

import os

from .linter import Linter
from .report import Report
from .utils import run_command


__all__ = []


DEFAULT_CONFIG = {
    # Filename filter rules
    'filefilter': ['+ *.h'],
}


DOXYGEN_CONFIG = """\
INPUT                  = {}
DOXYFILE_ENCODING      = UTF-8
PROJECT_NAME           = poor
GENERATE_HTML          = NO
GENERATE_LATEX         = NO
WARNINGS               = YES
WARN_IF_UNDOCUMENTED   = YES
WARN_IF_DOC_ERROR      = YES
WARN_FORMAT            = "~~WARN~~ $file:$line: $text"
GENERATE_AUTOGEN_DEF   = NO
"""


def lint(_config: dict, report: Report, _numproc: int = 1, _fixit: bool = False):
    """Lint with doxygen to find undocumented headers.

    Parameters
    ----------
    _config
        Dictionary that contains the configuration for the linter.
        _config is not used by this linter.
    report
        Collection of filenames and corresponding messages.
    _numproc
        The number of processors to use.
    _fixit
        When True, the linter will try to fix (a part of) the problems in each
        file.

    """
    command = ['doxygen', '--version']
    print('USING              : doxygen', run_command(command, verbose=False)[0].strip())

    if len(report.filenames) > 0:
        # Call doxygen in the doc subdirectory, mute output because it only confuses
        command = ['doxygen', '-']
        stdin = DOXYGEN_CONFIG.format(' '.join(report.filenames))
        print('STDIN              :')
        print(stdin)
        output = run_command(command, stdin=stdin)[1]

        # Parse the file doxygen_warnings
        prefix = os.getcwd() + '/'

        lines = output.split('\n')
        for line in lines:
            if line.startswith('~~WARN~~'):
                location, description = line[9:].split(None, 1)
                filename, lineno = location.split(':')[:2]
                if filename.startswith(prefix):
                    filename = filename[len(prefix):]
                report(filename, int(lineno), None, description)


LINTER = Linter('doxygen', lint, DEFAULT_CONFIG, language='cpp')

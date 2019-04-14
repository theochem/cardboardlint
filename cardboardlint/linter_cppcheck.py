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
"""Linter using Cppcheck.

This test calls the cppcheck program, see http://cppcheck.sourceforge.net/.
"""

from xml.etree import ElementTree

from .linter import Linter
from .report import Report
from .utils import run_command


__all__ = []


DEFAULT_CONFIG = {
    # Filename filter rules
    'filefilter': ['+ *.h', '+ *.h.in', '+ *.cpp', '+ *.c'],
}


def lint(_config: dict, report: Report, numproc: int = 1, _fixit: bool = False):
    """Lint with cppcheck.

    Parameters
    ----------
    _config
        Dictionary that contains the configuration for the linter.
        _config is not used by this linter.
    report
        Collection of filenames and corresponding messages.
    numproc
        The number of processors to use.
    _fixit
        When True, the linter will try to fix (a part of) the problems in each
        file.

    """
    # Get version
    print('USING VERSION      : {0}'.format(
        run_command(['cppcheck', '--version'], verbose=False)[0].strip()))

    if len(report.filenames) > 0:
        # Call Cppcheck
        command = (['cppcheck', '-j', str(numproc)] + report.filenames +
                   ['-q', '--enable=all', '--language=c++', '--std=c++11', '--xml',
                    '--suppress=missingIncludeSystem', '--suppress=unusedFunction'])
        xml_str = run_command(command)[1]
        etree = ElementTree.fromstring(xml_str)

        # Parse the output of Cppcheck into standard return values
        for error in etree:
            if 'file' not in error.attrib:
                continue
            # key = '{:<15}  {:<40}  {:<30}' % (error.attrib['severity'],
            #                                   error.attrib['file'],
            #                                   error.attrib['id'])
            text = '{} {} {}'.format(
                error.attrib['severity'], error.attrib['id'], error.attrib['msg'])
            lineno = int(error.attrib['line'])
            if lineno == 0:
                lineno = None
            report(error.attrib['file'], lineno, None, text)


LINTER = Linter('cppcheck', lint, DEFAULT_CONFIG, language='cpp')

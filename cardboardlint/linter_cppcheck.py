# -*- coding: utf-8 -*-
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
from __future__ import print_function

from xml.etree import ElementTree

from cardboardlint.common import run_command, Message, filter_filenames, static


__all__ = ['linter_cppcheck']


DEFAULT_CONFIG = {
    # Filename patterns to be considered for cppcheck.
    'include': ['*.h', '*.h.in', '*.cpp', '*.c'],
    # Optionally, exclusion rules that override the 'include' config above.
    'exclude': [],
}


@static
def linter_cppcheck(linter_config, files_lines):
    """Linter for cppcheck.

    Parameters
    ----------
    linter_config : dict
        Dictionary that contains the configuration for the linter
        Not supported
    files_lines : dict
        Dictionary of filename to the set of line numbers (that have been modified)
        See `run_diff` function in `carboardlinter`.
    """
    config = DEFAULT_CONFIG.copy()
    config.update(linter_config)

    # Get version
    print('USING VERSION      : {0}'.format(
        run_command(['cppcheck', '--version'], verbose=False)[0].strip()))

    # Get the relevant filenames
    filenames = filter_filenames(files_lines.keys(), config['include'], config['exclude'])

    messages = []
    if len(filenames) > 0:
        # Call Cppcheck
        command = (['cppcheck'] + filenames +
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
            messages.append(Message(error.attrib['file'], int(error.attrib['line']), None, text))

    return messages

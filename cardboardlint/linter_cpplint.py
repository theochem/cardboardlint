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
"""Linter using CPPLint.

This test calls the cpplint.py program, see https://github.com/google/styleguide
"""
from __future__ import print_function

from cardboardlint.common import run_command, Message, matches_filefilter, flag


__all__ = ['linter_cpplint']


DEFAULT_CONFIG = {
    # Filename filter rules
    'filefilter': ['+ *.h', '+ *.h.in', '+ *.cpp', '+ *.c'],
    # Location of the file
    'script': './cpplint.py'
}


def has_failed(_returncode, stdout, _stderr):
    """Determine if cpplint.py has failed."""
    return 'FATAL' in stdout


@flag(static=True, cpp=True)
def linter_cpplint(linter_config, files_lines):
    """Linter for cpplint.

    Parameters
    ----------
    linter_config : dict
        Dictionary that contains the configuration for the linter
        Not supported
    files_lines : dict
        Dictionary of filename to the set of line numbers (that have been modified)
        See `run_diff` function in `carboardlinter`.

    Returns
    -------
    messages : list
        The list of messages generated by the external linter.

    """
    config = DEFAULT_CONFIG.copy()
    config.update(linter_config)

    # Get the relevant filenames
    filenames = [filename for filename in files_lines
                 if matches_filefilter(filename, config['filefilter'])]

    messages = []
    if len(filenames) > 0:
        # Call cpplint
        command = ([config['script'], '--linelength=100', '--filter=-runtime/int'] +
                   filenames)
        output = run_command(command, has_failed=has_failed)[1]

        # Parse the output of cpplint into standard return values
        for line in output.split('\n')[:-1]:
            words = line.split()
            if len(words) == 0 or words[0].count(':') != 2:
                continue
            filename, lineno = words[0].split(':')[:2]
            description = ' '.join(words[1:-2])
            tag = words[-2]
            priority = words[-1]

            messages.append(Message(filename, int(lineno), None, '%s %s %s' % (
                priority, tag, description)))
    return messages

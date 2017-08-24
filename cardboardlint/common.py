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
"""Collection of classes and methods shared between different linters."""
from __future__ import print_function

from fnmatch import fnmatch
import subprocess


__all__ = ['Message', 'run_command', 'filter_filenames', 'filter_selection', 'tag']


class Message(object):
    """Error message and meta information.

    This class contains all the machinery that the trapdoor driver uses to check for new messages.
    When a context is available, it is used to compare two messages instead of line numbers. If not,
    the line numbers are used. Line numbers are a relatively poor descriptor for assessing if a
    message is new. For example, lines may have been inserted or removed, which changes the line
    numbers without actually changing any of the code.
    """

    def __init__(self, filename, lineno, charno, text, context=None):
        """Initialize a message.

        Parameters
        ----------
        filename : str
            The filename from which the message is reported.
        lineno : int (or None)
            The line number at which the error/problem is reported.
            None if no error/problem is reported.
        charno : int (or None)
            The character position at which the error/problem is reported.
            None if no error/problem is reported.
        text : str
            A description of the error/problem.
        context : str
            A string that (almost) uniquely identifies the location of the error without using line
            numbers.
        """
        if lineno is not None and not isinstance(lineno, int):
            raise TypeError('`lineno` must be an integer or None')
        if charno is not None and not isinstance(charno, int):
            raise TypeError('`charno` must be an integer or None')
        self.filename = filename
        self.lineno = lineno
        self.charno = charno
        self.text = text
        self.context = context

    def __lt__(self, other):
        """Test if one Message is less than another."""
        if self.__class__ != other.__class__:
            return self < other
        tup_self = (self.filename, self.lineno, self.charno, self.text, self.context)
        tup_other = (other.filename, other.lineno, other.charno, other.text, other.context)
        return tup_self < tup_other

    def __str__(self):
        """Return a nicely formatted string representation of the message."""
        # Fix the location string
        if self.filename is None:
            location = '(nofile)            '
        else:
            location = str(self.filename)
            location += '{:>6}'.format('' if self.lineno is None else self.lineno)
            location += '{:>6}'.format('' if self.charno is None else self.charno)
        return '{0:>70}   {1}'.format(location, self.text)

    def indiff(self, files_lines):
        """Test if Message occurs in git diff results by checking the line numbers.

        Parameters
        ----------
        files_lines : dict
            Dictionary of filename to the set of line numbers (that have been modified)
            Result of git diff from run_diff function. The set of line numbers may also
            be None, indicating that all lines should be considered in that file.
        """
        if self.filename in files_lines:
            line_numbers = files_lines[self.filename]
            return line_numbers is None or self.lineno is None or self.lineno in line_numbers
        else:
            return False


def run_command(command, verbose=True, cwd=None, has_failed=None):
    """Run command as subprocess with default settings suitable for trapdoor scripts.

    Parameters
    ----------
    command : list of str
        The command argument to be passed to Popen.
    verbose : bool
        When set to False, the command will not be printed on screen.
    cwd : str
        The working directory where the command is executed.
    has_failed : function(returncode, stdout, stderr)
        A function that determines if the subprocess has failed. The default
        behavior is to check for a non-zero return code.

    Returns
    -------
    output : (str, str)
        if Sucessful, the output collected from stdout and stderr are returned.

    Raises
    ------
    In case the subprocess returns a non-zero exit code, the stdout and stderr are printed
    on screen and RuntimeError is raised.
    """
    # Functions to detect failure
    def default_has_failed(returncode, _stdout, _stderr):
        """Default function to detect failed subprocess."""
        return returncode != 0
    if has_failed is None:
        has_failed = default_has_failed

    if verbose:
        print('RUNNING            : {0}'.format(' '.join(command)))
    proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd)
    stdout, stderr = proc.communicate()
    if has_failed(proc.returncode, stdout, stderr):
        print('STDOUT')
        print('------')
        print(stdout.decode('utf-8'))
        print('STDERR')
        print('------')
        print(stderr.decode('utf-8'))
        raise RuntimeError('Subprocess returned non-zero exit status {0}'.format(proc.returncode))
    else:
        return stdout.decode('utf-8'), stderr.decode('utf-8')


def filter_filenames(filenames, include, exclude):
    """Filter a list of filenames using include and exclude rules.

    First each filename is checked against the include rules. If matching an include rule,
    any exclude rule can still prevent the inclusion of that file.

    Parameters
    ----------
    filenames : list
        The list of filenames
    include : list
        A list of fnmatch patterns to include.
    exclude : list
        A list of fnmatch patterns to exclude.

    Returns
    -------
    filtered_filenames: list
        The list of filenames that pass the filters.
    """
    result = []
    for filename in filenames:
        accept = False
        for pattern in include:
            if fnmatch(filename, pattern):
                accept = True
                break
        if accept:
            for pattern in exclude:
                if fnmatch(filename, pattern):
                    accept = False
                    break
        if accept:
            result.append(filename)
    return result


def get_offset_step(suffix):
    """Return offset and step for a given selection suffix, e.g. '1/3' becomes (0, 3)"""
    if suffix == '':
        return 0, 1
    if suffix.count('/') != 1:
        raise ValueError('Could not parse selection argument suffix: "{}". It should '
                         'contain only one /.'.format(suffix))
    offset, step = suffix.split('/')
    step = int(step)
    offset = int(offset)
    if offset < 1 or offset > step:
        raise ValueError(('The first integer in the suffix {} should be in the range '
                          '[1, {}].').format(suffix, step))
    return offset - 1, step


def filter_selection(configs, selection):
    """Select some linter configs to be executed, based on the selection CLI argument.

    Parameters
    ----------
    configs : list
        A list of (linter_name, linter, linter_config) items.
    selection : str
        The argument given to the --selection command-line option.

    Returns
    -------
    filtered_configs : list
        A reduced list of items from configs.
    """
    if selection is None or selection == '' or selection == 'all':
        return configs
    elif selection.startswith('all'):
        offset, step = get_offset_step(selection[3:])
        return configs[offset::step]
    elif selection.startswith('static'):
        offset, step = get_offset_step(selection[6:])
        return [config for config in configs if config[1].static][offset::step]
    elif selection.startswith('dynamic'):
        offset, step = get_offset_step(selection[7:])
        return [config for config in configs if not config[1].static][offset::step]
    else:
        return [config for config in configs if config[0] in selection]


def tag(dynamic=None, static=None, python=False, cpp=False):
    """Decorate linter with tags."""
    if dynamic is None:
        if static is None:
            static = True
            dynamic = False
        else:
            dynamic = not static
    else:
        if static is None:
            static = not dynamic
        else:
            raise ValueError('You cannot set both static and dynamic, seriously!')
    def decorator(linter):
        """Assigns tags to a linter."""
        linter.static = not dynamic
        linter.dynamic = dynamic
        linter.python = python
        linter.cpp = cpp
        return linter
    return decorator

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


__all__ = ['Message', 'run_command', 'matches_filefilter', 'filter_configs', 'flag']


class Message(object):
    """Error message and meta information."""

    def __init__(self, filename, lineno, charno, text):
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

        """
        if lineno is not None and not isinstance(lineno, int):
            raise TypeError('`lineno` must be an integer or None')
        if charno is not None and not isinstance(charno, int):
            raise TypeError('`charno` must be an integer or None')
        self.filename = filename
        self.lineno = lineno
        self.charno = charno
        self.text = text

    def __lt__(self, other):
        """Test if one Message is less than another."""
        if self.__class__ != other.__class__:
            return self < other
        tup_self = (self.filename, self.lineno, self.charno, self.text)
        tup_other = (other.filename, other.lineno, other.charno, other.text)
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
        """Detect failed subprocess, default implementation."""
        return returncode != 0
    if has_failed is None:
        has_failed = default_has_failed

    if verbose:
        print('RUNNING            : {0}'.format(' '.join(command)))
    proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd)
    stdout, stderr = proc.communicate()
    if has_failed(proc.returncode, stdout, stderr):
        print('RETURN CODE: {}'.format(proc.returncode))
        print('STDOUT')
        print('------')
        print(stdout.decode('utf-8'))
        print('STDERR')
        print('------')
        print(stderr.decode('utf-8'))
        raise RuntimeError('Subprocess has failed.')
    else:
        return stdout.decode('utf-8'), stderr.decode('utf-8')


def matches_filefilter(filename, rules):
    """Test a filename against a list of filter rules.

    Parameters
    ----------
    filename : str
        A filename to be tested.
    rules : list
        A list of strings, starting with - (exclude) or + (include), followed by a glob
        pattern. Each file is tested against the rules in order. The first matching rule
        is applied. If no rules match, the file is excluded.

    Returns
    -------
    accepted: boolean
        True if the file should be included.
    """
    # Check format of the rules
    for rule in rules:
        if rule[0] not in '+-':
            raise ValueError('Unexpected first character in filename filter rule: {}'.format(
                rule[0]))

    for rule in rules:
        pattern = rule[1:].strip()
        if fnmatch(filename, pattern):
            return rule[0] == '+'


def get_offset_step(suffix):
    """Return offset and step for a given selection suffix, e.g. '1/3' becomes (0, 3)."""
    if suffix == '' or suffix is None:
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


def filter_configs(configs, selection, boolexpr, part):
    """Select some linter configs to be executed, based on the selection CLI argument.

    Parameters
    ----------
    configs : list
        A list of (linter_name, linter, linter_config) items.
    selection : list
        A list of linter names to be selected. All other linters will be omitted from the
        returned list of configs.
    boolexpr : str
        A boolean expression in terms of flags set on the linters. If it evaluates to
        False, the linter is omitted as well.
    part : str
        A string of the form N/M, to run only a part of the linters retained by the
        arguments above.

    Returns
    -------
    filtered_configs : list
        A reduced list of items from configs.

    """
    # Pass 1: by linter name (selection list)
    if not (selection is None or selection == []):
        configs = [config for config in configs if config[0] in selection]
    # Pass 2: boolean expression
    if not (boolexpr is None or boolexpr == ''):
        oldconfigs = configs
        configs = []
        for config in oldconfigs:
            namespace = config[1].flags.copy()
            namespace['name'] = config[0]
            if eval(boolexpr, namespace):  # pylint: disable=eval-used
                configs.append(config)
    # Pass 3: part N/M
    offset, step = get_offset_step(part)
    configs = configs[offset::step]
    return configs


def flag(dynamic=None, static=None, python=False, cpp=False):
    """Decorate linter with flags."""
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
        """Assign flags to a linter."""
        linter.flags = {'static': static, 'dynamic': dynamic, 'python': python, 'cpp': cpp}
        return linter

    return decorator

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
"""Utilities used by various parts of cardboardlint."""

from fnmatch import fnmatch
import subprocess


__all__ = ['run_command', 'matches_filefilter']


def run_command(command, verbose=True, cwd=None, has_failed=None, stdin=''):
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
    stdin : str
        Standard input to be provided to the script.

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
    proc = subprocess.Popen(
        command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, cwd=cwd)
    stdout, stderr = proc.communicate(stdin.encode('utf-8'))
    stdout = stdout.decode('utf-8')
    stderr = stderr.decode('utf-8')
    if has_failed(proc.returncode, stdout, stderr):
        print('RETURN CODE: {}'.format(proc.returncode))
        print('STDOUT')
        print('------')
        print(stdout)
        print('STDERR')
        print('------')
        print(stderr)
        raise RuntimeError('Subprocess has failed.')
    return stdout, stderr


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
    return False

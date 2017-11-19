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

import os
import re
from fnmatch import fnmatch
import subprocess


__all__ = ['Message', 'run_command', 'matches_filefilter', 'filter_configs', 'Linter',
           'derive_flags', 'apply_config_defaults']


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
        if not (lineno is None or (isinstance(lineno, int) and lineno > 0)):
            raise TypeError('`lineno` must be a positive integer or None')
        if not (charno is None or (isinstance(charno, int) and charno > 0)):
            raise TypeError('`charno` must be a positive integer or None')
        self.filename = filename
        self.lineno = lineno
        self.charno = charno
        self.text = text

    def __lt__(self, other):
        """Test if one Message is less than another."""
        if self.__class__ != other.__class__:
            raise TypeError('A Message instance can only be compared to another Message instance.')
        tup_self = (self.filename or '', self.lineno or 0, self.charno or 0, self.text)
        tup_other = (other.filename or '', other.lineno or 0, other.charno or 0, other.text)
        return tup_self < tup_other

    def format(self, color=True):
        """Return a nicely formatted string representation of the message."""
        if color:
            purple, red, endcolor, bold = '\033[35m', '\033[31m', '\033[0m', '\033[1m'
        else:
            purple, red, endcolor, bold = ['']*4
        # Fix the location string
        if self.filename is None:
            location = bold + '(nofile)' + endcolor
        else:
            linechar = '{}:{}'.format(
                '-' if self.lineno is None else self.lineno,
                '-' if self.charno is None else self.charno,
            )
            location = '{}{:9s}{} {}{}{}'.format(
                bold + red, linechar, endcolor, purple, str(self.filename), endcolor)
        # Return string with location and text
        return '{}  {}'.format(location, self.text)

    def __str__(self):
        """Return a human-readable string representation."""
        return self.format(color=False)

    def indiff(self, files_lines):
        """Test if Message occurs in git diff results by checking the line numbers.

        Parameters
        ----------
        files_lines : dict
            Dictionary of filename to the set of line numbers (that have been modified).
            Result of git diff from run_diff function. The set of line numbers may also
            be None, indicating that all lines should be considered in that file.

        """
        if self.filename in files_lines:
            line_numbers = files_lines[self.filename]
            return line_numbers is None or self.lineno is None or self.lineno in line_numbers
        else:
            return False


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
    else:
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

    Raises
    ------
    ValueError
        If first character of the pattern in `rules` is not '+' or '-'.
        If there is a double backslash in a pattern.

    """
    re_dir = re.compile(r'(?<!\\)' + os.sep)
    filename_split = re_dir.split(filename)
    for rule in rules:
        pattern_split = re_dir.split(rule[1:].strip())

        # Check format of the rules
        if rule[0] not in '+-':
            raise ValueError('Unexpected first character in filename filter rule: {}'.format(
                rule[0]))
        elif '\\' in rule[1:]:
            raise ValueError('Cannot have double backslash in the pattern.')
        elif len(pattern_split) > len(filename_split):
            continue

        # apply pattern
        if all(fnmatch(name, pattern)
               for name, pattern in zip(filename_split[::-1], pattern_split[::-1])):
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
        A list of (linter, linter_config) items.
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
        configs = [config for config in configs if config[0].name in selection]
    # Pass 2: boolean expression
    if not (boolexpr is None or boolexpr == ''):
        oldconfigs = configs
        configs = []
        for config in oldconfigs:
            namespace = config[0].flags.copy()
            namespace['name'] = config[0].name
            if eval(boolexpr, namespace):  # pylint: disable=eval-used
                configs.append(config)
    # Pass 3: part N/M
    offset, step = get_offset_step(part)
    configs = configs[offset::step]
    return configs


def parse_diff(diff_output):
    """Parse the output of a unified diff and return the files with lines that are new.

    Parameters
    ----------
    diff_output : str
        The standard output of the diff command

    Returns
    -------
    files_lines : dict
        A dictionary with (filename, lines) items, where lines is a set of line numbers.

    """
    # parse git diff output
    current_filename = None
    files_lines = {}
    for line in diff_output.splitlines():
        if line.startswith('+++ '):
            if line.startswith('+++ b/'):
                current_filename = line[6:]
            else:
                current_filename = None
        elif line.startswith('@@ ') and current_filename is not None:
            added_str = line.split()[2]
            # multiple lines added/modified
            if added_str.count(',') == 1:
                offset, nlines = added_str.split(',')
                line_numbers = set(range(int(offset), int(offset) + int(nlines)))
            # single line added/modified
            else:
                offset = int(added_str)
                line_numbers = set([offset])
            # store line numbers
            files_lines.setdefault(current_filename, set()).update(line_numbers)
    return files_lines


class Linter(object):
    """Run linter function with appropriate argument and keep track of meta info."""

    def __init__(self, name, run, default_config, style='static', language='generic'):
        """Initialize a Linter intsance.

        Parameters
        ----------
        name : str
            A short name for the linter.
        run : function
            A function taking two arguments: config (dict) and a list of filenames.
        default_config : dict
            The default configuration. All possible keys must be present.
        style : str
            "static" or "dynamic"
        language : str
            The file format or language the linter is designed for. Use "generic" if any
            text file can be linted.

        """
        self.name = name
        self.run = run
        self.default_config = default_config
        self.style = style
        self.language = language
        self.flags = derive_flags(style, language)

    def __call__(self, config, files_lines):
        """Run the linter.

        Parameters
        ----------
        config : dict
            Cofiguration of the linter, loaded from .cardboardlint.yml
        files_lines : dict
            Dictionary of filename to the set of line numbers (that have been modified).

        Returns
        -------
        messages : list
            A list of Message instances.

        """
        config = apply_config_defaults(self.name, config, self.default_config)

        # Get the relevant filenames
        filenames = [filename for filename in files_lines
                     if matches_filefilter(filename, config['filefilter'])]

        # Call the linter and return messages
        return self.run(config, filenames)


def derive_flags(style, language):
    """Create a dictionary of boolean flags."""
    valid_styles = ['static', 'dynamic']
    if style not in valid_styles:
        raise ValueError('Linter style should be one of {}'.format(valid_styles))
    valid_languages = ['generic', 'python', 'cpp', 'yaml']
    if language not in valid_languages:
        raise ValueError('Linter language should be one of {}'.format(valid_languages))
    flags = {}
    for name in valid_styles:
        flags[name] = (name == style)
    for name in valid_languages:
        flags[name] = (name == language)
    return flags


def apply_config_defaults(linter_name, config, default_config):
    """Add defaults to a config and check for unknown config settings.

    Parameters
    ----------
    linter_name : str
        The name of the linter
    config : dict
        A dictionary with a linter config loaded from the YAML file.
    default_config : dict
        A dictionary with the default configuration, which must contain all keys.

    Returns
    -------
    merged_config : dict
        The config with defaults added.

    """
    # Check for unknown config keys
    for key in config:
        if key not in default_config:
            raise ValueError('Unknown config key for linter {}: {}'.format(linter_name, key))
    # Fill in the default values
    merged_config = default_config.copy()
    merged_config.update(config)
    return merged_config

#!/usr/bin/env python
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
"""Cardboard linter driver script. See README.rst for details."""

from __future__ import print_function

import argparse
import sys

import yaml

from .common import run_command, matches_filefilter, filter_configs, parse_diff
from .linter_cppcheck import linter_cppcheck
from .linter_cpplint import linter_cpplint
from .linter_doxygen import linter_doxygen
from .linter_flake8 import linter_flake8
from .linter_header import linter_header
from .linter_import import linter_import
from .linter_namespace import linter_namespace
from .linter_pylint import linter_pylint
from .linter_pycodestyle import linter_pycodestyle
from .linter_pydocstyle import linter_pydocstyle
from .linter_whitespace import linter_whitespace
from .linter_yamllint import linter_yamllint


__all__ = ['main']


LINTERS = dict((linter.name, linter) for linter in [
    linter_cppcheck,
    linter_cpplint,
    linter_doxygen,
    linter_flake8,
    linter_header,
    linter_import,
    linter_namespace,
    linter_pylint,
    linter_pycodestyle,
    linter_pydocstyle,
    linter_whitespace,
    linter_yamllint,
])


def main():
    """Run selected liners and report."""
    # Get arguments.
    args = parse_args()

    # Load lint configuration for module.
    prefilter, configs = load_config('.cardboardlint.yml')

    # Process git diff and select only those files that match the prefilter.
    files_lines = {
        filename: linenumbers for filename, linenumbers
        in run_diff(args.refspec).items()
        if matches_filefilter(filename, prefilter)}

    # Select specific linter if desired.
    configs = filter_configs(configs, args.selection, args.boolexpr, args.part)

    returncode = 0
    for linter, linter_config in configs:
        print('~'*80)
        print('### {:^72} ###'.format(linter.name))
        print('~'*80)
        messages = [message for message
                    in linter(linter_config, files_lines)
                    if message.indiff(files_lines)]
        messages.sort()
        if len(messages) > 0:
            print()
            returncode = -1
            for message in messages:
                print(message.format())
        print()
    sys.exit(returncode)


def parse_args():
    """Parse the arguments given to the script."""
    parser = argparse.ArgumentParser(prog='cardboardlint')
    parser.add_argument(
        '-r', '--refspec', dest='refspec', nargs='?', default=None,
        help='The parent commit used to compute the diff. If given, only the files that '
             'have been changed will be compared. Otherwise, all files are compared.')
    parser.add_argument(
        '-f', '--filter', default='True', dest='boolexpr',
        help='A valid boolean Python expression, which may use the names static, '
             'dynamic, python or cpp. These are flags defined for every linter, '
             'which can be True or False. A static linter requires none of the build '
             'steps, otherwise it is dynamic.')
    parser.add_argument(
        '-p', '--part', default='',
        help='Specify a subset of the tests to be executed in the form N/M where N and M '
             'are integers. This means that the tests are divided in M groups of which '
             'the Nth is selected, with N going from 1 to N (inclusive).')
    parser.add_argument(
        dest='selection', nargs='*', default=None,
        help='Run just the given linters. List the names to be considered before '
             'applying filters. When none given, all configured linters are included.')
    return parser.parse_args()


def run_diff(refspec_parent):
    """Run git diff with respect to current branch.

    Parameters
    ----------
    refspec_parent : str
        Reference to the parent branch

    Returns
    -------
    files_lines : dict
        Dictionary with (filename,  line_numbers) to represent all changed lines in a way
        that allows efficient testing in the `indiff` method of the Message class. When
        line_numbers is None, it means that all lines should be considered for testing.

    """
    if refspec_parent is not None:
        # The option --relative is used to limit the output of git diff to the current
        # directory, to facilitate test runs in subdirectories.
        # -U0: generate 0 lines of context (i.e. only the lines that differ)
        command = ['git', 'diff', '-U0', refspec_parent, '--relative']
        diff_output = run_command(command, encoding=None)[0]
        files_lines = parse_diff(diff_output)
    else:
        # Just get the current list of files in the repo, including
        # untracked files, and include all lines
        command = ['git', 'ls-files', '--exclude-standard']
        ls_output = run_command(command)[0]
        files_lines = {filename: None for filename in ls_output.splitlines()}
        command = ['git', 'ls-files', '--others', '--exclude-standard']
        ls_output = run_command(command)[0]
        files_lines.update({filename: None for filename in ls_output.splitlines()})
    return files_lines


def load_config(config_file):
    """Return dictionary that corresponds to the given yaml file.

    Parameters
    ----------
    config_file : str
        Name of the configuration file

    Returns
    -------
    configs : list
        A list of (linter_name, linter, linter_config) tuples.

    """
    with open(config_file, 'r') as f:
        raw_config = yaml.safe_load(f)

    prefilter = raw_config.get('pre_filefilter', ['+ *'])

    configs = []
    for mapping in raw_config['linters']:
        if len(mapping) != 1:
            raise IOError('Every item in the linter section in .cardboardlint.yml should '
                          'only specify one linter. You probably have to add a dash in '
                          'front of a linter name, e.g. `- import` instead of `import`.')
        linter_name, linter_config = mapping.popitem()
        linter = LINTERS[linter_name]
        if linter_config is None:
            linter_config = {}
        configs.append((linter, linter_config))
    return prefilter, configs


if __name__ == '__main__':
    main()

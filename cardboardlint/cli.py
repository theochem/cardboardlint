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
"""Implementation of the cardboardlint command-line script."""


import argparse
from importlib import import_module
import os
from pkgutil import iter_modules
import sys
from typing import Tuple, List

import yaml

from .diff import parse_unified_diff, extract_files_lines
from .linter import Linter
from .report import Report
from .utils import run_command, matches_filefilter


__all__ = ['main', 'load_config', 'run_diff', 'filter_configs']


def main():
    """Run selected linters and report."""
    # Get arguments.
    args = parse_args()

    # Load lint configuration for module.
    prefilter, configs = load_config('.cardboardlint.yml', fixers_only=args.fix)

    # Process git diff and select only those files that match the prefilter.
    files_lines = {
        filename: linenumbers for filename, linenumbers
        in run_diff(args.refspec).items()
        if matches_filefilter(filename, prefilter)}

    # Select specific linter if desired.
    configs = filter_configs(configs, args.selection, args.boolexpr, args.part)

    returncode = 0
    for linter, linter_config in configs:
        report = Report(linter.name, files_lines)
        report.show_header()
        linter(linter_config, report, args.numproc, args.fix)
        if report.show_messages():
            returncode = -1
    sys.exit(returncode)


def parse_args():
    """Parse the arguments given to the script."""
    def parse_numcpu(string):
        if string == 'auto':
            if hasattr(os, 'sched_getaffinity'):
                # Keep pylint happy on OSX.
                # pylint: disable=no-member
                return len(os.sched_getaffinity(0))
            return os.cpu_count()
        return int(string)

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
        '-n', '--numproc', default=1, type=parse_numcpu,
        help='The number of cores to use. When auto is given, the number of available '
             'cores is determined with os.cpu_count(). This option is just passed on '
             'to linters that support it. Cardboardlint still runs all linters serially.')
    parser.add_argument(
        '-F', '--fix', default=False, action='store_true',
        help='Fix problems reported by linters. This restricts the selection of linters '
             'to just those that can fix problems. Messages are only printed for '
             'problems that could be fixed.')
    parser.add_argument(
        dest='selection', nargs='*', default=None,
        help='Run just the given linters. List the names to be considered before '
             'applying filters. When none given, all configured linters are included.')
    return parser.parse_args()


def _find_linters():
    """Return all linters found with pkgutil and importlib."""
    result = {}
    for module_info in iter_modules(import_module('cardboardlint').__path__):
        if not module_info.ispkg and module_info.name.startswith('linter_'):
            linter_module = import_module('cardboardlint.' + module_info.name)
            linter = getattr(linter_module, 'LINTER', None)
            if linter is not None:
                result[linter.name] = linter
    return result


LINTERS = _find_linters()


def load_config(config_file: str, fixers_only: bool = False) \
        -> Tuple[List[str], List[Tuple[Linter, dict]]]:
    """Return dictionary that corresponds to the given yaml file.

    Parameters
    ----------
    config_file
        Name of the configuration file
    fixers_only
        When True, only configs for linters with fixers are loaded.

    Returns
    -------
    prefilter
        A list of prefilter strings.
    configs
        A list of (linter, linter_config) tuples.

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
        linter = LINTERS.get(linter_name)
        if linter is None:
            raise ValueError("Unknown linter: {}".format(linter_name))
        if fixers_only and not linter.can_fix:
            continue
        if linter_config is None:
            linter_config = {}
        configs.append((linter, linter_config))
    return prefilter, configs


def run_diff(refspec_parent):
    """Run git diff with respect to current branch.

    Parameters
    ----------
    refspec_parent : str
        Reference to the parent branch

    Returns
    -------
    files_lines : dict
        Dictionary with (filename, line_numbers) to represent all changed lines
        in a way that allows efficient testing if a message should be reported.
        When line_numbers is None, it means that all lines should be considered
        for testing.

    """
    if refspec_parent is not None:
        # The option --relative is used to limit the output of git diff to the current
        # directory, to facilitate test runs in subdirectories.
        # -U0: generate 0 lines of context (i.e. only the lines that differ)
        command = ['git', 'diff', '-U0', refspec_parent, '--relative']
        # git diff should not print out binary data by default
        diff_output = run_command(command)[0]
        patch = parse_unified_diff(diff_output, 'a/', 'b/')
        files_lines = extract_files_lines(patch)
    else:
        # Just get the current list of files in the repo, including
        # untracked files, and include all lines
        command = ['git', 'ls-files', '--exclude-standard']
        ls_output = run_command(command)[0]
        files_lines = {filename: None for filename in ls_output.splitlines()}
        command = ['git', 'ls-files', '--others', '--exclude-standard']
        ls_output = run_command(command)[0]
        files_lines.update({filename: None for filename in ls_output.splitlines()})
    print('SELECTED FILES     :')
    for filename, lines in sorted(files_lines.items()):
        if lines is None:
            print('    (all) {}'.format(filename))
        else:
            print('  {:8d} {}'.format(len(lines), filename))
    print()
    return files_lines


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

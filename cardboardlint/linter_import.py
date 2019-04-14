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
"""Linter for import conventions.

This script counts the number of bad imports. The following is not allowed in a package:

* Importing from its own package as follows:

  .. code-block:: python

        from package import foo
  This is useful for packages where everything is implemented in submodules
  and __init__.py is only used to provide a namespace of the most common
  names from the submodules.
"""

import codecs

from .linter import Linter
from .report import Report


__all__ = []


DEFAULT_CONFIG = {
    # Filename filter rules
    'filefilter': ['- */test_*.py', '+ *.py', '+ *.pyx'],
    # Names of python packages in the project (no longer searched automatically).
    'packages': [],
}


def lint(config: dict, report: Report, _numproc: int = 1, _fixit: bool = False):
    """Lint import statements.

    Parameters
    ----------
    config
        Dictionary that contains the configuration for the linter.
    report
        Collection of filenames and corresponding messages.
    numproc
        The number of processors to use.
    _fixit
        When True, the linter will try to fix (a part of) the problems in each
        file.

    """
    print('PACKAGES           : {0}'.format(' '.join(config['packages'])))
    print('CHECKING FILES     : {0}'.format(' '.join(report.filenames)))

    # Loop all python and cython files
    if len(config['packages']) > 0:
        for filename in report.filenames:
            try:
                _check_file(filename, config, report)
            except UnicodeDecodeError as err:
                report(filename, None, None, str(err))


def _check_file(filename: str, config: dict, report: Report):
    """Look for bad imports in the given file.

    Parameters
    ----------
    filename
        File to be checked
    config
        Dictionary with configuration of the linters.
    report
        Collection of filenames and corresponding messages.

    """
    with codecs.open(filename, encoding='utf-8') as f:
        for lineno, line in enumerate(f):
            for package in config['packages']:
                # skip version import
                if u'from {0} import'.format(package) in line:
                    text = 'Wrong import from {0}'.format(package)
                    report(filename, lineno+1, None, text)


LINTER = Linter('import', lint, DEFAULT_CONFIG, language='python')

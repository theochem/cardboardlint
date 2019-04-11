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

from .report import Report


__all__ = ['Linter']


class Linter:
    """Run linter function with appropriate argument and keep track of meta info."""

    def __init__(self, name, lint, default_config, style='static',
                 language='generic', can_fix=False):
        """Initialize a Linter intsance.

        Parameters
        ----------
        name : str
            A short name for the linter.
        lint : function
            A function that runs the linter, taking three arguments: config
            (dict), a list of filenames and the number of processors to use.
        default_config : dict
            The default configuration. All possible keys must be present.
        style : str
            "static" or "dynamic"
        language : str
            The file format or language the linter is designed for. Use
            "generic" if any text file can be linted.
        can_fix
            True when linter supports 'fixit' argument.

        """
        self.name = name
        self.lint = lint
        self.default_config = default_config
        self.style = style
        self.language = language
        self.flags = derive_flags(style, language)
        self.can_fix = can_fix

    def __call__(self, config: dict, report: Report, numproc: int = 1, fixit: bool = False):
        """Run the linter.

        Parameters
        ----------
        config
            Dictionary that contains the configuration for the linter.
        report
            Collection of filenames and corresponding messages.
        numproc
            The number of processors to use.
        fixit
            Fix (a part of) the problems. Only fixed problems will be reported.

        Returns
        -------
        messages
            A list of Message instances.

        """
        if fixit and not self.can_fix:
            raise ValueError('Linter {} cannot fix files.'.format(self.name))
        # Complete the config dictionary with default values.
        config = apply_config_defaults(self.name, config, self.default_config)
        # Filter files to be reported on.
        report.filter(config['filefilter'])
        # Call the linter and return messages
        return self.lint(config, report, numproc, fixit)


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

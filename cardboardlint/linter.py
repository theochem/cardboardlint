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

from typing import List, Dict, Set

from .message import Message
from .utils import matches_filefilter


__all__ = ['Linter']


class Linter:
    """Run linter function with appropriate argument and keep track of meta info."""

    def __init__(self, name, lint, default_config, style='static', language='generic'):
        """Initialize a Linter intsance.

        Parameters
        ----------
        name : str
            A short name for the linter.
        lint : function
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
        self.lint = lint
        self.default_config = default_config
        self.style = style
        self.language = language
        self.flags = derive_flags(style, language)

    def __call__(self, config: dict, files_lines: Dict[str, Set[int]], numproc: int = 1) \
            -> List[Message]:
        """Run the linter.

        Parameters
        ----------
        config
            Dictionary that contains the configuration for the linter.
        files_lines
            Dictionary of filename to the set of line numbers (that have been modified).
        numproc
            The number of processors to use.

        Returns
        -------
        messages
            A list of Message instances.

        """
        config = apply_config_defaults(self.name, config, self.default_config)

        # Get the relevant filenames
        filenames = [filename for filename in files_lines
                     if matches_filefilter(filename, config['filefilter'])]

        # Call the linter and return messages
        return self.lint(config, filenames, numproc)


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

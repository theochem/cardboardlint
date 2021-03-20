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
"""Load version info or, when that failed, resort to bogus values."""


__all__ = ["__version__", "DEV_CLASSIFIER"]


try:
    from ._version import __version__, DEV_CLASSIFIER
except ImportError:
    __version__ = '0.0.0.post0'
    DEV_CLASSIFIER = 'Development Status :: 2 - Pre-Alpha'

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
"""Test cardboardlint.linter."""


from pytest import raises

from ..linter import derive_flags, apply_config_defaults


def test_flags():
    flags = derive_flags('static', 'cpp')
    assert flags['static']
    assert not flags['dynamic']
    assert flags['cpp']
    assert not flags['python']

    with raises(ValueError):
        derive_flags('foo', 'cpp')
    with raises(ValueError):
        derive_flags('dynamic', 'bar')


def test_apply_config_defaults():
    config = {'a': 1, 'b': 2}
    default_config = {'a': 0, 'b': -1, 'c': 3}
    assert apply_config_defaults('boo', config, default_config) == {'a': 1, 'b': 2, 'c': 3}
    assert apply_config_defaults('boo', {}, default_config) == {'a': 0, 'b': -1, 'c': 3}
    with raises(ValueError):
        apply_config_defaults('boo', config, {'a': 1})

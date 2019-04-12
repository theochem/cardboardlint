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
"""Test cardboardlint.cli."""


from pytest import raises

from ..cli import get_offset_step, filter_configs
from ..linter_cppcheck import LINTER as linter_cppcheck
from ..linter_pylint import LINTER as linter_pylint
from ..linter_import import LINTER as linter_import


def test_offset_step():
    assert get_offset_step(None) == (0, 1)
    assert get_offset_step('') == (0, 1)
    assert get_offset_step('1/1') == (0, 1)
    assert get_offset_step('1/2') == (0, 2)
    assert get_offset_step('2/2') == (1, 2)
    assert get_offset_step('1/3') == (0, 3)
    assert get_offset_step('2/3') == (1, 3)
    assert get_offset_step('3/3') == (2, 3)

    raises(ValueError, get_offset_step, '5')
    raises(ValueError, get_offset_step, '5/5/6')
    raises(ValueError, get_offset_step, '0/0')
    raises(ValueError, get_offset_step, '1/0')
    raises(ValueError, get_offset_step, '3/2')
    raises(ValueError, get_offset_step, '-1/2')


def test_filter_configs():
    configs = [
        (linter_pylint, {'pylintrc': '1'}),
        (linter_pylint, {'pylintrc': '2'}),
        # The following may be a bad idea. cppcheck combines info from related files
        # when provided. (This is just used here for testing the filter_configs function.)
        (linter_cppcheck, {'include': ['*.h.in']}),
        (linter_cppcheck, {'include': ['*.h']}),
        (linter_cppcheck, {'include': ['*.cpp']}),
        (linter_import, {}),
    ]
    assert filter_configs(configs, None, None, None) == configs
    assert filter_configs(configs, [], '', '') == configs
    assert filter_configs(configs, [], 'True', '') == configs
    assert filter_configs(configs, [], 'False', '') == []
    assert filter_configs(configs, ['cppcheck'], '', '') == \
        [configs[2], configs[3], configs[4]]
    assert filter_configs(configs, ['pylint'], '', '') == [configs[0], configs[1]]
    assert filter_configs(configs, ['pylint', 'import'], '', '') == \
        [configs[0], configs[1], configs[5]]
    assert filter_configs(configs, None, 'static', '') == \
        [configs[2], configs[3], configs[4], configs[5]]
    assert filter_configs(configs, None, 'dynamic', '') == [configs[0], configs[1]]
    assert filter_configs(configs, None, '', '1/2') == [configs[0], configs[2], configs[4]]
    assert filter_configs(configs, None, '', '2/2') == [configs[1], configs[3], configs[5]]
    assert filter_configs(configs, None, '', '1/3') == [configs[0], configs[3]]
    assert filter_configs(configs, None, '', '2/3') == [configs[1], configs[4]]
    assert filter_configs(configs, None, '', '3/3') == [configs[2], configs[5]]
    assert filter_configs(configs, None, 'static', '1/2') == [configs[2], configs[4]]
    assert filter_configs(configs, None, 'static', '2/2') == [configs[3], configs[5]]
    assert filter_configs(configs, None, 'dynamic', '1/2') == [configs[0]]
    assert filter_configs(configs, None, 'dynamic', '2/2') == [configs[1]]
    assert filter_configs(configs, None, 'dynamic', '1/3') == [configs[0]]
    assert filter_configs(configs, None, 'dynamic', '2/3') == [configs[1]]
    assert filter_configs(configs, None, 'dynamic', '3/3') == []
    assert filter_configs(configs, None, 'static and python', '') == [configs[5]]
    assert filter_configs(configs, None, 'static or python', '') == configs
    assert filter_configs(configs, None, 'name == "pylint"', '') == [configs[0], configs[1]]
    assert filter_configs(configs, None, 'name != "cppcheck"', '') == \
        [configs[0], configs[1], configs[5]]

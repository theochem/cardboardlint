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
"""Test some common functions."""


from nose.tools import assert_raises

from cardboardlint.common import get_offset_step, filter_selection, flag
from cardboardlint.linter_cppcheck import linter_cppcheck
from cardboardlint.linter_pylint import linter_pylint
from cardboardlint.linter_import import linter_import


def test_offset_step():
    assert get_offset_step(None) == (0, 1)
    assert get_offset_step('') == (0, 1)
    assert get_offset_step('1/1') == (0, 1)
    assert get_offset_step('1/2') == (0, 2)
    assert get_offset_step('2/2') == (1, 2)
    assert get_offset_step('1/3') == (0, 3)
    assert get_offset_step('2/3') == (1, 3)
    assert get_offset_step('3/3') == (2, 3)

    assert_raises(ValueError, get_offset_step, '5')
    assert_raises(ValueError, get_offset_step, '5/5/6')
    assert_raises(ValueError, get_offset_step, '0/0')
    assert_raises(ValueError, get_offset_step, '1/0')
    assert_raises(ValueError, get_offset_step, '3/2')
    assert_raises(ValueError, get_offset_step, '-1/2')


def test_filter_selection():
    configs = [
        ('pylint', linter_pylint, {'pylintrc': '1'}),
        ('pylint', linter_pylint, {'pylintrc': '2'}),
        # The following may be a bad idea. cppcheck combines info from related files
        # when provided. (This is just used here for testing the filter_selection function.)
        ('cppcheck', linter_cppcheck, {'include': ['*.h.in']}),
        ('cppcheck', linter_cppcheck, {'include': ['*.h']}),
        ('cppcheck', linter_cppcheck, {'include': ['*.cpp']}),
        ('import', linter_import, {}),
    ]
    assert filter_selection(configs, None, None, None) == configs
    assert filter_selection(configs, [], '', '') == configs
    assert filter_selection(configs, [], 'True', '') == configs
    assert filter_selection(configs, [], 'False', '') == []
    assert filter_selection(configs, ['cppcheck'], '', '') == \
        [configs[2], configs[3], configs[4]]
    assert filter_selection(configs, ['pylint'], '', '') == [configs[0], configs[1]]
    assert filter_selection(configs, ['pylint', 'import'], '', '') == \
        [configs[0], configs[1], configs[5]]
    assert filter_selection(configs, None, 'static', '') == \
        [configs[2], configs[3], configs[4], configs[5]]
    assert filter_selection(configs, None, 'dynamic', '') == [configs[0], configs[1]]
    assert filter_selection(configs, None, '', '1/2') == [configs[0], configs[2], configs[4]]
    assert filter_selection(configs, None, '', '2/2') == [configs[1], configs[3], configs[5]]
    assert filter_selection(configs, None, '', '1/3') == [configs[0], configs[3]]
    assert filter_selection(configs, None, '', '2/3') == [configs[1], configs[4]]
    assert filter_selection(configs, None, '', '3/3') == [configs[2], configs[5]]
    assert filter_selection(configs, None, 'static', '1/2') == [configs[2], configs[4]]
    assert filter_selection(configs, None, 'static', '2/2') == [configs[3], configs[5]]
    assert filter_selection(configs, None, 'dynamic', '1/2') == [configs[0]]
    assert filter_selection(configs, None, 'dynamic', '2/2') == [configs[1]]
    assert filter_selection(configs, None, 'dynamic', '1/3') == [configs[0]]
    assert filter_selection(configs, None, 'dynamic', '2/3') == [configs[1]]
    assert filter_selection(configs, None, 'dynamic', '3/3') == []
    assert filter_selection(configs, None, 'static and python', '') == [configs[5]]
    assert filter_selection(configs, None, 'static or python', '') == configs


def test_flags():
    @flag(static=True, python=True)
    def test_foo1():
        pass
    assert test_foo1.flags['static']
    assert not test_foo1.flags['dynamic']
    assert test_foo1.flags['python']
    assert not test_foo1.flags['cpp']

    @flag(static=False, python=True, cpp=True)
    def test_foo2():
        pass
    assert not test_foo2.flags['static']
    assert test_foo2.flags['dynamic']
    assert test_foo2.flags['python']
    assert test_foo2.flags['cpp']

    @flag(dynamic=True)
    def test_foo3():
        pass
    assert not test_foo3.flags['static']
    assert test_foo3.flags['dynamic']
    assert not test_foo3.flags['python']
    assert not test_foo3.flags['cpp']

    @flag(dynamic=False, cpp=True)
    def test_foo4():
        pass
    assert test_foo4.flags['static']
    assert not test_foo4.flags['dynamic']
    assert not test_foo4.flags['python']
    assert test_foo4.flags['cpp']

    with assert_raises(ValueError):
        @flag(dynamic=True, static=True)
        def test_foo5():  # pylint: disable=unused-variable
            pass

    with assert_raises(ValueError):
        @flag(dynamic=True, static=False)
        def test_foo6():  # pylint: disable=unused-variable
            pass

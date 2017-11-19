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


from __future__ import print_function

from nose.tools import assert_raises

from cardboardlint.common import Message, run_command, matches_filefilter, \
    get_offset_step, filter_configs, parse_diff, derive_flags, apply_config_defaults
from cardboardlint.linter_cppcheck import linter_cppcheck
from cardboardlint.linter_pylint import linter_pylint
from cardboardlint.linter_import import linter_import


def test_message():
    # formatting
    msg1 = Message('test.txt', 1, 4, 'error')
    assert msg1.format() == '\x1b[1m\x1b[31m1:4      \x1b[0m \x1b[35mtest.txt\x1b[0m  error'
    assert msg1.format(color=False) == '1:4       test.txt  error'
    assert msg1.format(color=False) == str(msg1)
    msg2 = Message('test.txt', None, 4, 'error')
    assert msg2.format() == '\x1b[1m\x1b[31m-:4      \x1b[0m \x1b[35mtest.txt\x1b[0m  error'
    assert msg2.format(color=False) == '-:4       test.txt  error'
    msg3 = Message('test.txt', 1, None, 'error')
    assert msg3.format() == '\x1b[1m\x1b[31m1:-      \x1b[0m \x1b[35mtest.txt\x1b[0m  error'
    assert msg3.format(color=False) == '1:-       test.txt  error'
    msg4 = Message(None, 1, 3, 'error')
    assert msg4.format() == '\x1b[1m(nofile)\x1b[0m  error'
    assert msg4.format(color=False) == '(nofile)  error'
    # comparison
    assert msg1 > msg3
    assert msg3 > msg2
    assert msg2 > msg4
    with assert_raises(TypeError):
        print(msg1 < 1)
    # sorting
    msgs = sorted([msg1, msg2, msg3, msg4])
    assert msgs == [msg4, msg2, msg3, msg1]
    with assert_raises(TypeError):
        msgs.insert(0, 1)
        msgs.sort()
    # wrong arguments
    with assert_raises(TypeError):
        Message('foo', -1, 4, 'bar')
    with assert_raises(TypeError):
        Message('foo', 4, -1, 'bar')
    # indiff
    assert msg1.indiff({'test.txt': set([1])})
    assert msg1.indiff({'test.txt': None})
    assert not msg1.indiff({'test.txt': set([2])})
    assert msg2.indiff({'test.txt': set([1])})
    assert msg2.indiff({'test.txt': None})
    assert msg2.indiff({'test.txt': set([2])})
    assert not msg2.indiff({'foo.txt': set([2])})


def test_run_command():
    assert run_command(['echo', 'foo']) == (u'foo\n', u'')
    with assert_raises(RuntimeError):
        run_command(['ls', 'asfdsadsafdasdfasd'])


def test_matches_filefilter():
    assert matches_filefilter('a.py', ['+ *'])
    assert matches_filefilter('foo/a.py', ['+ *'])
    assert matches_filefilter('foo/a.py', ['+ foo/*.py'])
    assert matches_filefilter('foo/a.py', ['- */test_*.py', '+ *.py'])
    assert not matches_filefilter('foo/test/test_a.py', ['- */test_*.py', '+ *.py'])
    assert matches_filefilter('scripts/runfoo', ['+ scripts/*'])

    assert matches_filefilter('foo/a.py', ['+ *.py'])
    assert not matches_filefilter('foo/a.py', ['+ bar/*.py'])
    assert not matches_filefilter('a.py', ['+ bar/*.py'])

    assert matches_filefilter('foo\\/a.py', ['+ foo*.py'])
    assert not matches_filefilter(r'foo\\/a.py', ['+ a.py'])
    assert not matches_filefilter(r'foo/\\/a.py', ['+ foo*.py'])
    assert matches_filefilter(r'foo/\\/a.py', ['+ foo/*.py'])

    assert_raises(ValueError, matches_filefilter, 'foo.py', ['b *.py'])
    assert_raises(ValueError, matches_filefilter, 'foo.py', ['bork'])
    assert_raises(ValueError, matches_filefilter, 'foo.py', ['+ \\*py'])


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


DIFFICULT_DIFF = """\
diff --git a/.travis.yml b/.travis.yml
index 951e42a..c6323b4 100644
--- a/.travis.yml
+++ b/.travis.yml
@@ -44,0 +45 @@ cache:
+  pip: true
@@ -46 +46,0 @@ cache:
-    - $HOME/.cache/pip
diff --git a/python-qcgrids/setup.cfg b/python-qcgrids/setup.cfg
deleted file mode 100644
index d25c9ea..0000000
--- a/python-qcgrids/setup.cfg
+++ /dev/null
@@ -1,3 +0,0 @@
-[build_ext]
-include-dirs = ../
-library-dirs = ../debug/qcgrids
index 948bde4..2795244 100644
--- a/python-qcgrids/tools/conda.recipe/meta.yaml
+++ b/python-qcgrids/tools/conda.recipe/meta.yaml
@@ -13 +13,6 @@ build:
-  script: python setup.py install
+  script:
+   - if [[ ${BUILD_TYPE} == "debug" ]]; then
+       python setup.py install --define CYTHON_TRACE_NOGIL;
+     else
+       python setup.py install;
+     fi
"""


def test_parse_diff():
    files_lines = parse_diff(DIFFICULT_DIFF)
    assert files_lines == {
        '.travis.yml': set([45]),
        'python-qcgrids/tools/conda.recipe/meta.yaml': set([13, 14, 15, 16, 17, 18])}


def test_flags():
    flags = derive_flags('static', 'cpp')
    assert flags['static']
    assert not flags['dynamic']
    assert flags['cpp']
    assert not flags['python']

    with assert_raises(ValueError):
        derive_flags('foo', 'cpp')
    with assert_raises(ValueError):
        derive_flags('dynamic', 'bar')


def test_apply_config_defaults():
    config = {'a': 1, 'b': 2}
    default_config = {'a': 0, 'b': -1, 'c': 3}
    assert apply_config_defaults('boo', config, default_config) == {'a': 1, 'b': 2, 'c': 3}
    assert apply_config_defaults('boo', {}, default_config) == {'a': 0, 'b': -1, 'c': 3}
    with assert_raises(ValueError):
        apply_config_defaults('boo', config, {'a': 1})

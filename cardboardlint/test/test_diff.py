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
"""Unit tests for cardboardlint.diff."""


from ..diff import parse_unified_diff, extract_files_lines


DIFF1 = """\
diff --git a/.travis.yml b/.travis.yml
index 951e42a..c6323b4 100644
--- a/.travis.yml
+++ b/.travis.yaml
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


def test_parse_unified_diff1():
    patch = parse_unified_diff(DIFF1, 'a/', 'b/')
    assert len(patch) == 3
    pf0 = patch[0]
    assert len(pf0.hunks) == 2
    assert pf0.source_filename == '.travis.yml'
    assert pf0.target_filename == '.travis.yaml'
    assert pf0.hunks[0].source_start == 43
    assert pf0.hunks[0].add_lines == ['  pip: true']
    assert pf0.hunks[0].del_lines == []
    assert pf0.hunks[1].source_start == 45
    assert pf0.hunks[1].add_lines == []
    assert pf0.hunks[1].del_lines == ['    - $HOME/.cache/pip']
    pf1 = patch[1]
    assert pf1.source_filename == 'python-qcgrids/setup.cfg'
    assert pf1.target_filename is None
    assert len(pf1.hunks) == 1
    assert pf1.hunks[0].source_start == 0
    assert pf1.hunks[0].add_lines == []
    assert pf1.hunks[0].del_lines == ['[build_ext]', 'include-dirs = ../',
                                      'library-dirs = ../debug/qcgrids']
    pf2 = patch[2]
    assert pf2.source_filename == 'python-qcgrids/tools/conda.recipe/meta.yaml'
    assert pf2.target_filename == 'python-qcgrids/tools/conda.recipe/meta.yaml'
    assert len(pf2.hunks) == 1
    assert pf2.hunks[0].source_start == 12
    assert pf2.hunks[0].add_lines == [
        '  script:', '   - if [[ ${BUILD_TYPE} == "debug" ]]; then',
        '       python setup.py install --define CYTHON_TRACE_NOGIL;',
        '     else', '       python setup.py install;', '     fi']
    assert pf2.hunks[0].del_lines == ['  script: python setup.py install']


def test_extract_files_lines1():
    patch = parse_unified_diff(DIFF1, 'a/', 'b/')
    files_lines = extract_files_lines(patch)
    assert files_lines == {
        '.travis.yaml': set([43]),
        'python-qcgrids/tools/conda.recipe/meta.yaml': set([12, 13, 14, 15, 16, 17])}


DIFF2 = '''\
--- original/cardboardlint/linter.py
+++ fixed/cardboardlint/linter.py
@@ -91,10 +91,12 @@
     """Create a dictionary of boolean flags."""
     valid_styles = ['static', 'dynamic']
     if style not in valid_styles:
-        raise ValueError('Linter style should be one of {}'.format(valid_styles))
+        raise ValueError(
+            'Linter style should be one of {}'.format(valid_styles))
     valid_languages = ['generic', 'python', 'cpp', 'yaml']
     if language not in valid_languages:
-        raise ValueError('Linter language should be one of {}'.format(valid_languages))
+        raise ValueError(
+            'Linter language should be one of {}'.format(valid_languages))
     flags = {}
     for name in valid_styles:
         flags[name] = (name == style)
@@ -124,7 +126,8 @@
     # Check for unknown config keys
     for key in config:
         if key not in default_config:
-            raise ValueError('Unknown config key for linter {}: {}'.format(linter_name, key))
+            raise ValueError(
+                'Unknown config key for linter {}: {}'.format(linter_name, key))
     # Fill in the default values
     merged_config = default_config.copy()
     merged_config.update(config)
'''


def test_parse_unified_diff2():
    patch = parse_unified_diff(DIFF2, 'original/', 'fixed/')
    assert len(patch) == 1
    pf0 = patch[0]
    assert pf0.source_filename == 'cardboardlint/linter.py'
    assert pf0.target_filename == 'cardboardlint/linter.py'
    assert len(pf0.hunks) == 3
    assert pf0.hunks[0].source_start == 93
    assert pf0.hunks[0].add_lines == [
        '        raise ValueError(',
        '            \'Linter style should be one of {}\'.format(valid_styles))']
    assert pf0.hunks[0].del_lines == [
        "        raise ValueError('Linter style should be one of {}'.format(valid_styles))"]
    assert pf0.hunks[1].source_start == 96
    assert pf0.hunks[1].add_lines == [
        "        raise ValueError(",
        "            'Linter language should be one of {}'.format(valid_languages))"]
    assert pf0.hunks[1].del_lines == [
        "        raise ValueError('Linter language should be one of {}'"
        ".format(valid_languages))"]
    assert pf0.hunks[2].source_start == 126
    assert pf0.hunks[2].add_lines == [
        "            raise ValueError(",
        "                'Unknown config key for linter {}: {}'.format(linter_name, key))"]
    assert pf0.hunks[2].del_lines == [
        "            raise ValueError('Unknown config key for linter {}: {}'"
        ".format(linter_name, key))"]


DIFF3 = '''\
--- original/poor1.py
+++ fixed/poor1.py
@@ -20,6 +20,8 @@
 # --
 """Examples of poor python style."""
 __all__ = ['sin']
+
+
 def sin(x):
     """Not working."""
     return 0.0
--- original/poor2.py
+++ fixed/poor2.py
@@ -26,7 +26,8 @@
 foo
 sin = math.sin
 foo
-def add(a,b):
+
+def add(a, b):
     \'\'\'Adds stuff.\'\'\'
     return a+b
     print('never executed')
'''


def test_parse_unified_diff3():
    patch = parse_unified_diff(DIFF3, 'original/', 'fixed/')
    assert len(patch) == 2
    pf0 = patch[0]
    assert pf0.source_filename == 'poor1.py'
    pf1 = patch[1]
    assert pf1.source_filename == 'poor2.py'


DIFF4 = '''\
--- poor1.py 2019-04-12 10:14:53.526289 +0000
+++ poor1.py 2019-04-12 10:14:53.746803 +0000
@@ -17,11 +17,11 @@
 #
 # You should have received a copy of the GNU General Public License
 # along with this program; if not, see <http://www.gnu.org/licenses/>
 # --
 """Examples of poor python style."""
-__all__ = ['sin']
+__all__ = ["sin"]
 foo
 foo
 def sin(x):
     """Not working."""
     return 0.0
--- poor2.py 2019-04-12 10:14:53.526289 +0000
+++ poor2.py 2019-04-12 10:14:53.749941 +0000
@@ -20,15 +20,15 @@
 """Examples of poor python style."""
 foo
 from math import sin
 import math
 foo
-__all__ = ['math', 'sin']
+__all__ = ["math", "sin"]
 foo
 sin = math.sin
 foo
 foo
 def add(a, b):
-    \'\'\'Adds stuff.\'\'\'
-    return a+b
-    print('never executed')
+    """Adds stuff."""
+    return a + b
+    print("never executed")
 foo
'''


def test_parse_unified_diff4():
    patch = parse_unified_diff(DIFF4, '', '')
    assert len(patch) == 2
    pf0 = patch[0]
    assert pf0.source_filename == 'poor1.py'
    pf1 = patch[1]
    assert pf1.source_filename == 'poor2.py'
    assert pf1.hunks[0].source_start == 24
    assert pf1.hunks[1].source_start == 30

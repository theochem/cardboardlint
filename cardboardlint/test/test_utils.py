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
"""Test cardboardlint.utils."""


from pytest import raises

from ..utils import run_command, matches_filefilter


def test_run_command():
    assert run_command(['echo', 'foo']) == (u'foo\n', u'')
    with raises(RuntimeError):
        run_command(['ls', 'asfdsadsafdasdfasd'])


def test_matches_filefilter():
    assert matches_filefilter('a.py', ['+ *'])
    assert matches_filefilter('foo/a.py', ['+ *'])
    assert matches_filefilter('foo/a.py', ['+ foo/*.py'])
    assert matches_filefilter('foo/a.py', ['- */test_*.py', '+ *.py'])
    assert not matches_filefilter('foo/test/test_a.py', ['- */test_*.py', '+ *.py'])
    assert matches_filefilter('bin/runfoo', ['+ bin/*'])

    with raises(ValueError):
        matches_filefilter('foo.py', ['b *.py'])
    with raises(ValueError):
        matches_filefilter('foo.py', ['bork'])

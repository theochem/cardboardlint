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
"""Test cardboardlint.message."""


from nose.tools import assert_raises

from ..message import Message


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

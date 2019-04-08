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


__all__ = ['Message']


class Message:
    """Error message and meta information."""

    def __init__(self, filename, lineno, charno, text):
        """Initialize a message.

        Parameters
        ----------
        filename : str
            The filename from which the message is reported.
        lineno : int (or None)
            The line number at which the error/problem is reported.
            None if no error/problem is reported.
        charno : int (or None)
            The character position at which the error/problem is reported.
            None if no error/problem is reported.
        text : str
            A description of the error/problem.

        """
        if not (lineno is None or (isinstance(lineno, int) and lineno > 0)):
            raise TypeError('`lineno` must be a positive integer or None')
        if not (charno is None or (isinstance(charno, int) and charno > 0)):
            raise TypeError('`charno` must be a positive integer or None')
        self.filename = filename
        self.lineno = lineno
        self.charno = charno
        self.text = text

    def __lt__(self, other):
        """Test if one Message is less than another."""
        if self.__class__ != other.__class__:
            raise TypeError('A Message instance can only be compared to another Message instance.')
        tup_self = (self.filename or '', self.lineno or 0, self.charno or 0, self.text)
        tup_other = (other.filename or '', other.lineno or 0, other.charno or 0, other.text)
        return tup_self < tup_other

    def format(self, color=True):
        """Return a nicely formatted string representation of the message."""
        if color:
            purple, red, endcolor, bold = '\033[35m', '\033[31m', '\033[0m', '\033[1m'
        else:
            purple, red, endcolor, bold = ['']*4
        # Fix the location string
        if self.filename is None:
            location = bold + '(nofile)' + endcolor
        else:
            linechar = '{}:{}'.format(
                '-' if self.lineno is None else self.lineno,
                '-' if self.charno is None else self.charno,
            )
            location = '{0}{1:9s}{2} {3}{4}{2}'.format(
                bold + red, linechar, endcolor, purple, str(self.filename))
        # Return string with location and text
        return '{}  {}'.format(location, self.text)

    def __str__(self):
        """Return a human-readable string representation."""
        return self.format(color=False)

    def indiff(self, files_lines):
        """Test if Message occurs in git diff results by checking the line numbers.

        Parameters
        ----------
        files_lines : dict
            Dictionary of filename to the set of line numbers (that have been modified).
            Result of git diff from run_diff function. The set of line numbers may also
            be None, indicating that all lines should be considered in that file.

        """
        if self.filename in files_lines:
            line_numbers = files_lines[self.filename]
            return line_numbers is None or self.lineno is None or self.lineno in line_numbers
        else:
            return False

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


import time

from .utils import matches_filefilter


__all__ = ['Report']


class Report:
    """A collections of filenames (with line numbers( and linter messages."""

    def __init__(self, linter_name: str, files_lines: dict):
        """Initialize a Report object.

        Parameters
        ----------
        linter_name
            The name of the linter to report on.
        files_lines
            Dictionary with (filename, line_numbers) to report on.

        """
        self.linter_name = linter_name
        self.files_lines = files_lines
        self.messages = []
        self._start_time = None

    @property
    def filenames(self):
        """Return the filenames to be linted."""
        return list(self.files_lines.keys())

    def __call__(self, filename: str, lineno: int, charno: int, text: str,
                 nline: int = 1) -> bool:
        """Propose a new error message.

        Parameters
        ----------
        filename
            The filename from which the message is reported.
        lineno
            The first line number at which the error/problem is reported.
            None if no error/problem is reported.
        charno
            The character position at which the error/problem is reported.
            None if no error/problem is reported.
        text
            A description of the error/problem.
        nline
            The number of lines this message applies to.

        Returns
        -------
        accepted
            True if the error message is relevant for changes in the current
            branch.

        """
        if filename in self.files_lines:
            line_numbers = self.files_lines[filename]
            if line_numbers is None or lineno is None or any(
                    iline in line_numbers for iline in range(lineno, lineno + nline)):
                self.messages.append(Message(filename, lineno, charno, text, nline))
                return True
        return False

    def filter_files(self, filefilter):
        """Restrict the filenames to report on by the given file filters."""
        self.files_lines = dict(
            (filename, lines) for filename, lines in self.files_lines.items()
            if matches_filefilter(filename, filefilter))

    def show_header(self):
        """Print a report header."""
        self._start_time = time.time()
        print('~'*80)
        print('### {:^72} ###'.format(self.linter_name))
        print('~'*80)

    def show_messages(self):
        """Print messages for the current linter to stdout."""
        if self.messages:
            self.messages.sort()
            print()
            last = None
            for message in self.messages:
                # Simple code to hide duplicates.
                current = message.format()
                if current != last:
                    print(current)
                last = current
        print()
        print('WALL TIME          : {:.2f} seconds'.format(time.time() - self._start_time))
        print()
        self._start_time = None
        return len(self.messages) > 0


class Message:
    """Error message and meta information."""

    def __init__(self, filename: str, lineno: int, charno: int, text: str, nline: int = 1):
        """Initialize a message.

        Parameters
        ----------
        filename
            The filename from which the message is reported.
        lineno
            The first line number at which the error/problem is reported.
            None if no error/problem is reported.
        charno
            The character position at which the error/problem is reported.
            None if no error/problem is reported.
        text
            A description of the error/problem.
        nline
            The number of lines this message applies to.

        """
        if not (lineno is None or (isinstance(lineno, int) and lineno > 0)):
            raise TypeError('`lineno` must be a positive integer or None')
        if not (charno is None or (isinstance(charno, int) and charno > 0)):
            raise TypeError('`charno` must be a positive integer or None')
        if not (isinstance(nline, int) and nline > 0):
            raise TypeError('`nline` must be a strictly positive integer, got {}.'.format(nline))
        self.filename = filename
        self.lineno = lineno
        self.charno = charno
        self.text = text
        self.nline = nline

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
            linechar = '{}{}:{}'.format(
                '-' if self.lineno is None else self.lineno,
                '..{}'.format(self.lineno + self.nline - 1) if self.nline > 1 else '',
                '-' if self.charno is None else self.charno,
            )
            location = '{0}{1:9s}{2} {3}{4}{2}'.format(
                bold + red, linechar, endcolor, purple, str(self.filename))
        # Return string with location and text
        return '{}  {}'.format(location, self.text)

    def __str__(self):
        """Return a human-readable string representation."""
        return self.format(color=False)

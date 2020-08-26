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
"""Tools for parsing, modifying and applying diffs.

This is a light-weight diff interface. It is similar to Python packages like
unidiff and whatthepatch, but much simpler and starting from different
requirements. In cardboardlint, a minimalistic representation of the diff is
sufficient: no context and fully splitted hunks. This is sufficient for our
needs and can be implemented with much simpler datastructures, which have no
internally redundant information, making it easier to remove or add hunks.
"""

from typing import NamedTuple, List


__all__ = ['Hunk', 'PatchedFile', 'parse_unified_diff', 'extract_files_lines']


class Hunk(NamedTuple):
    """A minimal hunk in a patch.

    Attributes
    ----------
    source_start
        The starting line in the original file to which the patch is applied.
        Zero-based counter.
    del_lines
        The lines to be deleted from the original at source_start.
    add_lines
        The lines to be added to the original at source_start.

    """

    source_start: int
    del_lines: List[str]
    add_lines: List[str]

    @property
    def source_length(self):
        """Return the number of removed lines."""
        return len(self.del_lines)

    @property
    def target_length(self):
        """Return the number of added lines."""
        return len(self.add_lines)


class PatchedFile(NamedTuple):
    """A minimal representation of a single patched file.

    Attributes
    ----------
    source_filename
        The original filename.
    target_filename
        The final filename.
    hunks
        Minimal hunks.

    """

    source_filename: str
    target_filename: str
    hunks: List[Hunk]

    @property
    def source_starts(self):
        """Return positions off all hunks in the original file."""
        return [hunk.source_start for hunk in self.hunks]

    @property
    def source_lengths(self):
        """Return lengths of the removed lines in the hunks."""
        return [hunk.source_length for hunk in self.hunks]

    @property
    def target_starts(self):
        """Return positions off all hunks in the final file."""
        result = []
        offset = 0
        for hunk in self.hunks:
            result.append(hunk.source_start + offset)
            offset += hunk.target_length - hunk.source_length
        return result

    @property
    def target_lengths(self):
        """Return lengths of the added lines in the hunks."""
        return [hunk.target_length for hunk in self.hunks]


def parse_unified_diff(diff_output: str, source_prefix: str,
                       target_prefix: str) -> List[PatchedFile]:
    """Parse the output of a unified diff and return the files with lines that are new.

    Parameters
    ----------
    diff_output
        The standard output of the diff command
    source_prefix
        The prefix directory used for the source files. This is stripped.
    target_prefix
        The prefix directory used for the target files. This is stripped.

    Returns
    -------
    patch
        A list of files with patch data.

    """
    hunks = None
    result = []
    lines = diff_output.splitlines()
    iline = 0
    while iline < len(lines):
        line = lines[iline]
        if line.startswith('--- '):
            source_filename = _parse_diff_filename(line, source_prefix, "Source")
            iline += 1
            hunks = None
        elif line.startswith('+++ '):
            target_filename = _parse_diff_filename(line, target_prefix, "Target")
            iline += 1
            hunks = None
        elif line.startswith('@@ '):
            # Counting from zero
            start = int(line.split()[1][1:].split(',')[0]) - 1
            if hunks is None:
                hunks = []
                result.append(PatchedFile(source_filename, target_filename, hunks))
            iline += 1
        elif line[0] in '+- ':
            assert hunks is not None
            iline = _parse_hunks(iline, start, lines, hunks)
        else:
            iline += 1
    return result


def _parse_diff_filename(line, prefix, label):
    """Parse a unified diff line starting with '--- ' or '+++ '."""
    filename = line.split()[1]
    if filename == '/dev/null':
        filename = None
    else:
        if not filename.startswith(prefix):
            raise ValueError("{} prefix not found: {}".format(label, filename))
        filename = filename[len(prefix):]
    return filename


def _parse_hunks(iline, start, lines, hunks):
    """Parse hunks within one @@ section of a unified diff file."""
    del_lines = []
    add_lines = []
    source_start = None
    while True:
        line = '' if iline == len(lines) else lines[iline]
        if line != "" and line[0] in '+-' and line[:4] not in ['+++ ', '--- ']:
            iline += 1
            if source_start is None:
                source_start = start
            if line[0] == '-':
                start += 1
                del_lines.append(line[1:])
            else:
                add_lines.append(line[1:])
        else:
            if add_lines or del_lines:
                hunks.append(Hunk(source_start, del_lines, add_lines))
                source_start = None
                del_lines = []
                add_lines = []
            if line.startswith(' '):
                start += 1
                iline += 1
            else:
                return iline


def extract_files_lines(patch: List[PatchedFile]) -> dict:
    """Get all target files and corresponding lines that are new from a patch.

    Parameters
    ----------
    patch
        The parsed diff.

    Returns
    -------
    files_lines
        A dictionary whose keys are filenames in and whose values are line
        indexes of new lines.

    """
    result = {}
    for patched_file in patch:
        if patched_file.target_filename is not None:
            lines = set([])
            for target_start, target_length in zip(patched_file.target_starts,
                                                   patched_file.target_lengths):
                lines.update(range(target_start, target_start + target_length))
            result[patched_file.target_filename] = lines
    return result

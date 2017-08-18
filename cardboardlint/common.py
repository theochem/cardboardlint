"""Collection of classes and methods shared between different linters."""
from __future__ import print_function

import subprocess
from fnmatch import fnmatch


__all__ = ['Message', 'run_command', 'filter_filenames']


class Message(object):
    """Error message and meta information.

    This class contains all the machinery that the trapdoor driver uses to check for new messages.
    When a context is available, it is used to compare two messages instead of line numbers. If not,
    the line numbers are used. Line numbers are a relatively poor descriptor for assessing if a
    message is new. For example, lines may have been inserted or removed, which changes the line
    numbers without actually changing any of the code.
    """

    def __init__(self, filename, lineno, charno, text, context=None):
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
        context : str
            A string that (almost) uniquely identifies the location of the error without using line
            numbers.
        """
        if lineno is not None and not isinstance(lineno, int):
            raise TypeError('`lineno` must be an integer or None')
        if charno is not None and not isinstance(charno, int):
            raise TypeError('`charno` must be an integer or None')
        self.filename = filename
        self.lineno = lineno
        self.charno = charno
        self.text = text
        self.context = context

    def __lt__(self, other):
        """Test if one Message is less than another."""
        if self.__class__ != other.__class__:
            return self < other
        tup_self = (self.filename, self.lineno, self.charno, self.text, self.context)
        tup_other = (other.filename, other.lineno, other.charno, other.text, other.context)
        return tup_self < tup_other

    def __str__(self):
        """Return a nicely formatted string representation of the message."""
        # Fix the location string
        if self.filename is None:
            location = '(nofile)            '
        else:
            location = str(self.filename)
            location += '{:>6}'.format('' if self.lineno is None else self.lineno)
            location += '{:>6}'.format('' if self.charno is None else self.charno)
        return '{0:>70}   {1}'.format(location, self.text)

    def indiff(self, files_lines):
        """Test if Message occurs in git diff results by checking the line numbers.

        Parameters
        ----------
        files_lines : dict
            Dictionary of filename to the set of line numbers (that have been modified)
            Result of git diff from run_diff function
        """
        line_numbers = files_lines.get(self.filename)
        return line_numbers is not None and (
            self.lineno in line_numbers or self.lineno is None)


def run_command(command, verbose=True, cwd=None, has_failed=None):
    """Run command as subprocess with default settings suitable for trapdoor scripts.

    Parameters
    ----------
    command : list of str
        The command argument to be passed to Popen.
    verbose : bool
        When set to False, the command will not be printed on screen.
    cwd : str
        The working directory where the command is executed.
    has_failed : function(returncode, stdout, stderr)
        A function that determines if the subprocess has failed. The default
        behavior is to check for a non-zero return code.

    Returns
    -------
    output : (str, str)
        if Sucessful, the output collected from stdout and stderr are returned.

    Raises
    ------
    In case the subprocess returns a non-zero exit code, the stdout and stderr are printed
    on screen and RuntimeError is raised.
    """
    # Functions to detect failure
    def default_has_failed(returncode, _stdout, _stderr):
        """Default function to detect failed subprocess."""
        return returncode != 0
    if has_failed is None:
        has_failed = default_has_failed

    if verbose:
        print('RUNNING            : {0}'.format(' '.join(command)))
    proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd)
    stdout, stderr = proc.communicate()
    if has_failed(proc.returncode, stdout, stderr):
        print('STDOUT')
        print('------')
        print(stdout.decode('utf-8'))
        print('STDERR')
        print('------')
        print(stderr.decode('utf-8'))
        raise RuntimeError('Subprocess returned non-zero exit status {0}'.format(proc.returncode))
    else:
        return stdout.decode('utf-8'), stderr.decode('utf-8')


def filter_filenames(filenames, include, exclude):
    """Filter a list of filenames using include and exclude rules.

    First each filename is checked against the include rules. If matching an include rule,
    any exclude rule can still prevent the inclusion of that file.

    Parameters
    ----------
    filenames : list
        The list of filenames
    include : list
        A list of fnmatch patterns to include.
    exclude : list
        A list of fnmatch patterns to exclude.

    Returns
    -------
    filtered_filenames: list
        The list of filenames that passes the filters.
    """
    result = []
    for filename in filenames:
        accept = False
        for pattern in include:
            if fnmatch(filename, pattern):
                accept = True
                break
        if accept:
            for pattern in exclude:
                if fnmatch(filename, pattern):
                    accept = False
                    break
        if accept:
            result.append(filename)
    return result

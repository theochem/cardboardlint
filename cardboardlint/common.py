"""Collection of classes and methods shared between different linters."""
import os
from fnmatch import fnmatch
import subprocess


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
        # FIXME: is it necessary for these attributes to be private?
        self._filename = filename
        self._lineno = lineno
        self._charno = charno
        self._text = text
        self._context = context

    @property
    def filename(self):
        return self._filename

    @property
    def lineno(self):
        return self._lineno

    @property
    def charno(self):
        return self._charno

    @property
    def text(self):
        return self._text

    @property
    def context(self):
        return self._context

    def __eq__(self, other):
        """Test if two Message's are equal."""
        # First come the usualy things for comparisons...
        if not (self.__class__ == other.__class__
                and self._filename == other._filename
                and self._charno == other._charno
                and self._text == other._text
                and self._context == other._context):
            return False
        # If still equal, then only use line numbers if no context is available.
        elif self._context is None and other._context is None:
            return self._lineno == other._lineno
        else:
            return True

    def __hash__(self):
        """Return a fast hash.

        The hash only includes the lineno if no context is present. If a context is
        present, it is used instead and the line number is not included in the hash. This
        convention is compatible with the code in __eq__.
        """
        if self._context is None:
            return hash((self._filename, self._lineno, self._charno, self._text))
        else:
            return hash((self._filename, self._charno, self._text, self._context))

    def __lt__(self, other):
        """Test if one Message is less than another."""
        if self.__class__ != other.__class__:
            return self < other
        tup_self = (self._filename, self._lineno, self._charno, self._text, self._context)
        tup_other = (other._filename, other._lineno, other._charno, other._text, other._context)
        return tup_self < tup_other

    def add_context(self, context):
        """Return an identical Message with context."""
        if self._context is not None:
            raise ValueError('This message already has context.')
        return Message(self._filename, self._lineno, self._charno, self._text, context)

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
        if files_lines is not None:
            line_numbers = files_lines.get(self._filename)
            return line_numbers is not None and self._lineno in line_numbers
        else:
            return True


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
    def default_has_failed(returncode, stdout, stderr):
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
        print(stdout)
        print('STDERR')
        print('------')
        print(stderr)
        raise RuntimeError('Subprocess returned non-zero exit status {0}'.format(proc.returncode))
    else:
        return stdout, stderr


def get_filenames(directories, include, exclude):
    """Return a list of file names

    Parameters
    ----------
    directories : list of str
        List of directories from which the files will be searched
    include : list of str
        List of regular expressions that the filename must satisfy
    exclude : list of str
        List of regular expressions that the filename must not satisfy

    Returns
    -------
    filenames : list
        List of filenames that satisfies the conditions in the config file
    """
    if not isinstance(directories, (list, tuple)):
        raise TypeError('directories must be given as a list or tuple')
    if not isinstance(include, (list, tuple)):
        raise TypeError('include must be given as a list or tuple')
    if not isinstance(exclude, (list, tuple)):
        raise TypeError('exclude must be given as a list or tuple')

    # Loop over all files in given directories
    result = []
    for directory in directories:
        for dirpath, _, filenames in os.walk(directory):
            # NOTE: replace unix filename pattern matching (fnmatch) with regular expression?
            if any(fnmatch(dirpath, e) for e in exclude):
                continue
            for filename in filenames:
                if not any(fnmatch(filename, i) or fnmatch(dirpath, i) for i in include):
                    continue
                if any(fnmatch(filename, e) for e in exclude):
                    continue

                result.append(os.path.join(dirpath, filename))
    return result

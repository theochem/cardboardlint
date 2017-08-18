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
        if files_lines is not None:
            line_numbers = files_lines.get(self.filename)
            return line_numbers is not None and self.lineno in line_numbers
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
        print(stdout.decode('utf-8'))
        print('STDERR')
        print('------')
        print(stderr.decode('utf-8'))
        raise RuntimeError('Subprocess returned non-zero exit status {0}'.format(proc.returncode))
    else:
        return stdout.decode('utf-8'), stderr.decode('utf-8')


def get_filenames(directories, include, exclude, files_lines=None):
    """Return a list of file names

    Parameters
    ----------
    directories : list of str
        List of directories from which the files will be searched
    include : list of str
        List of regular expressions that the filename must satisfy
    exclude : list of str
        List of regular expressions that the filename must not satisfy
    files_lines : dict
        Dictionary of files and lines that have been changed.
        Instead of searching for all files in the provided directories, only the provided files will
        be searched.
        Default searches through all files in the directories.

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

    # get list of directories and files to loop through
    if files_lines is None:
        dirs_files = ((dirpath, filenames) for directory in directories
                      for dirpath, _, filenames in os.walk(directory))
    else:
        dirs_files = []
        for filename in files_lines:
            dirpath, filenames = os.path.split(filename)
            if any(os.path.abspath(dirpath).startswith(os.path.abspath(directory))
                   for directory in directories):
                dirs_files.append((dirpath, filenames))

    # find files that satisfy the conditions
    for dirpath, filenames in dirs_files:
        # NOTE: replace unix filename pattern matching (fnmatch) with regular expression?
        if any(fnmatch(one_dir, e) for e in exclude for one_dir in dirpath.split(os.sep)):
            continue
        for filename in filenames:
            if any(fnmatch(filename, e) for e in exclude):
                continue
            if not any(fnmatch(filename, i) or
                       any(fnmatch(one_dir, i) for one_dir in dirpath.split(os.sep))
                       for i in include):
                continue

            result.append(os.path.join(dirpath, filename))
    return result

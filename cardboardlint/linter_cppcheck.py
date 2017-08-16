from xml.etree import ElementTree
from cardboardlint.common import run_command, Message


def linter_cppcheck(lintconfig, files_lines):
    """Linter for cppcheck.

    Parameters
    ----------
    config : dict
        Dictionary that contains the configuration for the linter
        Not supported
    files_lines : dict
        Dictionary of filename to the set of line numbers (that have been modified)
        See `run_diff` method in `carboardlint`
    """
    # Get version
    print('USING VERSION      :  {0}'.format(run_command(['cppcheck',
                                                          '--version'], verbose=False)[0].strip()))

    # Get the cpp filenames
    filenames = [filename for filename in files_lines
                 if filename[filename.rfind('.'):] in ['.h', '.h.in', '.cpp', '.c']]

    messages = set()
    if len(filenames) > 0:
        # Call Cppcheck
        command = (['cppcheck'] + filenames +
                   ['-q', '--enable=all', '--language=c++', '--std=c++11', '--xml',
                    '--suppress=missingIncludeSystem', '--suppress=unusedFunction'])
        xml_str = run_command(command)[1]
        etree = ElementTree.fromstring(xml_str)

        # Parse the output of Cppcheck into standard return values
        for error in etree:
            if 'file' not in error.attrib:
                continue
            # key = '{:<15}  {:<40}  {:<30}' % (error.attrib['severity'],
            #                                   error.attrib['file'],
            #                                   error.attrib['id'])
            text = '{} {} {}' % (error.attrib['severity'], error.attrib['id'], error.attrib['msg'])
            messages.add(Message(error.attrib['file'], int(error.attrib['line']), None, text))
    return messages

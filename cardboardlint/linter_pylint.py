from cardboardlint.common import Message, get_filenames, run_command


def linter_pylint(config, files_lines):
    """Linter for checking pylint results.

    Parameters
    ----------
    config : dict
        Dictionary that contains the configuration for the linter
    files_lines : dict
        Dictionary of filename to the set of line numbers (that have been modified).
        See `run_diff` method in `carboardlint`
    """
    # get Pylint version
    command = ['pylint', '--version', '--rcfile={0}'.format(config['default_config_file'])]
    print(run_command(command, verbose=False)[0])
    version_info = ''.join(run_command(command, verbose=False)[0].split('\n')[:2])
    print('USING              : {0}'.format(version_info))

    # Collect python files (pylint ignore is quite bad.. need to ignore manually)
    # i.e. create a list of all the files that will be tested for each rcfile/config file
    output = ''
    # run pylint test using each configuration
    for key, config_file in config.items():
        # NOTE: hopefully other custom configurations do not depend on the order because it might
        #       not be conserved. i.e. each rc file should correspond to a disjoint set of files
        if key == 'default_config_file' or 'config_file' not in key:
            continue

        # collect files
        index = key.split('_')[0]
        file_criteria = {'directories': config.get('{0}_directories'.format(index),
                                                   config['directories']),
                         'include': config.get('{0}_include'.format(index), config['include']),
                         'exclude': config.get('{0}_exclude'.format(index), [])}
        file_criteria['exclude'].extend(config['exclude'])
        files_to_test = get_filenames(files_lines=files_lines, **file_criteria)

        # call Pylint
        if len(files_to_test) == 0:
            continue
        output += run_command(['pylint'] + files_to_test,
                              ['--rcfile={0}'.format(config_file), '-j 2'],
                              has_failed=(lambda returncode, stdout, stderr:
                                          not 0 <= returncode < 32))[0]

        # exclude files that ran in the future
        config['exclude'].extend(files_to_test)

    # call Pylint on all the files that haven't been tested using the default_config_file
    files_to_test = get_filenames(directories=config['directories'], include=config['include'],
                                  exclude=config['exclude'], files_lines=files_lines)
    if len(files_to_test) != 0:
        output += run_command(['pylint'] + files_to_test +
                              ['--rcfile={0}'.format(config['default_config_file']), '-j 2'],
                              has_failed=(lambda returncode, stdout, stderr:
                                          not 0 <= returncode < 32))[0]

    messages = []
    if len(output) == 0:
        print('No files were selected. PyLint will not be run.')
        return messages

    # parse the output of Pylint into standard return values
    lines = output.split('\n')[:-1]
    score = lines[-2].split()[6]
    print('SCORE              : {0}'.format(score))
    for line in lines:
        # skip lines that don't contain error messages
        if '.py:' not in line:
            continue
        if line.startswith('Report'):
            break
        # extract error information
        msg_id, _keyword, location, msg = line.split(' ', 3)
        filename, pos = location.split(':')
        lineno, charno = pos.split(',')
        lineno = int(lineno)
        charno = int(charno)
        if charno == 0:
            charno = None
        messages.append(Message(filename, lineno, charno, '{0} {1}'.format(msg_id, msg)))
    return messages

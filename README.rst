.. image:: https://codecov.io/gh/theochem/cardboardlint/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/theochem/cardboardlint
.. image:: https://travis-ci.org/theochem/cardboardlint.svg?branch=master
    :target: https://travis-ci.org/theochem/cardboardlint


cardboardlint
-------------

Cheap lint solution for PRs.

This is a wrapper for a collection of linters, intended to be used on a project
in a Git repository. Cardboardlint can report only those messages related to
lines that have changed in your development branch, compared to another commit,
e.g. the HEAD of the branch to merge into. This is intended to make life
easier for contributors to a project: in their pull requests, they will only see
linting issues related to the code they have touched. Cardboardlint is a simple
non-hosted and more customizable alternative to commercial services like Hound
CI, Stickler CI, Linthub.io, landscape.io etc.

Cardboardlint can be used as follows:

- Install cardboardlint, which requires python 3.6 or 3.7 and PyYaml. You must
  have Python 3 installed, PyYaml will be installed automatically for you with
  the instructions below.

  .. code:: bash

      # Install cardboardlint with pip. Any of the following that works for you
      # is fine:
      pip install cardboardlint
      pip install cardboardlint --user
      python3 -m pip install cardboardlint
      python3 -m pip install cardboardlint --user
      # Or install cardboardlint with conda:
      conda install theochem::cardboardlint

- Add a ``.cardboardlint.yml`` to the root of your source tree. It should at least contain
  a ``linters`` section with a list of linters, e.g.

  .. code:: yaml

      linters:
      - pylint:
          pylintrc: tools/your_custom_pylintrc
      - cppcheck:
      - import:
      ...

  A list of supported linters is easily deduced from the source code. Just look into
  the ``cardboardlint/linter_*.py`` files. Each of these files has a module docstring with
  some explanations and a DEFAULT_CONFIG dictionary with the available configuration vars.

  You can repeat any linter multiple times with different configuration settings. This can
  be useful, e.g. when unit tests must be linted differently than the rest of the source
  code. This is a simple example where unit tests have a different pylint config:

  .. code:: yaml

      pre_filefilter: ['+ tools/demo/*.py', '- tools/*', '+ *']

      linters:
      - pylint:
          pylintrc: tools/pylintrc
          filefilter: ['- test_*.py', '+ *.py']
          exclude:
      - pylint:
          pylintrc: tools/pylintrc_tests
          filefilter: ['+ test_*.py']
      - import:
      ...


  When cardboardlint starts, it makes a list of files not ignored by
  git in the current repository. These filenames are first filtered by a
  so-called ``pre_filefilter``. Files that pass the ``pre_filefilter`` are then
  tested with linter-specific ``filefilters`` to end up with a list of files to
  be checked by a given linter.

  A ``pre_filefilter`` or ``filefilter`` consists of a list of rules to test if
  a file should be considered for linting or not. Each rule starts with a
  possible outcome, ``+`` (include) or a ``-`` (exclude), followed by a glob
  pattern. At the moment, the pattern ignores the presence of directory
  separators and treats the complete path as a single string on which the
  pattern is tested, using Pythons ``fnmatch`` builtin module. The rules are
  tested in order and when a pattern matches, the corresponding decision is made
  (include and exclude), without considering subsequent rules. When no patterns
  give a match, the file is excluded.

  The following tricks might be useful:

  - If you would like to include files that did not match any pattern, add
    ``'+ *'`` as last pattern, which is often useful for the ``pre_filefilter``.

  - If you would like to include all python files, in all directories, use
    ``'+ *.py'``. The wildcard will also match directories containing the Python
    file. For example it would match ``a/b`` in the path ``a/b.py``.

- Install the linters you intend to run (either locally or in your CI environment). These
  dependencies are not installed automatically because you may not want to use all of
  them.

  Conda packages for all linters supported linters can be found in the conda-forge channel
  on Anaconda: https://anaconda.org/conda-forge. For now, we have only added a
  package for ``cppcheck`` and ``cpplint``. All other linters were already available
  on conda-forge.

- Download and install the latest version from git and run the cardboardlinter.

  - Travis-CI (in ``.travis.yml``). This will only report messages for lines that have
    changed in the PR.

    .. code:: yaml

        install:
        # Install the latest cardboardlinter
        - if [ "$TRAVIS_PULL_REQUEST" != "false" ]; then
            pip install --upgrade git+https://github.com/theochem/cardboardlint.git@master#egg=cardboardlint;
          fi

        script:
        # Run the cardboardlinter, in case of pull requests
        - if [ "$TRAVIS_PULL_REQUEST" != "false" ]; then
            cardboardlinter --refspec $TRAVIS_BRANCH;
          fi

  - Local machine (without venv). This checks all of the code, not just lines that have
    changed.

    .. code:: bash

        pip install --upgrade --user git+https://github.com/theochem/cardboardlint.git@master#egg=cardboardlint
        cardboardlinter

  - One can also use Roberto to drive the entire build+test+package workflow,
    which includes linting with Cardboardlint.
    See https://theochem.github.io/roberto/


change log
----------

- Version 1.0.0 March 27

  First release, mainly in anticipation of API-breaking changes, which will
  result in a major version increase. By making a release, we can handle this
  change in API gracefully. Notable features include:

  - Support for the following linters: cppcheck, ccplint, doxygen, flake8,
    header (internal), import (internal), namespace (internal), pycodestyle,
    pydocstyle, pylint, whitespace (internal), yamllint

  - For all supported linters, the output can be restricted to files and (lines
    in those files) that have changed between two git commits. In pull requests,
    this will then only show errors that are relevant for the code touched in
    the PR. This is intended for making life easy for contributors, i.e. to not
    bother them with linting issues in code they have not touched.

  - Flexible file filtering, essentially a simplified version of rsync's file
    filtering rules.

  - Consistent and colored output for all linters, making it easy to process
    linting issues.

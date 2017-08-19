cardboardlint
-------------

Cheap lint solution for PRs.

This is a wrapper for other linters, which only reports messages related to lines that
have changed compared to some other commit, e.g. the head of the branch being merged into.
It is a simple and more customizable alternative to tools like Hound CI, Stickler CI,
Linthub.io etc.

It can be used as follows:

- Add a ``.cardboardlint.yml`` to the root of your source tree. It should at least contain the
  following:

  .. code:: yaml

      linters:
          - name_of_linter1:
              option_foo: bar
          - name_of_linter2:
          ...

  A list of supported linters is easily deduced from the source code. Just look into
  the ``cardboardlint/linter_*.py`` files. Each of these files has a module docstrong with
  some explanations and a DEFAULT_CONFIG dictionary with the available configuration vars.

  You can repeat any linter multiple times with different configuration settings. This can
  be useful, e.g. when unit tests must be linted differently than the rest of the source
  code.

- Install the linters you intend to run (either locally or in your CI environment). These
  dependencies are not installed automatically because you may not want to use all of them.

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

  - Local machine (without venv)

    .. code:: bash

        pip install --upgrade --user git+https://github.com/theochem/cardboardlint.git@master#egg=cardboardlint
        cardboardlinter

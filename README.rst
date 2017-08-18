cardboardlint
-------------

Cheap lint solution for PRs

This is a wrapper for other linters, which only reports messages related to lines that have changed since some ancestor commit.
It is a simple and more customizable alternative to tools like Hound CI, Stickler CI, Linthub.io etc.

It can be used as follows:

- Add a .cardboardlint.yml to the root of your source tree. It should at least contain the following:

  .. code::

      linters:
          name_of_linter1:
          name_of_linter2:
          ...

- Download and run the linter to your CI tests (or locally)

  .. code::

      pip install pyyaml
      wget https://raw.githubusercontent.com/theochem/cardboardlint/master/scripts/cardboardlint
      chmod +x cardboardlint
      ./cardboardlint

Development
===========

Install requirements. ::

    pipenv install --dev

Then activate the virtual environment created by pipenv. ::

    pipenv shell

Run unittests. ::

    pytest

Build packages. ::

    python setup.py build bdist_wheel

Because of the directory structure defined by ``setuptools``, the ``sshx.py`` cannot be run directly. Generally, we have to run ``python setup.py install`` before we run ``sshx``, which is really inefficient. To solve the problem, I've created an ``run.py`` script. ::

    ./run.py --help

Commit messages must match the `Conventional Commits <https://www.conventionalcommits.org/en/v1.0.0/>`_.


Releasing (Ignore it)
---------------------

It is the maintainer's job to release a new version. Therefore this section is wrote for me.

Before release a new version, maintainer must fully test the code to be released (which usually is the latest master branch) on a production environment. The recommended way is to build an ``bdist_wheel`` and install it on a new docker environment, then test all of the functions.

Version number should follow `Semantic Versioning <https://semver.org/>`_. Currently, I use `bumping <https://github.com/WqyJh/bumping>`_ to calculate the semver from git commit messages.


**Step 1**: calculating the currently version, the output is the version value like ``0.27.1``. ::

    bumping

**Step 2**: checkout a release branch from master branch. ::

    git checkout -b release-<version> master

**Step 3**: bump to new version and commit. ::

    ./bump_version.sh <version>

**Step 4**: generate changelog and commit. ::

    auto-changelog --latest-version <version>
    git add -A
    git commit -m "docs: udpate CHANGELOG.md"

**Step 5**: tag for new version. ::

    git tag <version>

**Step 6**: push release branch. **Note** that the travis-ci would build sshx and upload it to PyPI on tags. ::

    git push origin --tags release-<version>

**Step 7**: open a pull request from release branch to master branch and merge it.

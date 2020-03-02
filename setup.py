import unittest
import setuptools

from pipenv.project import Project
from pipenv.utils import convert_deps_to_pip

from sshx import __version__


pfile = Project(chdir=False).parsed_pipfile
requirements = convert_deps_to_pip(pfile['packages'], r=False)
test_requirements = convert_deps_to_pip(pfile['dev-packages'], r=False)


# entry points
entry_points = {
    'console_scripts': [
        'sshx = sshx.sshx:main'
    ]
}


# test suite
def load_test_suite():
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover('sshx/tests', top_level_dir='./')
    return test_suite


setuptools.setup(
    version=__version__,
    install_requires=requirements,
    tests_require=test_requirements,
    test_suite="setup.load_test_suite",
    entry_points=entry_points
)

import os
import sys
import platform
import unittest
import setuptools

from sshx import __version__

# test requires
tests_require = [
    'mock',
    'coverage',
]


# install requires
install_requires = [
    'paramiko',
    'itsdangerous',
    'pexpect;platform_system != "Windows"',
    'colorama;platform_system == "Windows"',
    'pywin32;platform_system == "Windows"',
    'pyuserinput;platform_system == "Windows"',
    'pyhook;platform_system == "Windows"',
]

dependency_links = []

if os.name == 'nt':
    dependency_links.append('https://wqyjh.github.io/python-wheels/pyhook/')

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
    tests_require=tests_require,
    install_requires=install_requires,
    dependency_links=dependency_links,
    test_suite="setup.load_test_suite",
    entry_points=entry_points
)

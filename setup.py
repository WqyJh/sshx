from __future__ import unicode_literals

import os
import sys
import platform
import unittest
import setuptools

# test requires
tests_require = [
    'mock',
    'coverage',
]


# install requires
_PYHOOK_URL = 'https://github.com/WqyJh/python-wheels/raw/master/pyHook/pyHook-1.5.1-{python}-{python}m-{platform}.whl'
pyhook_url = _PYHOOK_URL.format(
    python='cp%s%s' % platform.python_version_tuple()[0:2],
    platform=sys.platform
)

install_requires = [
    'paramiko',
    'itsdangerous',
    'colorama; platform_system == "Windows"',
    'pywin32; platform_system == "Windows"',
    'pyuserinput',
]

dependency_links = []

if os.name == 'nt':
    dependency_links.append(pyhook_url)

# entry points
entry_points = {
    'console_scripts': [
        'sshm = sshm.sshm:main'
    ]
}


# test suite
def load_test_suite():
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover('sshm/tests')
    return test_suite


setuptools.setup(
    tests_require=tests_require,
    install_requires=install_requires,
    dependency_links=dependency_links,
    test_suite="setup.load_test_suite",
    entry_points=entry_points
)

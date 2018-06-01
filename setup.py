import os
import unittest
import setuptools

# Documentation
with open("README.md", "r") as fh:
    long_description = fh.read()

# Dependencies
win32_requirements = [
    'colorama',
    'pywin32',
]

install_requires = [
    'paramiko',
    'itsdangerous',
]

if os.name == 'nt':
    # win32
    install_requires.extend(win32_requirements)

# Tests


def load_test_suite():
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover('sshm/tests')
    return test_suite


# entry_points
entry_points = {
    'console_scripts': [
        'sshm = sshm.sshm:main',
    ],
}


setuptools.setup(
    name="sshm",
    version="0.0.5",
    author="wqy",
    author_email="qiyingwangwqy@gmail.com",
    description="SSH with account managing",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/WqyJh/sshm",
    packages=setuptools.find_packages(),
    install_requires=install_requires,
    test_suite='setup.load_test_suite',
    entry_points=entry_points,
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ),
)

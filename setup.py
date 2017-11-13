#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Note: To use the 'upload' functionality of this file, you must:
#   $ pip install twine

# Adapted from "setup.py for Humans" - https://github.com/kennethreitz/setup.py

import io
import os
import sys
from shutil import rmtree

from setuptools import find_packages, setup, Command
from setuptools.command.test import test as TestCommand

NAME = 'flapjack'

here = os.path.abspath(os.path.dirname(__file__))

with io.open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = '\n' + f.read()

# Load the package's __version__.py module as a dictionary.
about = {}
with open(os.path.join(here, NAME, '__version__.py')) as f:
    exec(f.read(), about)


class PublishCommand(Command):
    """Support setup.py publish."""

    description = 'Build and publish the package'
    user_options = []

    @staticmethod
    def status(s):
        """Prints things in bold."""
        print('\033[1m{0}\033[0m'.format(s))

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        try:
            self.status('Removing previous builds…')
            rmtree(os.path.join(here, 'dist'))
        except OSError:
            pass

        self.status('Building Source and Wheel (universal) distribution…')
        os.system('{0} setup.py sdist bdist_wheel --universal'.format(
            sys.executable))

        self.status('Uploading the package to PyPi via Twine…')
        os.system('twine upload dist/*')

        sys.exit()


class PyTestCommand(TestCommand):
    """Support running PyTest with setup.py test."""

    description = TestCommand.description

    user_options = [('pytest-args=', 'a', "Arguments to pass to pytest")]

    def initialize_options(self):
        super().initialize_options()
        self.pytest_args = ''

    def run_tests(self):
        import shlex
        # Dependency only needs to be present when running tests
        import pytest
        exitcode = pytest.main(shlex.split(self.pytest_args) + ['--flake8'])
        if exitcode == 5:
            sys.exit(0)  # no tests is okay, since we don't have any tests yet
        sys.exit(exitcode)


setup(
    name=NAME,
    version=about['__version__'],
    description='Tool for developing components inside a flatpak runtime',
    long_description=long_description,
    author='Philip Chimento',
    author_email='philip@endlessm.com',
    url='https://github.com/endlessm/flapjack',

    packages=find_packages(),
    entry_points={
        'console_scripts': ['flapjack=flapjack.main:main'],
    },

    install_requires=[],
    tests_require=['pytest==3.0.6', 'pytest-flake8==0.8.1', 'flake8==3.2.0'],
    include_package_data=True,
    license='ISC',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        ('License :: OSI Approved :: '
         'GNU General Public License v2 or later (GPLv2+)'),
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development :: Build Tools',
    ],

    # setup.py publish support
    cmdclass={
        'publish': PublishCommand,
        'test': PyTestCommand,
    },
)

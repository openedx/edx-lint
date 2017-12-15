"""
edx-lint
========

A collection of code quality tools:

- A few pylint plugins to check for quality issues pylint misses.

- A command-line tool to generate config files like pylintrc from a master
  file (part of edx_lint), and a repo-specific tweaks file.

"""

import os

from setuptools import setup

# pbr does some things we don't need. Turn them off the only way pbr gives us.
os.environ['SKIP_GENERATE_AUTHORS'] = '1'
os.environ['SKIP_WRITE_GIT_CHANGELOG'] = '1'

setup(
    setup_requires=['pbr>=1.9', 'setuptools>=17.1'],
    pbr=True,
)

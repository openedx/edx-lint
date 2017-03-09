"""
edx-lint
========

A collection of code quality tools:

- A few pylint plugins to check for quality issues pylint misses.

- A command-line tool to generate config files like pylintrc from a master
  file (part of edx_lint), and a repo-specific tweaks file.

"""

from setuptools import setup

setup(
    setup_requires=['pbr>=1.9', 'setuptools>=17.1'],
    pbr=True,
)

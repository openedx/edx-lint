#!/usr/bin/env python

from setuptools import setup

setup(
    name='edx_lint',
    version='0.1',
    description='edX-authored pylint checkers',
    url='https://github.com/edx/edx-lint',
    packages=[
        'edx_lint',
        'edx_lint.pylint',
    ],
    install_requires=[
        'pylint>=1.4.0',
    ],
)

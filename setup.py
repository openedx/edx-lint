#!/usr/bin/env python

from setuptools import setup

setup(
    name='edx_lint',
    version='0.1',
    description='edX-authored pylint checkers',
    url='https://github.com/edx/edx-lint',

    packages=[
        'edx_lint',
        'edx_lint.cmd',
        'edx_lint.pylint',
    ],

    package_data={
        'edx_lint': [
            'files/*',
        ],
    },

    entry_points={
        'console_scripts': [
            'edx_lint = edx_lint.cmd.main:main',
        ],
    },

    install_requires=[
        'pylint>=1.4.0',
    ],
)

#!/usr/bin/env python

from setuptools import setup

setup(
    name='edx-lint',
    version='0.3.1',
    description='edX-authored pylint checkers',
    url='https://github.com/edx/edx-lint',
    author='edX',
    author_email='oscm@edx.org',
    license='Apache',

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
        'pylint==1.4.4',
        'pylint-django==0.6.1',
    ],
)

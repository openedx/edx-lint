#!/usr/bin/env python

from setuptools import setup

setup(
    name='edx-lint',
    version='0.4.1',
    description='edX-authored pylint checkers',
    url='https://github.com/edx/edx-lint',
    author='edX',
    author_email='oscm@edx.org',
    license='Apache',

    classifiers=[
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.4",
        "Topic :: Software Development :: Quality Assurance",
    ],

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
        'astroid==1.3.8',   # pylint doesn't pin astroid!?
        'pylint-django==0.6.1',
        'pylint-celery==0.3',
        'six>=1.10.0,<2.0.0',
    ],
)

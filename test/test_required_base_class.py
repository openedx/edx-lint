"""Unit tests for required-base-classes."""

import unittest

import astroid
from pylint.testutils import CheckerTestCase, Message, set_config

from edx_lint.pylint.required_base_class import RequiredBaseClassChecker


class RequiredBaseClassTestCase(CheckerTestCase):
    CHECKER_CLASS = RequiredBaseClassChecker

    def test_something(self):
        node = astroid.parse('''
        class MyClass(object):
            pass
        ''')
        with self.assertNoMessages():
            self.checker.visit_class(node)

    @set_config(required_base_class=["Foo:Bax"])
    def test_wut(self):
        node = astroid.parse('''
        class MyClass(object):
            pass
        ''')
        with self.assertNoMessages():
            self.checker.visit_class(node)

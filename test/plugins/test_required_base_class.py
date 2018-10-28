"""Unit tests for required-base-classes."""

import astroid
from pylint.testutils import CheckerTestCase, Message, set_config

from edx_lint.pylint.required_base_class import RequiredBaseClassChecker


class TestRequiredBaseClass(CheckerTestCase):
    """Unittest tests of RequiredBaseClassChecker."""

    CHECKER_CLASS = RequiredBaseClassChecker

    def test_no_messages_by_default(self):
        node = astroid.parse('''
            class MyClass(object):
                pass
        ''')
        with self.assertNoMessages():
            self.walk(node)

    @set_config(required_base_class=["BaseClass:MyMixin"])
    def test_no_messages_if_class_not_used(self):
        node = astroid.parse('''
            class MyClass(object):
                pass
        ''')
        with self.assertNoMessages():
            self.walk(node)

    @set_config(required_base_class=["unittest.case.TestCase:.MyTestMixin"])
    def test_error_if_class_is_not_used(self):
        node = astroid.parse('''
            from unittest import TestCase
            class MyClass(TestCase):
                pass
        ''')
        expected_msg = Message(
            'missing-required-base-class',
            node=node.body[-1],
            args=('MyClass', '.MyTestMixin'),
        )
        with self.assertAddsMessages(expected_msg):
            self.walk(node)

    @set_config(required_base_class=["unittest.case.TestCase:.MyTestMixin"])
    def test_no_messages_if_class_is_used(self):
        node = astroid.parse('''
            from unittest import TestCase
            class MyTestMixin(object):
                pass
            class MyClass(MyTestMixin, TestCase):
                pass
        ''')
        with self.assertNoMessages():
            self.walk(node)

    @set_config(required_base_class=["unittest.case.TestCase:.MyTestMixin"])
    def test_old_style_classes(self):
        # We don't support base class checking on old-style classes, but we
        # have to be sure not to fall over at least.
        node = astroid.parse('''
            class MyClass:
                pass
        ''')
        with self.assertNoMessages():
            self.walk(node)

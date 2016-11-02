"""Unit tests for required-base-classes."""

import astroid
from pylint.testutils import CheckerTestCase, Message, set_config

from edx_lint.pylint.required_base_class import RequiredBaseClassChecker


class RequiredBaseClassTestCase(CheckerTestCase):
    """Unittest tests of RequiredBaseClassChecker."""

    CHECKER_CLASS = RequiredBaseClassChecker

    def get_class_node(self, code):
        """Parse `code`, and return the last class node.

        The code should have at least one class definition.

        """
        node = astroid.parse(code)
        class_node = None
        for body_node in node.body:
            if getattr(body_node, 'type', 'none') == "class":
                class_node = body_node
        return class_node

    def test_no_messages_by_default(self):
        node = self.get_class_node('''
            class MyClass(object):
                pass
        ''')
        with self.assertNoMessages():
            self.checker.visit_class(node)

    @set_config(required_base_class=["BaseClass:MyMixin"])
    def test_no_messages_if_class_not_used(self):
        node = self.get_class_node('''
            class MyClass(object):
                pass
        ''')
        with self.assertNoMessages():
            self.checker.visit_class(node)

    @set_config(required_base_class=["unittest.case.TestCase:.MyTestMixin"])
    def test_error_if_class_is_not_used(self):
        node = self.get_class_node('''
            from unittest import TestCase
            class MyClass(TestCase):
                pass
        ''')
        expected_msg = Message(
            'missing-required-base-class',
            node=node,
            args=('MyClass', '.MyTestMixin'),
        )
        with self.assertAddsMessages(expected_msg):
            self.checker.visit_class(node)

    @set_config(required_base_class=["unittest.case.TestCase:.MyTestMixin"])
    def test_no_messages_if_class_is_used(self):
        node = self.get_class_node('''
            from unittest import TestCase
            class MyTestMixin(object):
                pass
            class MyClass(MyTestMixin, TestCase):
                pass
        ''')
        with self.assertNoMessages():
            self.checker.visit_class(node)

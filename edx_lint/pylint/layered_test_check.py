"""Pylint plugin: test classes derived from test classes."""

import astroid

from pylint.checkers import BaseChecker, utils
from pylint.interfaces import IAstroidChecker

from .common import BASE_ID, check_visitors


def register_checkers(linter):
    """Register checkers."""
    linter.register_checker(LayeredTestClassChecker(linter))


def is_test_case_class(node):
    """Is this node a test class?

    To be a test class, it has to derive from unittest.TestCase, and not
    have __test__ defined as False.

    """
    if not node.is_subtype_of("unittest.case.TestCase"):
        return False

    dunder_test = node.locals.get("__test__")
    if dunder_test:
        if isinstance(dunder_test[0], astroid.AssignName):
            value = list(dunder_test[0].assigned_stmts())
            if len(value) == 1 and isinstance(value[0], astroid.Const):
                return bool(value[0].value)

    return True


@check_visitors
class LayeredTestClassChecker(BaseChecker):
    """Pylint checker for tests inheriting test methods from other tests."""

    __implements__ = (IAstroidChecker,)

    name = "layered-test-class-checker"

    MESSAGE_ID = "test-inherits-tests"
    msgs = {
        ("E%d03" % BASE_ID): (
            u"test class %s inherits tests from %s",
            MESSAGE_ID,
            "Used when a test class inherits test methods from another test "
            "class, meaning the inherited tests will run more than once.",
        )
    }

    @utils.check_messages(MESSAGE_ID)
    def visit_classdef(self, node):
        """Check each class."""
        if not is_test_case_class(node):
            return

        for anc in node.ancestors():
            if not is_test_case_class(anc):
                continue
            for meth in anc.mymethods():
                if meth.name.startswith("test_"):
                    self.add_message(self.MESSAGE_ID, args=(node.name, anc.name), node=node)
                    # No need to belabor the point.
                    return

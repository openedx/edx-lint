"""Checker for using assertTrue/False instead of a more precise assert.

Hattip to Ned Batchelder for the idea:
http://nedbatchelder.com/blog/201505/writing_pylint_plugins.html
"""
import astroid

from pylint.interfaces import IAstroidChecker
from pylint.checkers import BaseChecker, utils

from .common import BASE_ID


def register_checkers(linter):
    """Register checkers."""
    linter.register_checker(AssertChecker(linter))


class AssertChecker(BaseChecker):
    """
    Implements a few pylint checks on unitests asserts - making sure the right assert is used if assertTrue or
    assertFalse are misused.
    """

    __implements__ = (IAstroidChecker,)

    name = 'assert-checker'

    AFFECTED_ASSERTS = ["assertTrue", "assertFalse"]

    USE_ASSERT_EQUAL = 'wrong-assert-should-be-assertequal'
    USE_ASSERT_IN = 'wrong-assert-should-be-assertin'
    USE_ASSERT_COMPARE = 'wrong-assert-should-be-assertcomparison'
    msgs = {
        'C%d90' % BASE_ID: (
            "%s is a comparison, use assertEqual.",
            USE_ASSERT_EQUAL,
             "Use assert(Not)Equal instead of assertTrue/False",
        ),

        'C%d91' % BASE_ID: (
            "%s is an in statement, use assertIn.",
            USE_ASSERT_IN,
            "Use assert(Not)In instead of assertTrue/False.",
        ),

        'C%d92' % BASE_ID: (
            "%s is a comparison, use assertGreater or assertLess.",
            USE_ASSERT_COMPARE,
            "Use assertGreater/Less instead of assertTrue/False",
        ),
    }

    @utils.check_messages(USE_ASSERT_EQUAL, USE_ASSERT_IN, USE_ASSERT_COMPARE)
    def visit_callfunc(self, node):
        """
        Check that various assertTrue/False functions are not misused.
        """
        if not isinstance(node.func, astroid.Getattr):
            # If it isn't a getattr ignore this. All the assertMethods are attrs of self:
            return

        if node.func.attrname not in self.AFFECTED_ASSERTS:
            # Not an attribute / assert we care about
            return

        first_arg = node.args[0]
        if not isinstance(first_arg, astroid.Compare):
            # Not a comparison, so this is probably ok:
            return

        if first_arg.ops[0][0] in ["==", "!="]:
            # An assertTrue/False with a compare should be assertEqual:
            self.add_message(self.USE_ASSERT_EQUAL, args=first_arg.as_string(), node=node)

        elif first_arg.ops[0][0] == "in":
            # An assertTrue/False with an in statement should be assertIn:
            self.add_message(self.USE_ASSERT_IN, args=first_arg.as_string(), node=node)

        elif "<" in first_arg.ops[0][0] or ">" in first_arg.ops[0][0]:
            # An assertTrue/False with a comparison should be assertGreater or assertLess:
            self.add_message(self.USE_ASSERT_COMPARE, args=first_arg.as_string(), node=node)

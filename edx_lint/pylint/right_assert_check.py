"""Checker for using assertTrue/False instead of a more precise assert.

Hattip to Ned Batchelder for the idea:
http://nedbatchelder.com/blog/201505/writing_pylint_plugins.html
"""
import astroid

from pylint.interfaces import IAstroidChecker
from pylint.checkers import BaseChecker, utils

from .common import BASE_ID, check_visitors


def register_checkers(linter):
    """Register checkers."""
    linter.register_checker(AssertChecker(linter))


@check_visitors
class AssertChecker(BaseChecker):
    """
    Implements a few pylint checks on unitests asserts - making sure the right
    assert is used if assertTrue or assertFalse are misused.
    """

    __implements__ = (IAstroidChecker,)

    name = "assert-checker"

    AFFECTED_ASSERTS = ["assertTrue", "assertFalse"]

    BETTER_COMPARES = {
        "==": "assertEqual",
        "!=": "assertNotEqual",
        "in": "assertIn",
        "not in": "assertNotIn",
        "<": "assertLess",
        "<=": "assertLessEqual",
        ">": "assertGreater",
        ">=": "assertGreaterEqual",
        "is": "assertIs",
        "is not": "assertIsNot",
    }

    BETTER_NONE_COMPARES = {
        "==": "assertIsNone",
        "is": "assertIsNone",
        "!=": "assertIsNotNone",
        "is not": "assertIsNotNone",
    }

    INVERTED_PAIRS = [
        ("assertEqual", "assertNotEqual"),
        ("assertIn", "assertNotIn"),
        ("assertLess", "assertGreaterEqual"),
        ("assertGreater", "assertLessEqual"),
        ("assertIs", "assertIsNot"),
        ("assertIsNone", "assertIsNotNone"),
    ]

    INVERTED = {}
    for yup, nope in INVERTED_PAIRS:
        INVERTED[yup] = nope
        INVERTED[nope] = yup

    MESSAGE_ID = "wrong-assert-type"
    msgs = {("C%d90" % BASE_ID): ("%s", MESSAGE_ID, "Use assert(Not)Equal instead of assertTrue/False")}

    @utils.check_messages(MESSAGE_ID)
    def visit_call(self, node):
        """
        Check that various assertTrue/False functions are not misused.
        """
        if not isinstance(node.func, astroid.Attribute):
            # If it isn't a getattr ignore this. All the assertMethods are
            # attributes of self:
            return

        if node.func.attrname not in self.AFFECTED_ASSERTS:
            # Not an attribute / assert we care about
            return

        first_arg = node.args[0]
        existing_code = "%s(%s)" % (node.func.attrname, first_arg.as_string())

        if isinstance(first_arg, astroid.Compare):
            if len(first_arg.ops) > 1:
                # This is a chained comparison, which we can't do anything with.
                return

            compare = first_arg.ops[0][0]
            right = first_arg.ops[0][1]
            if isinstance(right, astroid.Const) and right.value is None:
                # Comparing to None, handle specially.
                better = self.BETTER_NONE_COMPARES[compare]
            else:
                better = self.BETTER_COMPARES[compare]

            if node.func.attrname == "assertFalse":
                better = self.INVERTED[better]
            self.add_message(self.MESSAGE_ID, args=u"%s should be %s" % (existing_code, better), node=node)

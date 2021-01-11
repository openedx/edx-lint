"""Checker for simplifiable range() calls."""

import astroid

from pylint.checkers import BaseChecker, utils
from pylint.interfaces import IAstroidChecker

from .common import BASE_ID, check_visitors


def register_checkers(linter):
    """Register checkers."""
    linter.register_checker(RangeChecker(linter))


@check_visitors
class RangeChecker(BaseChecker):
    """
    Checks for range() and xrange() used with unneeded arguments.

    Bad:
        range(0, N)
        range(0, N, 1)

    OK:
        range(N)
        range(1, N)
        range(1, N, 2)

    The message id is simplifiable-range.

    """

    __implements__ = (IAstroidChecker,)

    name = "range-checker"

    RANGE_FUNCTIONS = ["range", "xrange"]

    MESSAGE_ID = "simplifiable-range"
    msgs = {("C%d20" % BASE_ID): ("%s() call could be %s-argument", MESSAGE_ID, "range() call could be simplified")}

    @utils.check_messages(MESSAGE_ID)
    def visit_call(self, node):
        """Called for every function call in the source code."""
        if not isinstance(node.func, astroid.Name):
            # It isn't a simple name, can't deduce what function it is.
            return

        if node.func.name not in self.RANGE_FUNCTIONS:
            # Not a function we care about.
            return

        first = node.args[0]
        if not isinstance(first, astroid.Const):
            # Computed first argument, can't tell what it is.
            return

        if not isinstance(first.value, int):
            # First argument is not an int, that's fine.
            return

        # If there are three args and the third is 1, that's bad.
        three1 = False
        if len(node.args) == 3:
            third = node.args[2]
            if isinstance(third, astroid.Const):
                if isinstance(third.value, int) and third.value == 1:
                    three1 = True

        if first.value == 0:
            # The first argument is 0, suspicious.
            if len(node.args) == 2:
                # range(0, n): bad.
                self.add_message(self.MESSAGE_ID, args=(node.func.name, "single"), node=node)
            elif three1:
                # range(0, n, 1): bad.
                self.add_message(self.MESSAGE_ID, args=(node.func.name, "single"), node=node)
        elif three1:
            # range(n, m, 1): bad.
            self.add_message(self.MESSAGE_ID, args=(node.func.name, "two"), node=node)

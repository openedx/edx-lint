"""Checker for simplifiable range() calls."""

import astroid

from pylint.checkers import BaseChecker
from pylint.interfaces import IAstroidChecker

from .common import BASE_ID


def register_checkers(linter):
    """Register checkers."""
    linter.register_checker(RangeChecker(linter))


class RangeChecker(BaseChecker):

    __implements__ = (IAstroidChecker,)

    name = 'range-checker'

    RANGE_FUNCTIONS = ["range", "xrange"]

    MESSAGE_ID = 'simplifiable-range'
    msgs = {
        'E%d20' % BASE_ID: (
            "%s() call could be single-argument",
            MESSAGE_ID,
            "range() call could be single-argument",
        ),
    }

    def visit_callfunc(self, node):
        if not isinstance(node.func, astroid.Name):
            # It isn't a simple name, can't deduce what function it is.
            return

        if node.func.name not in self.RANGE_FUNCTIONS:
            # Not a function we care about.
            return

        if not self.linter.is_message_enabled(self.MESSAGE_ID):
            return

        first = node.args[0]
        if not isinstance(first, astroid.Const):
            # Computed first argument, can't tell what it is.
            return

        if not (isinstance(first.value, int) and first.value == 0):
            # First argument is not 0, that's fine.
            return

        # The first argument is 0, suspicious.
        if len(node.args) == 2:
            # range(0, n): bad.
            self.add_message(self.MESSAGE_ID, args=node.func.name, node=node)
        elif len(node.args) == 3:
            # Bad if the third argument is 1.
            third = node.args[2]
            if isinstance(third, astroid.Const):
                if isinstance(third.value, int) and third.value == 1:
                    # range(0, n, 1): bad.
                    self.add_message(self.MESSAGE_ID, args=node.func.name, node=node)

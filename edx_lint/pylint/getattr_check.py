"""Check that getattr and setattr aren't being used with literal attribute names."""

import astroid

from pylint.checkers import BaseChecker, utils
from pylint.interfaces import IAstroidChecker

from .common import BASE_ID


def register_checkers(linter):
    """Register checkers."""
    linter.register_checker(GetSetAttrLiteralChecker(linter))


class GetSetAttrLiteralChecker(BaseChecker):

    __implements__ = (IAstroidChecker,)

    name = 'getattr-literal-checker'

    MESSAGE_ID = 'literal-used-as-attribute'
    msgs = {
        'E%d30' % BASE_ID: (
            "%s used with a literal attribute name",
            MESSAGE_ID,
            "getattr or setattr used with a literal attribute name",
        ),
    }

    @utils.check_messages(MESSAGE_ID)
    def visit_callfunc(self, node):
        if not isinstance(node.func, astroid.Name):
            # It isn't a simple name, can't deduce what function it is.
            return

        if node.func.name == "getattr":
            if len(node.args) != 2:
                # We only attend to 2-argument getattr()
                return
        elif node.func.name == "setattr":
            pass
        else:
            # Not a function we care about.
            return

        if not self.linter.is_message_enabled(self.MESSAGE_ID, line=node.fromlineno):
            return

        second = node.args[1]
        if isinstance(second, astroid.Const):
            if isinstance(second.value, basestring):
                # The first argument is a constant string! Bad!
                self.add_message(self.MESSAGE_ID, args=node.func.name, node=node)

        # All is well.

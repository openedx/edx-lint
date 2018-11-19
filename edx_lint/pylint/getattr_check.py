"""Check that getattr and setattr aren't being used with literal attribute names."""

import re

import six

import astroid
from pylint.checkers import BaseChecker, utils
from pylint.interfaces import IAstroidChecker

from .common import BASE_ID, check_visitors


def register_checkers(linter):
    """Register checkers."""
    linter.register_checker(GetSetAttrLiteralChecker(linter))


@check_visitors
class GetSetAttrLiteralChecker(BaseChecker):
    """
    Checks for string literals used as attribute names with getattr and
    friends.

    Bad:
        x = getattr(obj, "attr_name")
        setattr(obj, "attr_name", value)
        delattr(obj, "attr_name")

    OK:
        x = getattr(obj, "attr_name", default_value)

    The message id is literal-used-as-attribute.

    """
    __implements__ = (IAstroidChecker,)

    name = 'getattr-literal-checker'

    MESSAGE_ID = 'literal-used-as-attribute'
    msgs = {
        'C%d30' % BASE_ID: (
            u"%s using a literal attribute name",
            MESSAGE_ID,
            "getattr or setattr using with a literal attribute name",
        ),
    }

    @utils.check_messages(MESSAGE_ID)
    def visit_call(self, node):
        """Called for every function call in the source code."""
        if not isinstance(node.func, astroid.Name):
            # It isn't a simple name, can't deduce what function it is.
            return

        if node.func.name == "getattr":
            if len(node.args) != 2:
                # We only attend to 2-argument getattr()
                return
        elif node.func.name in ["setattr", "delattr"]:
            pass
        else:
            # Not a function we care about.
            return

        second = node.args[1]
        if isinstance(second, astroid.Const):
            if isinstance(second.value, six.string_types):
                # The second argument is a constant string! Might be bad!
                # Check the string value: if it's an identifier, then no need
                # for getattr.
                if re.search(r"^[a-zA-Z_][a-zA-Z0-9_]*$", second.value):
                    self.add_message(self.MESSAGE_ID, args=node.func.name, node=node)

        # All is well.

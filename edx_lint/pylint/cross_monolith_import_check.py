"""
Checks for unsafe @@TODO
"""

from pylint.checkers import BaseChecker
from pylint.interfaces import IAstroidChecker

from .common import BASE_ID, check_visitors


def register_checkers(linter):
    """Register checkers."""
    linter.register_checker(CrossMonolithImportChecker(linter))


@check_visitors
class CrossMonolithImportChecker(BaseChecker):
    """
    Checks for @@TODO
    """

    __implements__ = (IAstroidChecker,)

    name = "cross-monolith-import-checker"

    MESSAGE_ID = "cross-monolith-import"

    # @@TODO
    '''
    msgs = {
        "C{}57".format(BASE_ID): (
            u"yaml.load%s() call is unsafe, use yaml.safe_load%s()",
            MESSAGE_ID,
            "yaml.load*() is unsafe",
        )
    }

    @utils.check_messages(MESSAGE_ID)
    def visit_call(self, node):
        """
        Check whether a call is an unsafe call to yaml.load.
        """
        func_name = node.func.as_string()
        if func_name in self.UNSAFE_CALLS:
            suffix = func_name.lstrip("yaml.load")
            self.add_message(self.MESSAGE_ID, args=(suffix, suffix), node=node)
    '''
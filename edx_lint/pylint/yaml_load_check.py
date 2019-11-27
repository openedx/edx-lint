"""
Checks for unsafe ``yaml.load()`` calls.
The PyYAML library has not yet released a version
that addresses the vulnerability (listed below) in the commonly
called ``load()`` function.

Vulnerability: https://nvd.nist.gov/vuln/detail/CVE-2017-18342
PyYAML release plan: https://github.com/yaml/pyyaml/issues/193

When a new release is published, we may be able to remove this check.
"""

from pylint.checkers import BaseChecker, utils
from pylint.interfaces import IAstroidChecker

from .common import BASE_ID, check_visitors


def register_checkers(linter):
    """Register checkers."""
    linter.register_checker(YamlLoadChecker(linter))


@check_visitors
class YamlLoadChecker(BaseChecker):
    """
    Checks for unsafe ``yaml.load()`` calls.
    """

    __implements__ = (IAstroidChecker,)

    name = "yaml-load-checker"

    MESSAGE_ID = "unsafe-yaml-load"

    UNSAFE_CALLS = {"yaml.load", "yaml.load_all"}

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

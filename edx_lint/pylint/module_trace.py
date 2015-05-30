"""A pylint checker that simply records what module it's visiting.

This helps diagnose problems with pylint not running on all files.

To use, define an environment variable PYLINT_RECORD_FILES, with a value of
a file name to write them to:

    set PYLINT_RECORD_FILES=pylinted_files.txt

"""

import os

from pylint.checkers import BaseChecker
from pylint.interfaces import IAstroidChecker

from .common import BASE_ID


def register_checkers(linter):
    """Register checkers."""
    linter.register_checker(ModuleTracingChecker(linter))


class ModuleTracingChecker(BaseChecker):

    __implements__ = (IAstroidChecker,)

    name = 'module-tracing-checker'

    msgs = {
        'E%d00' % BASE_ID: (
            "bogus",
            "bogus",
            "bogus",
        ),
    }

    def visit_module(self, node):
        filename = os.environ.get("PYLINT_RECORD_FILES", "")
        if filename:
            with open(filename, "a") as f:
                f.write(node.file)
                f.write("\n")

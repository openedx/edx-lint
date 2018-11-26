"""Check that strings are unicode enough."""

import ast
import json
import re
import token

import six

from pylint.checkers import BaseTokenChecker
from pylint.interfaces import ITokenChecker, IRawChecker

from .common import BASE_ID, check_visitors


def register_checkers(linter):
    """Register checkers."""
    linter.register_checker(UnicodeFormatStringChecker(linter))


@check_visitors
class UnicodeFormatStringChecker(BaseTokenChecker):
    """
    XXXXXX

    The message id is xxxxxxx.

    """
    # ITokenChecker gets us process_tokens support.
    # IRawChecker gets us process_module support.
    __implements__ = (ITokenChecker, IRawChecker)

    name = 'unicode-format-string-checker'

    MESSAGE_ID = 'unicode-format-string'
    msgs = {
        'C%d11' % BASE_ID: (
            "Human-readable format strings should be unicode",
            MESSAGE_ID,
            "Human-readable format strings should be unicode",
        ),
    }

    def __init__(self, *args, **kwargs):
        super(UnicodeFormatStringChecker, self).__init__(*args, **kwargs)
        self._unicode_literals = False

    def process_module(self, node):
        """Called for each module being examined."""
        self._unicode_literals = "unicode_literals" in node.future_imports

    def process_tokens(self, tokens):
        if six.PY3:
            # Python 3 doesn't have this issue.
            return

        if self._unicode_literals:
            # If the whole module is __future__'d, then it's all fine.
            return

        for tok_type, tok_text, start, _, _ in tokens:
            if tok_type == token.STRING:
                if tok_text.lower().startswith(("u", "b", "ur", "br")):
                    # An explicit prefix is fine.
                    continue

                value = ast.literal_eval(tok_text)  # TODO: can this fail?

                if " " not in value:
                    # If there's no space, then it's probably not a message,
                    # leave it alone.
                    continue

                if not re.search(r"[%{]", value):
                    # There's no formatting character, leave it alone.
                    continue

                try:
                    json.loads(value)
                except ValueError:
                    # It's invalid JSON, keep checking.
                    pass
                else:
                    # Valid JSON isn't human-readable, leave it alone.
                    continue    # pragma: no cover   grr.. https://github.com/nedbat/coveragepy/issues/198

                self.add_message(self.MESSAGE_ID, line=start[0])

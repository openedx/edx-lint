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
    Checks that strings are unicode.

    Message ID is: unicode-format-string
    """

    # ITokenChecker gets us process_tokens support.
    # IRawChecker gets us process_module support.
    __implements__ = (ITokenChecker, IRawChecker)

    name = "unicode-format-string-checker"

    MESSAGE_ID = "unicode-format-string"
    msgs = {
        ("C%d11" % BASE_ID): (
            "Human-readable format strings should be unicode",
            MESSAGE_ID,
            "Human-readable format strings should be unicode",
        )
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

        previous_line_has_definition = False
        current_line_has_definition = False
        first_non_comment_line = None
        for index, (tok_type, tok_text, start, _, _) in enumerate(tokens):
            if first_non_comment_line is None and tok_type != 53:  # 53 is token.COMMENT
                first_non_comment_line = index

            # Keep track of whether previous line contained a function or class definition
            if tok_type in (token.NEWLINE, 54):  # 54 is token.NL
                previous_line_has_definition = current_line_has_definition
                current_line_has_definition = False
            elif tok_text in ["def", "class"]:
                current_line_has_definition = True

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

                if previous_line_has_definition:
                    # Previous line probably contains a function or class definition
                    # so this string is probably a docstring
                    continue
                if first_non_comment_line and index == first_non_comment_line:
                    # If this string is the first line of the file (excluding comments) it is a docstring
                    continue

                try:
                    json.loads(value)
                except ValueError:
                    # It's invalid JSON, keep checking.
                    pass
                else:
                    # Valid JSON isn't human-readable, leave it alone.
                    continue  # pragma: no cover   grr.. https://github.com/nedbat/coveragepy/issues/198

                self.add_message(self.MESSAGE_ID, line=start[0])

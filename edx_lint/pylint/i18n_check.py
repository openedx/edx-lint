"""Checker for incorrect string translation functions."""

import six

import astroid

from pylint.checkers import BaseChecker, utils
from pylint.interfaces import IAstroidChecker

from .common import BASE_ID, check_visitors


def register_checkers(linter):
    """Register checkers."""
    linter.register_checker(TranslationStringConstantsChecker(linter))


@check_visitors
class TranslationStringConstantsChecker(BaseChecker):
    u"""
    Checks for i18n translation functions (_, ugettext, ungettext, and many
    others) being called on something that isn't a string literal.

    Bad:
        _("hello {}".format(name))
        ugettext("Hello " + name)
        ugettext(value_from_database)

    OK:
        _("hello {}").format(name)

    The message id is `translation-of-non-string`.

    """

    __implements__ = (IAstroidChecker,)

    name = "translation-string-checker"

    TRANSLATION_FUNCTIONS = {
        "_",
        "gettext",
        "ngettext",
        "ngettext_lazy",
        "npgettext",
        "npgettext_lazy",
        "pgettext",
        "pgettext_lazy",
        "ugettext",
        "ugettext_lazy",
        "ugettext_noop",
        "ungettext",
        "ungettext_lazy",
    }

    MESSAGE_ID = "translation-of-non-string"
    msgs = {
        ("E%d10" % BASE_ID): (
            u"i18n function %s() must be called with a literal string",
            MESSAGE_ID,
            "i18n functions must be called with a literal string",
        )
    }

    @utils.check_messages(MESSAGE_ID)
    def visit_call(self, node):
        """Called for every function call in the source code."""
        if not isinstance(node.func, astroid.Name):
            # It isn't a simple name, can't deduce what function it is.
            return

        if node.func.name not in self.TRANSLATION_FUNCTIONS:
            # Not a function we care about.
            return

        first = node.args[0]
        if isinstance(first, astroid.Const):
            if isinstance(first.value, six.string_types):
                # The first argument is a constant string! All is well!
                return

        # Bad!
        self.add_message(self.MESSAGE_ID, args=node.func.name, node=node)

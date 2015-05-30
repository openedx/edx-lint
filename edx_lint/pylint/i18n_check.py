import astroid

from pylint.checkers import BaseChecker
from pylint.interfaces import IAstroidChecker

from .common import BASE_ID


def register_checkers(linter):
    """Register checkers."""
    linter.register_checker(TranslationStringConstantsChecker(linter))


class TranslationStringConstantsChecker(BaseChecker):

    __implements__ = (IAstroidChecker,)

    name = 'translation-string-checker'

    TRANSLATION_FUNCTIONS = set([
        '_',
        'gettext',
        'ngettext', 'ngettext_lazy',
        'npgettext', 'npgettext_lazy',
        'pgettext', 'pgettext_lazy',
        'ugettext', 'ugettext_lazy', 'ugettext_noop',
        'ungettext', 'ungettext_lazy',
    ])

    MESSAGE_ID = 'translation-of-non-string'
    msgs = {
        'E%d10' % BASE_ID: (
            "i18n function %s() must be called with a literal string",
            MESSAGE_ID,
            "i18n functions must be called with a literal string",
        ),
    }

    def visit_callfunc(self, node):
        if not isinstance(node.func, astroid.Name):
            # It isn't a simple name, can't deduce what function it is.
            return

        if node.func.name not in self.TRANSLATION_FUNCTIONS:
            # Not a function we care about.
            return

        if not self.linter.is_message_enabled(self.MESSAGE_ID):
            return

        first = node.args[0]
        if isinstance(first, astroid.Const):
            if isinstance(first.value, basestring):
                # The first argument is a constant string! All is well!
                return

        # Bad!
        self.add_message(self.MESSAGE_ID, args=node.func.name, node=node)

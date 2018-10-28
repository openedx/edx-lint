"""Test i18n_check.py"""

import astroid
from pylint.testutils import CheckerTestCase, Message

from edx_lint.pylint.i18n_check import TranslationStringConstantsChecker
from ..utils import get_module


class TestTranslationStringConstantsChecker(CheckerTestCase):
    CHECKER_CLASS = TranslationStringConstantsChecker

    def test_i18n_checker(self):
        bad_nodes = astroid.extract_node("""
            _("This is fine")
            _("Hello"+"There")          #@
            _(17)                       #@
            _("Hi, {0}".format(name))   #@
            gettext("hi, %s" % name)    #@
            foobar(12)
        """)
        module = get_module(bad_nodes[0])

        expected = [
            Message(msg_id='translation-of-non-string', node=bad_nodes[0], args='_'),
            Message(msg_id='translation-of-non-string', node=bad_nodes[1], args='_'),
            Message(msg_id='translation-of-non-string', node=bad_nodes[2], args='_'),
            Message(msg_id='translation-of-non-string', node=bad_nodes[3], args='gettext'),
        ]
        with self.assertAddsMessages(*expected):
            self.walk(module)

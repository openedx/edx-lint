"""Test i18n_check.py"""

from .pylint_test import run_pylint


def test_i18n_checker():
    source = """\
        _("This is fine")
        _("Hello"+"There")          #=A
        _(17)                       #=B
        _("Hi, {0}".format(name))   #=C
        gettext("hi, %s" % name)    #=D
        foobar(12)
    """

    msg_ids = "translation-of-non-string"
    messages = run_pylint(source, msg_ids)
    expected = {
        "A:translation-of-non-string:i18n function _() must be called with a literal string",
        "B:translation-of-non-string:i18n function _() must be called with a literal string",
        "C:translation-of-non-string:i18n function _() must be called with a literal string",
        "D:translation-of-non-string:i18n function gettext() must be called with a literal string",
    }
    assert expected == messages

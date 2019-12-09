"""Test unicode_check.py"""

import six

from .pylint_test import run_pylint


MSG_IDS = "unicode-format-string"


def test_unicode_checker():
    source = """\
    class Test():
        "docstring this is {fine}"

        def test():
            "docstring this is {fine}"
            pass
    "this is fine"
    "this is not {}".format("fine")         #=A
    "This is not %s" % ("fine",)            #=B
    '{"json": "is fine"}'
    u"Unicode strings are {}".format("fine")
    b"byte strings are %s." % ("fine,")
    "onewordis{}".format("fine")
    "pragma makes this {}".format("fine")   # pylint: disable=unicode-format-string
    """
    messages = run_pylint(source, MSG_IDS)

    # This checker only makes messages on Python 2.
    if six.PY2:
        expected = {
            "A:unicode-format-string:Human-readable format strings should be unicode",
            "B:unicode-format-string:Human-readable format strings should be unicode",
        }
    else:
        expected = set()

    assert expected == messages


def test_unicode_checker_with_future():
    source = """\
        "This is a docstring"
        from __future__ import unicode_literals

        "this is fine"
        u"this is fine"
        "this is {}".format("fine")
        "This is %s" % ("fine",)
        '{"json": "is fine"}'
        u"Unicode strings are {}".format("fine")
        "onewordis{}".format("fine")
        """
    messages = run_pylint(source, MSG_IDS)
    assert not messages

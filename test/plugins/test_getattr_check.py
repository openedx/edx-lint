"""Test getattr_check.py"""

import astroid
from pylint.testutils import CheckerTestCase, Message

from edx_lint.pylint.getattr_check import GetSetAttrLiteralChecker
from ..utils import get_module


class TestGetSetAttrLiteralChecker(CheckerTestCase):
    CHECKER_CLASS = GetSetAttrLiteralChecker

    def test_getattr_checker(self):
        bad_nodes = astroid.extract_node("""
            getattr(name, "hello")                  #@
            getattr(name, "hello", 17)
            setattr(name, "hello", hello)           #@
            setattr(name, "h" + "ello", world)
            delattr(name, "something")              #@
            delattr(name, "FOO".lower())

            # Account for this case in our code...
            world = getattr(name, 1)

            # We don't get confused by another function nname
            foobar(name, "hello")

            # Allow hyphenated strings to support our rest-api client which maps these to URLs
            getattr(name, "foo-bar")
        """)
        module = get_module(bad_nodes[0])

        expected = [
            Message(msg_id='literal-used-as-attribute', node=bad_nodes[0], args='getattr'),
            Message(msg_id='literal-used-as-attribute', node=bad_nodes[1], args='setattr'),
            Message(msg_id='literal-used-as-attribute', node=bad_nodes[2], args='delattr'),
        ]
        with self.assertAddsMessages(*expected):
            self.walk(module)

"""Test range_check.py"""

import astroid
from pylint.testutils import CheckerTestCase, Message
import pytest

from edx_lint.pylint.range_check import RangeChecker
from .utils import get_module


class TestRangeCheckerTest(CheckerTestCase):
    CHECKER_CLASS = RangeChecker

    @pytest.mark.parametrize("range_name", ["range", "xrange"])
    def test_range(self, range_name):
        bad_nodes = astroid.extract_node("""
            START, STOP, STEP = 0, 10, 1
            # Bad
            range(0, 10) #@
            range(0, STOP) #@
            range(0, 10, 1) #@
            range(0, STOP, 1) #@

            # Good
            range(10)
            range(1, 10)
            range(0, 10, 2)
            range(1, 10, 2)

            # no message when variables are involved
            range(START, 100)
            range(START, STOP)
            range(0, 10, STEP)

            # if it has four arguments, we don't know what's going on...
            range(0, 10, 1, "something")

            # trickier cases
            [range][0](0, 10)
            some_other_function(0, 10)

        """.replace("range", range_name))
        module = get_module(bad_nodes[0])

        expected = [
            Message(msg_id='simplifiable-range', node=node, args=range_name)
            for node in bad_nodes
        ]
        with self.assertAddsMessages(*expected):
            self.walk(module)

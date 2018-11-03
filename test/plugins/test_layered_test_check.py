"""Test layered_test_check.py"""

import astroid
from pylint.testutils import CheckerTestCase, Message

from edx_lint.pylint.layered_test_check import LayeredTestClassChecker
from ..utils import get_module


class TestLayeredTestClassChecker(CheckerTestCase):
    """Test layered_test_check.py"""

    CHECKER_CLASS = LayeredTestClassChecker

    def test_layered_test_checker(self):
        bad_nodes = astroid.extract_node("""
            import unittest

            # This is bad

            class TestCase(unittest.TestCase):
                def test_one(self):
                    pass

            class DerivedTestCase(TestCase):        #@
                def test_two(self):
                    pass

            # No big deal, the base class isn't a test.

            class TestHelpers(unittest.TestCase):
                __test__ = False
                def test_one(self):
                    pass

            class TestsWithHelpers(TestHelpers):
                __test__ = True
                def test_two(self):
                    pass

            # Bad: this base class is a test.

            class TestHelpers2(unittest.TestCase):
                __test__ = True
                def test_one(self):
                    pass

            class TestsWithHelpers2(TestHelpers2):  #@
                def test_two(self):
                    pass

            # Mixins are fine.

            class TestMixins(object):
                def test_one(self):
                    pass

            class TestsWithMixins(TestMixins, unittest.TestCase):
                def test_two(self):
                    pass

            # A base class which is a TestCase, but has no test methods.

            class EmptyTestCase(unittest.TestCase):
                def setUp(self):
                    super(EmptyTestCase, self).setUp()

            class ActualTestCase(EmptyTestCase):
                def test_something(self):
                    pass

            # Bizzaro __test__ examples to complete branch coverage.

            class WhatIsThis(unittest.TestCase):
                def __test__(self):
                    return self.fail("I don't know what I'm doing.")


            class TooTrickyForTheirOwnGood(unittest.TestCase):
                __test__ = 1 - 1
        """)
        module = get_module(bad_nodes[0])

        expected = [
            Message(msg_id='test-inherits-tests', node=bad_nodes[0], args=('DerivedTestCase', 'TestCase')),
            Message(msg_id='test-inherits-tests', node=bad_nodes[1], args=('TestsWithHelpers2', 'TestHelpers2')),
        ]
        with self.assertAddsMessages(*expected):
            self.walk(module)

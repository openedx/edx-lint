"""Test layered_test_check.py"""

from .pylint_test import run_pylint


def test_layered_test_checker():
    source = """\
        import unittest

        # This is bad

        class TestCase(unittest.TestCase):
            def test_one(self):
                pass

        class DerivedTestCase(TestCase):        #=A
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

        class TestsWithHelpers2(TestHelpers2):  #=B
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
                super().setUp()

        class ActualTestCase(EmptyTestCase):
            def test_something(self):
                pass

        # Bizzaro __test__ examples to complete branch coverage.

        class WhatIsThis(unittest.TestCase):
            def __test__(self):
                return self.fail("I don't know what I'm doing.")

        class TooTrickyForTheirOwnGood(unittest.TestCase):
            __test__ = 1 - 1

        # The warning can be disabled.

        class TestCase(unittest.TestCase):
            def test_one(self):
                pass

        class DerivedTestCase(TestCase):        # pylint: disable=test-inherits-tests
            def test_two(self):
                pass
    """
    msg_ids = "test-inherits-tests"
    messages = run_pylint(source, msg_ids)
    expected = {
        "A:test-inherits-tests:test class DerivedTestCase inherits tests from TestCase",
        "B:test-inherits-tests:test class TestsWithHelpers2 inherits tests from TestHelpers2",
    }
    assert expected == messages

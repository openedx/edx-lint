"""Test super_check.py"""

import pytest

from .pylint_test import run_pylint

MSG_IDS = "super-method-not-called,non-parent-method-called"


@pytest.mark.parametrize("method", ["setUp", "tearDown", "setUpClass", "tearDownClass"])
def test_unittest_super_check(method):
    source = (
        """\
        import unittest

        class GoodTestCase(unittest.TestCase):
            def {method}(self):
                super().{method}()

        class BadTestCase(unittest.TestCase):
            def {method}(self):         #=A
                self.i_am_bad = True

        class OldSchool(Mixin, unittest.TestCase):
            def {method}(self):
                Mixin.{method}(self)
                unittest.TestCase.{method}(self)

        def {method}(xyzzy):
            # Weird, but who cares?
            pass
        """
    ).format(method=method)
    messages = run_pylint(source, MSG_IDS)
    expected = {
        "A:super-method-not-called:super(...).{}() not called (unittest.case.TestCase)".format(
            method
        )
    }
    assert expected == messages


@pytest.mark.parametrize("method", ["setUpTestData"])
def test_django_super_check(method):
    source = (
        """\
        import django

        class GoodTestCase(django.test.TestCase):
            def {method}(self):
                super().{method}()

        class BadTestCase(django.test.TestCase):
            def {method}(self):         #=A
                self.i_am_bad = True
        """
    ).format(method=method)
    messages = run_pylint(source, MSG_IDS)
    expected = {
        "A:super-method-not-called:super(...).setUpTestData() not called (django.test.testcases.TestCase)"
    }
    assert expected == messages


def test_hamfisted_super():
    source = """\
        import unittest

        class SomeOtherClass(object):
            def setUp(self):
                pass

        class BadTestCase(unittest.TestCase):
            def setUp(self):
                foo("What").setUp(self)
                What.setUp(self)
                SomeOtherClass.setUp(self)   #=A
                super().setUp()
        """
    messages = run_pylint(source, MSG_IDS)
    expected = {
        "A:non-parent-method-called:setUp() was called from a non-parent class (source.SomeOtherClass)"
    }
    assert expected == messages


def test_good_super():
    source = """\
        import unittest

        def foo_func(bar):
            pass

        class GoodTestCase(unittest.TestCase):
            def setUp(self):
                self.foo_meth(bar)
                foo_func(bar)
                super().setUp()

            def tearDown(self):
                # Not sure why you would do it this way, ...
                base = super()
                base.tearDown()

            def foo_meth(self, bar):
                foo_func(bar)

            def test_something(self):
                pass

        class NotSureWhatThisIs(object):
            def setUp(self):
                pass
        """
    messages = run_pylint(source, MSG_IDS)
    assert not messages

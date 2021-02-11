"""Test unittest_assert_check.py"""

import pytest

from .pylint_test import run_pylint


def test_bad_asserts():
    source = """\
        import unittest

        class TestUnittestAssertions(unittest.TestCase):
            def test_wrong_usage(self):
                # This is the usage of unittest assert functions which shouldn't be used.
                self.assertEqual('foo'.upper(), 'FOO')

                true = True
                self.assertTrue(true)
                self.assertFalse(not true)

                self.assertIn("a", "lala")
                self.assertNotIn("b", "lala")

                self.assertGreater(1, 0)
                self.assertLess(1, 2)
        """
    messages = run_pylint(source, "avoid-unittest-asserts", '--load-plugins=edx_lint.pylint.unittest_assert')
    assert messages


def test_good_asserts():
    source = """\
        import unittest

        class TestPytestAssertions(unittest.TestCase):
            def test_right_usage(self):
                # This is the usage of pytest assert functions.
                assert 'foo'.upper() == 'FOO'

                true = True
                assert true
                assert not true

                assert "a" in "lala"
                assert "b" not in "lala"

                assert 1 > 0
                assert 1 < 2
        """
    messages = run_pylint(source, "avoid-unittest-asserts", '--load-plugins=edx_lint.pylint.unittest_assert')
    assert not messages


@pytest.mark.parametrize(
    "code, error",
    [
        (
            "assertTrue('foo'.upper() == 'FOO')",
            "assertTrue should be replaced with a pytest assertion something like `assert arg1`"
        ),
        (
            "assertFalse(500 == 501)",
            "assertFalse should be replaced with a pytest assertion something like `assert not arg1`"
        ),
        (
            "assertIn('a', 'lala')",
            "assertIn should be replaced with a pytest assertion something like `assert arg1 in arg2`"
        ),
        (
            "assertIsInstance(1, int)",
            "assertIsInstance should be replaced with a pytest assertion something like `assert isinstance(arg1, arg2)`"
        ),
        (
            "assertEqual('lala', 'lala')",
            "assertEqual should be replaced with a pytest assertion something like `assert arg1 == arg2`"
        ),
        (
            "assertAlmostEqual(6.999, 7)",
            "assertAlmostEqual should be replaced with a pytest assertion something like `assert math.isclose(arg1, "
            "arg2)`"
        ),
        (
            "assertIsNone(somevar)",
            "assertIsNone should be replaced with a pytest assertion something like `assert arg1 is None`"
        ),
    ],
)
def test_assert_hints(code, error):
    source = (
        """\
        import unittest

        class TestUnittestAssertions(unittest.TestCase):
            def test_wrong_usage(self):
                self.{}      #=A
        """
    ).format(code)
    messages = run_pylint(source, "avoid-unittest-asserts", '--load-plugins=edx_lint.pylint.unittest_assert')

    expected = {f"A:avoid-unittest-asserts:{error}"}
    assert expected == messages

"""
Test for the right_assert pylint plugin.
"""
import unittest


class TestStringMethods(unittest.TestCase):
    """
    Test class for the right_assert pylint plugin.
    """
    def test_right_usage(self):
        """
        This is the right usage of various assert functions.
        """
        self.assertEqual('foo'.upper(), 'FOO')

        true = True
        self.assertTrue(true)
        self.assertFalse(not true)

        self.assertIn("a", "lala")
        self.assertNotIn("b", "lala")

        self.assertGreater(1, 0)
        self.assertLess(1, 2)

    def test_wrong_usage(self):
        """
        This is the wrong usage of assertTrue and False, but test should still pass.
        right_assert should throw an error for each line here.
        """
        self.assertTrue('foo'.upper() == 'FOO')
        self.assertFalse(500 == 501)

        self.assertTrue("a" in "lala")
        self.assertFalse("b" not in "lala")

        self.assertTrue(1 > 0)
        self.assertFalse(1 < 2)

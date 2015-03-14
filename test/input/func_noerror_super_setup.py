"""A TestCase class that calls its parent setUp properly."""

import unittest

# pylint: disable=too-few-public-methods, missing-docstring

class GoodTestCase(unittest.TestCase):
    def setUp(self):
        self.i_am_good = True
        super(GoodTestCase, self).setUp()

    def tearDown(self):
        self.i_am_good = True
        super(GoodTestCase, self).tearDown()

    def test_something(self):
        self.assertEqual(1, 1)

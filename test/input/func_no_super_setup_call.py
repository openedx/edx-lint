"""A TestCase class that doesn't call super setUp or super tearDown."""

import unittest

# pylint: disable=too-few-public-methods, missing-docstring

class BadTestCase(unittest.TestCase):
    def setUp(self):
        self.i_am_bad = True

    def tearDown(self):
        self.i_am_bad = True

class AllowedToBeHalfBadTestCase(unittest.TestCase):
    # pylint: disable=super-method-not-called
    def setUp(self):
        self.i_am_bad = True
    # pylint: enable=super-method-not-called

    def tearDown(self):
        self.i_am_bad = True

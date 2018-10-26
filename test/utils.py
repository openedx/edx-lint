"""Testing support for pylint plugins."""

import unittest

import astroid.nodes
from pylint.testutils import CheckerTestCase


class PluginUnittestTestCase(CheckerTestCase, unittest.TestCase):
    def setUp(self):
        super(PluginUnittestTestCase, self).setUp()
        # CheckerTestCase is written for pytest, so we need to bridge over to
        # its setup method.
        self.setup_method()

def get_module(node):
    """Find the Module node from a child node."""
    while node.__class__ != astroid.nodes.Module:
        node = node.parent
    return node

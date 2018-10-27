"""Testing support for pylint plugins."""

import astroid.nodes


def get_module(node):
    """Find the Module node from a child node."""
    while node.__class__ != astroid.nodes.Module:
        node = node.parent
    return node

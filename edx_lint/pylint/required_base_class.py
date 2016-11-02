"""Pylint plugin: some classes have required base classes."""

import collections

import astroid
from astroid.scoped_nodes import get_locals     # not sure this is the right import

from pylint.checkers import BaseChecker, utils
from pylint.interfaces import IAstroidChecker

from .common import BASE_ID


def register_checkers(linter):
    """Register checkers."""
    linter.register_checker(RequiredBaseClassChecker(linter))


class RequiredBaseClassChecker(BaseChecker):
    """Pylint checker for required base classes."""

    __implements__ = (IAstroidChecker,)

    name = 'required-base-class-checker'

    MESSAGE_ID = "missing-required-base-class"
    msgs = {
        'E%d40' % BASE_ID: (
            "class %s is missing required base class %s",
            MESSAGE_ID,
            "Used when a class is missing a base class required by one of its "
            "other base classes.",
        ),
    }

    options = [
        ('required-base-class', {
            'default' : (),
            'type': 'csv',
            'metavar': '<class name pairs>',
            'help': 'Fooey'}
        ),
    ]

    def __init__(self, linter):
        super(RequiredBaseClassChecker, self).__init__(linter)
        self.class_map = collections.defaultdict(set)

    def open(self):
        if self.config.required_base_class:
            for pair in self.config.required_base_class:
                child, parent = pair.split(":")
                self.class_map[child].add(parent)

    @utils.check_messages(MESSAGE_ID)
    def visit_class(self, node):
        """Check each class."""
        if self.class_map:
            self.add_message(self.MESSAGE_ID, args=("Foo", self.class_map['Foo']), node=node)

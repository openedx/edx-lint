"""Pylint plugin: check that tests have used super() properly in setUp()."""

import astroid
import six

from pylint.checkers import BaseChecker
from pylint.interfaces import IAstroidChecker
from pylint.checkers.classes import _ancestors_to_call

from .common import BASE_ID


def register_checkers(linter):
    """Register checkers."""
    linter.register_checker(UnitTestSetupSuperChecker(linter))


class UnitTestSetupSuperChecker(BaseChecker):

    __implements__ = (IAstroidChecker,)

    name = 'unit-test-super-checker'

    MESSAGE_ID = 'super-method-not-called'
    METHOD_NAMES = ['setUp', 'tearDown']

    msgs = {
        'E%d01' % BASE_ID: (
            "super(...).%s() not called (%s)",
            "super-method-not-called",
            "setUp() must call super(...).setUp()",
        ),
        'E%d02' % BASE_ID: (
            "setUp() was called from a non-parent class (%s)",
            "non-parent-method-called",
            "setUp() should only be called for parent classes",
        ),
    }

    def visit_function(self, node):
        """check method arguments, overriding"""
        # ignore actual functions
        if not node.is_method():
            return

        method_name = node.name
        if method_name not in self.METHOD_NAMES:
            return

        if not self.linter.is_message_enabled(self.MESSAGE_ID):
            return

        klass_node = node.parent.frame()
        to_call = _ancestors_to_call(klass_node, method_name)

        not_called_yet = dict(to_call)
        for stmt in node.nodes_of_class(astroid.CallFunc):
            expr = stmt.func
            if not isinstance(expr, astroid.Getattr) \
                   or expr.attrname != method_name:
                continue
            # skip the test if using super
            if isinstance(expr.expr, astroid.CallFunc) and \
                   isinstance(expr.expr.func, astroid.Name) and \
               expr.expr.func.name == 'super':
                return
            try:
                klass = next(expr.expr.infer())
                if klass is astroid.YES:
                    continue
                # The infered klass can be super(), which was
                # assigned to a variable and the `__init__` was called later.
                #
                # base = super()
                # base.__init__(...)

                if (isinstance(klass, astroid.Instance) and
                        isinstance(klass._proxied, astroid.Class) and
                        is_builtin_object(klass._proxied) and
                        klass._proxied.name == 'super'):
                    return
                try:
                    del not_called_yet[klass]
                except KeyError:
                    if klass not in to_call:
                        self.add_message('non-parent-method-called',
                                         node=expr, args=klass.name)
            except astroid.InferenceError:
                continue

        for klass, method in six.iteritems(not_called_yet):
            if klass.name == 'object' or method.parent.name == 'object':
                continue
            self.add_message(self.MESSAGE_ID, args=(method_name, klass.name), node=node)

"""Pylint plugin: check that tests have used super() properly."""

import astroid
import six

from pylint.checkers import BaseChecker, utils
from pylint.interfaces import IAstroidChecker
from pylint.checkers.classes import _ancestors_to_call

from .common import BASE_ID, check_visitors, usable_class_name


def register_checkers(linter):
    """Register checkers."""
    linter.register_checker(UnitTestSetupSuperChecker(linter))


@check_visitors
class UnitTestSetupSuperChecker(BaseChecker):
    """
    Checks that unittest methods have used super() properly.

    It examines `setUp`, `tearDown`, `setUpClass`, and `tearDownClass` for
    correct use of super.  If there is no super, it issues a
    `super-method-not-called` error.  If super is used, but with the wrong
    class name, it issues a `non-parent-method-called` error.

    """

    __implements__ = (IAstroidChecker,)

    name = "unit-test-super-checker"

    NOT_CALLED_MESSAGE_ID = "super-method-not-called"
    NON_PARENT_MESSAGE_ID = "non-parent-method-called"

    METHOD_NAMES = ["setUp", "tearDown", "setUpClass", "tearDownClass", "setUpTestData"]

    msgs = {
        ("E%d01" % BASE_ID): (
            u"super(...).%s() not called (%s)",
            NOT_CALLED_MESSAGE_ID,
            "setUp() must call super(...).setUp()",
        ),
        ("E%d02" % BASE_ID): (
            u"%s() was called from a non-parent class (%s)",
            NON_PARENT_MESSAGE_ID,
            "setUp() should only be called for parent classes",
        ),
    }

    @utils.check_messages(NOT_CALLED_MESSAGE_ID, NON_PARENT_MESSAGE_ID)
    def visit_functiondef(self, node):
        """Called for every function definition in the source code."""
        # ignore actual functions
        if not node.is_method():
            return

        method_name = node.name
        if method_name not in self.METHOD_NAMES:
            return

        klass_node = node.parent.frame()
        to_call = _ancestors_to_call(klass_node, method_name)

        not_called_yet = dict(to_call)
        for stmt in node.nodes_of_class(astroid.Call):
            expr = stmt.func
            if not isinstance(expr, astroid.Attribute):
                continue
            if expr.attrname != method_name:
                continue

            # Skip the test if using super
            if (
                isinstance(expr.expr, astroid.Call)
                and isinstance(expr.expr.func, astroid.Name)
                and expr.expr.func.name == "super"
            ):
                return

            try:
                klass = next(expr.expr.infer())
                if klass is astroid.Uninferable:
                    continue

                # The infered klass can be super(), which was
                # assigned to a variable and the `__init__` was called later.
                #
                # base = super()
                # base.__init__(...)

                # pylint: disable=protected-access
                if (
                    isinstance(klass, astroid.Instance)
                    and isinstance(klass._proxied, astroid.ClassDef)
                    and utils.is_builtin_object(klass._proxied)
                    and klass._proxied.name == "super"
                ):
                    return
                if isinstance(klass, astroid.objects.Super):
                    return
                try:
                    del not_called_yet[klass]
                except KeyError:
                    if klass not in to_call:
                        self.add_message(
                            self.NON_PARENT_MESSAGE_ID, node=expr, args=(method_name, usable_class_name(klass))
                        )
            except astroid.InferenceError:
                continue

        for klass, method in six.iteritems(not_called_yet):
            if klass.name == "object" or method.parent.name == "object":
                continue
            self.add_message(self.NOT_CALLED_MESSAGE_ID, args=(method_name, usable_class_name(klass)), node=node)

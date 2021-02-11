"""Checker for using pytest assertion instead of unittest assertion."""
import astroid

from pylint.interfaces import IAstroidChecker
from pylint.checkers import BaseChecker, utils

from edx_lint.pylint.common import BASE_ID, check_visitors


def register_checkers(linter):
    """Register checkers."""
    linter.register_checker(UnittestAssertChecker(linter))


@check_visitors
class UnittestAssertChecker(BaseChecker):
    """
    Checks if a unit test assertion is used, Trigger warning to
    replace it with pytest assertions
    """

    __implements__ = (IAstroidChecker,)

    name = "unittest-assert-checker"

    UNITTEST_ASSERTS = [
        "assertTrue",
        "assertFalse",
        "assertEqual",
        "assertEquals",
        "assertNotEqual",
        "assertNotEquals",
        "assert_",
        "assertIn",
        "assertNotIn",
        "assertLess",
        "assertLessEqual",
        "assertGreater",
        "assertGreaterEqual",
        "assertAlmostEqual",
        "assertNotAlmostEqual",
        "assertIs",
        "assertIsNot",
        "assertIsNone",
        "assertIsNotNone",
        "assertIsInstance",
        "assertNotIsInstance",
        "assertRaises",
    ]

    ASSERT_MAPPING = {
        "assertEqual": "assert arg1 == arg2",
        "assertEquals": "assert arg1 == arg2",
        "assertNotEqual": "assert arg1 != arg2",
        "assertNotEquals": "assert arg1 != arg2",
        "assert_": "assert arg1",
        "assertTrue": "assert arg1",
        "assertFalse": "assert not arg1",
        "assertIn": "assert arg1 in arg2",
        "assertNotIn": "assert arg1 not in arg2",
        "assertIs": "assert arg1 is arg2",
        "assertIsNot": "assert arg1 is not arg2",
        "assertIsNone": "assert arg1 is None",
        "assertIsNotNone": "assert arg1 is not None",
        "assertIsInstance": "assert isinstance(arg1, arg2)",
        "assertNotIsInstance": "assert not isinstance(arg1, arg2)",
        "assertLess": "assert arg1 < arg2",
        "assertLessEqual": "assert arg1 <= arg2",
        "assertGreater": "assert arg1 > arg2",
        "assertGreaterEqual": "assert arg1 >= arg2",
        "assertAlmostEqual": "assert math.isclose(arg1, arg2)",
        "assertNotAlmostEqual": "assert not math.isclose(arg1, arg2)",
        "assertRaises": "pytest.raises(arg) or with pytest.raises(arg) as optional_var:",
    }

    MESSAGE_ID = "avoid-unittest-asserts"
    msgs = {
        ("C%d99" % BASE_ID): (
            "%s",
            MESSAGE_ID,
            "Avoid using unittest's assertion methods when using pytest, instead use the 'assert' statement"
        )
    }

    @utils.check_messages(MESSAGE_ID)
    def visit_call(self, node):
        """
        Check that unittest assertions are not used.
        """
        if not isinstance(node.func, astroid.Attribute):
            # If it isn't a getattr ignore this. All the assertMethods are
            # attributes of self:
            return

        if node.func.attrname not in self.UNITTEST_ASSERTS:
            # Not an attribute we care about
            return

        converted_assert = self.ASSERT_MAPPING.get(node.func.attrname, None)

        self.add_message(
            self.MESSAGE_ID,
            args=f"{node.func.attrname} should be replaced with a pytest assertion something like `{converted_assert}`",
            node=node
        )

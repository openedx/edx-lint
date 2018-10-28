"""Test super_check.py"""

import astroid
from pylint.testutils import CheckerTestCase, Message
import pytest

from edx_lint.pylint.super_check import UnitTestSetupSuperChecker
from ..utils import get_module


class TestUnitTestSetupSuperChecker(CheckerTestCase):
    """Test super_check.py"""

    CHECKER_CLASS = UnitTestSetupSuperChecker

    @pytest.mark.parametrize("method", [
        "setUp",
        "tearDown",
        "setUpClass",
        "tearDownClass",
    ])
    def test_super_check(self, method):
        bad_node = astroid.extract_node("""
            import unittest

            class GoodTestCase(unittest.TestCase):
                def {method}(self):
                    super(GoodTestCase, self).{method}()

            class BadTestCase(unittest.TestCase):
                def {method}(self):         #@
                    self.i_am_bad = True

            class OldSchool(Mixin, unittest.TestCase):
                def {method}(self):
                    Mixin.{method}(self)
                    unittest.TestCase.{method}(self)

            def {method}(xyzzy):
                # Weird, but who cares?
                pass
        """.format(method=method))
        module = get_module(bad_node)

        expected = Message(
            msg_id='super-method-not-called',
            node=bad_node,
            args=(method, 'TestCase'),
        )
        with self.assertAddsMessages(expected):
            self.walk(module)

    def test_hamfisted_super(self):
        bad_node = astroid.extract_node("""
            import unittest

            class SomeOtherClass(object):
                def setUp(self):
                    pass

            class BadTestCase(unittest.TestCase):
                def setUp(self):
                    foo("What").setUp(self)
                    What.setUp(self)
                    SomeOtherClass.setUp(self)   #@
                    super(BadTestCase, self).setUp()
        """)
        module = get_module(bad_node)

        expected = Message(
            msg_id='non-parent-method-called',
            node=bad_node.func,
            args=('setUp', 'SomeOtherClass'),
        )
        with self.assertAddsMessages(expected):
            self.walk(module)

    def test_good_super(self):
        node = astroid.extract_node("""
            import unittest

            def foo_func(bar):
                pass

            class GoodTestCase(unittest.TestCase):
                def setUp(self):
                    self.foo_meth(bar)
                    foo_func(bar)
                    super(GoodTestCase, self).setUp()

                def tearDown(self):
                    # Not sure why you would do it this way, ...
                    base = super(GoodTestCase, self)
                    base.tearDown()

                def foo_meth(self, bar):
                    foo_func(bar)

                def test_something(self):
                    pass

            class NotSureWhatThisIs(object):
                def setUp(self):
                    pass
        """)
        module = get_module(node)
        with self.assertNoMessages():
            self.walk(module)

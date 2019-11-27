"""Tests of edx_lint/pylint/common.py"""

import pytest

from edx_lint.pylint.common import check_visitors

# pylint: disable=unused-variable


def test_check_good_visitors():
    @check_visitors
    # pylint: disable=missing-class-docstring
    class ItsRight:
        def visit_call(self):
            pass  # pragma: no cover

        def this_isnt_checked(self):
            pass  # pragma: no cover

        def visit_classdef(self):
            pass  # pragma: no cover


def test_check_bad_visitors():
    msg = "Method visit_xyzzy doesn't correspond to a node class"
    with pytest.raises(Exception, match=msg):

        @check_visitors
        class ItsNotRight:
            def visit_xyzzy(self):
                pass  # pragma: no cover

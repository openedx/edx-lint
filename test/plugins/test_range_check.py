"""Test range_check.py"""

import pytest

from .pylint_test import run_pylint


@pytest.mark.parametrize("range_name", ["range", "xrange"])
def test_range(range_name):
    source = (
        """\
        START, STOP, STEP = 0, 10, 1
        # Bad
        range(0, 10)        #=A
        range(0, STOP)      #=B
        range(0, 10, 1)     #=C
        range(0, STOP, 1)   #=D
        range(10, 20, 1)    #=E

        # Good
        range(10)
        range(1, 10)
        range(0, 10, 2)
        range(1, 10, 2)

        # no message when variables are involved
        range(START, 100)
        range(START, STOP)
        range(0, 10, STEP)

        # if it has four arguments, we don't know what's going on...
        range(0, 10, 1, "something")

        # trickier cases
        range("something", "or other")
        [range][0](0, 10)
        some_other_function(0, 10)

    """
    ).replace("range", range_name)
    msg_ids = "simplifiable-range"
    messages = run_pylint(source, msg_ids)

    expected = {
        f"A:simplifiable-range:{range_name}() call could be single-argument",
        f"B:simplifiable-range:{range_name}() call could be single-argument",
        f"C:simplifiable-range:{range_name}() call could be single-argument",
        f"D:simplifiable-range:{range_name}() call could be single-argument",
        f"E:simplifiable-range:{range_name}() call could be two-argument",
    }
    assert expected == messages

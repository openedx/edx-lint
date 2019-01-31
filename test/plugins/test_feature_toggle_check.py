"""Test feature_toggle_check.py"""

import astroid

from .pylint_test import run_pylint


def test_waffle_missing_toggle_annotation_check():
    source = """\
        DisablePragmaWaffleFlag(NAMESPACE, 'disable_pragma_for_annotation')  #pylint: disable=waffle-missing-toggle-annotation
        
        # .. feature_toggle_name: annotated_flag
        WaffleFlag(NAMESPACE, 'annotated_flag')

        # .. wrong_annotation
        WaffleFlag(NAMESPACE, 'flag_with_bad_annotation') #=A

        WaffleFlag(NAMESPACE, FLAG_WITHOUT_ANNOTATION) #=B

        DerivedWaffleFlag(NAMESPACE, DERIVED_FLAG_WITHOUT_ANNOTATION) #=C
        
        WaffleSwitch(NAMESPACE, SWITCH_WITHOUT_ANNOTATION) #=D
        
        NotAFlag(NAMESPACE, NOT_A_WAFFLE_FLAG)
        """

    msg_ids = "waffle-missing-toggle-annotation"
    messages = run_pylint(source, msg_ids)
    expected = {
        "A:waffle-missing-toggle-annotation:waffle feature toggle ('flag_with_bad_annotation') is missing annotation",
        "B:waffle-missing-toggle-annotation:waffle feature toggle (FLAG_WITHOUT_ANNOTATION) is missing annotation",
        "C:waffle-missing-toggle-annotation:waffle feature toggle (DERIVED_FLAG_WITHOUT_ANNOTATION) is missing annotation",
        "D:waffle-missing-toggle-annotation:waffle feature toggle (SWITCH_WITHOUT_ANNOTATION) is missing annotation",
    }
    assert expected == messages


def test_illegal_waffle_usage_check():
    source = """\
        switch_is_active('disable_pragma')  #pylint: disable=illegal-waffle-usage

        switch_is_active('test_switch')  #=A

        switch_is_active(TEST_SWITCH)  #=B

        flag_is_active('test_flag')  #=C

        flag_is_active(TEST_FLAG)  #=D
        """

    # TODO: kill this and the import
    # tree = astroid.parse(source)
    # print(tree.repr_tree())

    msg_ids = "illegal-waffle-usage"
    messages = run_pylint(source, msg_ids)
    expected = {
        "A:illegal-waffle-usage:illegal waffle usage with ('test_switch'). use utility classes WaffleFlag, WaffleSwitch.",
        "B:illegal-waffle-usage:illegal waffle usage with (TEST_SWITCH). use utility classes WaffleFlag, WaffleSwitch.",
        "C:illegal-waffle-usage:illegal waffle usage with ('test_flag'). use utility classes WaffleFlag, WaffleSwitch.",
        "D:illegal-waffle-usage:illegal waffle usage with (TEST_FLAG). use utility classes WaffleFlag, WaffleSwitch.",
    }
    assert expected == messages

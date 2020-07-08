"""Test feature_toggle_check.py"""
from .pylint_test import run_pylint


def test_waffle_missing_toggle_annotation_check():
    source = """\
        DisablePragmaWaffleFlag(NAMESPACE, 'disable_pragma_for_annotation')  #pylint: disable=feature-toggle-needs-doc

        # .. toggle_name: annotated_flag
        WaffleFlag(NAMESPACE, 'annotated_flag')

        # .. toggle_name: course_waffle_annotated_flag
        CourseWaffleFlag(NAMESPACE, 'course_waffle_annotated_flag')

        # .. documented_elsewhere
        WaffleFlag(NAMESPACE, 'documented_elsewhere')

        NotAFlag(NAMESPACE, NOT_A_WAFFLE_FLAG)

        # .. wrong_annotation
        WaffleFlag(NAMESPACE, 'flag_with_bad_annotation') #=A

        WaffleFlag(NAMESPACE, FLAG_WITHOUT_ANNOTATION) #=B

        DerivedWaffleFlag(NAMESPACE, DERIVED_FLAG_WITHOUT_ANNOTATION) #=C

        WaffleSwitch(NAMESPACE, SWITCH_WITHOUT_ANNOTATION) #=D

        CourseWaffleFlag(NAMESPACE, COURSE_WAFFLE_FLAG_WITHOUT_ANNOTATION) #=E

        MissingCourseWithKwarg = CourseWaffleFlag( #=F
            waffle_namespace=waffle_flags(),
            flag_name=u'missing_course_with_kwarg',
        )
        """

    msg_ids = "feature-toggle-needs-doc"
    messages = run_pylint(source, msg_ids)
    expected = {
        "A:feature-toggle-needs-doc:feature toggle ('flag_with_bad_annotation') is missing annotation",
        "B:feature-toggle-needs-doc:feature toggle (FLAG_WITHOUT_ANNOTATION) is missing annotation",
        "C:feature-toggle-needs-doc:feature toggle (DERIVED_FLAG_WITHOUT_ANNOTATION) is missing annotation",
        "D:feature-toggle-needs-doc:feature toggle (SWITCH_WITHOUT_ANNOTATION) is missing annotation",
        "E:feature-toggle-needs-doc:feature toggle (COURSE_WAFFLE_FLAG_WITHOUT_ANNOTATION) is missing annotation",
        "F:feature-toggle-needs-doc:feature toggle (missing_course_with_kwarg) is missing annotation",
    }
    assert expected == messages


def test_config_models_missing_doc():
    source = """\
        from config_models.models import ConfigurationModel
        from django.db import models

        # .. toggle_name: my_toggle_name
        class CorrectlyAnnotatedConfig(ConfigurationModel):
            my_toggle_name = models.BooleanField(default=True)

        class DisabeldNoAnnotationsConfig(ConfigurationModel):  #pylint: disable=feature-toggle-needs-doc
            my_toggle_name = models.BooleanField(default=True)

        # .. wrong_annotation
        class WronglyAnnotatedConfig(ConfigurationModel): #=A
            my_toggle_name = models.BooleanField(default=True)

        class NoAnnotationsConfig(ConfigurationModel): #=B
            my_toggle_name = models.BooleanField(default=True)

        # .. documented_elsewhere: true
        class DocumentedElsewhereConfig(ConfigurationModel): #=A
            my_toggle_name = models.BooleanField(default=True)

        class NotAConfigurationModelClass():
            def __init__(self, value):
                self.value = value
        """

    msg_ids = "feature-toggle-needs-doc"
    messages = run_pylint(source, msg_ids)
    expected = {
        "A:feature-toggle-needs-doc:feature toggle (WronglyAnnotatedConfig) is missing annotation",
        "B:feature-toggle-needs-doc:feature toggle (NoAnnotationsConfig) is missing annotation",
    }
    assert expected == messages


def test_django_feature_flags_missing_doc():
    source = """\
        {
            "key_value": "value"
        }

        COURSE_DICT = {
            'COURSE1',
            'COURSE2',
            'COURSE3'
        }

        FEATURES = {  #=A
            # .. toggle_name: CORRECTLY_ANNOTATED_FLAG
            'CORRECTLY_ANNOTATED_FLAG': True,

            'NO_DOCUMENTATION_FLAG': False,

            # .. wrong_annotation
            'WRONG_DOCUMENTATION_FLAG': False,

            # .. documented_elsewhere: true
            'DOCUMENTED_ELSEWHERE': False,
        }

        FEATURES = {  #pylint: disable=feature-toggle-needs-doc
            'SECOND_NO_DOCUMENTATION_FLAG': False,
        }
        """

    msg_ids = "feature-toggle-needs-doc"
    messages = run_pylint(source, msg_ids)
    expected = {
        "A:feature-toggle-needs-doc:feature toggle (NO_DOCUMENTATION_FLAG) is missing annotation",
        "A:feature-toggle-needs-doc:feature toggle (WRONG_DOCUMENTATION_FLAG) is missing annotation",
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

    msg_ids = "illegal-waffle-usage"
    messages = run_pylint(source, msg_ids)
    expected = {
        "A:illegal-waffle-usage:illegal waffle usage with ('test_switch'): "
        "use utility classes WaffleFlag, WaffleSwitch, CourseWaffleFlag.",
        "B:illegal-waffle-usage:illegal waffle usage with (TEST_SWITCH): "
        "use utility classes WaffleFlag, WaffleSwitch, CourseWaffleFlag.",
        "C:illegal-waffle-usage:illegal waffle usage with ('test_flag'): "
        "use utility classes WaffleFlag, WaffleSwitch, CourseWaffleFlag.",
        "D:illegal-waffle-usage:illegal waffle usage with (TEST_FLAG): "
        "use utility classes WaffleFlag, WaffleSwitch, CourseWaffleFlag.",
    }
    assert expected == messages

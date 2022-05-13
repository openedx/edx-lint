"""Test annotations_check.py"""
# pylint: disable=toggle-non-boolean-default-value,toggle-empty-description,toggle-no-name,annotation-missing-token

from .pylint_test import run_pylint


def test_waffle_missing_toggle_annotation_check():
    source = """\
        DisablePragmaWaffleFlag(NAMESPACE, 'disable_pragma_for_annotation')  #pylint: disable=feature-toggle-needs-doc

        # .. toggle_name: annotated_flag
        WaffleFlag(NAMESPACE, 'annotated_flag')

        # .. toggle_name: course_waffle_annotated_flag
        CourseWaffleFlag(NAMESPACE, 'course_waffle_annotated_flag')

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


def test_code_annotations_checker():
    source = """
    # .. toggle_name: MYTOGGLE
    # .. toggle_name: MYTOGGLE
    """
    messages = run_pylint(source, "annotation-duplicate-token")
    expected = {
        "2:annotation-duplicate-token:found duplicate token '.. toggle_name:'"
    }
    assert expected == messages


def test_temporary_use_case_without_target_removal_date():
    source = """
    # .. toggle_name: MYTOGGLE
    # .. toggle_use_cases: temporary
    """
    messages = run_pylint(source, "toggle-missing-target-removal-date")
    expected = {
        "2:toggle-missing-target-removal-date:temporary feature toggle (MYTOGGLE) has no target removal date"
    }
    assert expected == messages


def test_empty_removal_date_on_permanent_use_case():
    source = """
    # .. toggle_name: MYTOGGLE
    # .. toggle_use_cases: open_edx
    """
    messages = run_pylint(source, "toggle-missing-target-removal-date")
    assert not messages


def test_toggle_with_empty_name():
    source = """
    # .. toggle_name:
    """
    messages = run_pylint(source, "toggle-no-name")
    expected = {
        "2:toggle-no-name:feature toggle has no name"
    }
    assert expected == messages


def test_toggle_with_empty_description():
    source = """
    # .. toggle_name: MYTOGGLE
    # .. toggle_description:
    """
    messages = run_pylint(source, "toggle-empty-description")
    expected = {
        "2:toggle-empty-description:feature toggle (MYTOGGLE) does not have a description"
    }
    assert expected == messages


def test_non_boolean_default_value():
    source = """
    # .. toggle_name: MYTOGGLE
    # .. toggle_default: something
    """
    messages = run_pylint(source, "toggle-non-boolean-default-value")
    expected = {
        "2:toggle-non-boolean-default-value:feature toggle (MYTOGGLE) default value must be boolean ('True' or 'False')"
    }
    assert expected == messages


def test_setting_boolean_default_value():
    source = """
    # .. setting_name: MYSETTING
    # .. setting_default: True
    """
    messages = run_pylint(source, "setting-boolean-default-value")
    expected = {
        "2:setting-boolean-default-value:setting annotation (MYSETTING) cannot have a boolean value"
    }
    assert expected == messages


def test_no_duplicate_annotation_errors():
    source = """
    # .. setting_default: something1
    # .. setting_description: something1
    x = 1

    # .. setting_name: MYTOGGLE2
    # .. setting_default: something2
    # .. setting_description: something2
    x = 2
    """
    messages = run_pylint(source, "annotation-missing-token")
    expected = {
        "2:annotation-missing-token:missing non-optional annotation: '.. setting_name:'"
    }
    assert expected == messages


def test_missing_annotation():
    source = """
    # .. toggle_name: MYTOGGLE1
    waffle1 = WaffleFlag('MYTOGGLE1')
    waffle2 = WaffleFlag('MYTOGGLE2')
    """
    messages = run_pylint(source, "toggle-missing-annotation")
    expected = {
        "4:toggle-missing-annotation:missing feature toggle annotation"
    }
    assert expected == messages


def test_missing_annotation_for_unnamed_toggle():
    source = """
    # annotated waffle flag
    # .. toggle_name: MYTOGGLE1
    waffle1 = CourseWaffleFlag()
    # unannotated waffle flag
    waffle2 = ExperimentWaffleFlag()
    """
    messages = run_pylint(source, "toggle-missing-annotation")
    expected = {
        "6:toggle-missing-annotation:missing feature toggle annotation"
    }
    assert expected == messages


def test_invalid_import_from_django_waffle():
    source = """
    from waffle import waffle_is_active
    import waffle
    """
    messages = run_pylint(source, "invalid-django-waffle-import")
    expected = {
        "2:invalid-django-waffle-import:invalid Django Waffle import",
        "3:invalid-django-waffle-import:invalid Django Waffle import",
    }
    assert expected == messages

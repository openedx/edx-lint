"""Tests for PiiAnnotationChecker (pii-invalid-no-pii-annotation / W7633).

Fires when a concrete Django model has ``.. no_pii:`` but still contains
PII fields.
"""

from .pylint_test import run_pylint

_ID = "pii-invalid-no-pii-annotation"


def _run(source):
    return run_pylint(source, _ID, "--pii-terms=email,username")


def _has(messages, marker):
    return any(m.startswith(f"{marker}:{_ID}:") for m in messages)


# -- basic detection ----------------------------------------------------------

def test_no_pii_docstring_with_pii_field():
    """.. no_pii: docstring + PII field fires on the class line."""
    source = """\
        class LearnerProfile(Model):
            '''
            .. no_pii: Stores only course metadata.
            '''
            course_id = None
            email = None                                #=A
    """
    messages = _run(source)
    assert _has(messages, "A")
    assert any("email" in m for m in messages)


def test_no_pii_multiple_pii_fields_single_message():
    """Multiple PII fields produce exactly one message per field."""
    source = """\
        class Profile(Model):
            '''.. no_pii:'''
            email = None                                #=A
            username = None                             #=B
            phone_number = None
    """
    messages = _run(source)
    assert len(messages) == 2
    assert _has(messages, "A")
    assert _has(messages, "B")


def test_no_pii_with_non_pii_fields_ok():
    """.. no_pii: with genuinely non-PII fields does not fire."""
    source = """\
        class CourseGrade(Model):
            '''.. no_pii:'''
            is_passing = True
            percent = 0.0
    """
    assert not _run(source)


def test_class_without_annotation_not_checked():
    """Model with PII fields but no annotation is out of scope."""
    source = """\
        class BadModel(Model):
            email = None
            username = None
    """
    assert not _run(source)


def test_pii_annotated_class_not_checked():
    """Model with .. pii: annotation and PII fields is correct — no warning."""
    source = """\
        class UserProfile(Model):
            '''
            .. pii: Stores learner email.
            .. pii_types: email_address
            .. pii_retirement: local_api
            '''
            email = None
    """
    assert not _run(source)


def test_no_pii_instance_attr_in_method_flagged():
    """self.username = ... inside __init__ of a .. no_pii: model fires."""
    source = """\
        class UserData(Model):
            '''.. no_pii:'''
            def __init__(self, data):
                self.username = data.username           #=A
                self.is_active = data.active
    """
    messages = _run(source)
    assert _has(messages, "A")
    assert any("self.username" in m for m in messages)


def test_no_pii_annotated_instance_attr_in_method_flagged():
    """self.email: str = ... inside method of a .. no_pii: model fires."""
    source = """\
        class UserData(Model):
            '''.. no_pii:'''
            def __init__(self, value):
                self.email: str = value                #=A
    """
    messages = _run(source)
    assert _has(messages, "A")
    assert any("self.email" in m for m in messages)


def test_no_pii_annotated_assignment_flagged():
    """email: str = '' (AnnAssign) on a .. no_pii: model fires."""
    source = """\
        class Profile(Model):
            '''.. no_pii:'''
            email: str = ""                             #=A
    """
    assert _has(_run(source), "A")


def test_no_pii_inline_disable_suppresses():
    """Inline disable for pii-invalid-no-pii-annotation suppresses the rule."""
    source = """\
        class Profile(Model):
            '''.. no_pii:'''
            email = None  # pylint: disable=pii-invalid-no-pii-annotation
    """
    assert not _run(source)


# -- model eligibility (mirrors django_find_annotations scope) ----------------

def test_plain_python_class_not_checked():
    """Plain Python class (not a Model subclass) is not in scope."""
    source = """\
        class ServiceHelper:
            '''.. no_pii:'''
            email = None
            username = None
    """
    assert not _run(source)


def test_abstract_django_model_not_checked():
    """Abstract Django model (Meta.abstract = True) is not checked."""
    source = """\
        class AbstractBase(Model):
            '''.. no_pii:'''
            email = None
            class Meta:
                abstract = True
    """
    assert not _run(source)


def test_proxy_django_model_not_checked():
    """Proxy Django model (Meta.proxy = True) is not checked."""
    source = """\
        class ConcreteModel(Model):
            '''.. no_pii:'''
            course_id = None

        class ProxyView(ConcreteModel):
            '''.. no_pii:'''
            email = None
            class Meta:
                proxy = True
    """
    assert not _run(source)


def test_concrete_model_indirect_inheritance_checked():
    """Concrete model inheriting Model indirectly is still checked."""
    source = """\
        class TimeStampedModel(Model):
            '''.. no_pii:'''
            course_id = None

        class CourseEnrollment(TimeStampedModel):
            '''.. no_pii:'''
            username = None                             #=A
    """
    messages = _run(source)
    assert _has(messages, "A")
    assert any("username" in m for m in messages)


def test_non_model_class_with_pii_but_no_annotation_ignored():
    """Plain class with PII fields and no annotation — not checked."""
    source = """\
        class DataTransferObject:
            email = None
            username = None
    """
    assert not _run(source)

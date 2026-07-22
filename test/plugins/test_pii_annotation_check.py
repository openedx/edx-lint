"""Tests for PiiAnnotationChecker (pii-invalid-no-pii-annotation / W7633).

Fires when a concrete Django model has ``.. no_pii:`` but still contains PII fields.
"""

from .pylint_test import run_pylint

_ID = "pii-invalid-no-pii-annotation"


def _run(source):
    return run_pylint(source, _ID)


def _has(messages, marker):
    return any(m.startswith(f"{marker}:{_ID}:") for m in messages)


# -- basic detection ----------------------------------------------------------

def test_no_pii_docstring_with_pii_field():
    """.. no_pii: docstring + PII field fires on the class line."""
    source = """\
        class LearnerProfile(Model):                    #=A
            '''
            .. no_pii: Stores only course metadata.
            '''
            course_id = None
            email = None
    """
    messages = _run(source)
    assert _has(messages, "A")
    assert any("email" in m for m in messages)


def test_no_pii_comment_above_class():
    """# .. no_pii: comment above class with PII field fires."""
    source = """\
        # .. no_pii:
        class CourseEnrollment(Model):                  #=A
            course_id = None
            username = None
    """
    messages = _run(source)
    assert _has(messages, "A")
    assert any("username" in m for m in messages)


def test_no_pii_multiple_pii_fields_single_message():
    """Multiple PII fields produce exactly one message listing all."""
    source = """\
        class Profile(Model):                           #=A
            '''.. no_pii:'''
            email = None
            username = None
            phone_number = None
    """
    messages = _run(source)
    assert len(messages) == 1
    msg = list(messages)[0]
    assert "email" in msg and "username" in msg and "phone_number" not in msg


def test_no_pii_with_only_safe_fields_ok():
    """.. no_pii: with only safe surrogate keys does not fire."""
    source = """\
        class Enrollment(Model):
            '''.. no_pii:'''
            course_id = None
            user_id = None
    """
    assert not _run(source)


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
    """Model with PII fields but no annotation is out of scope for this rule."""
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
        class UserData(Model):                          #=A
            '''.. no_pii:'''
            def __init__(self, data):
                self.username = data.username
                self.is_active = data.active
    """
    messages = _run(source)
    assert _has(messages, "A")
    assert any("self.username" in m for m in messages)


def test_no_pii_annotated_assignment_flagged():
    """email: str = '' (AnnAssign) on a .. no_pii: model fires."""
    source = """\
        class Profile(Model):                           #=A
            '''.. no_pii:'''
            email: str = ""
    """
    assert _has(_run(source), "A")


def test_no_pii_inline_disable_suppresses():
    """Inline pylint:disable=pii-invalid-no-pii-annotation suppresses the rule."""
    source = """\
        class Profile(Model):  # pylint: disable=pii-invalid-no-pii-annotation
            '''.. no_pii:'''
            email = None
    """
    assert not _run(source)


def test_decorator_between_comment_annotation_and_class():
    """Decorator between # .. no_pii: comment and class is still detected."""
    source = """\
        # .. no_pii:
        @some_decorator
        class Enrollment(Model):                        #=A
            username = None
    """
    assert _has(_run(source), "A")


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

        class CourseEnrollment(TimeStampedModel):       #=A
            '''.. no_pii:'''
            username = None
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

"""Tests for pii_annotation_check.py (PiiAnnotationChecker).

Covers the ``pii-invalid-no-pii-annotation`` rule (W7633) emitted by the
``pii-annotation-checker`` checker.

This rule fires when a concrete (non-abstract, non-proxy) Django model class
is annotated with ``.. no_pii:`` yet still contains fields or instance
attributes whose names match the configured PII terms.

Message format produced by run_pylint:
    "{line_marker}:{symbol}:{message_text}"

e.g.  "A:pii-invalid-no-pii-annotation:Django model 'Profile' is annotated ..."

We test for exact symbol presence using substring matching on the
marker:symbol prefix.
"""

from .pylint_test import run_pylint


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_ANN_ID = "pii-invalid-no-pii-annotation"


def _run(source):
    """Run pylint checking only pii-invalid-no-pii-annotation."""
    return run_pylint(source, _ANN_ID)


def _has(messages, marker, symbol):
    """Return True if messages contains one with the given marker and symbol."""
    prefix = f"{marker}:{symbol}:"
    return any(m.startswith(prefix) for m in messages)


# ===========================================================================
# pii-invalid-no-pii-annotation: basic detection
# ===========================================================================


def test_no_pii_docstring_with_pii_field():
    """Django model with ``.. no_pii:`` docstring and a PII field fires on the class line."""
    source = """\
        class LearnerProfile(Model):                    #=A
            '''
            .. no_pii: Stores only course metadata.
            '''
            course_id = None
            email = None
    """
    messages = _run(source)
    assert _has(messages, "A", _ANN_ID)
    assert any("email" in m for m in messages)


def test_no_pii_comment_above_class():
    """``# .. no_pii:`` comment above a Django model with PII field fires."""
    source = """\
        # .. no_pii:
        class CourseEnrollment(Model):                  #=A
            course_id = None
            username = None
    """
    messages = _run(source)
    assert _has(messages, "A", _ANN_ID)
    assert any("username" in m for m in messages)


def test_no_pii_multiple_pii_fields_single_message():
    """Multiple PII fields on a Django model produce exactly one message listing all."""
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
    assert "email" in msg
    assert "username" in msg
    assert "phone_number" in msg


def test_no_pii_with_only_safe_fields_ok():
    """Django model with ``.. no_pii:`` and only safe surrogate keys does not fire."""
    source = """\
        class Enrollment(Model):
            '''.. no_pii:'''
            course_id = None
            user_id = None
            block_id = None
    """
    messages = _run(source)
    assert not messages


def test_no_pii_with_non_pii_fields_ok():
    """Django model with ``.. no_pii:`` and genuinely non-PII fields is fine."""
    source = """\
        class CourseGrade(Model):
            '''.. no_pii:'''
            is_passing = True
            percent = 0.0
            created = None
    """
    messages = _run(source)
    assert not messages


def test_class_without_annotation_not_checked():
    """A Django model with PII fields but NO annotation is out of scope for this rule."""
    source = """\
        class BadModel(Model):
            email = None
            username = None
    """
    messages = _run(source)
    assert not messages


def test_pii_annotated_class_not_checked():
    """A Django model with ``.. pii:`` annotation and PII fields is correct — no warning."""
    source = """\
        class UserProfile(Model):
            '''
            .. pii: Stores learner email.
            .. pii_types: email_address
            .. pii_retirement: local_api
            '''
            email = None
    """
    messages = _run(source)
    assert not messages


def test_no_pii_instance_attr_in_method_flagged():
    """``self.phone_number = ...`` inside __init__ of a Django model is caught."""
    source = """\
        class UserData(Model):                          #=A
            '''.. no_pii:'''
            def __init__(self, data):
                self.phone_number = data.phone
                self.is_active = data.active
    """
    messages = _run(source)
    assert _has(messages, "A", _ANN_ID)
    assert any("self.phone_number" in m for m in messages)


def test_no_pii_annotated_assignment_flagged():
    """``email: str = ""`` (AnnAssign) on a Django model is caught."""
    source = """\
        class Profile(Model):                           #=A
            '''.. no_pii:'''
            email: str = ""
    """
    messages = _run(source)
    assert _has(messages, "A", _ANN_ID)


def test_no_pii_inline_disable_suppresses():
    """``# pylint: disable=pii-invalid-no-pii-annotation`` suppresses the rule."""
    source = """\
        class Profile(Model):  # pylint: disable=pii-invalid-no-pii-annotation
            '''.. no_pii:'''
            email = None
    """
    messages = _run(source)
    assert not messages


def test_decorator_between_comment_annotation_and_class():
    """A decorator between the ``# .. no_pii:`` comment and a Django model class is still detected."""
    source = """\
        # .. no_pii:
        @some_decorator
        class Enrollment(Model):                        #=A
            username = None
    """
    messages = _run(source)
    assert _has(messages, "A", _ANN_ID)


# ===========================================================================
# pii-invalid-no-pii-annotation: Django model eligibility
# (mirrors DjangoSearch.requires_annotations() from code_annotations)
# ===========================================================================


def test_plain_python_class_not_checked():
    """A plain Python class (not a Django Model subclass) with ``.. no_pii:`` and
    PII fields is NOT flagged — only Django models are in scope."""
    source = """\
        class ServiceHelper:
            '''.. no_pii:'''
            email = None
            username = None
    """
    messages = _run(source)
    assert not messages


def test_abstract_django_model_not_checked():
    """An abstract Django model (``abstract = True`` in Meta) is NOT checked.

    ``django_find_annotations`` skips abstract models because they never
    create database tables; this checker mirrors that behaviour.
    """
    source = """\
        class AbstractBase(Model):
            '''.. no_pii:'''
            email = None
            class Meta:
                abstract = True
    """
    messages = _run(source)
    assert not messages


def test_proxy_django_model_not_checked():
    """A proxy Django model (``proxy = True`` in Meta) is NOT checked.

    ``django_find_annotations`` skips proxy models because they share
    the database table of their concrete parent; this checker mirrors
    that behaviour.
    """
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
    messages = _run(source)
    # ConcreteModel is concrete and has no PII — should not fire.
    # ProxyView is a proxy — should not fire.
    assert not messages


def test_concrete_model_indirect_inheritance_checked():
    """A concrete model that inherits from Model indirectly (through a custom
    base) is still checked — mirroring django_find_annotations coverage."""
    source = """\
        class TimeStampedModel(Model):
            '''.. no_pii:'''
            course_id = None

        class CourseEnrollment(TimeStampedModel):       #=A
            '''.. no_pii:'''
            username = None
    """
    messages = _run(source)
    # CourseEnrollment is concrete and has a PII field — should fire.
    assert _has(messages, "A", _ANN_ID)
    assert any("username" in m for m in messages)


def test_non_model_class_with_pii_but_no_annotation_ignored():
    """A plain class with PII fields and NO annotation — not a model, not checked."""
    source = """\
        class DataTransferObject:
            email = None
            username = None
    """
    messages = _run(source)
    assert not messages

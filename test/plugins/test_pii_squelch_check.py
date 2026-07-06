"""Tests for pii_squelch_check.py (PiiMissingSquelchChecker).

Covers the three missing-squelch-guard rules under checker name ``pii-missing-squelch``:

    pii-missing-squelch        (W7630)
    pii-missing-squelch      (W7631)
    pii-missing-squelch  (W7632)

Scope: checks only fire inside annotation-eligible Django model methods.
  - Models with ``.. no_pii:``       → entirely skipped (safe, no squelch check).
  - Models with ``.. pii:`` or none  → checked: methods must use SQUELCH guard.
  - Standalone functions / module-level code → entirely out of scope.

Every test source defines a top-level ``class Model: pass`` stub so the
checker's raw-AST BFS can recognise subclasses without Django being installed.

Message format produced by run_pylint:
    "{line_marker}:{symbol}:{message_text}"
e.g.  "A:pii-missing-squelch:Log call exposes PII term 'email' without ..."
"""

import pytest

from .pylint_test import run_pylint


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run(source, *msg_ids):
    """Run pylint and return the set of messages for the given msg_ids."""
    return run_pylint(source, ",".join(msg_ids))


def _has(messages, marker, symbol):
    """Return True if messages contains one with the given marker and symbol."""
    prefix = f"{marker}:{symbol}:"
    return any(m.startswith(prefix) for m in messages)


ALL_SQUELCH_IDS = ("pii-missing-squelch", "pii-missing-squelch", "pii-missing-squelch")


# ===========================================================================
# pii-missing-squelch — inside a .. pii: annotated Django model method
# ===========================================================================


def test_pii_in_log_bare_name():
    """Bare PII variable logged inside a pii model method without guard fires."""
    source = """\
import logging
log = logging.getLogger(__name__)
class Model:
    pass
class UserModel(Model):
    '''.. pii: Stores user PII.'''
    def notify(self):
        log.info("user: %s", email)          #=A
"""
    messages = _run(source, "pii-missing-squelch")
    assert _has(messages, "A", "pii-missing-squelch")


def test_pii_in_log_fstring():
    """PII inside an f-string logged in a pii model method fires."""
    source = """\
import logging
log = logging.getLogger(__name__)
class Model:
    pass
class UserModel(Model):
    '''.. pii: Stores user PII.'''
    def notify(self):
        log.warning(f"email: {email}")       #=A
"""
    messages = _run(source, "pii-missing-squelch")
    assert _has(messages, "A", "pii-missing-squelch")


def test_pii_in_log_attribute_access():
    """Attribute access self.email logged in a pii model method fires."""
    source = """\
import logging
log = logging.getLogger(__name__)
class Model:
    pass
class UserModel(Model):
    '''.. pii: Stores user PII.'''
    email = None
    def notify(self):
        log.error("failed: %s", self.email)  #=A
"""
    messages = _run(source, "pii-missing-squelch")
    assert _has(messages, "A", "pii-missing-squelch")


def test_pii_in_log_nested_in_dict():
    """PII inside a dict value logged in a pii model method fires."""
    source = """\
import logging
log = logging.getLogger(__name__)
class Model:
    pass
class UserModel(Model):
    '''.. pii: Stores user PII.'''
    def notify(self):
        log.info("%s", {"email": email})     #=A
"""
    messages = _run(source, "pii-missing-squelch")
    assert _has(messages, "A", "pii-missing-squelch")


def test_pii_in_log_string_literal_not_flagged():
    """A literal log message mentioning a PII word does NOT fire inside a pii model.

    Only actual PII variable/attribute references are flagged — string
    literals that name a PII field are message text, not PII values.
    """
    source = """\
import logging
log = logging.getLogger(__name__)
class Model:
    pass
class UserModel(Model):
    '''.. pii: Stores user PII.'''
    def notify(self):
        log.info("user email: unknown")
        log.info("Email field is required")
        log.info("Invalid email format")
"""
    messages = _run(source, "pii-missing-squelch")
    assert not messages


def test_pii_in_log_guarded_by_bare_flag():
    """PII log inside ``if not SQUELCH_PII_IN_LOGS:`` in a pii model is allowed."""
    source = """\
import logging
SQUELCH_PII_IN_LOGS = True
log = logging.getLogger(__name__)
class Model:
    pass
class UserModel(Model):
    '''.. pii: Stores user PII.'''
    def notify(self):
        if not SQUELCH_PII_IN_LOGS:
            log.info("email=%s", email)
"""
    messages = _run(source, "pii-missing-squelch")
    assert not messages


def test_pii_in_log_guarded_by_flag_positive():
    """PII log in else-branch of ``if SQUELCH_PII_IN_LOGS:`` in a pii model is allowed."""
    source = """\
import logging
SQUELCH_PII_IN_LOGS = True
log = logging.getLogger(__name__)
class Model:
    pass
class UserModel(Model):
    '''.. pii: Stores user PII.'''
    def notify(self):
        if SQUELCH_PII_IN_LOGS:
            log.info("user_id=%s", user_id)
        else:
            log.info("email=%s", email)
"""
    messages = _run(source, "pii-missing-squelch")
    assert not messages


def test_pii_in_log_guarded_by_settings_features_subscript():
    """settings.FEATURES['SQUELCH_PII_IN_LOGS'] guard inside a pii model is recognised."""
    source = """\
import logging
log = logging.getLogger(__name__)
class Model:
    pass
class UserModel(Model):
    '''.. pii: Stores user PII.'''
    def notify(self):
        if not settings.FEATURES['SQUELCH_PII_IN_LOGS']:
            log.info("email=%s", email)
"""
    messages = _run(source, "pii-missing-squelch")
    assert not messages


def test_pii_in_log_guarded_by_settings_features_get():
    """settings.FEATURES.get('SQUELCH_PII_IN_LOGS') guard inside a pii model is recognised."""
    source = """\
import logging
log = logging.getLogger(__name__)
class Model:
    pass
class UserModel(Model):
    '''.. pii: Stores user PII.'''
    def notify(self):
        if not settings.FEATURES.get('SQUELCH_PII_IN_LOGS'):
            log.info("username=%s", username)
"""
    messages = _run(source, "pii-missing-squelch")
    assert not messages


def test_pii_in_log_guarded_by_settings_attribute():
    """settings.SQUELCH_PII_IN_LOGS guard inside a pii model is recognised."""
    source = """\
import logging
log = logging.getLogger(__name__)
class Model:
    pass
class UserModel(Model):
    '''.. pii: Stores user PII.'''
    def notify(self):
        if not settings.SQUELCH_PII_IN_LOGS:
            log.info("phone=%s", phone_number)
"""
    messages = _run(source, "pii-missing-squelch")
    assert not messages


def test_pii_in_log_safe_function_wrapping():
    """PII wrapped in redact() inside a pii model is not flagged."""
    source = """\
import logging
log = logging.getLogger(__name__)
class Model:
    pass
class UserModel(Model):
    '''.. pii: Stores user PII.'''
    def notify(self):
        log.info("value=%s", redact(email))
"""
    messages = _run(source, "pii-missing-squelch")
    assert not messages


def test_pii_in_log_safe_key_not_flagged():
    """user_id is a safe surrogate key — not flagged even inside a pii model."""
    source = """\
import logging
log = logging.getLogger(__name__)
class Model:
    pass
class EnrollmentModel(Model):
    '''.. pii: Stores enrollment data.'''
    def log_action(self):
        log.info("enrolled user_id=%s", user_id)
"""
    messages = _run(source, "pii-missing-squelch")
    assert not messages


def test_pii_in_log_non_pii_name_not_flagged():
    """Completely unrelated variable names inside a pii model do not fire."""
    source = """\
import logging
log = logging.getLogger(__name__)
class Model:
    pass
class CourseModel(Model):
    '''.. pii: Stores course data.'''
    def log_action(self):
        log.info("enrolled course: %s", course_data)
"""
    messages = _run(source, "pii-missing-squelch")
    assert not messages


def test_pii_in_log_multiple_levels():
    """All standard log levels inside a pii model trigger the rule."""
    for method in ("debug", "info", "warning", "error", "critical", "exception"):
        source = (
            "import logging\n"
            "log = logging.getLogger(__name__)\n"
            "class Model:\n"
            "    pass\n"
            "class UserModel(Model):\n"
            "    '''.. pii: Stores user PII.'''\n"
            "    def notify(self):\n"
            f"        log.{method}('msg: %s', email)     #=A\n"
        )
        messages = _run(source, "pii-missing-squelch")
        assert _has(messages, "A", "pii-missing-squelch"), (
            f"Expected pii-missing-squelch for log.{method} inside a pii model"
        )


def test_pii_in_log_inline_disable_suppresses():
    """Inline ``# pylint: disable=pii-missing-squelch`` suppresses the warning inside a model."""
    source = """\
import logging
log = logging.getLogger(__name__)
class Model:
    pass
class UserModel(Model):
    '''.. pii: Stores user PII.'''
    def notify(self):
        log.info("email=%s", email)  # pylint: disable=pii-missing-squelch
"""
    messages = _run(source, "pii-missing-squelch")
    assert not messages


# ===========================================================================
# OEP-0030 new terms — job title, social media, website
# ===========================================================================


def test_pii_in_log_job_title_fires():
    """job_title inside a pii model fires (OEP-0030: 'Job title' is PII)."""
    source = """\
import logging
log = logging.getLogger(__name__)
class Model:
    pass
class ProfileModel(Model):
    '''.. pii: Stores learner profile PII.'''
    def log_profile(self):
        log.info("user info: %s", job_title)     #=A
"""
    messages = _run(source, "pii-missing-squelch")
    assert _has(messages, "A", "pii-missing-squelch")


def test_pii_in_log_title_attribute_fires():
    """self.title inside a pii model fires (OEP-0030: 'Job title' is PII)."""
    source = """\
import logging
log = logging.getLogger(__name__)
class Model:
    pass
class ProfileModel(Model):
    '''.. pii: Stores learner profile PII.'''
    title = None
    def log_profile(self):
        log.info("user: %s", self.title)         #=A
"""
    messages = _run(source, "pii-missing-squelch")
    assert _has(messages, "A", "pii-missing-squelch")


def test_pii_in_log_social_fires():
    """social_link inside a pii model fires (OEP-0030: social media is PII)."""
    source = """\
import logging
log = logging.getLogger(__name__)
class Model:
    pass
class ProfileModel(Model):
    '''.. pii: Stores learner profile PII.'''
    def log_profile(self):
        log.info("link: %s", social_link)        #=A
"""
    messages = _run(source, "pii-missing-squelch")
    assert _has(messages, "A", "pii-missing-squelch")


def test_pii_in_log_website_fires():
    """user_website inside a pii model fires (OEP-0030: website is PII)."""
    source = """\
import logging
log = logging.getLogger(__name__)
class Model:
    pass
class ProfileModel(Model):
    '''.. pii: Stores learner profile PII.'''
    def log_profile(self):
        log.info("site: %s", user_website)       #=A
"""
    messages = _run(source, "pii-missing-squelch")
    assert _has(messages, "A", "pii-missing-squelch")


# ===========================================================================
# Non-OEP-0030 terms: token and secret never fire
# ===========================================================================


def test_token_not_flagged_not_in_oep30():
    """'token' is not an OEP-0030 PII field — does not fire inside a model."""
    source = """\
import logging
log = logging.getLogger(__name__)
class Model:
    pass
class SessionModel(Model):
    '''.. pii: Stores session data.'''
    def log_action(self):
        log.info("auth: %s", access_token)
"""
    messages = _run(source, "pii-missing-squelch")
    assert not messages


def test_secret_not_flagged_not_in_oep30():
    """'secret' is not an OEP-0030 PII field — does not fire inside a model."""
    source = """\
import logging
log = logging.getLogger(__name__)
class Model:
    pass
class ApiModel(Model):
    '''.. pii: Stores API data.'''
    def log_action(self):
        log.info("key: %s", api_secret)
"""
    messages = _run(source, "pii-missing-squelch")
    assert not messages


# ===========================================================================
# pii-missing-squelch — inside a .. pii: annotated Django model method
# ===========================================================================


def test_pii_in_print_bare():
    """print(pii_var) inside a pii model method fires."""
    source = """\
class Model:
    pass
class UserModel(Model):
    '''.. pii: Stores user PII.'''
    def display(self):
        print(username)                          #=A
"""
    messages = _run(source, "pii-missing-squelch")
    assert _has(messages, "A", "pii-missing-squelch")


def test_pii_in_print_fstring():
    """print() with PII in an f-string inside a pii model fires."""
    source = """\
class Model:
    pass
class UserModel(Model):
    '''.. pii: Stores user PII.'''
    def display(self):
        print(f"user: {username}")               #=A
"""
    messages = _run(source, "pii-missing-squelch")
    assert _has(messages, "A", "pii-missing-squelch")


def test_pii_in_print_guarded():
    """print() with PII inside SQUELCH guard in a pii model does not fire."""
    source = """\
SQUELCH_PII_IN_LOGS = True
class Model:
    pass
class UserModel(Model):
    '''.. pii: Stores user PII.'''
    def display(self):
        if not SQUELCH_PII_IN_LOGS:
            print(username)
"""
    messages = _run(source, "pii-missing-squelch")
    assert not messages


def test_pii_in_stdout_write():
    """sys.stdout.write() with PII inside a pii model fires."""
    source = """\
import sys
class Model:
    pass
class ReportModel(Model):
    '''.. pii: Stores report PII.'''
    def export(self):
        sys.stdout.write(email)                  #=A
"""
    messages = _run(source, "pii-missing-squelch")
    assert _has(messages, "A", "pii-missing-squelch")


def test_pii_in_stderr_write():
    """sys.stderr.write() with PII inside a pii model fires."""
    source = """\
import sys
class Model:
    pass
class ReportModel(Model):
    '''.. pii: Stores report PII.'''
    def export(self):
        sys.stderr.write(username)               #=A
"""
    messages = _run(source, "pii-missing-squelch")
    assert _has(messages, "A", "pii-missing-squelch")


def test_pii_in_print_safe_key_not_flagged():
    """Printing user_id (safe surrogate key) inside a pii model does not fire."""
    source = """\
class Model:
    pass
class EnrollmentModel(Model):
    '''.. pii: Stores enrollment data.'''
    def display(self):
        print(user_id)
"""
    messages = _run(source, "pii-missing-squelch")
    assert not messages


# ===========================================================================
# pii-missing-squelch — inside a .. pii: annotated Django model method
# ===========================================================================


def test_pii_in_exception_bare():
    """raise ValueError(pii_var) inside a pii model fires."""
    source = """\
class Model:
    pass
class PaymentModel(Model):
    '''.. pii: Stores payment PII.'''
    def validate(self):
        raise ValueError(email)                  #=A
"""
    messages = _run(source, "pii-missing-squelch")
    assert _has(messages, "A", "pii-missing-squelch")


def test_pii_in_exception_fstring():
    """raise ValueError(f\"...{pii}...\") inside a pii model fires."""
    source = """\
class Model:
    pass
class PaymentModel(Model):
    '''.. pii: Stores payment PII.'''
    def validate(self):
        raise ValueError(f"bad username: {username}")   #=A
"""
    messages = _run(source, "pii-missing-squelch")
    assert _has(messages, "A", "pii-missing-squelch")


def test_pii_in_exception_guarded():
    """Exception with PII inside SQUELCH guard in a pii model does not fire."""
    source = """\
SQUELCH_PII_IN_LOGS = True
class Model:
    pass
class PaymentModel(Model):
    '''.. pii: Stores payment PII.'''
    def validate(self):
        if not SQUELCH_PII_IN_LOGS:
            raise ValueError(email)
"""
    messages = _run(source, "pii-missing-squelch")
    assert not messages


def test_pii_in_exception_safe_function():
    """Exception with PII wrapped in redact() inside a pii model does not fire."""
    source = """\
class Model:
    pass
class PaymentModel(Model):
    '''.. pii: Stores payment PII.'''
    def validate(self):
        raise ValueError(redact(email))
"""
    messages = _run(source, "pii-missing-squelch")
    assert not messages


def test_pii_in_exception_safe_key():
    """Exception with safe surrogate key (user_id) inside a pii model does not fire."""
    source = """\
class Model:
    pass
class PaymentModel(Model):
    '''.. pii: Stores payment PII.'''
    def validate(self):
        raise ValueError(user_id)
"""
    messages = _run(source, "pii-missing-squelch")
    assert not messages


def test_non_sink_call_not_flagged():
    """An arbitrary function call with PII inside a pii model is not flagged."""
    source = """\
class Model:
    pass
class UserModel(Model):
    '''.. pii: Stores user PII.'''
    def process(self):
        some_function(email)
"""
    messages = _run(source, *ALL_SQUELCH_IDS)
    assert not messages


# ===========================================================================
# Scope: standalone / module-level code is OUT OF SCOPE for squelch checks
# ===========================================================================


def test_standalone_function_not_checked():
    """Logs inside a standalone function (not inside any model) are NOT checked.

    The squelch-guard check only applies to methods inside Django model
    classes.  Code outside a model is out of OEP-0030 annotation scope.
    """
    source = """\
import logging
log = logging.getLogger(__name__)
def standalone_helper(email):
    log.info(email)
"""
    messages = _run(source, "pii-missing-squelch")
    assert not messages


def test_module_level_print_not_checked():
    """A print() at module level is NOT checked — only model methods are in scope."""
    source = """\
print(username)
"""
    messages = _run(source, "pii-missing-squelch")
    assert not messages


def test_module_level_raise_not_checked():
    """A raise at module level is NOT checked — only model methods are in scope."""
    source = """\
raise ValueError(email)
"""
    messages = _run(source, "pii-missing-squelch")
    assert not messages


# ===========================================================================
# Scope: .. no_pii: models are completely skipped for squelch checks
# ===========================================================================


def test_squelch_exempt_in_no_pii_model():
    """Logs inside a model annotated with .. no_pii: are entirely skipped.

    The .. no_pii: annotation declares the model safe — no squelch guard
    is required even if PII-named attributes are passed to a log sink.
    """
    source = """\
import logging
log = logging.getLogger(__name__)
class Model:
    pass
class SafeModel(Model):
    '''.. no_pii: This model holds no PII.'''
    email = None
    def log_something(self):
        log.info(self.email)
"""
    messages = _run(source, "pii-missing-squelch")
    assert not messages


def test_squelch_enforced_in_pii_model():
    """Unguarded PII log inside a .. pii: annotated model fires."""
    source = """\
import logging
log = logging.getLogger(__name__)
class Model:
    pass
class UnsafeModel(Model):
    '''.. pii: Stores user PII.'''
    email = None
    def log_something(self):
        log.info(self.email)                     #=A
"""
    messages = _run(source, "pii-missing-squelch")
    assert _has(messages, "A", "pii-missing-squelch")


def test_squelch_enforced_in_unannotated_model():
    """Unguarded PII log inside a model with NO annotation also fires.

    A model without any PII annotation has not been declared safe and has
    not been declared PII-aware; the checker conservatively flags it.
    """
    source = """\
import logging
log = logging.getLogger(__name__)
class Model:
    pass
class UnannotatedModel(Model):
    email = None
    def log_something(self):
        log.info(self.email)                     #=A
"""
    messages = _run(source, "pii-missing-squelch")
    assert _has(messages, "A", "pii-missing-squelch")


def test_squelch_enforced_guarded_in_pii_model():
    """Properly guarded PII log inside a .. pii: model does NOT fire."""
    source = """\
import logging
SQUELCH_PII_IN_LOGS = True
log = logging.getLogger(__name__)
class Model:
    pass
class UnsafeModel(Model):
    '''.. pii: Stores user PII.'''
    email = None
    def log_something(self):
        if not SQUELCH_PII_IN_LOGS:
            log.info(self.email)
"""
    messages = _run(source, "pii-missing-squelch")
    assert not messages

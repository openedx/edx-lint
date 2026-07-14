"""Tests for PiiMissingSquelchChecker (pii-missing-squelch / W7630).

Checks fire only inside non-abstract, non-proxy Django model methods.
Models annotated ``.. no_pii:`` are skipped; all others are enforced.
"""

from .pylint_test import run_pylint

_ID = "pii-missing-squelch"


def _run(source):
    return run_pylint(source, _ID)


def _has(messages, marker):
    return any(m.startswith(f"{marker}:{_ID}:") for m in messages)


# -- pii-in-log ---------------------------------------------------------------

def test_pii_in_log_bare_name():
    """Unguarded PII variable in log.info fires."""
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
    assert _has(_run(source), "A")


def test_pii_in_log_fstring():
    """PII inside an f-string in a log call fires."""
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
    assert _has(_run(source), "A")


def test_pii_in_log_attribute_access():
    """self.email passed to log fires."""
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
    assert _has(_run(source), "A")


def test_pii_in_log_nested_in_dict():
    """PII inside a dict value passed to log fires."""
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
    assert _has(_run(source), "A")


def test_pii_in_log_string_literal_not_flagged():
    """String literals containing PII words are not flagged (not actual PII values)."""
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
"""
    assert not _run(source)


def test_pii_in_log_guarded_by_bare_flag():
    """PII log inside ``if not SQUELCH_PII_IN_LOGS:`` is safe."""
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
    assert not _run(source)


def test_pii_in_log_guarded_by_flag_positive():
    """PII log in else-branch of ``if SQUELCH_PII_IN_LOGS:`` is safe."""
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
    assert not _run(source)


def test_pii_in_log_guarded_by_settings_features_subscript():
    """settings.FEATURES['SQUELCH_PII_IN_LOGS'] guard is recognised."""
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
    assert not _run(source)


def test_pii_in_log_guarded_by_settings_features_get():
    """settings.FEATURES.get('SQUELCH_PII_IN_LOGS') guard is recognised."""
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
    assert not _run(source)


def test_pii_in_log_guarded_by_settings_attribute():
    """settings.SQUELCH_PII_IN_LOGS guard is recognised."""
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
    assert not _run(source)


def test_pii_in_log_safe_function_wrapping():
    """PII wrapped in redact() is not flagged."""
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
    assert not _run(source)


def test_pii_in_log_safe_key_not_flagged():
    """Surrogate key user_id is not flagged."""
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
    assert not _run(source)


def test_pii_in_log_non_pii_name_not_flagged():
    """Non-PII variable names are not flagged."""
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
    assert not _run(source)


def test_pii_in_log_multiple_levels():
    """All standard log levels fire inside a pii model."""
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
        assert _has(_run(source), "A"), f"Expected pii-missing-squelch for log.{method}"


def test_pii_in_log_inline_disable_suppresses():
    """Inline pylint:disable=pii-missing-squelch suppresses the warning."""
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
    assert not _run(source)


# -- OEP-0030 extended terms --------------------------------------------------

def test_pii_in_log_job_title_fires():
    """job_title fires (OEP-0030 PII term)."""
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
    assert _has(_run(source), "A")


def test_pii_in_log_social_link_fires():
    """social_link fires (OEP-0030 PII term — explicit form)."""
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
    assert _has(_run(source), "A")


def test_pii_in_log_profile_image_fires():
    """profile_image fires (OEP-0030 PII term — explicit form)."""
    source = """\
import logging
log = logging.getLogger(__name__)
class Model:
    pass
class ProfileModel(Model):
    '''.. pii: Stores learner profile PII.'''
    profile_image = None
    def log_profile(self):
        log.info("img: %s", self.profile_image)  #=A
"""
    assert _has(_run(source), "A")


def test_pii_in_log_ip_address_fires():
    """ip_address fires (OEP-0030 PII term — explicit form)."""
    source = """\
import logging
log = logging.getLogger(__name__)
class Model:
    pass
class SessionModel(Model):
    '''.. pii: Stores session PII.'''
    ip_address = None
    def log_session(self):
        log.info("ip: %s", self.ip_address)      #=A
"""
    assert _has(_run(source), "A")


# -- Curated exclusions: formerly-generic terms no longer fire by default -----

def test_bare_name_not_flagged():
    """self.name inside a PII model does NOT fire — 'name' removed from defaults."""
    source = """\
import logging
log = logging.getLogger(__name__)
class Model:
    pass
class UserModel(Model):
    '''.. pii: Stores user PII.'''
    name = None
    def log_action(self):
        log.info("item: %s", self.name)
"""
    assert not _run(source)


def test_bare_title_not_flagged():
    """self.title inside a PII model does NOT fire — bare 'title' removed from defaults."""
    source = """\
import logging
log = logging.getLogger(__name__)
class Model:
    pass
class ProfileModel(Model):
    '''.. pii: Stores learner profile PII.'''
    title = None
    def log_profile(self):
        log.info("user: %s", self.title)
"""
    assert not _run(source)


def test_bare_image_not_flagged():
    """self.image inside a PII model does NOT fire — generic 'image' removed from defaults."""
    source = """\
import logging
log = logging.getLogger(__name__)
class Model:
    pass
class CourseModel(Model):
    '''.. pii: Stores course data.'''
    image = None
    def log_course(self):
        log.info("img: %s", self.image)
"""
    assert not _run(source)


def test_bare_ip_not_flagged():
    """self.ip inside a PII model does NOT fire — bare 'ip' removed from defaults."""
    source = """\
import logging
log = logging.getLogger(__name__)
class Model:
    pass
class SessionModel(Model):
    '''.. pii: Stores session PII.'''
    ip = None
    def log_session(self):
        log.info("ip: %s", self.ip)
"""
    assert not _run(source)


def test_token_not_flagged_not_in_oep30():
    """'token' is not an OEP-0030 field — never fires."""
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
    assert not _run(source)


def test_secret_not_flagged_not_in_oep30():
    """'secret' is not an OEP-0030 field — never fires."""
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
    assert not _run(source)


# -- pii-in-print -------------------------------------------------------------

def test_pii_in_print_bare():
    """print(pii_var) inside a pii model fires."""
    source = """\
class Model:
    pass
class UserModel(Model):
    '''.. pii: Stores user PII.'''
    def display(self):
        print(username)                          #=A
"""
    assert _has(_run(source), "A")


def test_pii_in_print_fstring():
    """print() with PII in an f-string fires."""
    source = """\
class Model:
    pass
class UserModel(Model):
    '''.. pii: Stores user PII.'''
    def display(self):
        print(f"user: {username}")               #=A
"""
    assert _has(_run(source), "A")


def test_pii_in_print_guarded():
    """print() with PII inside SQUELCH guard does not fire."""
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
    assert not _run(source)


def test_pii_in_stdout_write():
    """sys.stdout.write() with PII fires."""
    source = """\
import sys
class Model:
    pass
class ReportModel(Model):
    '''.. pii: Stores report PII.'''
    def export(self):
        sys.stdout.write(email)                  #=A
"""
    assert _has(_run(source), "A")


def test_pii_in_stderr_write():
    """sys.stderr.write() with PII fires."""
    source = """\
import sys
class Model:
    pass
class ReportModel(Model):
    '''.. pii: Stores report PII.'''
    def export(self):
        sys.stderr.write(username)               #=A
"""
    assert _has(_run(source), "A")


def test_pii_in_print_safe_key_not_flagged():
    """Printing user_id (safe surrogate key) does not fire."""
    source = """\
class Model:
    pass
class EnrollmentModel(Model):
    '''.. pii: Stores enrollment data.'''
    def display(self):
        print(user_id)
"""
    assert not _run(source)


# -- pii-in-exception ---------------------------------------------------------

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
    assert _has(_run(source), "A")


def test_pii_in_exception_fstring():
    """raise ValueError(f-string with PII) fires."""
    source = """\
class Model:
    pass
class PaymentModel(Model):
    '''.. pii: Stores payment PII.'''
    def validate(self):
        raise ValueError(f"bad username: {username}")   #=A
"""
    assert _has(_run(source), "A")


def test_pii_in_exception_guarded():
    """Exception with PII inside SQUELCH guard does not fire."""
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
    assert not _run(source)


def test_pii_in_exception_safe_function():
    """raise ValueError(redact(pii)) does not fire."""
    source = """\
class Model:
    pass
class PaymentModel(Model):
    '''.. pii: Stores payment PII.'''
    def validate(self):
        raise ValueError(redact(email))
"""
    assert not _run(source)


def test_pii_in_exception_safe_key():
    """raise ValueError(user_id) does not fire (safe surrogate key)."""
    source = """\
class Model:
    pass
class PaymentModel(Model):
    '''.. pii: Stores payment PII.'''
    def validate(self):
        raise ValueError(user_id)
"""
    assert not _run(source)


def test_non_sink_call_not_flagged():
    """Arbitrary function calls with PII are not flagged."""
    source = """\
class Model:
    pass
class UserModel(Model):
    '''.. pii: Stores user PII.'''
    def process(self):
        some_function(email)
"""
    assert not _run(source)


# -- Scope: out-of-model code is not checked ----------------------------------

def test_standalone_function_not_checked():
    """Logs inside a standalone function (not a model method) are not checked."""
    source = """\
import logging
log = logging.getLogger(__name__)
def standalone_helper(email):
    log.info(email)
"""
    assert not _run(source)


def test_module_level_print_not_checked():
    """Module-level print() is not checked."""
    source = """\
print(username)
"""
    assert not _run(source)


def test_module_level_raise_not_checked():
    """Module-level raise is not checked."""
    source = """\
raise ValueError(email)
"""
    assert not _run(source)


# -- Scope: .. no_pii: models are skipped -------------------------------------

def test_squelch_exempt_in_no_pii_model():
    """Logs inside a .. no_pii: model are entirely skipped."""
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
    assert not _run(source)


def test_squelch_enforced_in_pii_model():
    """Unguarded PII log inside a .. pii: model fires."""
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
    assert _has(_run(source), "A")


def test_squelch_enforced_in_unannotated_model():
    """Unguarded PII log inside a model with no annotation fires (conservative)."""
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
    assert _has(_run(source), "A")


def test_squelch_enforced_guarded_in_pii_model():
    """Properly guarded PII log inside a .. pii: model does not fire."""
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
    assert not _run(source)


def test_pii_in_log_new_safe_keys_not_flagged():
    """CI-discovered safe keys do not trigger a warning."""
    source = """\
import logging
log = logging.getLogger(__name__)
class Model:
    pass
class SafeKeyModel(Model):
    '''.. pii: Stores user PII.'''
    service_username = None
    email_enabled = None
    email_sent_on = None
    require_course_email_auth = None
    attr_full_name = None
    location = None
    _location = None
    proctoring_escalation_email = None
    email_cadence = None
    def notify(self):
        log.info(self.service_username)
        log.info(self.email_enabled)
        log.info(self.email_sent_on)
        log.info(self.require_course_email_auth)
        log.info(self.attr_full_name)
        log.info(self.location)
        log.info(self._location)
        log.info(self.proctoring_escalation_email)
        log.info(self.email_cadence)
"""
    assert not _run(source)

"""Plugin management for edx-lint.

This module imports all our plugins, and creates the register function that
will register them with pylint.

PII checking is split into two separate checkers:

* ``pii_squelch_check`` — ``PiiMissingSquelchChecker`` (checker name:
  ``pii-missing-squelch``) handles the single missing-squelch-guard rule
  (also named ``pii-missing-squelch``).
  It also owns all shared PII options (``pii-terms``, ``pii-safe-functions``,
  ``pii-safe-key-patterns``, ``pii-squelch-flag``, ``pii-django-model-bases``).

* ``pii_annotation_check`` — ``PiiAnnotationChecker`` (checker name:
  ``pii-annotation-checker``) handles the ``pii-invalid-no-pii-annotation``
  rule.  It reads shared options from the linter config populated by the
  squelch checker above, so registration order matters: squelch first.
"""

from edx_lint.pylint import (
    annotations_check,
    getattr_check,
    i18n_check,
    module_trace,
    pii_squelch_check,
    pii_annotation_check,
    range_check,
    super_check,
    layered_test_check,
    right_assert_check,
    yaml_load_check,
)

MODS = [
    annotations_check,
    getattr_check,
    i18n_check,
    module_trace,
    # pii_squelch_check MUST come before pii_annotation_check so that the
    # shared PII options are registered in linter.config before the annotation
    # checker's _ensure_config_cached() reads them.
    pii_squelch_check,
    pii_annotation_check,
    range_check,
    super_check,
    layered_test_check,
    right_assert_check,
    yaml_load_check,
]


def register(linter):
    """Registering additional checkers.
    However, we will also use it to amend existing checker config.
    """
    # add all of the checkers
    for mod in MODS:
        mod.register_checkers(linter)

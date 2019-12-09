"""Plugin management for edx-lint.

This module imports all our plugins, and creates the register function that
will register them with pylint.
"""

from edx_lint.pylint import (
    feature_toggle_check,
    getattr_check,
    i18n_check,
    module_trace,
    range_check,
    super_check,
    layered_test_check,
    right_assert_check,
    unicode_check,
    yaml_load_check,
)

MODS = [
    feature_toggle_check,
    getattr_check,
    i18n_check,
    module_trace,
    range_check,
    super_check,
    layered_test_check,
    right_assert_check,
    unicode_check,
    yaml_load_check,
]


def register(linter):
    """Registering additional checkers.
    However, we will also use it to amend existing checker config.
    """
    # add all of the checkers
    for mod in MODS:
        mod.register_checkers(linter)

from edx_lint.pylint import (
    getattr_check, i18n_check, module_trace, range_check, super_check,
    layered_test_check,
)


def register(linter):
    """Registering additional checkers.
    However, we will also use it to amend existing checker config.
    """
    # add all of the checkers
    for mod in [
        getattr_check, i18n_check, module_trace, range_check, super_check,
        layered_test_check,
    ]:
        mod.register_checkers(linter)

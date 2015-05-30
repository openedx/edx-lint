from edx_lint.pylint import i18n_check, module_trace, range_check, super_check


def register(linter):
    """Registering additional checkers.
    However, we will also use it to amend existing checker config.
    """
    # add all of the checkers
    for mod in [i18n_check, module_trace, range_check, super_check]:
        mod.register_checkers(linter)

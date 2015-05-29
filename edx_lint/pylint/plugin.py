from edx_lint.pylint import super_check, i18n_check, module_trace


def register(linter):
    """Registering additional checkers.
    However, we will also use it to amend existing checker config.
    """
    # add all of the checkers
    for mod in [super_check, i18n_check, module_trace]:
        mod.register_checkers(linter)

from edx_lint.pylint import checkers, i18n_check


def register(linter):
    """Registering additional checkers.
    However, we will also use it to amend existing checker config.
    """
    # add all of the checkers
    for mod in [checkers, i18n_check]:
        mod.register_checkers(linter)

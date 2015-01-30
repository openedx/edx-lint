from edx_lint.pylint.checkers import register_checkers


def register(linter):
    """Registering additional checkers.
    However, we will also use it to amend existing checker config.
    """
    # add all of the checkers
    register_checkers(linter)

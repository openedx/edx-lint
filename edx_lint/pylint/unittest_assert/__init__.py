"""edx_lint unittest_assert module (optional plugin for unittest assertion checks).

Add this to your pylintrc::

    load-plugins=edx_lint.pylint.unittest_assert

"""

from .unittest_assert_check import register_checkers

register = register_checkers

"""
edx_lint filters_docstring module (optional plugin for filters docstrings).

Add this to your pylintrc::
    load-plugins=edx_lint.pylint.filters_docstring
"""

from .filters_docstring_check import register_checkers

register = register_checkers

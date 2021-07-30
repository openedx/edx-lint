"""
edx_lint events_annotation module (optional plugin for events inline code-annotations
checks).

Add this to your pylintrc::
    load-plugins=edx_lint.pylint.events_annotation
"""

from .events_annotation_check import register_checkers

register = register_checkers

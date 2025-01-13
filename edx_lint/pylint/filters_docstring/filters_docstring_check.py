"""
Pylint checker for the format of the docstrings of filters.

A filter's docstring should have the following structure:

1. Description: Any non-empty text followed by a blank line.
2. Filter Type: A line that starts with "Filter Type:".
3. Trigger: A line that starts with "Trigger:".
"""

from pylint.checkers import BaseChecker, utils
import re
from ..common import BASE_ID


def register_checkers(linter):
    """
    Register checkers.
    """
    linter.register_checker(FiltersDocstringFormatChecker(linter))


class FiltersDocstringFormatChecker(BaseChecker):
    """Pylint checker for the format of the docstrings of filters."""

    name = "docstring-format-checker"

    FILTER_DOCSTRING_MISSING_DESCRIPTION = "filter-docstring-missing-description"
    FILTER_DOCSTRING_MISSING_TYPE = "filter-docstring-missing-type"
    FILTER_DOCSTRING_MISSING_TRIGGER = "filter-docstring-missing-trigger"

    msgs = {
        ("E%d90" % BASE_ID): (
            "Filter's (%s) docstring is missing the required description section",
            FILTER_DOCSTRING_MISSING_DESCRIPTION,
            "filters docstring is missing the required description section",
        ),
        ("E%d91" % BASE_ID): (
            "Filter's (%s) docstring is missing the required filter type section",
            FILTER_DOCSTRING_MISSING_TYPE,
            "filters docstring is missing the required filter type section",
        ),
        ("E%d92" % BASE_ID): (
            "Filter's (%s) docstring is missing the required trigger section",
            FILTER_DOCSTRING_MISSING_TRIGGER,
            "filters docstring is missing the required trigger section",
        ),
    }

    options = ()

    @utils.only_required_for_messages(
        FILTER_DOCSTRING_MISSING_DESCRIPTION,
        FILTER_DOCSTRING_MISSING_TYPE,
        FILTER_DOCSTRING_MISSING_TRIGGER,
    )
    def visit_classdef(self, node):
        """Visit a class definition and check its docstring."""
        if not node.is_subtype_of("openedx_filters.tooling.OpenEdxPublicFilter"):
            return

        docstring = node.doc_node.value if node.doc_node else ""
        if not (error_messages := self._check_docstring_format(docstring)):
            return
        for error_message in error_messages:
            self.add_message(error_message, node=node, args=(node.name,))

    def _check_docstring_format(self, docstring):
        """
        Check the format of the docstring for errors and return a list of error messages.

        The docstring should have the following structure:
        1. Description: Any non-empty text followed by a blank line.
        2. Filter Type: A line that starts with "Filter Type:".
        3. Trigger: A line that starts with "Trigger:".

        For example:

        ```
        Description:
        Filter used to modify the certificate rendering process.

        ... (more description)

        Filter Type:
            org.openedx.learning.certificate.render.started.v1

        Trigger:
            - Repository: openedx/edx-platform
            - Path: lms/djangoapps/certificates/views/webview.py
            - Function or Method: render_html_view
        ```
        """
        required_sections = [
            (r"Description:\s*.*\n", self.FILTER_DOCSTRING_MISSING_DESCRIPTION),
            (r"Filter Type:\s*.*\n", self.FILTER_DOCSTRING_MISSING_TYPE),
            (
                r"Trigger:\s*(NA|-\s*Repository:\s*[^\n]+\s*-\s*Path:\s*[^\n]+\s*-\s*Function\s*or\s*Method:\s*[^\n]+)",
                self.FILTER_DOCSTRING_MISSING_TRIGGER,
            ),
        ]
        error_messages = []
        for pattern, error_message in required_sections:
            if not re.search(pattern, docstring, re.MULTILINE):
                error_messages.append(error_message)
        return error_messages

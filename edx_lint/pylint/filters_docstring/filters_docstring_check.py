"""
Pylint checker for the format of the docstrings of filters.

A filter's docstring should have the following structure:

1. Description: Any non-empty text followed by a blank line.
2. Filter Type: A line that starts with "Filter Type:".
3. Trigger: A line that starts with "Trigger:".
"""

import re

from pylint.checkers import BaseChecker, utils

from edx_lint.pylint.common import BASE_ID


def register_checkers(linter):
    """
    Register checkers.
    """
    linter.register_checker(FiltersDocstringFormatChecker(linter))


class FiltersDocstringFormatChecker(BaseChecker):
    """Pylint checker for the format of the docstrings of filters."""

    name = "filters-docstring-format"

    DOCSTRING_MISSING_PURPOSE_OR_BADLY_FORMATTED = "filter-docstring-missing-purpose"
    DOCSTRING_MISSING_OR_INCORRECT_TYPE = "filter-docstring-missing-or-incorrect-type"
    DOCSTRING_MISSING_TRIGGER_OR_BADLY_FORMATTED = "filter-docstring-missing-trigger"

    msgs = {
        ("E%d91" % BASE_ID): (
            "Filter's (%s) docstring is missing the required `Purpose` section or is badly formatted",
            DOCSTRING_MISSING_PURPOSE_OR_BADLY_FORMATTED,
            "filters docstring is missing the required `Purpose` section or is badly formatted",
        ),
        ("E%d93" % BASE_ID): (
            "Filter's (%s) docstring `Filter Type` section is missing or incorrect",
            DOCSTRING_MISSING_OR_INCORRECT_TYPE,
            "filters docstring `Filter Type` section is missing or incorrect",
        ),
        ("E%d94" % BASE_ID): (
            "Filter's (%s) docstring is missing the required `Trigger` section or is badly formatted",
            DOCSTRING_MISSING_TRIGGER_OR_BADLY_FORMATTED,
            "filters docstring is missing the required `Trigger` section or is badly formatted",
        ),
    }

    @utils.only_required_for_messages(
        DOCSTRING_MISSING_PURPOSE_OR_BADLY_FORMATTED,
        DOCSTRING_MISSING_OR_INCORRECT_TYPE,
        DOCSTRING_MISSING_TRIGGER_OR_BADLY_FORMATTED,
    )
    def visit_classdef(self, node):
        """
        Visit a class definition and check its docstring.

        If the class is a subclass of OpenEdxPublicFilter, check the format of its docstring. Skip the
        OpenEdxPublicFilter class itself.

        """
        if not node.is_subtype_of("openedx_filters.tooling.OpenEdxPublicFilter") or node.name == "OpenEdxPublicFilter":
            return

        docstring = node.doc_node.value if node.doc_node else ""
        if not (error_messages := self._check_docstring_format(node, docstring)):
            return
        for error_message in error_messages:
            self.add_message(error_message, node=node, args=(node.name,))

    def _check_docstring_format(self, node, docstring):
        """
        Check the format of the docstring for errors and return a list of error messages.

        The docstring should have the following structure:
        1. Description: Any non-empty text followed by a blank line.
        2. Filter Type: A line that starts with "Filter Type:".
        3. Trigger: A line that starts with "Trigger:".

        For example:

        ```
        Purpose:
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
        error_messages = []
        if error_message := self._check_purpose_missing_or_badly_formatted(docstring):
            error_messages.append(error_message)
        if error_message := self._check_filter_type_missing_or_incorrect(node, docstring):
            error_messages.append(error_message)
        if error_message := self._check_trigger_missing_or_badly_formatted(docstring):
            error_messages.append(error_message)
        return error_messages

    def _check_purpose_missing_or_badly_formatted(self, docstring):
        """
        Check if the purpose is missing or badly formatted.

        If the purpose is missing or badly formatted, return the error message. Otherwise, return.
        """
        if not re.search(r"Purpose:\s*.*\n", docstring):
            return self.DOCSTRING_MISSING_PURPOSE_OR_BADLY_FORMATTED
        return None

    def _check_filter_type_missing_or_incorrect(self, node, docstring):
        """
        Check if the filter type is missing or incorrect.

        If the filter type is missing or incorrect, return the error message. Otherwise, return.
        """
        filter_type = node.locals["filter_type"][0].statement().value.value
        if not re.search(r"Filter Type:\s*%s" % filter_type, docstring):
            return self.DOCSTRING_MISSING_OR_INCORRECT_TYPE
        return None

    def _check_trigger_missing_or_badly_formatted(self, docstring):
        """
        Check if the trigger is missing or badly formatted.

        If the trigger is missing or badly formatted, return the error message. Otherwise, return.
        """
        if not re.search(
            r"Trigger:\s*(NA|-\s*Repository:\s*[^\n]+\s*-\s*Path:\s*[^\n]+\s*-\s*Function\s*or\s*Method:\s*[^\n]+)",
            docstring,
            re.MULTILINE,
        ):
            return self.DOCSTRING_MISSING_TRIGGER_OR_BADLY_FORMATTED
        return None

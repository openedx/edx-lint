"""
Pylint plugin: checks that feature toggles are properly annotated.
"""

import re

from pylint.checkers import BaseChecker, utils
from pylint.interfaces import IAstroidChecker

from .common import BASE_ID, check_visitors


def register_checkers(linter):
    """
    Register checkers.
    """
    linter.register_checker(FeatureToggleChecker(linter))


class AnnotationLines:
    """
    AnnotationLines provides utility methods to work with a string in terms of
    lines.  As an example, it can convert a Call node into a list of its contents
    separated by line breaks.
    """

    # Regex searches for annotations like: # .. toggle or # .. documented_elsewhere
    _ANNOTATION_REGEX = re.compile(r"[\s]*#[\s]*\.\.[\s]*(toggle|documented_elsewhere)")

    def __init__(self, module_node):
        """
        Arguments:
            module_node: The visited module node.
        """
        module_as_binary = module_node.stream().read()

        file_encoding = module_node.file_encoding
        if file_encoding is None:
            file_encoding = "UTF-8"

        module_as_string = module_as_binary.decode(file_encoding)
        self._list_of_string_lines = module_as_string.split("\n")

    def is_line_annotated(self, line_number):
        """
        Checks if the provided line number is annotated.
        """
        if line_number < 1 or self._line_count() < line_number:
            return False

        return bool(self._ANNOTATION_REGEX.match(self._get_line_contents(line_number)))

    def _line_count(self):
        """
        Gets the number of lines in the string.
        """
        return len(self._list_of_string_lines)

    def _get_line_contents(self, line_number):
        """
        Gets the line of text designated by the provided line number.
        """
        return self._list_of_string_lines[line_number - 1]


@check_visitors
class FeatureToggleChecker(BaseChecker):
    """
    Checks that feature toggles are properly annotated and best practices
    are followed.
    """

    __implements__ = (IAstroidChecker,)

    name = "feature-toggle-checker"

    TOGGLE_NOT_ANNOTATED_MESSAGE_ID = "feature-toggle-needs-doc"
    ILLEGAL_WAFFLE_MESSAGE_ID = "illegal-waffle-usage"

    _CHECK_CAPITAL_REGEX = re.compile(r"[A-Z]")
    _WAFFLE_TOGGLE_CLASSES = ("WaffleFlag", "WaffleSwitch", "CourseWaffleFlag")
    _ILLEGAL_WAFFLE_FUNCTIONS = ["flag_is_active", "switch_is_active"]

    msgs = {
        ("E%d40" % BASE_ID): (
            u"feature toggle (%s) is missing annotation",
            TOGGLE_NOT_ANNOTATED_MESSAGE_ID,
            "feature toggle is missing annotation",
        ),
        ("E%d41" % BASE_ID): (
            u"illegal waffle usage with (%s): use utility classes {}.".format(", ".join(_WAFFLE_TOGGLE_CLASSES)),
            ILLEGAL_WAFFLE_MESSAGE_ID,
            u"illegal waffle usage: use utility classes {}.".format(", ".join(_WAFFLE_TOGGLE_CLASSES)),
        ),
    }

    def __init__(self, *args, **kwargs):
        super(FeatureToggleChecker, self).__init__(*args, **kwargs)
        self._lines = None

    def visit_module(self, node):
        """Parses the module code to provide access to comments."""
        self._lines = AnnotationLines(node)

    def check_waffle_class_annotated(self, node):
        """
        Check Call node for waffle class instantiation with missing annotations.
        """
        if not hasattr(node.func, "name"):
            return

        # Looking for class instantiation, so should start with a capital letter
        starts_with_capital = self._CHECK_CAPITAL_REGEX.match(node.func.name)
        if not starts_with_capital:
            return

        # Search for toggle classes that require an annotation
        if not node.func.name.endswith(self._WAFFLE_TOGGLE_CLASSES):
            return

        if not self._lines.is_line_annotated(node.lineno - 1):
            feature_toggle_name = "UNKNOWN"

            if node.keywords is not None:
                for node_key in node.keywords:
                    if node_key.arg == "flag_name":
                        feature_toggle_name = node_key.value.value

            if feature_toggle_name == "UNKNOWN":
                if len(node.args) >= 2:
                    feature_toggle_name = node.args[1].as_string()

            self.add_message(self.TOGGLE_NOT_ANNOTATED_MESSAGE_ID, args=(feature_toggle_name,), node=node)

    def check_configuration_model_annotated(self, node):
        """
        Checks class definitions to see if they subclass ConfigurationModel.
        If they do, they should be correctly annotated.
        """
        if "ConfigurationModel" not in node.basenames:
            return
        if not self._lines.is_line_annotated(node.lineno - 1):
            config_model_subclass_name = node.name

            self.add_message(self.TOGGLE_NOT_ANNOTATED_MESSAGE_ID, args=(config_model_subclass_name,), node=node)

    def check_django_feature_flag_annotated(self, node):
        """
        Checks dictionary definitions to see if the django feature flags
        dict FEATURES is being set. If it is, entries should be
        correctly annotated.
        """
        try:
            parent_target_name = node.parent.targets[0].name
        except AttributeError:
            return

        if parent_target_name == "FEATURES":
            for key, _ in node.items:
                if not self._lines.is_line_annotated(key.lineno - 1):
                    django_feature_toggle_name = key.value

                    self.add_message(
                        self.TOGGLE_NOT_ANNOTATED_MESSAGE_ID, args=(django_feature_toggle_name,), node=node
                    )

    def check_illegal_waffle_usage(self, node):
        """
        Check Call node for illegal waffle calls.
        """
        if not hasattr(node.func, "name"):
            return

        if node.func.name in self._ILLEGAL_WAFFLE_FUNCTIONS:
            feature_toggle_name = "UNKNOWN"
            if len(node.args) >= 1:
                feature_toggle_name = node.args[0].as_string()

            self.add_message(self.ILLEGAL_WAFFLE_MESSAGE_ID, args=(feature_toggle_name,), node=node)

    @utils.check_messages(TOGGLE_NOT_ANNOTATED_MESSAGE_ID, ILLEGAL_WAFFLE_MESSAGE_ID)
    def visit_call(self, node):
        """
        Performs various checks on Call nodes.
        """
        self.check_waffle_class_annotated(node)
        self.check_illegal_waffle_usage(node)

    @utils.check_messages(TOGGLE_NOT_ANNOTATED_MESSAGE_ID)
    def visit_classdef(self, node):
        """
        Checks class definitions for potential ConfigurationModel
        implementations.
        """
        self.check_configuration_model_annotated(node)

    @utils.check_messages(TOGGLE_NOT_ANNOTATED_MESSAGE_ID)
    def visit_dict(self, node):
        """
        Checks Dict nodes in case a Django FEATURES dictionary is being
        initialized.
        """
        self.check_django_feature_flag_annotated(node)

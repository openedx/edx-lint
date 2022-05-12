"""
Pylint plugin: checks that feature toggles are properly annotated.
"""

import os
import re

import pkg_resources

from astroid.node_classes import Const, Name
from code_annotations import annotation_errors
from code_annotations.base import AnnotationConfig
from code_annotations.find_static import StaticSearch
from pylint.checkers import BaseChecker, utils
from pylint.interfaces import IAstroidChecker

from .common import BASE_ID, check_visitors


def register_checkers(linter):
    """
    Register checkers.
    """
    linter.register_checker(FeatureToggleChecker(linter))
    linter.register_checker(CodeAnnotationChecker(linter))
    linter.register_checker(FeatureToggleAnnotationChecker(linter))
    linter.register_checker(SettingAnnotationChecker(linter))


def check_all_messages(msgs):
    """
    Decorator to automatically assign all messages from a class to the list of messages handled by a checker method.

    Inspired by pylint.checkers.util.check_messages
    """

    def store_messages(func):
        func.checks_msgs = [message[1] for message in msgs]
        return func

    return store_messages


class AnnotationLines:
    """
    AnnotationLines provides utility methods to work with a string in terms of
    lines.  As an example, it can convert a Call node into a list of its contents
    separated by line breaks.
    """

    # Regex searches for annotations like: # .. toggle
    _ANNOTATION_REGEX = re.compile(r"[\s]*#[\s]*\.\.[\s]*(toggle)")

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
            "feature toggle (%s) is missing annotation",
            TOGGLE_NOT_ANNOTATED_MESSAGE_ID,
            "feature toggle is missing annotation",
        ),
        ("E%d41" % BASE_ID): (
            "illegal waffle usage with (%s): use utility classes {}.".format(
                ", ".join(_WAFFLE_TOGGLE_CLASSES)
            ),
            ILLEGAL_WAFFLE_MESSAGE_ID,
            "illegal waffle usage: use utility classes {}.".format(
                ", ".join(_WAFFLE_TOGGLE_CLASSES)
            ),
        ),
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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

            self.add_message(
                self.TOGGLE_NOT_ANNOTATED_MESSAGE_ID,
                args=(feature_toggle_name,),
                node=node,
            )

    def check_configuration_model_annotated(self, node):
        """
        Checks class definitions to see if they subclass ConfigurationModel.
        If they do, they should be correctly annotated.
        """
        if "ConfigurationModel" not in node.basenames:
            return
        if not self._lines.is_line_annotated(node.lineno - 1):
            config_model_subclass_name = node.name

            self.add_message(
                self.TOGGLE_NOT_ANNOTATED_MESSAGE_ID,
                args=(config_model_subclass_name,),
                node=node,
            )

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
                        self.TOGGLE_NOT_ANNOTATED_MESSAGE_ID,
                        args=(django_feature_toggle_name,),
                        node=node,
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

            self.add_message(
                self.ILLEGAL_WAFFLE_MESSAGE_ID, args=(feature_toggle_name,), node=node
            )

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


@check_visitors
class AnnotationBaseChecker(BaseChecker):
    """
    Code annotation checkers should almost certainly inherit from this class.

    The CONFIG_FILENAMES class attribute is a list of str filenames located in code_annotations/contrib/config.
    """

    # Override this in child classes
    CONFIG_FILENAMES = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config_search = []
        for config_filename in self.CONFIG_FILENAMES:
            config_path = pkg_resources.resource_filename(
                "code_annotations",
                os.path.join("contrib", "config", config_filename),
            )
            config = AnnotationConfig(config_path, verbosity=-1)
            search = StaticSearch(config)
            self.config_search.append((config, search))
            self.current_module_annotations = []

    def check_module(self, node):
        """
        Perform checks on all annotation groups for this module.
        """
        for config, search in self.config_search:
            # This is a hack to avoid re-creating AnnotationConfig every time
            config.source_path = node.path[0]
            all_results = search.search()

            for _file_name, results in all_results.items():
                for annotations_group in search.iter_groups(results):
                    self.current_module_annotations.append(annotations_group)
                    self.check_annotation_group(search, annotations_group, node)

    def leave_module(self, _node):
        self.current_module_annotations.clear()

    def check_annotation_group(self, search, annotations, node):
        raise NotImplementedError


class CodeAnnotationChecker(AnnotationBaseChecker):
    """
    Run generic code annotation checks.

    This makes use of code-annotations `check_results()` method. Elements from
    `search.annotation_errors` are then parsed and exposed to pylint. Note that modifying the creation order of the
    error types in code-annotations will lead to a modification of the numerical IDs of the errors here, so this should
    be avoided as much as possible.

    When creating a new annotation configuration, its filename should be added to
    CodeAnnotationChecker.CONFIG_FILENAMES (see AnnotationBaseChecker docs).
    """
    CONFIG_FILENAMES = ["feature_toggle_annotations.yaml", "setting_annotations.yaml"]
    __implements__ = (IAstroidChecker,)
    name = "code-annotations"
    msgs = {
        ("E%d%d" % (BASE_ID, index + 50)): (
            error_type.message,
            error_type.symbol,
            error_type.description,
        )
        for index, error_type in enumerate(annotation_errors.TYPES)
    }

    @check_all_messages(msgs)
    def visit_module(self, node):
        """
        Run all checks on a single module.
        """
        self.check_module(node)

    def check_annotation_group(self, search, annotations, node):
        search.check_group(annotations)
        for (annotation, AnnotationErrorType, args) in search.annotation_errors:
            self.add_message(
                AnnotationErrorType.symbol,
                args=args,
                node=node,
                line=annotation["line_number"],
            )
        search.annotation_errors.clear()


class FeatureToggleAnnotationChecker(AnnotationBaseChecker):
    """
    Parse feature toggle annotations and ensure best practices are followed.
    """

    CONFIG_FILENAMES = ["feature_toggle_annotations.yaml"]

    __implements__ = (IAstroidChecker,)

    name = "toggle-annotations"

    NO_NAME_MESSAGE_ID = "toggle-no-name"
    EMPTY_DESCRIPTION_MESSAGE_ID = "toggle-empty-description"
    MISSING_TARGET_REMOVAL_DATE_MESSAGE_ID = "toggle-missing-target-removal-date"
    NON_BOOLEAN_DEFAULT_VALUE = "toggle-non-boolean-default-value"
    MISSING_ANNOTATION = "toggle-missing-annotation"
    INVALID_DJANGO_WAFFLE_IMPORT = "invalid-django-waffle-import"

    msgs = {
        ("E%d60" % BASE_ID): (
            "feature toggle has no name",
            NO_NAME_MESSAGE_ID,
            "Feature toggle name must be present and be the first annotation",
        ),
        ("E%d61" % BASE_ID): (
            "feature toggle (%s) does not have a description",
            EMPTY_DESCRIPTION_MESSAGE_ID,
            "Feature toggles must include a thorough description",
        ),
        ("E%d62" % BASE_ID): (
            "temporary feature toggle (%s) has no target removal date",
            MISSING_TARGET_REMOVAL_DATE_MESSAGE_ID,
            "Temporary feature toggles must include a target removal date",
        ),
        ("E%d63" % BASE_ID): (
            "feature toggle (%s) default value must be boolean ('True' or 'False')",
            NON_BOOLEAN_DEFAULT_VALUE,
            "Feature toggle default values must be boolean",
        ),
        ("E%d64" % BASE_ID): (
            "missing feature toggle annotation",
            MISSING_ANNOTATION,
            (
                "When a WaffleFlag/Switch object is created, a corresponding annotation must be present above in the"
                " same module and with a matching name",
            )
        ),
        ("E%d65" % BASE_ID): (
            "invalid Django Waffle import",
            INVALID_DJANGO_WAFFLE_IMPORT,
            (
                "Do not directly access Django Waffle objects and methods. Instead, import from"
                " edx_toggles.toggles.",
            )
        ),
    }

    TOGGLE_FUNC_NAMES = [
        "WaffleFlag",
        "NonNamespacedWaffleFlag",
        "WaffleSwitch",
        "NonNamespacedWaffleSwitch",
        "CourseWaffleFlag",
        "ExperimentWaffleFlag",
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_module_annotated_toggle_names = set()
        self.current_module_annotation_group_line_numbers = []

    @check_all_messages(msgs)
    def visit_module(self, node):
        """
        Run all checks on a single module.
        """
        self.check_module(node)

    def leave_module(self, _node):
        self.current_module_annotated_toggle_names.clear()
        self.current_module_annotation_group_line_numbers.clear()

    def check_annotation_group(self, search, annotations, node):
        """
        Perform checks on a single annotation group.
        """
        if not annotations:
            return

        target_removal_date = None
        temporary_use_case = False
        toggle_name = ""
        toggle_description = ""
        toggle_default = None
        line_number = None
        for annotation in annotations:
            if line_number is None:
                line_number = annotation["line_number"]
                self.current_module_annotation_group_line_numbers.append(line_number)
            if annotation["annotation_token"] == ".. toggle_name:":
                toggle_name = annotation["annotation_data"]
                self.current_module_annotated_toggle_names.add(toggle_name)
            elif annotation["annotation_token"] == ".. toggle_description:":
                toggle_description = annotation["annotation_data"].strip()
            elif annotation["annotation_token"] == ".. toggle_use_cases:":
                if "temporary" in annotation["annotation_data"]:
                    temporary_use_case = True
            elif annotation["annotation_token"] == ".. toggle_target_removal_date:":
                target_removal_date = annotation["annotation_data"]
            elif annotation["annotation_token"] == ".. toggle_default:":
                toggle_default = annotation["annotation_data"]

        if not toggle_name:
            self.add_message(
                self.NO_NAME_MESSAGE_ID,
                node=node,
                line=line_number,
            )
        if not toggle_description:
            self.add_message(
                self.EMPTY_DESCRIPTION_MESSAGE_ID,
                args=(toggle_name,),
                node=node,
                line=line_number,
            )
        if temporary_use_case and not target_removal_date:
            self.add_message(
                self.MISSING_TARGET_REMOVAL_DATE_MESSAGE_ID,
                args=(toggle_name,),
                node=node,
                line=line_number,
            )
        if toggle_default not in ["True", "False"]:
            self.add_message(
                self.NON_BOOLEAN_DEFAULT_VALUE,
                args=(toggle_name,),
                node=node,
                line=line_number,
            )

    @utils.check_messages(MISSING_ANNOTATION)
    def visit_call(self, node):
        """
        Check for missing annotations.
        """
        if self.is_annotation_missing(node):
            self.add_message(
                self.MISSING_ANNOTATION,
                node=node,
            )

    @utils.check_messages(INVALID_DJANGO_WAFFLE_IMPORT)
    def visit_import(self, node):
        if node.names[0][0] == "waffle":
            self.add_message(
                self.INVALID_DJANGO_WAFFLE_IMPORT,
                node=node,
            )

    @utils.check_messages(INVALID_DJANGO_WAFFLE_IMPORT)
    def visit_importfrom(self, node):
        if node.modname == "waffle":
            self.add_message(
                self.INVALID_DJANGO_WAFFLE_IMPORT,
                node=node,
            )

    def is_annotation_missing(self, node):
        """
        Check whether the node corresponds to a toggle instance creation. if yes, check that it is annotated.
        """
        if (
            not isinstance(node.func, Name)
            or node.func.name not in self.TOGGLE_FUNC_NAMES
        ):
            return False

        if not self.current_module_annotation_group_line_numbers:
            # There are no annotations left
            return True

        annotation_line_number = self.current_module_annotation_group_line_numbers[0]
        if annotation_line_number > node.tolineno:
            # The next annotation is located after the current node
            return True
        self.current_module_annotation_group_line_numbers.pop(0)

        # Check literal toggle name arguments
        if node.args and isinstance(node.args[0], Const) and isinstance(node.args[0].value, str):
            toggle_name = node.args[0].value
            if toggle_name not in self.current_module_annotated_toggle_names:
                return True
        return False


class SettingAnnotationChecker(AnnotationBaseChecker):
    """
    Perform checks on setting annotations.
    """

    CONFIG_FILENAMES = ["setting_annotations.yaml"]

    __implements__ = (IAstroidChecker,)

    name = "setting-annotations"

    BOOLEAN_DEFAULT_VALUE = "setting-boolean-default-value"

    msgs = {
        ("E%d70" % BASE_ID): (
            "setting annotation (%s) cannot have a boolean value",
            BOOLEAN_DEFAULT_VALUE,
            "Setting with boolean values should be annotated as feature toggles",
        ),
    }

    @check_all_messages(msgs)
    def visit_module(self, node):
        """
        Run all checks on a single module.
        """
        self.check_module(node)

    def check_annotation_group(self, search, annotations, node):
        """
        Perform checks on a single annotation group.
        """
        if not annotations:
            return

        setting_name = ""
        setting_default = None
        line_number = None
        for annotation in annotations:
            if line_number is None:
                line_number = annotation["line_number"]
            if annotation["annotation_token"] == ".. setting_name:":
                setting_name = annotation["annotation_data"]
            elif annotation["annotation_token"] == ".. setting_default:":
                setting_default = annotation["annotation_data"]

        if setting_default in ["True", "False"]:
            self.add_message(
                self.BOOLEAN_DEFAULT_VALUE,
                args=(setting_name,),
                node=node,
                line=line_number,
            )

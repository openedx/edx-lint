"""Pylint plugin: checks that feature toggles are properly annotated."""

import re

from pylint.checkers import BaseChecker, utils
from pylint.interfaces import IAstroidChecker

from .common import BASE_ID, check_visitors


def register_checkers(linter):
    """Register checkers."""
    linter.register_checker(FeatureToggleChecker(linter))

class AnnotationLines(object):
    """
    StringLines provides utility methods to work with a string in terms of
    lines.  As an example, it can convert an index into a line number or column
    number (i.e. index into the line).
    """

    # Regex searches for annotations like: [    # .. ]
    _ANNOTATION_REGEX = re.compile(r'[\s\S]*#[\s\S]*?\.\.[\s\S]*?feature_toggle')

    def __init__(self, module_node):
        """
        Arguments:
            module_node: The visited module node.
        """
        module_as_binary = module_node.stream().read()
        self._string = module_as_binary.decode("iso8859-1")

        self._line_start_indexes = self._process_line_breaks(self._string)
        # this is an exclusive index used in the case that the template doesn't
        # end with a new line
        self.eof_index = len(self._string)

    def is_line_annotated(self, line_number):
        """
        Checks if the provided line number is annotated.
        """
        if line_number < 1 or self.line_count() < line_number:
            return False

        return bool(
            self._ANNOTATION_REGEX.match(self._line_number_to_line(line_number))
        )

    def line_count(self):
        """
        Gets the number of lines in the string.
        """
        return len(self._line_start_indexes)

    def _process_line_breaks(self, string):
        """
        Creates a list, where each entry represents the index into the string
        where the next line break was found.

        Arguments:
            string: The string in which to find line breaks.

        Returns:
             A list of indices into the string at which each line begins.

        """
        line_start_indexes = [0]
        index = 0
        while True:
            index = string.find('\n', index)
            if index < 0:
                break
            index += 1
            line_start_indexes.append(index)
        return line_start_indexes

    def _line_number_to_line(self, line_number):
        """
        Gets the line of text designated by the provided line number.

        Arguments:
            line_number: The line number of the line we want to find.

        Returns:
            The line of text designated by the provided line number.

        """
        start_index = self._line_start_indexes[line_number - 1]
        if len(self._line_start_indexes) == line_number:
            line = self._string[start_index:]
        else:
            end_index = self._line_start_indexes[line_number]
            line = self._string[start_index:end_index - 1]
        return line


@check_visitors
class FeatureToggleChecker(BaseChecker):
    """
    Checks that feature toggles are properly annotated.
    """

    __implements__ = (IAstroidChecker,)

    name = 'feature-toggle-annotation-checker'

    WAFFLE_NOT_ANNOTATED_MESSAGE_ID = 'waffle-missing-toggle-annotation'
    ILLEGAL_WAFFLE_MESSAGE_ID = 'illegal-waffle-usage'

    _CHECK_CAPITAL_REGEX = re.compile(r'[A-Z]')
    _WAFFLE_TOGGLE_CLASSES = ['WaffleFlag', 'WaffleSwitch',]
    _ILLEGAL_WAFFLE_FUNCTIONS = ['flag_is_active', 'switch_is_active',]

    msgs = {
        'E%d40' % BASE_ID: (
            u"waffle feature toggle (%s) is missing annotation",
            WAFFLE_NOT_ANNOTATED_MESSAGE_ID,
            "waffle feature toggle is missing annotation",
        ),
        'E%d41' % BASE_ID: (
            u"illegal waffle usage with (%s). use utility classes {}.".format(', '.join(_WAFFLE_TOGGLE_CLASSES)),
            ILLEGAL_WAFFLE_MESSAGE_ID,
            "illegal waffle usage. use utility classes {}.".format(', '.join(_WAFFLE_TOGGLE_CLASSES)),
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
        # Looking for class instantiation, so should start with a capital letter
        starts_with_capital = self._CHECK_CAPITAL_REGEX.match(node.func.name)
        if not starts_with_capital:
            return

        # Search for toggle classes that require an annotation
        if not any(node.func.name.endswith(toggle_class) for toggle_class in self._WAFFLE_TOGGLE_CLASSES):
            return

        if not self._lines.is_line_annotated(node.lineno - 1):
            feature_toggle_name = 'UNKNOWN'
            if len(node.args) >= 2:
                feature_toggle_name = node.args[1].as_string()

            self.add_message(
                self.WAFFLE_NOT_ANNOTATED_MESSAGE_ID,
                args=(feature_toggle_name,),
                node=node,
            )

    def check_illegal_waffle_usage(self, node):
        """
        Check Call node for illegal waffle calls.
        """
        if node.func.name in self._ILLEGAL_WAFFLE_FUNCTIONS:
            feature_toggle_name = 'UNKNOWN'
            if len(node.args) >= 1:
                feature_toggle_name = node.args[0].as_string()

            self.add_message(
                self.ILLEGAL_WAFFLE_MESSAGE_ID,
                args=(feature_toggle_name,),
                node=node,
            )

    @utils.check_messages(WAFFLE_NOT_ANNOTATED_MESSAGE_ID, ILLEGAL_WAFFLE_MESSAGE_ID)
    def visit_call(self, node):
        """
        Performs various checks on Call nodes.

        """
        # TODO: THIS WAS A HACK TO GET THIS TO WORK ON:
        # - /edx/app/edxapp/edx-platform/openedx/features/course_experience/__init__.py
        # - without this have, we saw...
        #    Stack Trace
        #       ...
        #       starts_with_capital = self._CHECK_CAPITAL_REGEX.match(node.func.name)
        #    AttributeError: 'Attribute' object has no attribute 'name'
        if not hasattr(node.func, 'name'):
            return

        self.check_waffle_class_annotated(node)
        self.check_illegal_waffle_usage(node)

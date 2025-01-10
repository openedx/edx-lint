"""
Pylint plugin: checks that Open edX Events are properly annotated.
"""

from astroid.nodes.node_classes import Const, Name
from pylint.checkers import utils

from edx_lint.pylint.annotations_check import AnnotationBaseChecker, check_all_messages
from edx_lint.pylint.common import BASE_ID


def register_checkers(linter):
    """
    Register checkers.
    """
    linter.register_checker(EventsAnnotationChecker(linter))


class EventsAnnotationChecker(AnnotationBaseChecker):
    """
    Perform checks on events annotations.
    """

    CONFIG_FILENAMES = ["openedx_events_annotations.yaml"]

    name = "events-annotations"

    NO_TYPE_MESSAGE_ID = "event-no-type"
    NO_NAME_MESSAGE_ID = "event-no-name"
    NO_DATA_MESSAGE_ID = "event-no-data"
    NO_STATUS_MESSAGE_ID = "event-no-status"
    NO_DESCRIPTION_MESSAGE_ID = "event-empty-description"
    MISSING_ANNOTATION = "event-missing-annotation"

    msgs = {
        ("E%d80" % BASE_ID): (
            "event annotation has no type",
            NO_TYPE_MESSAGE_ID,
            "Events annotations type must be present and be the first annotation",
        ),
        ("E%d81" % BASE_ID): (
            "event annotation (%s) has no name",
            NO_NAME_MESSAGE_ID,
            "Events annotations name must be present",
        ),
        ("E%d82" % BASE_ID): (
            "event annotation (%s) has no data argument",
            NO_DATA_MESSAGE_ID,
            "Events annotations must include data argument",
        ),
        ("E%d83" % BASE_ID): (
            "event annotation (%s) has no status",
            NO_STATUS_MESSAGE_ID,
            "Events annotations must include the status of event",
        ),
        ("E%d84" % BASE_ID): (
            "event annotation (%s) does not have a description",
            NO_DESCRIPTION_MESSAGE_ID,
            "Events annotations must include a short description",
        ),
        ("E%d85" % BASE_ID): (
            "missing event annotation",
            MISSING_ANNOTATION,
            (
                "When an Open edX event object is created, a corresponding annotation must be present above in the"
                " same module and with a matching name",
            )
        ),
    }

    EVENT_CLASS_NAMES = ["OpenEdxPublicSignal"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_module_annotated_event_names = set()
        self.current_module_annotation_group_line_numbers = []

    @check_all_messages(msgs)
    def visit_module(self, node):
        """
        Run all checks on a single module.
        """
        self.check_module(node)

    def leave_module(self, _node):
        self.current_module_annotated_event_names.clear()
        self.current_module_annotation_group_line_numbers.clear()

    def check_annotation_group(self, search, annotations, node):
        """
        Perform checks on a single annotation group.
        """
        if not annotations:
            return

        event_type = ""
        event_name = ""
        event_data = ""
        event_description = ""
        line_number = None
        for annotation in annotations:
            if line_number is None:
                line_number = annotation["line_number"]
                self.current_module_annotation_group_line_numbers.append(line_number)
            if annotation["annotation_token"] == ".. event_type:":
                event_type = annotation["annotation_data"]
            elif annotation["annotation_token"] == ".. event_name:":
                event_name = annotation["annotation_data"]
                self.current_module_annotated_event_names.add(event_name)
            elif annotation["annotation_token"] == ".. event_data:":
                event_data = annotation["annotation_data"]
            elif annotation["annotation_token"] == ".. event_description:":
                event_description = annotation["annotation_data"]

        if not event_type:
            self.add_message(
                self.NO_TYPE_MESSAGE_ID,
                node=node,
                line=line_number,
            )

        if not event_name:
            self.add_message(
                self.NO_NAME_MESSAGE_ID,
                args=(event_type,),
                node=node,
                line=line_number,
            )

        if not event_data:
            self.add_message(
                self.NO_DATA_MESSAGE_ID,
                args=(event_type,),
                node=node,
                line=line_number,
            )

        if not event_description:
            self.add_message(
                self.NO_DESCRIPTION_MESSAGE_ID,
                args=(event_type,),
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

    def is_annotation_missing(self, node):
        """
        Check whether the node corresponds to a toggle instance creation. if yes, check that it is annotated.
        """
        if (
            not isinstance(node.func, Name)
            or node.func.name not in self.EVENT_CLASS_NAMES
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

        # Check literal event name arguments
        if node.args and isinstance(node.args[0], Const) and isinstance(node.args[0].value, str):
            event_name = node.args[0].value
            if event_name not in self.current_module_annotated_event_names:
                return True
        return False

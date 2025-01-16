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
    MISSING_OR_INCORRECT_ANNOTATION = "missing-or-incorrect-annotation"

    msgs = {
        ("E%d80" % BASE_ID): (
            "Event type must be present and be the first annotation",
            NO_TYPE_MESSAGE_ID,
            "event type must be present and be the first annotation",
        ),
        ("E%d81" % BASE_ID): (
            "Event annotation (%s) has no name",
            NO_NAME_MESSAGE_ID,
            "Event annotations must include a name",
        ),
        ("E%d82" % BASE_ID): (
            "Event annotation (%s) has no data",
            NO_DATA_MESSAGE_ID,
            "event annotations must include a data",
        ),
        ("E%d84" % BASE_ID): (
            "Event annotation (%s) has no description",
            NO_DESCRIPTION_MESSAGE_ID,
            "Events annotations must include a short description",
        ),
        ("E%d85" % BASE_ID): (
            "Event annotation is missing or incorrect",
            MISSING_OR_INCORRECT_ANNOTATION,
            (
                "When an Open edX event object is created, a corresponding annotation must be present above in the"
                " same module and with a matching type",
            )
        ),
    }

    EVENT_CLASS_NAMES = ["OpenEdxPublicSignal"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_module_annotated_event_types = []
        self.current_module_event_data = []
        self.current_module_annotation_group_line_numbers = []
        self.current_module_annotation_group_map = {}

    @check_all_messages(msgs)
    def visit_module(self, node):
        """
        Run all checks on a single module.
        """
        self.check_module(node)

    def leave_module(self, _node):
        self.current_module_annotation_group_line_numbers.clear()
        self.current_module_annotation_group_map.clear()

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
                self.current_module_annotation_group_map[line_number] = ()
            if annotation["annotation_token"] == ".. event_type:":
                event_type = annotation["annotation_data"]
            elif annotation["annotation_token"] == ".. event_name:":
                event_name = annotation["annotation_data"]
            elif annotation["annotation_token"] == ".. event_data:":
                event_data = annotation["annotation_data"]
            elif annotation["annotation_token"] == ".. event_description:":
                event_description = annotation["annotation_data"]
            if event_type and event_data:
                self.current_module_annotation_group_map[line_number] = (event_type, event_data,)

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

    @utils.only_required_for_messages(MISSING_OR_INCORRECT_ANNOTATION)
    def visit_call(self, node):
        """
        Check for missing annotations.
        """
        if self._is_annotation_missing_or_incorrect(node):
            self.add_message(
                self.MISSING_OR_INCORRECT_ANNOTATION,
                node=node,
            )

    def _is_annotation_missing_or_incorrect(self, node):
        """
        Check if an annotation is missing or incorrect for an event.

        An annotation is considered missing when:
        - The annotation is not present above the event object.

        An annotation is considered incorrect when:
        - The annotation is present above the event object but the type of the annotation does
        not match the type of the event object.
        - The annotation is present above the event object but the data of the annotation does
        not match the data of the event object.
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
        annotation_line_number = self.current_module_annotation_group_line_numbers.pop(0)

        current_annotation_group = self.current_module_annotation_group_map[annotation_line_number]
        if not current_annotation_group:
            # The annotation group with type and data for the line is empty, but should be caught by the annotation
            # checks
            return False

        current_event_type, current_event_data = current_annotation_group
        # All event definitions have two keyword arguments, the first is the event type and the second is the
        # event data. For example:
        # OpenEdxPublicSignal(
        #     event_type="org.openedx.subdomain.action.emitted.v1",
        #     event_data={"my_data": MyEventData},
        # )
        node_event_type = node.keywords[0].value.value
        node_event_data = node.keywords[1].value.items[0][1].name
        if node_event_type != current_event_type or node_event_data != current_event_data:
            return True

        return False

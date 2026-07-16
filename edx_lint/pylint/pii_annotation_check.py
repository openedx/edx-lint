"""
PII Annotation Checker — flags Django models annotated ``.. no_pii:`` that
still contain likely-PII fields or instance attributes (W7633).
"""

from pylint.checkers import BaseChecker, utils

from .common import BASE_ID, check_visitors
from ._pii_common import PiiConfigMixin


def register_checkers(linter):
    """
    Register the PII annotation checker.
    """
    linter.register_checker(PiiAnnotationChecker(linter))


@check_visitors
class PiiAnnotationChecker(PiiConfigMixin, BaseChecker):
    """
    Fires ``pii-invalid-no-pii-annotation`` (W7633) when a concrete Django model
    is annotated ``.. no_pii:`` but still has fields matching the PII terms list.
    Abstract and proxy models are skipped, mirroring django_find_annotations scope.
    """

    name = "pii-annotation-checker"

    msgs = {
        ("W%d33" % BASE_ID): (
            "Django model '%s' is annotated as no_pii but contains likely PII field(s): %s",
            "pii-invalid-no-pii-annotation",
            "Django model annotated with '.. no_pii:' contains fields that look like PII. "
            "Replace the annotation with '.. pii:' and the required metadata, or add "
            "the field name to pii-safe-key-patterns if it is genuinely non-sensitive. "
            "Only concrete (non-abstract, non-proxy) Django Model subclasses are checked, "
            "matching the scope of 'code_annotations django_find_annotations'.",
        ),
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._source_lines = []           # source lines for comment-annotation lookup
        # Config caches — reset each module via _init_pii_caches() in visit_module.
        self._pii_terms_cache = None
        self._safe_keys_cache = None
        self._django_model_bases_cache = None
        self._module_classdefs = {}       # class name → ClassDef for BFS ancestry

    @utils.only_required_for_messages("pii-invalid-no-pii-annotation")
    def visit_module(self, node):
        """
        Reset all per-module state and cache source lines for annotation lookup.
        """
        self._init_pii_caches()
        self._module_classdefs = {}
        try:
            module_bytes = node.stream().read()
            encoding = node.file_encoding or "utf-8"
            self._source_lines = module_bytes.decode(encoding).splitlines()
        except Exception:  # pylint: disable=broad-except
            self._source_lines = []

    @utils.only_required_for_messages("pii-invalid-no-pii-annotation")
    def visit_classdef(self, node):
        """
        Flag PII fields in ``.. no_pii:``-annotated Django model classes.
        """
        # Index for same-module ancestry BFS.
        self._module_classdefs[node.name] = node

        if not self._is_annotation_eligible_django_model(node):
            return
        if not self._class_has_no_pii_annotation(node):
            return

        pii_fields = self._collect_pii_fields(node)
        if pii_fields:
            self.add_message(
                "pii-invalid-no-pii-annotation",
                node=node,
                args=(node.name, ", ".join(pii_fields)),
            )

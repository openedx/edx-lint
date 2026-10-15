"""
PII Annotation Checker — flags Django models annotated ``.. no_pii:`` that
still contain PII fields or instance attributes (W7633).
"""

import re

from astroid import exceptions as astroid_exceptions
from astroid import nodes as astroid_nodes
from pylint.checkers import BaseChecker, utils

from .common import BASE_ID, check_visitors


# Regex that detects ``.. no_pii:`` in class docstrings.
_NO_PII_DOCSTRING_RE = re.compile(r"\.\.\s*no_pii", re.IGNORECASE)


def register_checkers(linter):
    """Register the PII annotation checker."""
    linter.register_checker(PiiAnnotationChecker(linter))


@check_visitors
class PiiAnnotationChecker(BaseChecker):
    """Flags concrete ``.. no_pii:`` Django models that still contain PII."""

    name = "pii-annotation-checker"
    PII_INVALID_ANNOTATION_MESSAGE_ID = "pii-invalid-no-pii-annotation"

    # Message definitions
    msgs = {
        ("W%d33" % BASE_ID): (
            "Django model '%s' is annotated as no_pii "
            "but contains PII field: '%s'",
            PII_INVALID_ANNOTATION_MESSAGE_ID,
            "Model claims no_pii but has PII-named fields. "
            "Update annotation to '.. pii:' or rename the field.",
        ),
    }

    # Options must be defined on the checker so it can be configured
    # independently.
    options = (
        (
            "pii-terms",
            {
                "default": None,
                "type": "csv",
                "metavar": "<comma-separated PII terms>",
                "help": "List of PII terms to flag.",
            },
        ),
        (
            "pii-django-model-bases",
            {
                "default": "Model",
                "type": "csv",
                "metavar": "<comma-separated base class names>",
                "help": "Base class *names* that identify a Django model.",
            },
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._parsed_pii_terms = None
        self._parsed_django_model_bases = None
        self._module_classdefs = {}

    @utils.only_required_for_messages("pii-invalid-no-pii-annotation")
    def visit_module(self, _node):
        """Reset all per-module state."""
        # Reset parsed configs so option values are re-read for each module.
        self._reset_parsed_config()
        self._parsed_django_model_bases = None
        self._module_classdefs = {}

    def _reset_parsed_config(self):
        """Reset per-module parsed configs to None."""
        self._parsed_pii_terms = None

    def _parse_and_store_config(self):
        """Parse pii-terms config on first call within a module."""
        if self._parsed_pii_terms is not None:
            return
        linter_config = self.linter.config
        raw_terms = getattr(linter_config, "pii_terms", None)
        if raw_terms is None:
            raise ValueError("The 'pii_terms' setting must be configured.")
        self._parsed_pii_terms = [
            term.strip().lower() for term in raw_terms if term.strip()
        ]

    def _pii_terms(self):
        self._parse_and_store_config()
        return self._parsed_pii_terms

    def _is_pii_name(self, name):
        """
        Return True if *name* is a PII identifier.

        Substring match of any pii-term inside *name* → PII.
        """
        normalized_name = name.lower()
        return any(term in normalized_name for term in self._pii_terms())

    @utils.only_required_for_messages(PII_INVALID_ANNOTATION_MESSAGE_ID)
    def visit_classdef(self, node):
        """
        Detect PII fields in Django model classes annotated
        with ``.. no_pii:``.
        """
        # Index every class definition for same-module ancestry BFS.
        self._module_classdefs[node.name] = node

        if not self._is_annotation_eligible_django_model(node):
            return
        if not self._docstring_has_no_pii(node):
            return

        pii_fields = self._collect_pii_fields(node)
        for field_name, field_node in pii_fields:
            self.add_message(
                self.PII_INVALID_ANNOTATION_MESSAGE_ID,
                node=field_node,
                args=(node.name, field_name),
            )

    def _is_annotation_eligible_django_model(self, node):
        """
        Return True if *node* is a concrete (non-abstract, non-proxy)
        Django model.

        Tries astroid's resolved ancestor walk first (works when Django is
        importable), then falls back to raw AST base-name BFS for standalone
        pylint runs.
        """
        model_bases = self._django_model_bases()

        # Primary path: astroid type-inference ancestor resolution.
        is_model_subclass = False
        try:
            for ancestor in node.ancestors():
                if ancestor.name in model_bases:
                    is_model_subclass = True
                    break
        except astroid_exceptions.AstroidError:
            # Inference failed (e.g. Django not installed).
            # Fall back to raw AST.
            pass

        # Fallback: walk raw AST base names for standalone/offline runs.
        if not is_model_subclass:
            is_model_subclass = self._raw_ast_is_model_subclass(node)

        if not is_model_subclass:
            return False

        # Skip abstract and proxy models (detected via inner Meta class).
        if any(
            self._meta_has_true_flag(node, flag)
            for flag in ("abstract", "proxy")
        ):
            return False

        return True

    def _django_model_bases(self):
        """
        Return the set of base class names that identify a Django model.

        Lazily initialised from ``pii-django-model-bases`` linter option on
        first call per module; reset to None by visit_module so options are
        re-read for each module.
        """
        if self._parsed_django_model_bases is None:
            raw = getattr(
                self.linter.config,
                "pii_django_model_bases",
                ["Model"],
            )
            self._parsed_django_model_bases = {
                base.strip() for base in raw if base.strip()
            }
        return self._parsed_django_model_bases

    def _raw_ast_is_model_subclass(self, node):
        """
        Return True if *node* inherits from a model base using BFS over
        raw AST names.

        Only classes defined in the same module can be followed transitively.
        External bases (e.g. ``django.db.models.Model``) are matched by bare
        name against ``pii-django-model-bases``.
        """
        model_bases = self._django_model_bases()
        visited = set()
        queue = list(self._direct_base_names(node))
        while queue:
            name = queue.pop(0)
            if name in visited:
                continue
            visited.add(name)
            if name in model_bases:
                return True
            # Follow same-module parent if known.
            parent_node = self._module_classdefs.get(name)
            if parent_node is not None:
                queue.extend(self._direct_base_names(parent_node))
        return False

    @staticmethod
    def _direct_base_names(classdef_node):
        """
        Yield the simple name of each direct base class in *classdef_node*.

        Handles both ``Name`` nodes (``Model``) and ``Attribute`` nodes
        (``models.Model`` → yields ``"Model"``).
        """
        for base in classdef_node.bases:
            if isinstance(base, astroid_nodes.Name):
                yield base.name
            elif isinstance(base, astroid_nodes.Attribute):
                yield base.attrname

    @staticmethod
    def _meta_has_true_flag(classdef_node, flag_name):
        """
        Return True if the inner ``Meta`` class sets ``flag_name = True``.
        """
        for child in classdef_node.body:
            if not (
                isinstance(child, astroid_nodes.ClassDef)
                and child.name == "Meta"
            ):
                continue
            for stmt in child.body:
                if not isinstance(stmt, astroid_nodes.Assign):
                    continue
                for target in stmt.targets:
                    if (
                        isinstance(target, astroid_nodes.AssignName)
                        and target.name == flag_name
                        and isinstance(stmt.value, astroid_nodes.Const)
                        and stmt.value.value is True
                    ):
                        return True
        return False

    def _docstring_has_no_pii(self, node):
        """
        Return True if the class docstring contains ``.. no_pii:``.
        """
        docstring = node.doc_node.value if node.doc_node else ""
        return bool(_NO_PII_DOCSTRING_RE.search(docstring))

    def _collect_pii_fields(self, node):
        """
        Return PII-like field names and their AST nodes found in
        the class body.

        Scans:
        - Class-level ``Assign`` targets:    ``email = models.EmailField()``
        - Class-level ``AnnAssign`` targets: ``email: str = ""``
        - Method-body instance assignments (both ``Assign`` and ``AnnAssign``):
          ``self.email = ...`` and ``self.email: str = ...``.
        """
        found = []

        for child in node.body:
            # Class-level simple assignment: ``email = ...``
            if isinstance(child, astroid_nodes.Assign):
                for target in child.targets:
                    if isinstance(target, astroid_nodes.AssignName):
                        if self._is_pii_name(target.name):
                            found.append((target.name, child))

            # Class-level annotated assignment: ``email: str = ""``
            elif isinstance(child, astroid_nodes.AnnAssign):
                if isinstance(child.target, astroid_nodes.AssignName):
                    if self._is_pii_name(child.target.name):
                        found.append((child.target.name, child))

            # Instance attributes set inside methods: ``self.email = ...``
            elif isinstance(child, astroid_nodes.FunctionDef):
                for stmt in child.nodes_of_class(astroid_nodes.Assign):
                    for target in stmt.targets:
                        if (
                            isinstance(target, astroid_nodes.AssignAttr)
                            and isinstance(target.expr, astroid_nodes.Name)
                            and target.expr.name == "self"
                            and self._is_pii_name(target.attrname)
                        ):
                            found.append((f"self.{target.attrname}", stmt))

                # Annotated instance assignments: ``self.email: str = ...``
                for stmt in child.nodes_of_class(astroid_nodes.AnnAssign):
                    target = stmt.target
                    if (
                        isinstance(target, astroid_nodes.AssignAttr)
                        and isinstance(target.expr, astroid_nodes.Name)
                        and target.expr.name == "self"
                        and self._is_pii_name(target.attrname)
                    ):
                        found.append((f"self.{target.attrname}", stmt))

        return found

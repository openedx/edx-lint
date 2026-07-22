"""
PII Annotation Checker — flags Django models annotated ``.. no_pii:`` that
still contain likely-PII fields or instance attributes (W7633).
"""

import re

from astroid import exceptions as astroid_exceptions
from astroid import nodes as astroid_nodes
from pylint.checkers import BaseChecker, utils

from .common import BASE_ID, check_visitors
from ._pii_common import PiiConfigMixin


# ---------------------------------------------------------------------------
# Annotation-specific constants
# ---------------------------------------------------------------------------

# Regexes that detect ``.. no_pii:`` in class docstrings and comment lines.
_NO_PII_DOCSTRING_RE = re.compile(r"\.\.\s*no_pii", re.IGNORECASE)
_NO_PII_COMMENT_RE = re.compile(r"[\s]*#[\s]*\.\.\s*no_pii", re.IGNORECASE)

# Number of source lines *above* the ``class`` statement to scan for a
# comment-style ``# .. no_pii:`` annotation.  10 lines is wide enough to
# bridge decorators, blank lines, and other separators.
_ANNOTATION_LOOKAHEAD = 10


def register_checkers(linter):
    """Register the PII annotation checker."""
    linter.register_checker(PiiAnnotationChecker(linter))


@check_visitors
class PiiAnnotationChecker(PiiConfigMixin, BaseChecker):
    """
    Fires ``pii-invalid-no-pii-annotation`` (W7633) when a concrete Django model
    is annotated ``.. no_pii:`` but still has fields matching the PII terms list.
    Abstract and proxy models are skipped, mirroring django_find_annotations scope.
    """

    name = "pii-annotation-checker"

    # Message definitions
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

    # Lifecycle
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Cached per-module source lines for comment-style annotation lookup.
        self._source_lines = []
        # Config caches — explicitly initialised here so pylint knows they
        # exist; reset per-module via _init_pii_caches() in visit_module.
        self._pii_terms_cache = None
        self._safe_keys_cache = None
        self._django_model_bases_cache = None
        # Per-module mapping of class name → ClassDef node, used by
        # _raw_ast_is_model_subclass to resolve same-module ancestors.
        self._module_classdefs = {}

    # AST Visitors
    @utils.only_required_for_messages("pii-invalid-no-pii-annotation")
    def visit_module(self, node):
        """Cache source lines and reset all per-module state."""
        # Reset config caches so option values are re-read for each module.
        self._init_pii_caches()
        self._django_model_bases_cache = None
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
        Detect PII fields in Django model classes annotated with ``.. no_pii:``.
        """
        # Index every class definition in the module for same-module ancestry BFS.
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

    # Django model eligibility helpers
    def _is_annotation_eligible_django_model(self, node):
        """
        Return True if *node* is a concrete (non-abstract, non-proxy) Django model.

        Tries astroid's resolved ancestor walk first (works when Django is importable),
        then falls back to raw AST base-name BFS for standalone pylint runs.
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
            # Inference failed (e.g. Django not installed) — fall back to raw AST.
            pass

        # Fallback: walk raw AST base names for standalone/offline runs.
        if not is_model_subclass:
            is_model_subclass = self._raw_ast_is_model_subclass(node)

        if not is_model_subclass:
            return False

        # Skip abstract and proxy models (detected via inner Meta class).
        if any(self._meta_has_true_flag(node, flag) for flag in ("abstract", "proxy")):
            return False

        return True

    def _django_model_bases(self):
        """
        Return the set of base class names that identify a Django model.

        Lazily initialised from ``pii-django-model-bases`` linter option on
        first call per module; reset to None by visit_module so options are
        re-read for each module.
        """
        if self._django_model_bases_cache is None:
            raw = getattr(self.linter.config, "pii_django_model_bases", ["Model"])
            self._django_model_bases_cache = {b.strip() for b in raw if b.strip()}
        return self._django_model_bases_cache

    def _raw_ast_is_model_subclass(self, node):
        """
        Return True if *node* inherits from a model base by BFS over raw AST names.

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
            if not (isinstance(child, astroid_nodes.ClassDef) and child.name == "Meta"):
                continue
            for stmt in child.body:
                if not isinstance(stmt, astroid_nodes.Assign):
                    continue
                for target in stmt.targets:
                    if (isinstance(target, astroid_nodes.AssignName)
                            and target.name == flag_name
                            and isinstance(stmt.value, astroid_nodes.Const)
                            and stmt.value.value is True):
                        return True
        return False

    # Annotation detection helpers
    def _class_has_no_pii_annotation(self, node):
        """
        Return True if *node* carries a ``.. no_pii:`` annotation.

        Checks the class docstring first, then comment lines above the class.
        """
        return self._docstring_has_no_pii(node) or self._comment_has_no_pii(node)

    def _docstring_has_no_pii(self, node):
        """
        Return True if the class docstring contains ``.. no_pii:``.
        """
        docstring = node.doc_node.value if node.doc_node else ""
        return bool(_NO_PII_DOCSTRING_RE.search(docstring))

    def _comment_has_no_pii(self, node):
        """
        Return True if a ``# .. no_pii:`` comment appears above the class.

        Scans up to ``_ANNOTATION_LOOKAHEAD`` source lines before the class
        statement, covering decorators and blank lines between the comment and
        the class declaration.
        """
        if not self._source_lines:
            return False
        # node.lineno is 1-indexed; convert to 0-indexed for list access.
        end = node.lineno - 1       # exclusive (the ``class`` line itself)
        start = max(0, end - _ANNOTATION_LOOKAHEAD)
        for line in self._source_lines[start:end]:
            if _NO_PII_COMMENT_RE.match(line):
                return True
        return False

    # Field collection helpers
    def _collect_pii_fields(self, node):
        """
        Return all PII-like field name strings found in the class body.

        Scans:
        - Class-level ``Assign`` targets:    ``email = models.EmailField()``
        - Class-level ``AnnAssign`` targets: ``email: str = ""``
        - ``self.X`` attribute assignments in method bodies, reported as ``"self.X"``.
        """
        found = []

        for child in node.body:
            # Class-level simple assignment: ``email = ...``
            if isinstance(child, astroid_nodes.Assign):
                for target in child.targets:
                    if isinstance(target, astroid_nodes.AssignName):
                        if self._is_pii_name(target.name):
                            found.append(target.name)

            # Class-level annotated assignment: ``email: str = ""``
            elif isinstance(child, astroid_nodes.AnnAssign):
                if isinstance(child.target, astroid_nodes.AssignName):
                    if self._is_pii_name(child.target.name):
                        found.append(child.target.name)

            # Instance attributes set inside methods: ``self.email = ...``
            elif isinstance(child, astroid_nodes.FunctionDef):
                for stmt in child.nodes_of_class(astroid_nodes.Assign):
                    for target in stmt.targets:
                        if (isinstance(target, astroid_nodes.AssignAttr)
                                and isinstance(target.expr, astroid_nodes.Name)
                                and target.expr.name == "self"
                                and self._is_pii_name(target.attrname)):
                            found.append(f"self.{target.attrname}")

        return found

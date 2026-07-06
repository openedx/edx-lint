"""
PII Annotation Checker for edx-lint.

Detects Django model classes annotated with ``.. no_pii:`` (in their docstring
or in a comment immediately above the class) that still contain likely-PII
fields or instance attributes.

Message ID: ``pii-invalid-no-pii-annotation`` (W7633)
Checker name: ``pii-annotation-checker``

Only Django model classes that are annotation-eligible are checked — i.e.
classes that are a non-abstract, non-proxy subclass of
``django.db.models.Model``.  This exactly mirrors the set of models
considered by ``code_annotations django_find_annotations`` (the
``DjangoSearch.requires_annotations()`` predicate).

Usage
-----
Enable or disable on the command line::

    pylint --enable=pii-invalid-no-pii-annotation  src/
    pylint --disable=pii-annotation-checker        src/   # disables whole checker

Inline suppression::

    class MyModel(Model):  # pylint: disable=pii-invalid-no-pii-annotation
        '''.. no_pii:'''
        email = None  # genuinely safe in this context

Reference: OEP-30 — PII Markup and Auditing
https://open-edx-proposals.readthedocs.io/en/latest/best-practices/oep-0030-bp-personally-identifiable-information.html
"""

from pylint.checkers import BaseChecker, utils

from .common import BASE_ID, check_visitors
from ._pii_common import PiiConfigMixin


def register_checkers(linter):
    """Register the PII annotation checker."""
    linter.register_checker(PiiAnnotationChecker(linter))


@check_visitors
class PiiAnnotationChecker(PiiConfigMixin, BaseChecker):
    """Checks for stale ``.. no_pii:`` annotations on Django model classes.

    Fires ``pii-invalid-no-pii-annotation`` (W7633) when a concrete
    (non-abstract, non-proxy) Django model class is annotated with
    ``.. no_pii:`` yet still contains fields or instance attributes whose
    names match the configured PII terms.

    Annotation forms recognised:

    * Docstring containing ``.. no_pii:`` (primary — edx-platform convention).
    * Comment ``# .. no_pii:`` appearing within ``_ANNOTATION_LOOKAHEAD`` lines
      above the ``class`` keyword (fallback).

    This checker does **not** define its own options.  All PII-related options
    (``pii-terms``, ``pii-safe-key-patterns``, ``pii-django-model-bases``, etc.)
    are defined by :class:`~edx_lint.pylint.pii_squelch_check.PiiMissingSquelchChecker`
    and are read from ``linter.config`` via :class:`~._pii_common.PiiConfigMixin`
    with safe defaults, so this checker is independently usable even if the
    squelch checker is not loaded.
    """

    name = "pii-annotation-checker"

    # ------------------------------------------------------------------
    # Message definitions
    # ------------------------------------------------------------------
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

    # No options are defined here — all shared PII options live on
    # PiiMissingSquelchChecker and are accessed through self.linter.config.

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Cached per-module source lines for comment-style annotation lookup.
        self._source_lines = []
        # Config caches — reset per module, populated lazily on first use.
        self._init_pii_caches()
        # Per-module mapping of class name → ClassDef node, used by
        # _raw_ast_is_model_subclass to resolve same-module ancestors.
        self._module_classdefs = {}

    # ------------------------------------------------------------------
    # AST Visitors
    # ------------------------------------------------------------------

    @utils.only_required_for_messages("pii-invalid-no-pii-annotation")
    def visit_module(self, node):
        """Cache source lines and reset all per-module state."""
        # Reset config caches so option values are re-read for each module.
        self._pii_terms_cache = None
        self._safe_functions_cache = None
        self._safe_keys_cache = None
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
        """Detect PII fields in Django model classes annotated with ``.. no_pii:``.

        Only checks classes that are annotation-eligible Django models, mirroring
        the ``DjangoSearch.requires_annotations()`` predicate used by
        ``code_annotations django_find_annotations``:

        - Must be a subclass of ``django.db.models.Model`` (or a configured base).
        - Must **not** be abstract (no ``abstract = True`` in the inner ``Meta``).
        - Must **not** be a proxy model (no ``proxy = True`` in the inner ``Meta``).
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

"""
PII Missing Squelch Checker — flags log/print/exception calls inside Django
model methods that expose PII without a SQUELCH_PII_IN_LOGS guard (W7630).
"""

from astroid import nodes as astroid_nodes
from pylint.checkers import BaseChecker, utils

from .common import BASE_ID, check_visitors
from ._pii_common import _LOG_METHODS, PiiConfigMixin


def register_checkers(linter):
    """
    Register the PII missing-squelch checker.
    """
    linter.register_checker(PiiMissingSquelchChecker(linter))


@check_visitors
class PiiMissingSquelchChecker(PiiConfigMixin, BaseChecker):
    """
    Flags unguarded PII in log/print/exception calls inside Django model methods.
    """

    name = "pii-missing-squelch"

    msgs = {
        ("W%d30" % BASE_ID): (
            "PII term '%s' exposed in %s without a SQUELCH_PII_IN_LOGS guard. "
            "Wrap with: if not SQUELCH_PII_IN_LOGS: ...",
            "pii-missing-squelch",
            "A log call, print/stdout/stderr write, or raised exception inside a "
            "Django model method exposes likely PII without a SQUELCH_PII_IN_LOGS "
            "guard. Wrap the offending line with: if not SQUELCH_PII_IN_LOGS: ...",
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

    @utils.only_required_for_messages("pii-missing-squelch")
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

    @utils.only_required_for_messages("pii-missing-squelch")
    def visit_classdef(self, node):
        """
        Index class definitions for same-module ancestry resolution.
        """
        self._module_classdefs[node.name] = node

    @utils.only_required_for_messages("pii-missing-squelch")
    def visit_call(self, node):
        """
        Check log and print/stdout/stderr calls for unguarded PII.
        """
        if self._is_log_call(node):
            self._check_sink(node, "log call")
        elif self._is_print_call(node):
            self._check_sink(node, "print/stdout/stderr")

    @utils.only_required_for_messages("pii-missing-squelch")
    def visit_raise(self, node):
        """
        Check raised exceptions for unguarded PII.
        """
        exc = node.exc
        if not self._requires_squelch_check(node) or exc is None or not isinstance(exc, astroid_nodes.Call):
            return
        all_args = list(exc.args) + [kw.value for kw in (exc.keywords or [])]
        for arg in all_args:
            pii_term = self._contains_pii(arg)
            if pii_term:
                if not self._is_inside_squelch_guard(node):
                    self.add_message(
                        "pii-missing-squelch",
                        node=exc,
                        args=(pii_term, "raised exception"),
                    )
                return  # at most one message per raise

    def _is_log_call(self, node):
        """
        Return True if *node* is a standard logging method call.
        """
        if not isinstance(node.func, astroid_nodes.Attribute):
            return False
        return node.func.attrname in _LOG_METHODS

    def _is_print_call(self, node):
        """
        Return True if *node* is a print() or sys.stdout/stderr write() call.
        """
        # bare print()
        if isinstance(node.func, astroid_nodes.Name) and node.func.name == "print":
            return True
        # sys.stdout.write(...) / sys.stderr.write(...) / self.stdout.write(...)
        if (
            isinstance(node.func, astroid_nodes.Attribute)
            and node.func.attrname == "write"
            and isinstance(node.func.expr, astroid_nodes.Attribute)
            and node.func.expr.attrname in ("stdout", "stderr")
        ):
            return True
        return False

    def _check_sink(self, node, sink_label):
        """
        Emit ``pii-missing-squelch`` if *node* has a PII argument outside a squelch guard.
        """
        if not self._requires_squelch_check(node):
            return

        all_args = list(node.args) + [kw.value for kw in (node.keywords or [])]
        for arg in all_args:
            pii_term = self._contains_pii(arg)
            if pii_term:
                if not self._is_inside_squelch_guard(node):
                    self.add_message(
                        "pii-missing-squelch",
                        node=node,
                        args=(pii_term, sink_label),
                    )
                return  # at most one message per call

    def _requires_squelch_check(self, node):
        """
        Return True if *node* is inside an eligible Django model without ``.. no_pii:``.
        """
        current = node.parent
        while current is not None:
            if isinstance(current, astroid_nodes.ClassDef):
                if self._is_annotation_eligible_django_model(current):
                    # Require squelch guard only when the model lacks .. no_pii:.
                    return not self._class_has_no_pii_annotation(current)
                # Inside a non-model class — keep walking up.
            current = current.parent
        # Not inside any Django model class → out of scope, skip.
        return False

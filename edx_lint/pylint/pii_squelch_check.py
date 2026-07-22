"""
PII Missing Squelch Checker — flags log/print/exception calls that expose PII
without a SQUELCH_PII_IN_LOGS guard (W7630).

Checks run across the entire repository, not limited to Django models.
"""

from astroid import nodes as astroid_nodes
from pylint.checkers import BaseChecker, utils

from .common import BASE_ID, check_visitors
from ._pii_common import PiiConfigMixin


# ---------------------------------------------------------------------------
# Squelch-specific constants
# ---------------------------------------------------------------------------

# Logging method names recognised as PII output sinks.
_LOG_METHODS = frozenset({
    "debug", "info", "warning", "warn", "error",
    "critical", "exception", "log",
})

# Default name of the feature-flag that gates PII-inclusive output.
_DEFAULT_SQUELCH_FLAG = "SQUELCH_PII_IN_LOGS"


def register_checkers(linter):
    """Register the PII missing-squelch checker."""
    linter.register_checker(PiiMissingSquelchChecker(linter))


@check_visitors
class PiiMissingSquelchChecker(PiiConfigMixin, BaseChecker):
    """
    Flags unguarded PII in log/print/exception calls across all Python code.
    """

    name = "pii-missing-squelch"

    # Message definitions — one symbol covers log + print + exception
    msgs = {
        ("W%d30" % BASE_ID): (
            "PII term '%s' exposed in %s without a SQUELCH_PII_IN_LOGS guard. "
            "Wrap with: if not SQUELCH_PII_IN_LOGS: ...",
            "pii-missing-squelch",
            "A log call, print/stdout/stderr write, or raised exception exposes "
            "likely PII without a SQUELCH_PII_IN_LOGS "
            "guard.  Wrap the offending line with: if not SQUELCH_PII_IN_LOGS: ...",
        ),
    }

    # Configurable options
    # NOTE: All shared PII options are declared here so they appear in
    #       linter.config before PiiAnnotationChecker reads them via getattr().
    options = (
        (
            "pii-terms",
            {
                "default": (
                    # Conservative MVP defaults: high-sensitivity, commonly-exposed terms.
                    # Repositories can expand this list via pylintrc [PII] pii-terms.
                    "email, username, password"
                ),
                "type": "csv",
                "metavar": "<comma-separated PII terms>",
                "help": (
                    "Comma-separated OEP-0030 PII identifier substrings matched against "
                    "variable names and attribute accesses passed to log/print/exception "
                    "sinks.  String literals are NOT matched — only variable/attribute "
                    "references."
                ),
            },
        ),
        (
            "pii-safe-key-patterns",
            {
                "default": (
                    "user_id, course_id, thread_id, comment_id, block_id, "
                    "usage_id, usage_key, anonymous_user_id, service_username, "
                    "email_enabled, email_sent_on, email_scheduled, "
                    "require_course_email_auth, reported_content_email_notifications, "
                    "email_reminder_sent, eligibility_email_message, receipt_email_message, "
                    "proctoring_escalation_email, email_cadence, "
                    "attr_full_name, default_full_name, attr_first_name, default_first_name, "
                    "attr_last_name, default_last_name, attr_username, default_username, "
                    "attr_email, default_email, skip_email_verification, location, _location, "
                    "example_full_name"
                ),
                "type": "csv",
                "metavar": "<comma-separated safe key patterns>",
                "help": (
                    "Exact identifiers that look like PII terms but are approved as "
                    "non-sensitive (e.g. surrogate keys, flag fields).  Exact match only."
                ),
            },
        ),
        (
            "pii-squelch-flag",
            {
                "default": _DEFAULT_SQUELCH_FLAG,
                "type": "string",
                "metavar": "<flag name>",
                "help": (
                    "Name of the feature toggle that gates PII-inclusive log/print/exception "
                    "output.  PII sinks must be inside an if-block that tests this flag. "
                    "Default: SQUELCH_PII_IN_LOGS."
                ),
            },
        ),
        (
            "pii-django-model-bases",
            {
                "default": "Model",
                "type": "csv",
                "metavar": "<comma-separated base class names>",
                "help": (
                    "Base class *names* that identify a Django model.  Used by "
                    "pii-invalid-no-pii-annotation (W7633).  Default: Model."
                ),
            },
        ),
    )

    # Lifecycle
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Config caches — reset per-module via _init_pii_caches() in visit_module.
        self._pii_terms_cache = None
        self._safe_keys_cache = None

    # AST Visitors
    @utils.only_required_for_messages("pii-missing-squelch")
    def visit_module(self, node):  # pylint: disable=unused-argument
        """Reset per-module config caches."""
        self._init_pii_caches()

    @utils.only_required_for_messages("pii-missing-squelch")
    def visit_call(self, node):
        """
        Check logging and print/stdout/stderr calls for unguarded PII.
        """
        if self._is_log_call(node):
            self._check_sink(node, "log call")
        elif self._is_print_call(node):
            self._check_sink(node, "print/stdout/stderr")

    @utils.only_required_for_messages("pii-missing-squelch")
    def visit_raise(self, node):
        """
        Check raised exceptions for unguarded PII in their messages.
        """
        if node.exc is None:
            return
        exc = node.exc
        if not isinstance(exc, astroid_nodes.Call):
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

    # Sink identification helpers
    def _is_log_call(self, node):
        """
        Return True if *node* is a call to a standard logging method.
        """
        if not isinstance(node.func, astroid_nodes.Attribute):
            return False
        return node.func.attrname in _LOG_METHODS

    def _is_print_call(self, node):
        """
        Return True if *node* is a print() or stdout/stderr write() call.
        """
        # bare print()
        if isinstance(node.func, astroid_nodes.Name) and node.func.name == "print":
            return True
        # sys.stdout.write(...) / sys.stderr.write(...) / self.stdout.write(...)
        if isinstance(node.func, astroid_nodes.Attribute) and node.func.attrname == "write":
            return True
        return False

    def _check_sink(self, node, sink_label):
        """
        Emit ``pii-missing-squelch`` if any argument of *node* contains PII
        and the call is not inside a SQUELCH_PII_IN_LOGS guard.
        """
        all_args = list(node.args)
        for kw in node.keywords or []:
            all_args.append(kw.value)
        for arg in all_args:
            pii_term = self._contains_pii(arg)
            if pii_term:
                if not self._is_inside_squelch_guard(node):
                    self.add_message(
                        "pii-missing-squelch",
                        node=node,
                        args=(pii_term, sink_label),
                    )
                return  # at most one message per call-site

    # PII detection helpers
    def _contains_pii(self, node):
        """
        Recursively inspect *node* and return the first PII term found, or None.

        Checked node types:
        - ``Name``: plain variable reference — check the variable name.
        - ``Attribute``: ``self.email`` — check the attribute name only.
        - ``Call``: recurse into positional args and keyword values.
        - ``JoinedStr`` (f-string): recurse into each ``FormattedValue`` child.
        - ``BinOp``: recurse left and right (catches ``"email: %s" % email``).
        - ``Tuple / List / Set``: recurse into each element.
        - ``Dict``: recurse into values (keys are typically string literals).
        - ``Const`` (string literal): never flagged — format strings are safe.
        """
        if node is None:
            return None

        match node:
            # A plain name: check it directly.
            case astroid_nodes.Name():
                if self._is_pii_name(node.name):
                    return node.name

            # An attribute access (e.g. user.email, request.user.username).
            case astroid_nodes.Attribute():
                if self._is_pii_name(node.attrname):
                    return node.attrname

            # A call: recurse into args and keyword values.
            case astroid_nodes.Call():
                for arg in node.args:
                    found = self._contains_pii(arg)
                    if found:
                        return found
                for kw in node.keywords or []:
                    found = self._contains_pii(kw.value)
                    if found:
                        return found

            # f-string: recurse into each interpolated {expr}.
            case astroid_nodes.JoinedStr():
                for child in node.values:
                    if isinstance(child, astroid_nodes.FormattedValue):
                        found = self._contains_pii(child.value)
                        if found:
                            return found

            # Binary op (e.g. "hello " + username  or  "email: %s" % email).
            case astroid_nodes.BinOp():
                return self._contains_pii(node.left) or self._contains_pii(node.right)

            # Tuple / List / Set: recurse into each element.
            case astroid_nodes.Tuple() | astroid_nodes.List() | astroid_nodes.Set():
                for elt in node.elts:
                    found = self._contains_pii(elt)
                    if found:
                        return found

            # Dict: recurse into values (keys are usually string identifiers).
            case astroid_nodes.Dict():
                for _key, value in node.items:
                    found = self._contains_pii(value)
                    if found:
                        return found

        return None

    # Squelch-guard helpers
    def _squelch_flag(self):
        """Return the configured squelch feature-flag name."""
        return getattr(self.linter.config, "pii_squelch_flag", _DEFAULT_SQUELCH_FLAG)

    def _test_references_flag(self, test, flag):
        """
        Return True if the AST condition *test* references *flag*.

        Recognised guard patterns:
        1. ``getattr(settings, 'SQUELCH_PII_IN_LOGS', False)``  (Call → getattr)
        2. ``settings.SQUELCH_PII_IN_LOGS``                     (Attribute)
        3. ``settings.FEATURES.get('SQUELCH_PII_IN_LOGS')``     (Call → .get)
        4. ``settings.FEATURES['SQUELCH_PII_IN_LOGS']``         (Subscript)
        5. ``SQUELCH_PII_IN_LOGS.is_enabled()``                 (Call → method)
        6. ``SQUELCH_PII_IN_LOGS``                              (bare Name)
        7. ``not SQUELCH_PII_IN_LOGS``  (and all negated forms) (UnaryOp)
        """
        # Pattern 1: getattr(settings, 'FLAG', False)
        if (isinstance(test, astroid_nodes.Call)
                and isinstance(test.func, astroid_nodes.Name)
                and test.func.name == "getattr"
                and len(test.args) >= 2):
            second_arg = test.args[1]
            if isinstance(second_arg, astroid_nodes.Const) and second_arg.value == flag:
                return True

        # Pattern 2: settings.FLAG  (Attribute)
        if isinstance(test, astroid_nodes.Attribute) and test.attrname == flag:
            return True

        # Pattern 3: settings.FEATURES.get('FLAG')
        if (isinstance(test, astroid_nodes.Call)
                and isinstance(test.func, astroid_nodes.Attribute)
                and test.func.attrname == "get"
                and test.args):
            first_arg = test.args[0]
            if isinstance(first_arg, astroid_nodes.Const) and first_arg.value == flag:
                return True

        # Pattern 4: settings.FEATURES['FLAG']  (Subscript)
        if isinstance(test, astroid_nodes.Subscript):
            slc = test.slice
            # Compatibility: older astroid versions wrap slices in an Index node.
            _IndexNode = getattr(astroid_nodes, "Index", None)
            if _IndexNode is not None and isinstance(slc, _IndexNode):  # pylint: disable=isinstance-second-argument-not-valid-type
                slc = slc.value
            if isinstance(slc, astroid_nodes.Const) and slc.value == flag:
                return True

        # Pattern 5: FLAG.is_enabled() / FLAG.is_active() / FLAG.is_waffle_flag_active()
        if (isinstance(test, astroid_nodes.Call)
                and isinstance(test.func, astroid_nodes.Attribute)
                and test.func.attrname in ("is_enabled", "is_active", "is_waffle_flag_active")):
            if self._test_references_flag(test.func.expr, flag):
                return True

        # Pattern 6: bare Name
        if isinstance(test, astroid_nodes.Name) and test.name == flag:
            return True

        # Pattern 7 & all negated forms: not <expr>
        if isinstance(test, astroid_nodes.UnaryOp) and test.op == "not":
            return self._test_references_flag(test.operand, flag)

        return False

    def _is_inside_squelch_guard(self, node):
        """
        Return True if *node* is nested inside any branch of an if-statement
        whose condition tests the squelch flag.

        Any if-block referencing the flag — ``if FLAG:``, ``if not FLAG:``,
        or any ``settings.*`` / ``getattr`` / method-call equivalent — counts
        as a guard for both the if-body and the else-body.
        """
        flag = self._squelch_flag()
        current = node.parent
        while current is not None:
            if isinstance(current, astroid_nodes.Module):
                break
            if isinstance(current, astroid_nodes.If):
                if self._test_references_flag(current.test, flag):
                    return True
            current = current.parent
        return False

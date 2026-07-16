"""
Shared PII checker infrastructure: constants, option defaults, and helpers.

- ``PiiOptionsChecker``: registers all [PII] pylint options once so both
  checkers can read them from ``linter.config`` without ordering constraints.
- ``PiiConfigMixin``: mixin with cached config access and all PII-detection
  helpers shared by ``PiiMissingSquelchChecker`` and ``PiiAnnotationChecker``.
"""

import re

from astroid import nodes as astroid_nodes
from pylint.checkers import BaseChecker

from .common import check_visitors


# Logging method names treated as output sinks.
_LOG_METHODS = frozenset({
    "debug", "info", "warning", "warn", "error",
    "critical", "exception", "log",
})

# Regexes for ``.. no_pii:`` in docstrings and inline comments.
_NO_PII_DOCSTRING_RE = re.compile(r"\.\.\s*no_pii", re.IGNORECASE)
_NO_PII_COMMENT_RE = re.compile(r"[\s]*#[\s]*\.\.\s*no_pii", re.IGNORECASE)

# Lines above ``class`` to scan for a comment-style annotation.
_ANNOTATION_LOOKAHEAD = 5

# Default squelch feature-flag name.
_DEFAULT_SQUELCH_FLAG = "SQUELCH_PII_IN_LOGS"

# OEP-0030 PII identifier substrings — substring-matched against variable names.
_DEFAULT_PII_TERMS = [
    "email", "secondary_email",
    "username", "retired_username",
    "password",
    "full_name", "first_name", "last_name",
    "phone", "phone_number",
    "birth_date",
    "ip_address",
    "address", "mailing_address",
    "gender",
    "profile_image",
    "job_title",
    "social_link",
]

# Exact-match safe keys: identifiers that look like PII but are not sensitive.
_DEFAULT_SAFE_KEYS = [
    "user_id", "course_id", "thread_id", "comment_id",
    "block_id", "usage_id", "usage_key", "anonymous_user_id",
    "service_username",
    "email_enabled", "email_sent_on", "email_scheduled",
    "require_course_email_auth", "reported_content_email_notifications",
    "email_reminder_sent", "eligibility_email_message", "receipt_email_message",
    "proctoring_escalation_email", "email_cadence",
    "attr_full_name", "default_full_name", "attr_first_name", "default_first_name",
    "attr_last_name", "default_last_name", "attr_username", "default_username",
    "attr_email", "default_email", "skip_email_verification",
    "location", "_location",
    "example_full_name",
]


# PiiOptionsChecker — owns all [PII] option declarations.
@check_visitors
class PiiOptionsChecker(BaseChecker):
    """
    Registers the shared [PII] pylint options (pii-terms, pii-safe-key-patterns,
    pii-squelch-flag, pii-django-model-bases) so they appear in ``linter.config``
    before any checker reads them.  No messages or visitors — options only.
    """

    name = "pii-options"

    options = (
        (
            "pii-terms",
            {
                "default": ", ".join(_DEFAULT_PII_TERMS),
                "type": "csv",
                "metavar": "<comma-separated PII terms>",
                "help": (
                    "Comma-separated OEP-0030 PII identifier substrings matched against "
                    "variable names and attribute accesses passed to log/print/exception "
                    "sinks.  String literals are NOT matched."
                ),
            },
        ),
        (
            "pii-safe-key-patterns",
            {
                "default": ", ".join(_DEFAULT_SAFE_KEYS),
                "type": "csv",
                "metavar": "<comma-separated safe key patterns>",
                "help": (
                    "Exact identifiers that look like PII terms but are approved as "
                    "non-sensitive (e.g. surrogate keys, flag fields). Exact match only."
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
                    "Name of the feature toggle that gates PII-inclusive output. "
                    "PII sinks must be inside an if-block testing this flag. "
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
                    "Base class names that identify a Django model. "
                    "Both PII checkers only fire inside non-abstract, non-proxy "
                    "subclasses of these bases. Default: Model."
                ),
            },
        ),
    )


def register_checkers(linter):
    """
    Register the PII options provider.
    """
    linter.register_checker(PiiOptionsChecker(linter))


# PiiConfigMixin — shared config access and PII-detection helpers.
class PiiConfigMixin:
    """
    Mixin providing cached config reads and all PII-detection helpers.
    """

    def _init_pii_caches(self):
        """
        Reset per-module config cache slots to ``None`` (call from visit_module).
        """
        self._pii_terms_cache = None
        self._safe_keys_cache = None
        self._django_model_bases_cache = None

    def _ensure_config_cached(self):
        """
        Populate config caches from linter.config on the first call per module.
        """
        if self._pii_terms_cache is not None:
            return

        cfg = self.linter.config

        self._pii_terms_cache = [
            term.strip().lower()
            for term in getattr(cfg, "pii_terms", _DEFAULT_PII_TERMS)
            if term.strip()
        ]
        self._safe_keys_cache = {
            key.strip().lower()
            for key in getattr(cfg, "pii_safe_key_patterns", _DEFAULT_SAFE_KEYS)
            if key.strip()
        }
        self._django_model_bases_cache = {
            base.strip()
            for base in getattr(cfg, "pii_django_model_bases", ["Model"])
            if base.strip()
        }

    def _pii_terms(self):
        self._ensure_config_cached()
        return self._pii_terms_cache

    def _safe_keys(self):
        self._ensure_config_cached()
        return self._safe_keys_cache

    def _squelch_flag(self):
        return getattr(self.linter.config, "pii_squelch_flag", _DEFAULT_SQUELCH_FLAG)

    def _is_inside_squelch_guard(self, node):
        """
        Return True if *node* is nested inside an ``if`` block that tests the
        configured squelch flag.  Recognised patterns:

        1. ``if SQUELCH_PII_IN_LOGS:``
        2. ``if not SQUELCH_PII_IN_LOGS:``
        3. ``if settings.SQUELCH_PII_IN_LOGS:``
        4. ``if settings.FEATURES['SQUELCH_PII_IN_LOGS']:``
        5. ``if settings.FEATURES.get('SQUELCH_PII_IN_LOGS'):``
        6. ``if SQUELCH_PII_IN_LOGS.is_enabled():``
        7. ``if not SQUELCH_PII_IN_LOGS.is_active():``
        8. ``if getattr(settings, 'SQUELCH_PII_IN_LOGS', False):``
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

    def _test_references_flag(self, test, flag):
        """
        Return True if AST node *test* references the squelch *flag*.
        """
        # Pattern 1: if SQUELCH_PII_IN_LOGS:
        if isinstance(test, astroid_nodes.Name):
            return test.name == flag

        # Pattern 2: if not <X>:  — recurse into the operand
        if isinstance(test, astroid_nodes.UnaryOp) and test.op == "not":
            return self._test_references_flag(test.operand, flag)

        # Pattern 3: if settings.SQUELCH_PII_IN_LOGS:
        if isinstance(test, astroid_nodes.Attribute):
            if test.attrname == flag:
                return True

        # Pattern 4: if settings.FEATURES['SQUELCH_PII_IN_LOGS']:
        if isinstance(test, astroid_nodes.Subscript):
            slc = test.slice
            _IndexNode = getattr(astroid_nodes, "Index", None)
            if _IndexNode is not None and isinstance(slc, _IndexNode):  # pylint: disable=isinstance-second-argument-not-valid-type
                slc = slc.value
            if isinstance(slc, astroid_nodes.Const) and slc.value == flag:
                return True

        # Pattern 5 & 6: method calls — dict.get(flag) or flag_obj.is_enabled()
        if isinstance(test, astroid_nodes.Call):
            func = test.func
            if isinstance(func, astroid_nodes.Attribute):
                method = func.attrname
                if method in ("get", "is_enabled", "is_active", "is_waffle_flag_active"):
                    # dict.get('SQUELCH_PII_IN_LOGS') — check first arg
                    if test.args:
                        first_arg = test.args[0]
                        if isinstance(first_arg, astroid_nodes.Const) and first_arg.value == flag:
                            return True
                    # flag_obj.is_enabled() — check the receiver
                    if self._test_references_flag(func.expr, flag):
                        return True

            # Pattern 8: getattr(settings, 'SQUELCH_PII_IN_LOGS', False)
            if (
                isinstance(func, astroid_nodes.Name)
                and func.name == "getattr"
                and len(test.args) >= 2
            ):
                second_arg = test.args[1]
                if isinstance(second_arg, astroid_nodes.Const) and second_arg.value == flag:
                    return True

        return False

    def _contains_pii(self, node):
        """
        Recursively inspect *node*; return the first PII term found, or None.
        Checks Name, Attribute, f-strings, binary ops, dicts, and nested calls.
        String literals are NOT checked.
        """
        if node is None:
            return None

        # A plain name: check it directly.
        if isinstance(node, astroid_nodes.Name):
            if self._is_pii_name(node.name):
                return node.name

        # An attribute access (e.g. user.email, request.user.username).
        elif isinstance(node, astroid_nodes.Attribute):
            if self._is_pii_name(node.attrname):
                return node.attrname

        # A call: recurse into args and keyword values.
        elif isinstance(node, astroid_nodes.Call):
            for arg in node.args:
                found = self._contains_pii(arg)
                if found:
                    return found
            for kw in node.keywords or []:
                found = self._contains_pii(kw.value)
                if found:
                    return found

        # f-string: recurse into each formatted value.
        elif isinstance(node, astroid_nodes.JoinedStr):
            for value in node.values:
                if isinstance(value, astroid_nodes.FormattedValue):
                    found = self._contains_pii(value.value)
                    if found:
                        return found

        # Binary operation (e.g. "hello " + username  or  "email: %s" % email).
        elif isinstance(node, astroid_nodes.BinOp):
            return self._contains_pii(node.left) or self._contains_pii(node.right)

        # Tuple / List / Set: recurse into each element.
        elif isinstance(node, (astroid_nodes.Tuple, astroid_nodes.List, astroid_nodes.Set)):
            for elt in node.elts:
                found = self._contains_pii(elt)
                if found:
                    return found

        # Dict: recurse into values (keys are usually string identifiers).
        elif isinstance(node, astroid_nodes.Dict):
            for _key, value in node.items:
                found = self._contains_pii(value)
                if found:
                    return found

        return None

    def _is_pii_name(self, name):
        """
        Return True if *name* is a likely PII identifier.

        Safe-key exact match takes priority; then substring match against pii-terms.
        """
        lower = name.lower()
        if lower in self._safe_keys():
            return False
        for term in self._pii_terms():
            if term in lower:
                return True
        return False

    def _is_annotation_eligible_django_model(self, node):
        """
        Return True if *node* is a concrete (non-abstract, non-proxy) Django model.
        """
        self._ensure_config_cached()
        model_bases = self._django_model_bases_cache

        # Try astroid's resolved ancestor walk first (works when Django is importable).
        is_model_subclass = False
        try:
            for ancestor in node.ancestors():
                if ancestor.name in model_bases:
                    is_model_subclass = True
                    break
        except Exception:  # pylint: disable=broad-except
            pass

        # Fallback: walk raw AST base names for standalone pylint runs.
        if not is_model_subclass:
            is_model_subclass = self._raw_ast_is_model_subclass(node)

        if not is_model_subclass:
            return False

        # Skip abstract and proxy models (checked via inner Meta class).
        if any(self._meta_has_true_flag(node, flag) for flag in ("abstract", "proxy")):
            return False

        return True

    def _raw_ast_is_model_subclass(self, node):
        """
        Return True if *node* inherits from a model base using raw AST names (BFS).
        """
        model_bases = self._django_model_bases_cache
        visited = set()
        queue = list(self._direct_base_names(node))
        while queue:
            name = queue.pop(0)
            if name in visited:
                continue
            visited.add(name)
            if name in model_bases:
                return True
            parent_node = self._module_classdefs.get(name)
            if parent_node is not None:
                queue.extend(self._direct_base_names(parent_node))
        return False

    @staticmethod
    def _direct_base_names(classdef_node):
        """
        Yield the simple name of each direct base class in *classdef_node*.
        """
        for base in classdef_node.bases:
            if isinstance(base, astroid_nodes.Name):
                yield base.name
            elif isinstance(base, astroid_nodes.Attribute):
                yield base.attrname

    @staticmethod
    def _meta_has_true_flag(classdef_node, flag_name):
        """
        Return True if the inner ``Meta`` class sets *flag_name* = True.
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

    def _class_has_no_pii_annotation(self, node):
        """
        Return True if *node* has a ``.. no_pii:`` annotation (docstring or comment).
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
        Return True if a comment annotation appears above the class.
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

    def _collect_pii_fields(self, node):
        """
        Return all PII-like field names found in the class body.
        """
        found = []
        for child in node.body:
            # simple assignment: email = models.EmailField()
            if isinstance(child, astroid_nodes.Assign):
                for target in child.targets:
                    if isinstance(target, astroid_nodes.AssignName):
                        if self._is_pii_name(target.name):
                            found.append(target.name)

            # annotated assignment: email: str = ""
            elif isinstance(child, astroid_nodes.AnnAssign):
                if isinstance(child.target, astroid_nodes.AssignName):
                    if self._is_pii_name(child.target.name):
                        found.append(child.target.name)

            # instance attributes set inside methods: self.email = ...
            elif isinstance(child, astroid_nodes.FunctionDef):
                for stmt in child.nodes_of_class(astroid_nodes.Assign):
                    for target in stmt.targets:
                        if (
                            isinstance(target, astroid_nodes.AssignAttr)
                            and isinstance(target.expr, astroid_nodes.Name)
                            and target.expr.name == "self"
                            and self._is_pii_name(target.attrname)
                        ):
                            found.append(f"self.{target.attrname}")

        return found

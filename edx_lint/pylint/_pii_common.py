"""
Shared constants and helpers for the PII pylint checkers.

This module is an *internal* library — it is not a checker and has no
``register_checkers`` entry point.  It is imported by:

* :mod:`edx_lint.pylint.pii_squelch_check`  — the missing-squelch checker
* :mod:`edx_lint.pylint.pii_annotation_check` — the annotation checker

Contents
--------
* Module-level constants (``_LOG_METHODS``, regexes, look-ahead distance,
  default squelch-flag name).
* :class:`PiiConfigMixin` — a mixin that provides cached access to pylint
  config options and all shared helper methods (PII-name matching,
  SQUELCH guard detection, Django model eligibility, annotation detection,
  field scanning).

Both concrete checker classes inherit from this mixin so that every helper
is implemented exactly once.
"""

import re

from astroid import nodes as astroid_nodes


# ---------------------------------------------------------------------------
# Logging method names that are treated as output sinks.
# ---------------------------------------------------------------------------
_LOG_METHODS = frozenset({
    "debug", "info", "warning", "warn", "error",
    "critical", "exception", "log",
})

# ---------------------------------------------------------------------------
# Regex patterns used to detect ``.. no_pii:`` in docstrings / comments.
# ---------------------------------------------------------------------------
_NO_PII_DOCSTRING_RE = re.compile(r"\.\.\s*no_pii", re.IGNORECASE)
_NO_PII_COMMENT_RE = re.compile(r"[\s]*#[\s]*\.\.\s*no_pii", re.IGNORECASE)

# How many lines *above* the ``class`` keyword to search for a comment annotation.
_ANNOTATION_LOOKAHEAD = 5

# Default name of the squelch feature flag.
_DEFAULT_SQUELCH_FLAG = "SQUELCH_PII_IN_LOGS"


class PiiConfigMixin:
    """Mixin that provides cached access to PII-related pylint config options.

    Both :class:`~edx_lint.pylint.pii_squelch_check.PiiMissingSquelchChecker`
    and :class:`~edx_lint.pylint.pii_annotation_check.PiiAnnotationChecker`
    inherit from this mixin.

    All options (``pii-terms``, ``pii-safe-functions``, etc.) are defined
    on ``PiiMissingSquelchChecker``.  The annotation checker reads those
    values from ``self.linter.config`` via ``getattr`` with safe defaults, so
    it works correctly whether or not the squelch checker is also loaded.
    """

    # ------------------------------------------------------------------
    # Initialisation helpers (call from __init__ of each concrete checker)
    # ------------------------------------------------------------------

    def _init_pii_caches(self):
        """Initialise the per-module config cache slots to ``None``."""
        self._pii_terms_cache = None
        self._safe_functions_cache = None
        self._safe_keys_cache = None
        self._django_model_bases_cache = None

    # ------------------------------------------------------------------
    # Cached config helpers
    # ------------------------------------------------------------------

    def _ensure_config_cached(self):
        """Populate the config caches on the first call within a module.

        Reads option values from ``self.linter.config`` using ``getattr``
        with sensible defaults so that each checker is independently usable
        even if the other checker (and its options) is not loaded.
        """
        if self._pii_terms_cache is not None:
            return

        cfg = self.linter.config

        raw_terms = getattr(cfg, "pii_terms", [
            "email", "secondary_email",
            "username", "retired_username",
            "password",
            "name", "full_name", "first_name", "last_name",
            "phone", "phone_number",
            "birth_date",
            "ip", "ip_address",
            "location", "address", "mailing_address",
            "gender", "sex",
            "bio", "biography",
            "profile_image", "image", "video",
            "title", "job_title",
            "social", "website",
        ])
        self._pii_terms_cache = [t.strip().lower() for t in raw_terms if t.strip()]

        raw_fns = getattr(
            cfg, "pii_safe_functions",
            ["redact", "redact_pii", "mask", "mask_pii", "hash_pii", "obfuscate", "obfuscate_pii"],
        )
        self._safe_functions_cache = {f.strip() for f in raw_fns if f.strip()}

        raw_keys = getattr(cfg, "pii_safe_key_patterns", [
            "user_id", "course_id", "thread_id", "comment_id",
            "block_id", "usage_id", "usage_key", "anonymous_user_id",
        ])
        self._safe_keys_cache = {k.strip().lower() for k in raw_keys if k.strip()}

        raw_bases = getattr(cfg, "pii_django_model_bases", ["Model"])
        self._django_model_bases_cache = {b.strip() for b in raw_bases if b.strip()}

    def _pii_terms(self):
        self._ensure_config_cached()
        return self._pii_terms_cache

    def _safe_functions(self):
        self._ensure_config_cached()
        return self._safe_functions_cache

    def _safe_keys(self):
        self._ensure_config_cached()
        return self._safe_keys_cache

    def _squelch_flag(self):
        return getattr(self.linter.config, "pii_squelch_flag", _DEFAULT_SQUELCH_FLAG)

    # ------------------------------------------------------------------
    # SQUELCH_PII_IN_LOGS guard detection
    # ------------------------------------------------------------------

    def _is_inside_squelch_guard(self, node):
        """Walk up the AST parent chain and return True if *node* is nested
        inside an ``if`` block that tests the configured squelch flag.

        Recognised patterns (flag name is configurable via pii-squelch-flag):

        1. ``if SQUELCH_PII_IN_LOGS:``
        2. ``if not SQUELCH_PII_IN_LOGS:``
        3. ``if settings.SQUELCH_PII_IN_LOGS:``
        4. ``if settings.FEATURES['SQUELCH_PII_IN_LOGS']:``
        5. ``if settings.FEATURES.get('SQUELCH_PII_IN_LOGS'):``
        6. ``if SQUELCH_PII_IN_LOGS.is_enabled():``
        7. ``if not SQUELCH_PII_IN_LOGS.is_active():``
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
        """Return True if AST node *test* references the squelch *flag*."""
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
            # astroid wraps index in an Index node in older versions
            if hasattr(astroid_nodes, "Index") and isinstance(slc, astroid_nodes.Index):
                slc = slc.value  # type: ignore[attr-defined]
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

        return False

    # ------------------------------------------------------------------
    # Recursive PII detection inside AST subtrees
    # ------------------------------------------------------------------

    def _contains_pii(self, node):
        """Recursively inspect *node* for likely PII.

        Returns the first matching PII term string, or ``None``.

        NOTE: String literals (Const nodes) are intentionally NOT checked.
        A log message like ``log.info("user email: unknown")`` contains the
        word "email" in the message text, but no actual PII value is leaking.
        Only variable names (Name) and attribute accesses (Attribute) carry
        real user data and are checked.  Matching Const nodes caused false
        positives on every log message that described a PII field.
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

        # A call: if it's a safe function, stop; otherwise recurse into args.
        elif isinstance(node, astroid_nodes.Call):
            func_name = self._call_func_name(node)
            if func_name and func_name in self._safe_functions():
                return None
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

    # ------------------------------------------------------------------
    # PII name matching
    # ------------------------------------------------------------------

    def _is_pii_name(self, name):
        """Return True if *name* is a likely PII identifier.

        Rules:

        - Exact match against pii-safe-key-patterns → **not** PII.
        - Substring match of any pii-term inside *name* → PII.
        """
        lower = name.lower()
        if lower in self._safe_keys():
            return False
        for term in self._pii_terms():
            if term in lower:
                return True
        return False

    @staticmethod
    def _call_func_name(node):
        """Return the simple function name for a Call node, or ``None``."""
        if isinstance(node.func, astroid_nodes.Name):
            return node.func.name
        if isinstance(node.func, astroid_nodes.Attribute):
            return node.func.attrname
        return None

    # ------------------------------------------------------------------
    # Django model eligibility detection
    # ------------------------------------------------------------------

    def _is_annotation_eligible_django_model(self, node):
        """Return True if *node* is an annotation-eligible Django model.

        Replicates the exact predicate used by
        ``code_annotations.find_django.DjangoSearch.requires_annotations()``:

        1. The class must be a subclass of ``django.db.models.Model`` (detected
           via astroid's ancestor walking when Django is importable, or via a
           raw AST base-name BFS over the module's class definitions otherwise).
        2. The class must **not** be abstract: its inner ``Meta`` class must not
           contain ``abstract = True``.
        3. The class must **not** be a proxy model: its inner ``Meta`` class must
           not contain ``proxy = True``.
        """
        self._ensure_config_cached()
        model_bases = self._django_model_bases_cache

        # 1a. Try astroid's resolved ancestor walk (works when Django is on
        #     the import path — i.e. in a real Django project lint run).
        is_model_subclass = False
        try:
            for ancestor in node.ancestors():
                if ancestor.name in model_bases:
                    is_model_subclass = True
                    break
        except Exception:  # pylint: disable=broad-except
            pass

        # 1b. Fallback: walk raw AST base names.  Handles standalone pylint
        #     runs where Django is not importable and astroid cannot resolve
        #     the MRO.  We do a BFS over module-level class definitions
        #     collected in ``self._module_classdefs``.
        if not is_model_subclass:
            is_model_subclass = self._raw_ast_is_model_subclass(node)

        if not is_model_subclass:
            return False

        # 2 & 3. Must not be abstract or proxy (checked via inner Meta class).
        if self._meta_has_true_flag(node, "abstract"):
            return False
        if self._meta_has_true_flag(node, "proxy"):
            return False

        return True

    def _raw_ast_is_model_subclass(self, node):
        """Return True if *node* inherits from a known model base via raw AST names.

        BFS over the module-level class definitions.  At each step checks
        whether any direct base name matches a configured
        ``pii-django-model-bases`` name, or a class in the same module that
        is itself a model subclass.
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
        """Yield the simple names of each direct base in *classdef_node*.

        Handles two common forms:

        - ``class Foo(Model):``        → ``Name(name='Model')``
        - ``class Foo(models.Model):`` → ``Attribute(attrname='Model')``
        """
        for base in classdef_node.bases:
            if isinstance(base, astroid_nodes.Name):
                yield base.name
            elif isinstance(base, astroid_nodes.Attribute):
                yield base.attrname

    @staticmethod
    def _meta_has_true_flag(classdef_node, flag_name):
        """Return True if the inner ``Meta`` class of *classdef_node* sets
        *flag_name* to ``True``.

        Looks for an assignment of the form ``<flag_name> = True`` inside a
        nested class named ``Meta``.  This is the AST-level equivalent of
        checking ``model._meta.abstract`` or ``model._meta.proxy`` at runtime.
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

    # ------------------------------------------------------------------
    # Class annotation detection (.. no_pii:)
    # ------------------------------------------------------------------

    def _class_has_no_pii_annotation(self, node):
        """Return True if *node* carries a ``.. no_pii:`` annotation.

        Checks two locations:

        A. The class docstring (primary — edx-platform model convention).
        B. Comment lines up to ``_ANNOTATION_LOOKAHEAD`` lines above the class
           keyword (fallback — used in some repos).
        """
        return self._docstring_has_no_pii(node) or self._comment_has_no_pii(node)

    def _docstring_has_no_pii(self, node):
        """Return True if the class docstring contains ``.. no_pii:``."""
        docstring = node.doc_node.value if node.doc_node else ""
        return bool(_NO_PII_DOCSTRING_RE.search(docstring))

    def _comment_has_no_pii(self, node):
        """Return True if a comment annotation appears above the class."""
        if not self._source_lines:
            return False
        # node.lineno is 1-indexed; convert to 0-indexed for list access.
        end = node.lineno - 1       # exclusive (the ``class`` line itself)
        start = max(0, end - _ANNOTATION_LOOKAHEAD)
        for line in self._source_lines[start:end]:
            if _NO_PII_COMMENT_RE.match(line):
                return True
        return False

    # ------------------------------------------------------------------
    # Field scanning inside a class body
    # ------------------------------------------------------------------

    def _collect_pii_fields(self, node):
        """Return a list of PII-like field names found in the class body.

        Scans three locations:

        1. Class-level ``Assign`` (Django model fields, class variables).
        2. Class-level ``AnnAssign`` (PEP 526 annotated attributes).
        3. ``self.attr =`` assignments inside method bodies.
        """
        found = []
        for child in node.body:
            # Location 1: simple assignment  (email = models.EmailField())
            if isinstance(child, astroid_nodes.Assign):
                for target in child.targets:
                    if isinstance(target, astroid_nodes.AssignName):
                        if self._is_pii_name(target.name):
                            found.append(target.name)

            # Location 2: annotated assignment  (email: str = "")
            elif isinstance(child, astroid_nodes.AnnAssign):
                if isinstance(child.target, astroid_nodes.AssignName):
                    if self._is_pii_name(child.target.name):
                        found.append(child.target.name)

            # Location 3: instance attributes inside methods
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

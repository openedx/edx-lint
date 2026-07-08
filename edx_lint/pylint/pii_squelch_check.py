"""
PII Missing Squelch Checker — flags log/print/exception calls inside Django
model methods that expose PII without a SQUELCH_PII_IN_LOGS guard (W7630).
"""

from astroid import nodes as astroid_nodes
from pylint.checkers import BaseChecker, utils

from .common import BASE_ID, check_visitors
from ._pii_common import _LOG_METHODS, _DEFAULT_SQUELCH_FLAG, PiiConfigMixin


def register_checkers(linter):
    """Register the PII missing-squelch checker."""
    linter.register_checker(PiiMissingSquelchChecker(linter))


@check_visitors
class PiiMissingSquelchChecker(PiiConfigMixin, BaseChecker):
    """Flags unguarded PII in log/print/exception calls inside Django model methods.

    Fires ``pii-missing-squelch`` (W7630). Skips .. no_pii: models, abstract/proxy
    models, standalone functions, and any call wrapped in a SQUELCH_PII_IN_LOGS guard.
    """

    name = "pii-missing-squelch"

    # ------------------------------------------------------------------
    # Message definitions — one symbol covers log + print + exception
    # ------------------------------------------------------------------
    msgs = {
        ("W%d30" % BASE_ID): (
            "PII term '%s' exposed in %s without a SQUELCH_PII_IN_LOGS guard. "
            "Wrap with: if not SQUELCH_PII_IN_LOGS: ...",
            "pii-missing-squelch",
            "A log call, print/stdout/stderr write, or raised exception inside a "
            "Django model method exposes likely PII without a SQUELCH_PII_IN_LOGS "
            "guard.  Wrap the offending line with: if not SQUELCH_PII_IN_LOGS: ...",
        ),
    }

    # ------------------------------------------------------------------
    # Configurable options
    # NOTE: All shared PII options are defined here.  PiiAnnotationChecker
    #       reads them from linter.config via getattr() with safe defaults.
    # ------------------------------------------------------------------
    options = (
        (
            "pii-terms",
            {
                "default": (
                    # OEP-0030 PII fields (https://open-edx-proposals.readthedocs.io/en/latest/
                    # architectural-decisions/oep-0030-arch-pii-markup-and-auditing.html)
                    "email,secondary_email,"           # email_address
                    "username,retired_username,"       # username
                    "password,"                        # password
                    "name,full_name,first_name,last_name,"  # name
                    "phone,phone_number,"              # phone_number
                    "birth_date,"                      # birth_date
                    "ip,ip_address,"                   # ip
                    "location,address,mailing_address,"  # location
                    "gender,sex,"                      # gender / sex
                    "bio,biography,"                   # biography
                    "profile_image,image,video,"       # image / video
                    "title,job_title,"                 # job title
                    "social,website"                   # external_service (social media, website)
                ),
                "type": "csv",
                "metavar": "<comma-separated PII terms>",
                "help": (
                    "Comma-separated list of identifier substrings treated as PII per OEP-0030. "
                    "Matches variable names and attribute accesses passed to log/print/exception "
                    "sinks. String literals in log messages are NOT matched — only actual PII "
                    "variable and attribute references are flagged."
                ),
            },
        ),
        (
            "pii-safe-functions",
            {
                "default": (
                    "redact,redact_pii,mask,mask_pii,hash_pii,obfuscate,obfuscate_pii"
                ),
                "type": "csv",
                "metavar": "<comma-separated safe function names>",
                "help": (
                    "Functions that safely transform PII. Calls wrapped in one of these "
                    "functions will not be flagged."
                ),
            },
        ),
        (
            "pii-safe-key-patterns",
            {
                "default": (
                    "user_id,course_id,thread_id,comment_id,block_id,"
                    "usage_id,usage_key,anonymous_user_id"
                ),
                "type": "csv",
                "metavar": "<comma-separated safe key patterns>",
                "help": (
                    "Exact identifiers that look like PII terms but are approved as "
                    "non-sensitive (e.g. surrogate keys). Exact match only."
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
                    "output. PII sinks must be inside an if-block that tests this flag. "
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
                    "Comma-separated list of base class *names* that identify a Django model. "
                    "The squelch checks only fire inside non-abstract, non-proxy subclasses of "
                    "these bases (mirroring 'code_annotations django_find_annotations'). "
                    "Default: Model."
                ),
            },
        ),
    )

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Cached per-module source lines for comment-style annotation lookup.
        self._source_lines = []
        # Config caches — explicitly initialised here so pylint knows they
        # exist; reset per-module via _init_pii_caches() in visit_module.
        self._pii_terms_cache = None
        self._safe_functions_cache = None
        self._safe_keys_cache = None
        self._django_model_bases_cache = None
        # Per-module mapping of class name → ClassDef node, used by
        # _raw_ast_is_model_subclass to resolve same-module ancestors.
        self._module_classdefs = {}

    # ------------------------------------------------------------------
    # AST Visitors
    # ------------------------------------------------------------------

    @utils.only_required_for_messages(
        "pii-missing-squelch"
    )
    def visit_module(self, node):
        """Cache source lines and reset all per-module state."""
        # Reset config caches so options are re-read for each module.
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
        """Index every class definition for same-module ancestry resolution.

        This is required so that ``_raw_ast_is_model_subclass`` can walk the
        inheritance chain of classes defined in the same module without
        relying on astroid's import resolution (which requires Django to be
        installed in the linting environment).
        """
        self._module_classdefs[node.name] = node

    @utils.only_required_for_messages("pii-missing-squelch")
    def visit_call(self, node):
        """Check logging and print/stdout/stderr calls for unguarded PII."""
        if self._is_log_call(node):
            self._check_sink(node, "log call")
        elif self._is_print_call(node):
            self._check_sink(node, "print/stdout/stderr")

    @utils.only_required_for_messages("pii-missing-squelch")
    def visit_raise(self, node):
        """Check raised exceptions for unguarded PII in their messages.

        Only fires when the raise statement is inside an annotation-eligible
        Django model method that is not annotated ``.. no_pii:``.
        Raises outside a Django model (standalone code, module-level) are
        entirely out of scope.
        """
        if not self._requires_squelch_check(node):
            return
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

    # ------------------------------------------------------------------
    # Sink identification helpers
    # ------------------------------------------------------------------

    def _is_log_call(self, node):
        """Return True if *node* is a call to a standard logging method."""
        if not isinstance(node.func, astroid_nodes.Attribute):
            return False
        return node.func.attrname in _LOG_METHODS

    def _is_print_call(self, node):
        """Return True if *node* is a print() or stdout/stderr write() call."""
        # bare print()
        if isinstance(node.func, astroid_nodes.Name) and node.func.name == "print":
            return True
        # self.stdout.write(...)  /  sys.stdout.write(...)  /  stderr.write(...)
        if isinstance(node.func, astroid_nodes.Attribute) and node.func.attrname == "write":
            return True
        return False

    def _check_sink(self, node, sink_label):
        """Emit ``pii-missing-squelch`` if any argument of *node* contains PII
        and the call is not inside a SQUELCH_PII_IN_LOGS guard.

        *sink_label* is a human-readable description of the sink type
        (e.g. ``'log call'``, ``'print/stdout/stderr'``) included in the
        emitted message so the developer knows what to fix.

        Squelch checks are ONLY enforced inside Django model classes that do
        not carry a ``.. no_pii:`` annotation.  Standalone functions and
        ``.. no_pii:``-annotated models are entirely skipped.
        """
        if not self._requires_squelch_check(node):
            return

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
                return  # at most one message per call

    def _requires_squelch_check(self, node):
        """Return True if *node* is inside an eligible Django model that is
        NOT annotated with ``.. no_pii:``.

        Scope rules:

        * Inside a Django model annotated ``.. no_pii:``  → **SKIP** (safe model).
        * Inside a Django model with ``.. pii:`` or no annotation → **CHECK**.
        * Standalone functions, module-level code, non-model classes → **SKIP**.

        This mirrors the original scope: only Django model methods are subject
        to squelch-guard enforcement.  Code outside a model is not in scope
        because it is not subject to OEP-0030 annotation requirements.
        """
        current = node.parent
        while current is not None:
            if isinstance(current, astroid_nodes.ClassDef):
                if self._is_annotation_eligible_django_model(current):
                    # Inside an eligible model — require guard ONLY if not safe.
                    return not self._class_has_no_pii_annotation(current)
                # Inside a non-model class — keep walking up.
            current = current.parent
        # Not inside any Django model class → out of scope, skip.
        return False

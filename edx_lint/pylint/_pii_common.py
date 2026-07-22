"""
Shared PII name-matching helpers for the PII pylint checkers.

Contains only code shared by both pii_squelch_check (W7630) and
pii_annotation_check (W7633). Checker-specific logic lives in each
checker's own module.
"""


class PiiConfigMixin:
    """
    Mixin providing cached access to pii-terms and safe-key config options.

    Used by both PiiMissingSquelchChecker (W7630) and PiiAnnotationChecker (W7633).
    Each checker calls _init_pii_caches() in visit_module to reset per-module state.
    """

    def _init_pii_caches(self):
        """Reset per-module config caches to None."""
        self._pii_terms_cache = None
        self._safe_keys_cache = None

    def _ensure_config_cached(self):
        """Populate pii-terms and safe-key caches on first call within a module."""
        if self._pii_terms_cache is not None:
            return
        cfg = self.linter.config
        raw_terms = getattr(cfg, "pii_terms", ["email", "username", "password"])
        self._pii_terms_cache = [t.strip().lower() for t in raw_terms if t.strip()]
        raw_keys = getattr(cfg, "pii_safe_key_patterns", [])
        self._safe_keys_cache = {k.strip().lower() for k in raw_keys if k.strip()}

    def _pii_terms(self):
        self._ensure_config_cached()
        return self._pii_terms_cache

    def _safe_keys(self):
        self._ensure_config_cached()
        return self._safe_keys_cache

    def _is_pii_name(self, name):
        """
        Return True if *name* is a likely PII identifier.

        - Exact match against pii-safe-key-patterns → not PII.
        - Substring match of any pii-term inside *name* → PII.
        """
        lower = name.lower()
        if lower in self._safe_keys():
            return False
        return any(term in lower for term in self._pii_terms())

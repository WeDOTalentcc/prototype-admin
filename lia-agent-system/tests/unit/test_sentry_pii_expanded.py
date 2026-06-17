"""
Anti-regressão · W3-013 + W3-028 (2026-05-23).

W3-013: Sentry PII patterns 3→12 (8 canonical reuse + 4 security new).
W3-028: LangSmith fail-fast em production environment.
"""
from __future__ import annotations

import re

import pytest


class TestW3013SentryPIIPatternsExpanded:
    """Sentry agora scrubba >= 10 PII patterns (era 3)."""

    def test_pii_patterns_count_at_least_10(self) -> None:
        from app.core.sentry import _PII_PATTERNS

        assert len(_PII_PATTERNS) >= 10, (
            f"Sentry deve ter >= 10 PII patterns. Got: {len(_PII_PATTERNS)}"
        )

    def test_scrub_email(self) -> None:
        from app.core.sentry import _scrub_pii

        result = _scrub_pii("Contact: joao@example.com for details")
        assert "joao@example.com" not in result
        assert "[EMAIL" in result.upper()

    def test_scrub_cpf(self) -> None:
        from app.core.sentry import _scrub_pii

        result = _scrub_pii("CPF: 123.456.789-00")
        assert "123.456.789-00" not in result

    def test_scrub_password_in_log(self) -> None:
        """W3-013 new security pattern: password redacted."""
        from app.core.sentry import _scrub_pii

        result = _scrub_pii("password=supersecret123")
        assert "supersecret123" not in result
        assert "REDACTED" in result.upper()

    def test_scrub_api_key(self) -> None:
        from app.core.sentry import _scrub_pii

        result = _scrub_pii("api_key=sk-test-abc123")
        assert "sk-test-abc123" not in result

    def test_scrub_bearer_token(self) -> None:
        from app.core.sentry import _scrub_pii

        result = _scrub_pii("Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.abc")
        assert "eyJ" not in result

    def test_scrub_credit_card(self) -> None:
        from app.core.sentry import _scrub_pii

        # Standard credit card format
        result = _scrub_pii("Card: 4111 1111 1111 1111")
        assert "4111" not in result or "1111 1111 1111 1111" not in result

    def test_canonical_pii_reused(self) -> None:
        """W3-013 canonical reuse: Sentry deve incluir patterns de pii_masking."""
        from app.core.sentry import _PII_PATTERNS

        try:
            from app.shared.pii_masking import _LLM_PROMPT_PII_PATTERNS
        except ImportError:
            pytest.skip("Canonical pii_masking not available")

        # Subset check: cada pattern canonical aparece em sentry _PII_PATTERNS
        canonical_strs = {str(p[0].pattern) for p in _LLM_PROMPT_PII_PATTERNS}
        sentry_strs = {str(p[0].pattern) for p in _PII_PATTERNS}
        assert canonical_strs.issubset(sentry_strs), (
            f"Sentry deve reusar TODOS os {len(canonical_strs)} canonical patterns. "
            f"Missing: {canonical_strs - sentry_strs}"
        )


class TestW3028LangSmithFailFast:
    """LangSmith fail-fast em production/staging."""

    def test_main_module_has_fail_fast_check(self) -> None:
        """Verifica que app/main.py wirou `_LANGSMITH_OK` guard."""
        from pathlib import Path

        main_path = (
            Path(__file__).resolve().parents[2] / "app" / "main.py"
        )
        src = main_path.read_text()
        assert "_LANGSMITH_OK" in src, (
            "main.py DEVE ter `_LANGSMITH_OK = configure_langsmith()` (W3-028)"
        )
        assert "production" in src and "raise RuntimeError" in src, (
            "main.py DEVE ter fail-fast em prod/staging (W3-028)"
        )

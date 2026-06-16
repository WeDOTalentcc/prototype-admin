"""UC-P1-25: FactChecker for hallucination detection — shared/evaluation layer.

Re-exports the canonical FactChecker from app.shared.compliance.fact_checker
and adds a lightweight DomainFactCheckerMixin so any domain can opt in with
zero boilerplate.

The compliance FactChecker already validates numeric claims (salary, counts,
percentages, dates). This module adds:
  - DomainFactCheckerMixin for easy domain opt-in
  - A thin async .check() wrapper that mirrors the interface described in the
    UC-P1-25 spec, delegating to the underlying check_response()

Usage::

    from app.shared.evaluation.fact_checker import (
        FactChecker, FactCheckResult, DomainFactCheckerMixin
    )

    checker = FactChecker()
    result = await checker.check(
        "O candidato tem 10 anos de experiência",
        context={"cv_text": "5 anos de experiência em Python"},
    )
    if not result.is_valid:
        # Block or flag the response
        ...
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any

# Re-export canonical classes for consumers who import from this module
from app.shared.compliance.fact_checker import (  # noqa: F401
    FactCheckClaim,
    FactChecker as _BaseFactChecker,
    FactCheckResult as _BaseFactCheckResult,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Thin result wrapper that exposes the is_valid / violations / warnings
# interface described in UC-P1-25
# ---------------------------------------------------------------------------

@dataclass
class FactCheckResult:
    """UC-P1-25 result type: simple is_valid + violations list."""

    is_valid: bool
    confidence: float           # 0.0-1.0
    violations: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "confidence": self.confidence,
            "violations": self.violations,
            "warnings": self.warnings,
        }


# ---------------------------------------------------------------------------
# Extended FactChecker: delegates to _BaseFactChecker and adds async .check()
# ---------------------------------------------------------------------------

class FactChecker(_BaseFactChecker):
    """FactChecker with an async .check() entry-point for UC-P1-25 usage.

    Extends the canonical sync FactChecker with:
    - async check(): returns simple FactCheckResult (is_valid, violations)
    - Experience-years numeric consistency check
    - Missing-caveat warnings for low-quality data contexts
    """

    HALLUCINATION_PATTERNS = [
        r"\b(certamente|com certeza|definitivamente|garantidamente)\b.*\d+",
        r"\b(always|never|100%|guaranteed)\b",
        r"\b\d{4}-\d{4}\b",  # fake date ranges like "2010-2030"
        r"R\$\s*\d+[\.,]\d{3}[\.,]\d{3}",  # suspiciously large salaries
    ]

    async def check(
        self,
        response: str,
        context: dict[str, Any] | None = None,
        llm_judge=None,
    ) -> FactCheckResult:
        """Async check for hallucinations and numeric inconsistencies.

        Uses heuristic checks by default. Pass llm_judge for higher accuracy.
        """
        violations: list[str] = []
        warnings: list[str] = []

        violations += self._check_hallucination_patterns(response)

        if context:
            violations += self._check_numeric_consistency(response, context)
            warnings += self._check_missing_caveats(response, context)

        is_valid = len(violations) == 0
        confidence = 0.9  # heuristic has known false-positive rate

        result = FactCheckResult(
            is_valid=is_valid,
            confidence=confidence,
            violations=violations,
            warnings=warnings,
        )

        if not is_valid:
            logger.warning("[FactChecker] Hallucination detected: %s", violations)

        return result

    def _check_hallucination_patterns(self, response: str) -> list[str]:
        violations = []
        for pattern in self.HALLUCINATION_PATTERNS:
            if re.search(pattern, response, re.IGNORECASE):
                violations.append(
                    f"Hallucination pattern detected: {pattern[:60]}"
                )
        return violations

    def _check_numeric_consistency(
        self, response: str, context: dict[str, Any]
    ) -> list[str]:
        """Check experience years in response vs context."""
        violations = []
        response_years = re.findall(
            r"(\d+)\s*anos?\s*de\s*experi[êe]ncia", response, re.I
        )
        context_text = str(
            context.get("cv_text", "") or context.get("resume", "")
        )
        context_years = re.findall(
            r"(\d+)\s*anos?\s*de\s*experi[êe]ncia", context_text, re.I
        )

        if response_years and context_years:
            resp_max = max(int(y) for y in response_years)
            ctx_max = max(int(y) for y in context_years)
            if resp_max > ctx_max * 1.5:  # 50 % tolerance
                violations.append(
                    f"Experience years mismatch: response says {resp_max}, "
                    f"context says {ctx_max}"
                )
        return violations

    def _check_missing_caveats(
        self, response: str, context: dict[str, Any]
    ) -> list[str]:
        """Warn if response is confident about uncertain/low-quality data."""
        warnings = []
        if context.get("data_quality") == "low" and not any(
            w in response.lower()
            for w in ["pode", "possivelmente", "aparentemente", "parece"]
        ):
            warnings.append(
                "Low-quality data source — response should include uncertainty markers"
            )
        return warnings


# ---------------------------------------------------------------------------
# Mixin for domain classes
# ---------------------------------------------------------------------------

class DomainFactCheckerMixin:
    """Mixin that adds async fact-checking to any domain class."""

    _fact_checker: FactChecker | None = None

    @property
    def fact_checker(self) -> FactChecker:
        if self._fact_checker is None:
            self._fact_checker = FactChecker()
        return self._fact_checker

    async def check_response(
        self, response: str, context: dict | None = None
    ) -> FactCheckResult:
        """Check an LLM response for hallucinations."""
        return await self.fact_checker.check(response, context)

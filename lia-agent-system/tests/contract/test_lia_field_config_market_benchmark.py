"""BUG-C4-B regression sensor: LiaFieldConfigService.suggest_field_value MUST
NOT raise AttributeError when fallback chain reaches market_benchmark branch.

Context (audit 2026-05-23): Sensor F-26 (expanded in C.4 commit 9c3caaa62)
detected that LiaFieldConfigService called `self._get_market_benchmark(
field_key, job_context, company_profile)` at line 834 — but that method
only existed in IntelligentDataOrchestrator (and there with a totally
different signature: zero-arg lazy loader). The canonical method on this
class is ``_from_market_benchmark`` (line ~431) with EXACTLY the right
signature. The buggy line was a stale rename never propagated.

Strategy: assert (a) the suggestion flow never raises AttributeError when
the fallback chain exhausts to market_benchmark, and (b) the canonical
_from_market_benchmark method is the one invoked.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def service():
    from app.domains.cv_screening.services.lia_field_config_service import (
        LiaFieldConfigService,
    )
    return LiaFieldConfigService(db=MagicMock())


def test_canonical_from_market_benchmark_method_exists(service):
    """RED guard for the canonical impl — must stay on the class."""
    assert hasattr(service, "_from_market_benchmark"), (
        "Canonical _from_market_benchmark removed — BUG-C4-B fix relies on it."
    )


def test_ghost_get_market_benchmark_no_longer_referenced():
    """The stale `self._get_market_benchmark(...)` call site MUST be gone
    (it was the F-26 C.4 ghost reference producing AttributeError).

    We scan line-by-line ignoring commented lines (the BUG-C4-B fix retains
    an explanatory comment that mentions the old name for context)."""
    import pathlib
    src = pathlib.Path(
        "app/domains/cv_screening/services/lia_field_config_service.py"
    ).read_text()
    forbidden = "self._get_market_benchmark("
    live_offenders = []
    for lineno, line in enumerate(src.splitlines(), start=1):
        stripped = line.lstrip()
        if stripped.startswith("#"):
            continue  # comment line — safe
        if forbidden in line:
            live_offenders.append(f"line {lineno}: {line.strip()}")
    assert not live_offenders, (
        f"BUG-C4-B regression: live call to {forbidden!r} found in:\n"
        + "\n".join(live_offenders)
        + "\nShould be self._from_market_benchmark(...) instead."
    )


@pytest.mark.asyncio
async def test_suggest_field_value_market_benchmark_branch_no_attribute_error(
    service,
):
    """Integration smoke: when fallback chain exhausts to market_benchmark,
    suggest_field_value must NOT raise AttributeError (BUG-C4-B symptom)."""
    from uuid import uuid4

    # Force the "value is None" branch by making _resolve_fallback return None.
    # That branch is the F-26 site that previously called the ghost method.
    service._load_toggles = AsyncMock(return_value={})
    service._load_company_profile = AsyncMock(return_value=None)
    service._load_job_history = AsyncMock(return_value=[])
    service._resolve_fallback = MagicMock(return_value=(None, MagicMock(), 0.0))
    service._from_market_benchmark = MagicMock(return_value="benchmark-value")

    result = await service.suggest_field_value(
        company_id=str(uuid4()),
        field_key="salary_ranges",
        job_context={"seniority": "Pleno"},
    )

    # Must NOT raise AttributeError and the canonical method must have been
    # invoked with the exact 3-arg signature that the call-site uses.
    assert service._from_market_benchmark.called, (
        "Canonical _from_market_benchmark must be invoked when fallback "
        "chain exhausts (BUG-C4-B fix). Previously self._get_market_benchmark "
        "was called, which did not exist on this class."
    )
    assert result["suggested_value"] == "benchmark-value"


def test_call_site_uses_canonical_three_arg_signature():
    """The 3-arg signature (field_key, job_context, company_profile) MUST be
    preserved — IntelligentDataOrchestrator._get_market_benchmark has a
    totally different signature (zero-arg lazy loader), so any 'delegation'
    refactor that points at the orchestrator method would silently break."""
    import inspect
    from app.domains.cv_screening.services.lia_field_config_service import (
        LiaFieldConfigService,
    )
    sig = inspect.signature(LiaFieldConfigService._from_market_benchmark)
    params = list(sig.parameters.keys())
    # self + 3 positional args
    assert params[:4] == ["self", "field_key", "job_context", "company_profile"], (
        f"Canonical signature drift detected: {params}. "
        "BUG-C4-B fix is wired to (field_key, job_context, company_profile)."
    )

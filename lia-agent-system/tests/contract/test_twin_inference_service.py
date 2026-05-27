"""Wave C2.7 (2026-05-27) — TwinInferenceService contract tests.

Cobertura inicial Digital Twins:
- evaluate happy path (3+ decisions => score 0-100 OR evaluation_failed flag)
- evaluate LLM failure (REGRA 4 anti-silent-fallback)
- evaluate cross-tenant => LookupError
- _retrieve_similar fallback recency
- _calculate_confidence monotonic

Production-quality + AI architecture + compliance-risk:
asserts REGRA 4 evaluation_failed + LGPD tenant filtering.
"""
from __future__ import annotations

import json
import sys
import types
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

pytestmark = pytest.mark.asyncio


def _make_twin(twin_id="twin-1", company_id="comp-1", name="Joao SME",
               decision_count=10, specialties=None):
    twin = MagicMock()
    twin.id = twin_id
    twin.company_id = company_id
    twin.twin_name = name
    twin.decision_count = decision_count
    twin.specialties = specialties or ["tech-recruiting"]
    return twin


def _inject_fake_get_llm(monkeypatch, response_content=None, raises=None):
    """Patch llm_factory.get_llm via sys.modules injection (lazy import target)."""
    mod = sys.modules.get("app.shared.providers.llm_factory")
    if mod is None:
        # import to ensure presence
        import app.shared.providers.llm_factory as mod  # noqa

    mock_llm = MagicMock()
    if raises is not None:
        mock_llm.ainvoke = AsyncMock(side_effect=raises)
    else:
        resp = MagicMock()
        resp.content = response_content
        mock_llm.ainvoke = AsyncMock(return_value=resp)

    monkeypatch.setattr(mod, "get_llm", lambda tier="default": mock_llm, raising=False)
    return mock_llm


async def test_evaluate_with_real_decisions_returns_valid_score(monkeypatch):
    """Twin com 3+ decisions + LLM ok => score 0-100, decision != evaluation_failed."""
    from app.services.twin_inference_service import TwinInferenceService

    twin = _make_twin(decision_count=15)

    repo_mock = MagicMock()
    repo_mock.get_by_id = AsyncMock(return_value=twin)
    examples = [
        {"decision": "approved", "reasoning": "Strong python",
         "candidate_snapshot": {"name": "A"}, "similarity": 0.9},
        {"decision": "approved", "reasoning": "Good cultural fit",
         "candidate_snapshot": {"name": "B"}, "similarity": 0.85},
        {"decision": "rejected", "reasoning": "Lacks seniority",
         "candidate_snapshot": {"name": "C"}, "similarity": 0.8},
    ]
    repo_mock.search_similar_decisions = AsyncMock(return_value=examples)
    repo_mock.get_twin_decisions = AsyncMock(return_value=[])

    svc = TwinInferenceService()
    _inject_fake_get_llm(
        monkeypatch,
        response_content=json.dumps({
            "score": 78, "decision": "approved",
            "reasoning": "Forte fit tecnico.",
        }),
    )

    db = AsyncMock()
    with patch.object(svc, "_embed", AsyncMock(return_value=[0.1] * 384)), \
         patch("app.domains.agent_studio.repositories.digital_twin_repository.DigitalTwinRepository",
               return_value=repo_mock):
        result = await svc.evaluate(
            twin_id="twin-1",
            candidate_profile={"name": "Candidate X", "skills": ["python"]},
            job_context={"title": "Senior Python Dev"},
            company_id="comp-1",
            k=5,
            db=db,
        )

    assert result.evaluation_failed is False
    assert result.score is not None
    assert 0 <= result.score <= 100
    assert result.decision in ("approved", "rejected", "maybe")
    assert result.needs_manual_review is False


async def test_evaluate_llm_failure_returns_evaluation_failed_flag(monkeypatch):
    """REGRA 4 anti-silent-fallback: LLM raise => evaluation_failed=True + needs_manual_review."""
    from app.services.twin_inference_service import TwinInferenceService

    twin = _make_twin(decision_count=20)
    repo_mock = MagicMock()
    repo_mock.get_by_id = AsyncMock(return_value=twin)
    repo_mock.search_similar_decisions = AsyncMock(return_value=[])
    repo_mock.get_twin_decisions = AsyncMock(return_value=[])

    svc = TwinInferenceService()
    _inject_fake_get_llm(monkeypatch, raises=RuntimeError("LLM provider down"))

    db = AsyncMock()
    with patch.object(svc, "_embed", AsyncMock(return_value=[0.1] * 384)), \
         patch("app.domains.agent_studio.repositories.digital_twin_repository.DigitalTwinRepository",
               return_value=repo_mock):
        result = await svc.evaluate(
            twin_id="twin-1",
            candidate_profile={"name": "X"},
            job_context={"title": "Y"},
            company_id="comp-1",
            db=db,
        )

    assert result.evaluation_failed is True
    assert result.needs_manual_review is True
    assert result.failure_reason is not None
    assert result.score is None
    assert result.decision == "evaluation_failed"
    assert result.confidence == 0.0


async def test_evaluate_cross_tenant_raises_lookup_error():
    """Twin de outra company => repo.get_by_id retorna None => LookupError fail-closed."""
    from app.services.twin_inference_service import TwinInferenceService

    repo_mock = MagicMock()
    repo_mock.get_by_id = AsyncMock(return_value=None)

    svc = TwinInferenceService()
    db = AsyncMock()
    with patch("app.domains.agent_studio.repositories.digital_twin_repository.DigitalTwinRepository",
               return_value=repo_mock):
        with pytest.raises(LookupError) as excinfo:
            await svc.evaluate(
                twin_id="other-tenant-twin",
                candidate_profile={"name": "X"},
                job_context={"title": "Y"},
                company_id="comp-1",
                db=db,
            )
        assert "twin_id" in str(excinfo.value)


async def test_evaluate_signature_requires_company_id():
    """evaluate signature DEVE ter company_id explicit (multi-tenancy fail-closed)."""
    from app.services.twin_inference_service import TwinInferenceService
    import inspect

    sig = inspect.signature(TwinInferenceService.evaluate)
    assert "company_id" in sig.parameters
    assert "twin_id" in sig.parameters


async def test_retrieve_similar_fallback_recency_when_no_embedding():
    """_retrieve_similar sem embedding => fallback recent via repo.get_twin_decisions."""
    from app.services.twin_inference_service import TwinInferenceService

    svc = TwinInferenceService()
    fake_decision = MagicMock()
    fake_decision.decision = "approved"
    fake_decision.reasoning = "test"
    fake_decision.candidate_snapshot = {"x": 1}

    repo_mock = MagicMock()
    repo_mock.get_twin_decisions = AsyncMock(return_value=[fake_decision])

    out = await svc._retrieve_similar(
        repo=repo_mock, twin_id="t-1", company_id="comp-1",
        embedding=None, k=5,
    )
    assert isinstance(out, list)
    assert len(out) == 1
    assert out[0]["similarity"] == 0.5
    assert out[0]["decision"] == "approved"


async def test_calculate_confidence_grows_with_corpus():
    """_calculate_confidence(decision_count, examples) increases monotonically with corpus."""
    from app.services.twin_inference_service import TwinInferenceService

    low = TwinInferenceService._calculate_confidence(0, [])
    mid = TwinInferenceService._calculate_confidence(20, [{"similarity": 0.7}])
    high = TwinInferenceService._calculate_confidence(
        100, [{"similarity": 0.95}, {"similarity": 0.9}]
    )

    assert low <= mid <= high
    assert 0.0 <= low <= 1.0
    assert 0.0 <= high <= 1.0

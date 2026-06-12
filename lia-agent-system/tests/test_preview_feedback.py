"""
Sensor — endpoint read-only de preview de feedback (item 3 / 1-exemplo bulk).
Camada 2 (Unitario BE — pytest). Chama a funcao do endpoint direto com deps mockadas.
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from app.api.v1.recruitment_stages.stages_transition import preview_feedback
from app.api.v1.recruitment_stages._shared import PreviewFeedbackRequest


def _stage_repo_with_company(name="ACME Tecnologia"):
    repo = MagicMock()
    result = MagicMock()
    result.first = MagicMock(return_value=(name, name))
    repo.db.execute = AsyncMock(return_value=result)
    return repo


@pytest.mark.asyncio
async def test_preview_rejection_uses_client_name_no_vendor():
    with patch(
        "app.domains.automation.services.candidate_context_aggregator.CandidateContextAggregator"
    ) as MockAgg:
        MockAgg.return_value.aggregate = AsyncMock(
            return_value={"name": "Maria Silva", "job": {"title": "Analista"}}
        )
        resp = await preview_feedback(
            PreviewFeedbackRequest(
                vacancy_candidate_id="vc-1", to_stage="rejected",
                sub_status="over_qualified", channel="email",
            ),
            MagicMock(id="u1"),
            _stage_repo_with_company(),
            "co-1",
        )
    assert resp.body
    assert "WeDoTalent" not in resp.body
    assert "ACME Tecnologia" in resp.body
    assert resp.channel == "email"
    assert resp.high_risk is False


@pytest.mark.asyncio
async def test_preview_high_risk_flag_and_generic():
    with patch(
        "app.domains.automation.services.candidate_context_aggregator.CandidateContextAggregator"
    ) as MockAgg:
        MockAgg.return_value.aggregate = AsyncMock(
            return_value={"name": "Joao", "job": {"title": "Dev"}}
        )
        resp = await preview_feedback(
            PreviewFeedbackRequest(
                vacancy_candidate_id="vc-2", to_stage="rejected",
                sub_status="negative_references", channel="email",
            ),
            MagicMock(id="u1"),
            _stage_repo_with_company(),
            "co-1",
        )
    assert resp.high_risk is True
    # alto risco -> IA nunca redige -> generico (fallback)
    assert resp.generated_by == "fallback_template"
    assert resp.ai_personalized is False
    assert "WeDoTalent" not in resp.body


@pytest.mark.asyncio
async def test_preview_whatsapp_uses_template_only():
    with patch(
        "app.domains.automation.services.candidate_context_aggregator.CandidateContextAggregator"
    ) as MockAgg:
        MockAgg.return_value.aggregate = AsyncMock(
            return_value={"name": "Ana", "job": {"title": "QA"}}
        )
        resp = await preview_feedback(
            PreviewFeedbackRequest(
                vacancy_candidate_id="vc-3", to_stage="rejected",
                sub_status="over_qualified", channel="whatsapp",
            ),
            MagicMock(id="u1"),
            _stage_repo_with_company(),
            "co-1",
        )
    assert resp.uses_template_only is True
    assert resp.ai_personalized is False

"""Testa que publish_job rejeita vaga sem perguntas WSI aprovadas."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


def _make_ctx(company_id="comp-001"):
    ctx = MagicMock()
    ctx.company_id = company_id
    return ctx


@pytest.fixture
def state_without_approval():
    return {
        "job_id": "job-001",
        "jd_enriched": True,
        "jd_approved": True,
        "questions_approved": None,
        "wsi_questions": [],
        "screening_mode": "compact",
    }


@pytest.fixture
def state_with_approval():
    return {
        "job_id": "job-001",
        "jd_enriched": True,
        "jd_approved": True,
        "questions_approved": True,
        "wsi_questions": [{"id": "q1", "question": "...", "block": "technical"}],
        "screening_mode": "compact",
    }


def test_publish_blocked_without_questions_approved(state_without_approval):
    from app.domains.job_creation.orchestrator.wizard_service_tools import _handle_publish_job

    ctx = _make_ctx()
    result = _handle_publish_job(state_without_approval, {"confirm": True}, ctx)
    # ToolResult has .error and .llm_message attributes
    assert result.error is True
    msg = (result.llm_message or "").lower()
    assert any(k in msg for k in ["triagem", "perguntas", "wsi", "aprovad"])


def test_publish_allowed_with_questions_approved(state_with_approval):
    from app.domains.job_creation.orchestrator.wizard_service_tools import _handle_publish_job

    ctx = _make_ctx()
    with patch(
        "app.domains.job_creation.nodes.publish.publish_node",
        return_value={"job_id": "job-001", "share_link": "https://example.com"},
    ):
        result = _handle_publish_job(state_with_approval, {"confirm": True}, ctx)

    # Should NOT return questions/triagem error — either success or different error
    msg = (result.llm_message or "").lower()
    # The wsi/triagem block check should NOT be triggered
    assert result.error is not True or "triagem" not in msg

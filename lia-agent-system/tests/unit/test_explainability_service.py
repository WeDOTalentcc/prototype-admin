"""UC-P1-16: ExplainabilityService — LGPD Art.20 compliance."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_generate_candidate_explanation_returns_dict():
    """generate_candidate_explanation returns a dict with status key."""
    from app.shared.services.explainability_service import ExplainabilityService
    svc = ExplainabilityService()
    mock_decision = MagicMock()
    mock_decision.decision = "approved"
    mock_decision.score = 4.5
    mock_decision.confidence = 0.85
    mock_decision.criteria_used = ["skills", "experience"]
    mock_decision.criteria_ignored = ["age"]
    mock_decision.reasoning = ["Strong Python skills", "Relevant experience"]
    mock_decision.created_at = MagicMock()
    mock_decision.created_at.isoformat.return_value = "2026-05-02T10:00:00"
    mock_decision.id = "log-001"
    mock_decision.agent_name = "cv_screening_agent"
    mock_decision.decision_type = "cv_screening"
    mock_decision.human_reviewed_at = None

    with patch("app.shared.services.explainability_service.AsyncSessionLocal") as mock_session_cls:
        mock_session = AsyncMock()
        mock_session_cls.return_value.__aenter__.return_value = mock_session
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_decision]
        mock_session.execute = AsyncMock(return_value=mock_result)

        result = await svc.generate_candidate_explanation(
            company_id="company_1",
            candidate_id="cand_1",
            job_vacancy_id="job_1",
        )

    assert isinstance(result, dict)
    assert "status" in result


@pytest.mark.asyncio
async def test_generate_candidate_explanation_no_data():
    """Returns no_data status when no audit logs found."""
    from app.shared.services.explainability_service import ExplainabilityService
    svc = ExplainabilityService()
    with patch("app.shared.services.explainability_service.AsyncSessionLocal") as mock_session_cls:
        mock_session = AsyncMock()
        mock_session_cls.return_value.__aenter__.return_value = mock_session
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)
        result = await svc.generate_candidate_explanation("c", "x", "j")
    assert result["status"] == "no_data"
    assert isinstance(result["message"], str)
    assert len(result["message"]) > 10


@pytest.mark.asyncio
async def test_format_for_candidate_message_returns_string():
    """format_for_candidate_message returns a non-trivial string."""
    from app.shared.services.explainability_service import ExplainabilityService
    svc = ExplainabilityService()
    explanation_data = {
        "status": "approved",
        "overall_score": 4.2,
        "evaluation_criteria": [{"criterion": "Competências técnicas", "key": "skills"}],
        "transparency_note": "Para garantir processo justo...",
        "suggestions": [],
    }
    with patch.object(svc, "generate_candidate_explanation", new=AsyncMock(return_value=explanation_data)):
        result = await svc.format_for_candidate_message("company_1", "cand_1", "job_1")
    assert isinstance(result, str)
    assert len(result) > 20


def test_explainability_service_lgpd_ignored_criteria_defined():
    """IGNORED_LABELS covers all LGPD-protected attributes (Art.20)."""
    from app.shared.services.explainability_service import ExplainabilityService
    protected = {"age", "gender", "ethnicity", "marital_status", "religion"}
    assert protected.issubset(set(ExplainabilityService.IGNORED_LABELS.keys())), (
        "IGNORED_LABELS must cover all LGPD-protected attributes"
    )


def test_explainability_service_has_required_methods():
    """ExplainabilityService exposes all LGPD Art.20 methods."""
    from app.shared.services.explainability_service import ExplainabilityService
    for method in ["generate_candidate_explanation", "format_for_candidate_message",
                   "generate_recruiter_summary"]:
        assert hasattr(ExplainabilityService, method), f"Missing method: {method}"

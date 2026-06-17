"""Testa que add_wsi_question respeita o limite máximo por modo."""
import pytest
from unittest.mock import patch, MagicMock


def make_questions(n: int, block: str = "technical") -> list[dict]:
    return [{"id": f"q{i}", "block": block, "question": f"Q{i}", "framework": "CBI",
             "competency": "Python", "weight": 0.8} for i in range(n)]


def make_state(questions: list, mode: str = "full") -> dict:
    return {
        "job_id": "job-001",
        "wsi_questions": questions,
        "screening_mode": mode,
        "seniority_resolved": "pleno",
    }


@pytest.mark.parametrize("mode,max_q", [("full", 12), ("compact", 7)])
def test_add_blocked_at_max(mode, max_q):
    """Com max perguntas, add_wsi_question deve retornar orientação para substituir."""
    from app.domains.job_creation.orchestrator.wizard_service_tools import _handle_add_wsi_question
    state = make_state(make_questions(max_q), mode=mode)
    result = _handle_add_wsi_question(state, {"block": "technical"}, MagicMock())
    assert result.error is True
    msg = result.llm_message.lower()
    assert any(k in msg for k in ["substituir", "substitua", "limite", "máximo", "remov", "replace"])
    # NÃO deve ter modificado questions
    assert "wsi_questions" not in (result.state_updates or {})


@pytest.mark.parametrize("mode,below_max", [("full", 11), ("compact", 6)])
def test_add_allowed_below_max(mode, below_max):
    """Abaixo do limite, deve permitir adicionar (mock do _wsi_suggest_single)."""
    from app.domains.job_creation.orchestrator.wizard_service_tools import _handle_add_wsi_question
    state = make_state(make_questions(below_max), mode=mode)
    mock_res = {"success": True, "question": "Nova Q?", "block": "technical",
                "framework": "CBI", "competency": "Algo", "weight": 0.8}
    with patch("app.domains.job_creation.orchestrator.wizard_service_tools._wsi_suggest_single",
               return_value=mock_res):
        result = _handle_add_wsi_question(state, {"block": "technical"}, MagicMock())
    assert result.error is not True
    updates = result.state_updates or {}
    assert "wsi_questions" in updates
    assert len(updates["wsi_questions"]) == below_max + 1

"""TDD W0-A: Recruiter assignment — wizard publish deve gravar recruiter+email."""
import os
import pytest
from unittest.mock import MagicMock, patch


def test_state_has_recruiter_fields():
    import typing
    from app.domains.job_creation.state import JobCreationState
    hints = typing.get_type_hints(JobCreationState)
    assert "parsed_recruiter_name" in hints
    assert "parsed_recruiter_email" in hints


def test_publish_node_injects_recruiter():
    captured_job_data = {}

    def mock_create_job(job_data):
        captured_job_data.update(job_data)
        return MagicMock(success=True, data={"data": {"id": "123", "attributes": {"id": "123", "uid": "123"}}})

    mock_api = MagicMock()
    mock_api.create_job.side_effect = mock_create_job
    mock_api.save_screening_config.return_value = MagicMock(success=True, data={})
    mock_api.save_question_set.return_value = MagicMock(success=True, data={})
    mock_api.publish_job.return_value = MagicMock(success=True, data={})
    mock_api.get_share_link.return_value = MagicMock(success=True, data={"share_link": "http://test"})

    minimal_state = {
        "session_id": "sess-1", "user_id": "user-1", "workspace_id": 1,
        "company_id": "company-1", "auth_token": "tok", "language": "pt-BR",
        "jd_enriched": {"titulo_padronizado": "Eng", "about_role": "Desc",
                        "skills_obrigatorias": [], "competencias_comportamentais": [], "responsabilidades": []},
        "jd_approved": True, "questions_approved": True, "policy_confirmed_publish": True,
        "wsi_questions": [], "eligibility_questions": [], "screening_mode": "compact",
        "conversation_messages": [], "publish_platforms": ["website"],
        "parsed_recruiter_name": "Paulo Moraes",
        "parsed_recruiter_email": "paulo.moraes@wedotalent.cc",
    }

    from app.domains.job_creation.policy_gate import PolicyDecision
    mock_policy_result = MagicMock()
    mock_policy_result.decision = PolicyDecision.ALLOW

    with patch.dict(os.environ, {"RAILS_API_URL": "http://mock-rails"}), \
         patch("app.domains.job_creation.graph._get_api_client", return_value=mock_api), \
         patch("app.domains.job_creation.graph.evaluate_wizard_policy", return_value=mock_policy_result), \
         patch("app.domains.job_creation.graph.emit_policy_block_audit"):
        from app.domains.job_creation.nodes import publish as _pub_mod
        import importlib; importlib.reload(_pub_mod)
        _pub_mod.publish_node(minimal_state)

    assert captured_job_data.get("recruiter") == "Paulo Moraes", \
        f"recruiter ausente. Capturado: {captured_job_data.get('recruiter')!r}"
    assert captured_job_data.get("recruiter_email") == "paulo.moraes@wedotalent.cc", \
        f"recruiter_email ausente. Capturado: {captured_job_data.get('recruiter_email')!r}"


def test_build_state_reads_user_from_context():
    from app.domains.job_creation.services.wizard_session_service import WizardSessionService
    state = WizardSessionService._build_state(
        thread_id="thread-1", user_message="quero criar uma vaga", user_id="user-1",
        company_id="550e8400-e29b-41d4-a716-446655440000", session_id="sess-1",
        context={"user_name": "Paulo Moraes", "user_email": "paulo.moraes@wedotalent.cc"},
        prior_state={},
    )
    assert state.get("parsed_recruiter_name") == "Paulo Moraes"
    assert state.get("parsed_recruiter_email") == "paulo.moraes@wedotalent.cc"


def test_recruiter_persists_across_turns():
    from app.domains.job_creation.services.wizard_session_service import WizardSessionService
    state = WizardSessionService._build_state(
        thread_id="thread-1", user_message="continua", user_id="user-1",
        company_id="550e8400-e29b-41d4-a716-446655440000", session_id="sess-1",
        context={},
        prior_state={
            "parsed_recruiter_name": "Paulo Moraes",
            "parsed_recruiter_email": "paulo.moraes@wedotalent.cc",
        },
    )
    assert state.get("parsed_recruiter_name") == "Paulo Moraes"
    assert state.get("parsed_recruiter_email") == "paulo.moraes@wedotalent.cc"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

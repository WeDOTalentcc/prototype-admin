"""Tests for W0-B — jd_similar_reuse_id consumed on wizard publish."""
import os
from unittest.mock import MagicMock, patch


# ─── Helper ──────────────────────────────────────────────────────────────────

def _make_api_mock(job_id: str = "00000000-0000-0000-0000-000000000002"):
    m = MagicMock()
    m.create_job.return_value = MagicMock(
        success=True,
        data={"data": {"id": job_id, "attributes": {"id": job_id, "uid": job_id}}},
    )
    m.save_screening_config.return_value = MagicMock(success=True, data={})
    m.save_question_set.return_value = MagicMock(success=True, data={})
    m.publish_job.return_value = MagicMock(success=True, data={})
    m.get_share_link.return_value = MagicMock(success=True, data={"share_link": None})
    return m


def _minimal_state(**extras):
    base = {
        "session_id": "s", "user_id": "u",
        "workspace_id": "00000000-0000-0000-0000-000000000001",
        "company_id": "00000000-0000-0000-0000-000000000001",
        "auth_token": "t", "language": "pt-BR",
        "jd_enriched": {
            "titulo_padronizado": "Dev Python",
            "about_role": "d", "skills_obrigatorias": [],
            "competencias_comportamentais": [], "responsabilidades": [],
        },
        "jd_approved": True, "questions_approved": True,
        "policy_confirmed_publish": True,
        "wsi_questions": [], "eligibility_questions": [],
        "screening_mode": "compact",
        "conversation_messages": [], "publish_platforms": ["website"],
    }
    base.update(extras)
    return base


def _policy_allow():
    from app.domains.job_creation.policy_gate import PolicyDecision
    r = MagicMock()
    r.decision = PolicyDecision.ALLOW
    return r


# ─── Test 1: jd_similar_reuse_id field exists in JobCreationState ────────────

def test_state_has_jd_similar_reuse_id_field():
    """JobCreationState TypedDict declares jd_similar_reuse_id: Optional[str]."""
    import typing
    from app.domains.job_creation.state import JobCreationState
    hints = typing.get_type_hints(JobCreationState)
    assert "jd_similar_reuse_id" in hints


# ─── Test 2: increment_reuse_fire_and_forget is callable ─────────────────────

def test_increment_reuse_fire_and_forget_callable():
    """Function is importable and callable."""
    from app.domains.job_creation.services.jd_similar_service import (
        increment_reuse_fire_and_forget,
    )
    assert callable(increment_reuse_fire_and_forget)


# ─── Test 3: publish_node calls increment_reuse when reuse_id in state ───────

def test_publish_node_calls_increment_reuse_when_reuse_id_set():
    """When jd_similar_reuse_id is in state, increment_reuse_fire_and_forget is called."""
    job_id = "00000000-0000-0000-0000-000000000002"
    reuse_id = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"

    mock_api = _make_api_mock(job_id=job_id)
    mock_increment = MagicMock()

    state = _minimal_state(jd_similar_reuse_id=reuse_id)

    with (
        patch.dict(os.environ, {"RAILS_API_URL": "http://mock-rails"}),
        patch("app.domains.job_creation.graph._get_api_client", return_value=mock_api),
        patch("app.domains.job_creation.graph.evaluate_wizard_policy", return_value=_policy_allow()),
        patch("app.domains.job_creation.graph.emit_policy_block_audit"),
        patch(
            "app.domains.job_creation.services.jd_similar_service.record_jd_fire_and_forget",
            MagicMock(),
        ),
        patch(
            "app.domains.job_management.services.job_pattern_service.record_outcome_fire_and_forget",
            MagicMock(),
        ),
        patch(
            "app.domains.job_creation.services.jd_similar_service.increment_reuse_fire_and_forget",
            mock_increment,
        ),
    ):
        import importlib
        from app.domains.job_creation.nodes import publish as _pub_mod
        importlib.reload(_pub_mod)
        _pub_mod.publish_node(state)

    mock_increment.assert_called_once()
    call = mock_increment.call_args
    kw = call.kwargs or {}
    pos = call.args or ()
    if kw:
        assert kw["company_id"] == "00000000-0000-0000-0000-000000000001"
        assert kw["record_id"] == reuse_id
    else:
        assert pos[0] == "00000000-0000-0000-0000-000000000001"
        assert pos[1] == reuse_id


# ─── Test 4: no reuse_id → increment NOT called ──────────────────────────────

def test_publish_node_does_not_call_increment_when_no_reuse_id():
    """Without jd_similar_reuse_id, increment_reuse_fire_and_forget is NOT called."""
    job_id = "00000000-0000-0000-0000-000000000003"
    mock_api = _make_api_mock(job_id=job_id)
    mock_increment = MagicMock()

    state = _minimal_state()  # no jd_similar_reuse_id

    with (
        patch.dict(os.environ, {"RAILS_API_URL": "http://mock-rails"}),
        patch("app.domains.job_creation.graph._get_api_client", return_value=mock_api),
        patch("app.domains.job_creation.graph.evaluate_wizard_policy", return_value=_policy_allow()),
        patch("app.domains.job_creation.graph.emit_policy_block_audit"),
        patch(
            "app.domains.job_creation.services.jd_similar_service.record_jd_fire_and_forget",
            MagicMock(),
        ),
        patch(
            "app.domains.job_management.services.job_pattern_service.record_outcome_fire_and_forget",
            MagicMock(),
        ),
        patch(
            "app.domains.job_creation.services.jd_similar_service.increment_reuse_fire_and_forget",
            mock_increment,
        ),
    ):
        import importlib
        from app.domains.job_creation.nodes import publish as _pub_mod
        importlib.reload(_pub_mod)
        _pub_mod.publish_node(state)

    mock_increment.assert_not_called()


# ─── Test 5: _build_state extracts jd_similar_reuse_id from right_panel_form ─

def test_build_state_extracts_reuse_id_from_panel_form():
    """_build_state promotes jd_similar_reuse_id from right_panel_form to top-level state."""
    from app.domains.job_creation.services.wizard_session_service import WizardSessionService

    state = WizardSessionService._build_state(
        thread_id="t1", user_message="reusar JD", user_id="u1",
        company_id="550e8400-e29b-41d4-a716-446655440000", session_id="s1",
        context={
            "right_panel_form": {
                "jd_similar_reuse_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
                "other_field": "value",
            }
        },
        prior_state={},
    )
    assert state.get("jd_similar_reuse_id") == "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"

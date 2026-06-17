"""Tests for the honest P&E → Agent handoff contract (Task #1222)."""
from app.domains.base import DomainResponse
from app.shared.execution.agent_handoff import (
    DEFERRED_AGENTS,
    HANDOFF_METADATA_KEY,
    AgentHandoff,
    build_handoff,
    build_handoff_message,
    build_handoff_response,
    deferred_agent_for,
)


class TestDeferredAgentRegistry:
    def test_registry_has_canonical_kinds(self):
        assert set(DEFERRED_AGENTS) == {
            "triagem_wsi",
            "sourcing_continuo",
            "onboarding",
        }

    def test_registry_kind_matches_key(self):
        for key, agent in DEFERRED_AGENTS.items():
            assert agent.kind == key
            assert agent.label.strip()


class TestDeferredAgentFor:
    def test_triagem_steps_are_deferred(self):
        for action in (
            "screen_candidates",
            "run_wsi_screening",
            "send_wsi_batch",
            "list_pending_screening",
        ):
            agent = deferred_agent_for("cv_screening", action)
            assert agent is not None
            assert agent.kind == "triagem_wsi"

    def test_sourcing_start_is_deferred(self):
        agent = deferred_agent_for("sourcing", "start_sourcing")
        assert agent is not None
        assert agent.kind == "sourcing_continuo"

    def test_onboarding_steps_are_deferred(self):
        assert deferred_agent_for("communication", "request_onboarding_documents").kind == "onboarding"
        assert deferred_agent_for("interview_scheduling", "schedule_day_one").kind == "onboarding"
        assert deferred_agent_for("communication", "notify_team_new_hire").kind == "onboarding"

    def test_discrete_actions_are_not_deferred(self):
        # These are legitimate one-shot P&E actions — must NOT be deferred.
        assert deferred_agent_for("automation", "move_candidate_stage") is None
        assert deferred_agent_for("communication", "send_notification") is None
        assert deferred_agent_for("job_management", "enrich_job_description") is None
        assert deferred_agent_for("cv_screening", "parse_and_create_candidate") is None
        assert deferred_agent_for("sourcing", "search_candidates") is None


class TestBuildHandoff:
    def test_build_handoff_for_deferred(self):
        handoff = build_handoff("cv_screening", "run_wsi_screening")
        assert isinstance(handoff, AgentHandoff)
        assert handoff.kind == "triagem_wsi"
        assert handoff.executed is False  # never faked

    def test_build_handoff_none_for_discrete(self):
        assert build_handoff("automation", "move_candidate_stage") is None

    def test_message_is_explicit_and_never_fakes_success(self):
        agent = DEFERRED_AGENTS["triagem_wsi"]
        msg = build_handoff_message(agent)
        assert agent.label in msg
        lowered = msg.lower()
        assert "ainda não está disponível" in lowered
        assert "não executei" in lowered


class TestBuildHandoffResponse:
    def test_response_for_deferred_is_honest_failure(self):
        resp = build_handoff_response("sourcing", "start_sourcing")
        assert isinstance(resp, DomainResponse)
        assert resp.success is False  # it did not run
        assert HANDOFF_METADATA_KEY in resp.metadata
        meta = resp.metadata[HANDOFF_METADATA_KEY]
        assert meta["kind"] == "sourcing_continuo"
        assert meta["executed"] is False

    def test_response_none_for_discrete(self):
        assert build_handoff_response("automation", "move_candidate_stage") is None

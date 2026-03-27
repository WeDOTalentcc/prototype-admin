"""
Contract Test: Multi-Tenant Isolation
=======================================
Verifies that the AgentInput/AgentOutput contract enforces multi-tenant
isolation. company_id is a mandatory field — no agent operation should
be possible without it.

This is a cross-cutting contract that applies to ALL agents.
"""
import pytest
from pydantic import ValidationError

from lia_agents_core.agent_interface import AgentInput, AgentOutput


class TestMultiTenantIsolationContract:

    def test_agent_input_requires_company_id(self):
        """AgentInput without company_id must raise ValidationError."""
        with pytest.raises((ValidationError, TypeError)):
            AgentInput(
                message="test",
                session_id="s-001",
                user_id="u-001",
                # company_id intentionally omitted
            )

    def test_agent_input_requires_user_id(self):
        """AgentInput without user_id must raise ValidationError."""
        with pytest.raises((ValidationError, TypeError)):
            AgentInput(
                message="test",
                session_id="s-001",
                company_id="c-001",
                # user_id intentionally omitted
            )

    def test_agent_input_requires_session_id(self):
        """AgentInput without session_id must raise ValidationError."""
        with pytest.raises((ValidationError, TypeError)):
            AgentInput(
                message="test",
                company_id="c-001",
                user_id="u-001",
                # session_id intentionally omitted
            )

    def test_agent_input_company_id_is_string(self):
        """company_id must be a string (UUIDs, slugs, etc. all accepted)."""
        valid_ids = [
            "company-uuid-001",
            "550e8400-e29b-41d4-a716-446655440000",
            "wedotalent",
        ]
        for cid in valid_ids:
            inp = AgentInput(
                message="test", session_id="s-001", company_id=cid, user_id="u-001"
            )
            assert inp.company_id == cid

    def test_different_tenants_have_isolated_inputs(self):
        """Two AgentInputs with different company_ids must not share state."""
        inp_a = AgentInput(
            message="vaga Python",
            context={"draft": {"title": "Dev A"}},
            session_id="session-a",
            company_id="company-a",
            user_id="user-a",
        )
        inp_b = AgentInput(
            message="vaga Java",
            context={"draft": {"title": "Dev B"}},
            session_id="session-b",
            company_id="company-b",
            user_id="user-b",
        )
        # Pydantic creates independent copies — modifying one must not affect the other
        inp_a.context["draft"]["title"] = "MODIFIED"
        assert inp_b.context["draft"]["title"] == "Dev B", (
            "Modifying one tenant's context must not affect another"
        )

    def test_agent_input_context_defaults_to_empty_dict(self):
        """context defaults to {} — no shared mutable default."""
        inp1 = AgentInput(message="a", session_id="s1", company_id="c1", user_id="u1")
        inp2 = AgentInput(message="b", session_id="s2", company_id="c2", user_id="u2")
        inp1.context["key"] = "value"
        # inp2.context must NOT have been mutated
        assert "key" not in inp2.context, "context must use per-instance default_factory"

    def test_agent_output_state_updates_defaults_to_empty_dict(self):
        """state_updates defaults to {} — no shared mutable default."""
        out1 = AgentOutput(message="out1")
        out2 = AgentOutput(message="out2")
        out1.state_updates["key"] = "value"
        assert "key" not in out2.state_updates, (
            "state_updates must use per-instance default_factory"
        )

    def test_agent_output_actions_defaults_to_empty_list(self):
        """actions defaults to [] — no shared mutable default."""
        out1 = AgentOutput(message="out1")
        out2 = AgentOutput(message="out2")
        out1.actions.append({"action_type": "test"})
        assert len(out2.actions) == 0, (
            "actions must use per-instance default_factory"
        )

    def test_agent_input_accepts_empty_message_string(self):
        """Empty message string must be valid (agent may handle it gracefully)."""
        inp = AgentInput(
            message="",
            session_id="s-001",
            company_id="c-001",
            user_id="u-001",
        )
        assert inp.message == ""

    def test_agent_input_conversation_history_defaults_to_empty_list(self):
        """conversation_history defaults to [] — independent per instance."""
        inp1 = AgentInput(message="a", session_id="s1", company_id="c1", user_id="u1")
        inp2 = AgentInput(message="b", session_id="s2", company_id="c2", user_id="u2")
        inp1.conversation_history.append({"role": "user", "content": "hello"})
        assert len(inp2.conversation_history) == 0, (
            "conversation_history must use per-instance default_factory"
        )

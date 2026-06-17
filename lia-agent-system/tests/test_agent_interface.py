import pytest
from lia_agents_core.agent_interface import (
    AgentInput,
    AgentOutput,
    AgentAction,
    NavigationCommand,
    BaseAgent,
)
from lia_agents_core.working_memory import AgentWorkingMemory, WorkingMemorySchema


class TestAgentInterface:
    def test_agent_input_creation(self):
        inp = AgentInput(
            message="test",
            session_id="s1",
            company_id="c1",
            user_id="u1",
        )
        assert inp.message == "test"
        assert inp.session_id == "s1"
        assert inp.company_id == "c1"
        assert inp.user_id == "u1"
        assert inp.context == {}
        assert inp.conversation_history == []
        assert inp.metadata == {}

    def test_agent_input_with_context(self):
        inp = AgentInput(
            message="create job",
            session_id="s2",
            company_id="c2",
            user_id="u2",
            context={"stage": "input-evaluation"},
            metadata={"source": "chat"},
        )
        assert inp.context["stage"] == "input-evaluation"
        assert inp.metadata["source"] == "chat"

    def test_agent_input_with_conversation_history(self):
        history = [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi"},
        ]
        inp = AgentInput(
            message="next",
            session_id="s1",
            company_id="c1",
            user_id="u1",
            conversation_history=history,
        )
        assert len(inp.conversation_history) == 2

    def test_agent_output_creation(self):
        out = AgentOutput(message="response", confidence=0.9)
        assert out.message == "response"
        assert out.confidence == 0.9
        assert out.actions == []
        assert out.state_updates == {}
        assert out.navigation is None
        assert out.reasoning_steps == []
        assert out.tool_results == []
        assert out.metadata == {}
        assert out.error is None

    def test_agent_output_with_actions(self):
        action = AgentAction(
            action_type="call_tool",
            params={"tool": "search", "args": {"q": "test"}},
        )
        out = AgentOutput(
            message="done",
            confidence=0.8,
            actions=[action],
        )
        assert len(out.actions) == 1
        assert out.actions[0].action_type == "call_tool"
        assert out.actions[0].requires_confirmation is False

    def test_agent_output_with_navigation(self):
        nav = NavigationCommand(
            target_stage="jd-enrichment",
            reason="Fields complete",
            auto_navigate=False,
        )
        out = AgentOutput(
            message="Let's move on",
            confidence=0.85,
            navigation=nav,
        )
        assert out.navigation is not None
        assert out.navigation.target_stage == "jd-enrichment"

    def test_agent_output_confidence_bounds(self):
        out = AgentOutput(message="test", confidence=0.0)
        assert out.confidence == 0.0

        out2 = AgentOutput(message="test", confidence=1.0)
        assert out2.confidence == 1.0

        with pytest.raises(Exception):
            AgentOutput(message="test", confidence=1.5)

        with pytest.raises(Exception):
            AgentOutput(message="test", confidence=-0.1)

    def test_navigation_command(self):
        nav = NavigationCommand(
            target_stage="next",
            reason="criteria met",
            auto_navigate=False,
        )
        assert nav.target_stage == "next"
        assert nav.auto_navigate is False
        assert nav.reason == "criteria met"

    def test_navigation_command_auto_navigate(self):
        nav = NavigationCommand(
            target_stage="salary",
            reason="auto",
            auto_navigate=True,
        )
        assert nav.auto_navigate is True

    def test_agent_action(self):
        action = AgentAction(
            action_type="update_field",
            params={"field": "title", "value": "Engineer"},
            requires_confirmation=True,
        )
        assert action.action_type == "update_field"
        assert action.params["field"] == "title"
        assert action.requires_confirmation is True

    def test_agent_action_defaults(self):
        action = AgentAction(action_type="navigate")
        assert action.params == {}
        assert action.requires_confirmation is False

    def test_agent_output_with_error(self):
        out = AgentOutput(
            message="Error occurred",
            confidence=0.0,
            error="Something broke",
        )
        assert out.error == "Something broke"


class TestAgentWorkingMemory:
    def test_model_fields(self):
        columns = {c.name for c in AgentWorkingMemory.__table__.columns}
        expected = {
            "id", "session_id", "domain", "current_stage",
            "collected_fields", "current_plan", "pending_actions",
            "adjustment_history", "parecer_data", "accepted_suggestions",
            "rejected_suggestions", "agent_notes", "iteration_count",
            "last_intent", "last_confidence", "created_at", "updated_at",
            "company_id", "user_id",
        }
        assert expected.issubset(columns), f"Missing columns: {expected - columns}"

    def test_tablename(self):
        assert AgentWorkingMemory.__tablename__ == "agent_working_memory"


class TestWorkingMemorySchema:
    def test_default_values(self):
        schema = WorkingMemorySchema(
            session_id="s1",
            domain="wizard",
        )
        assert schema.session_id == "s1"
        assert schema.domain == "wizard"
        assert schema.current_stage is None
        assert schema.collected_fields == {}
        assert schema.current_plan == []
        assert schema.pending_actions == []
        assert schema.adjustment_history == []
        assert schema.parecer_data == {}
        assert schema.accepted_suggestions == []
        assert schema.rejected_suggestions == []
        assert schema.agent_notes is None
        assert schema.iteration_count == 0
        assert schema.last_intent is None
        assert schema.last_confidence is None

    def test_schema_with_values(self):
        schema = WorkingMemorySchema(
            session_id="s2",
            domain="pipeline",
            current_stage="review",
            collected_fields={"title": {"value": "Dev", "confidence": 0.9}},
            iteration_count=5,
            last_intent="create_job",
            last_confidence=0.95,
            company_id="c1",
            user_id="u1",
        )
        assert schema.current_stage == "review"
        assert schema.collected_fields["title"]["value"] == "Dev"
        assert schema.iteration_count == 5
        assert schema.last_confidence == 0.95

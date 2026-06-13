import pytest
from app.domains.job_creation.orchestrator.wizard_tools import (
    build_tool_registry,
    ToolContext,
)


class TestScreeningDeadlineTool:
    """Sensor: set_screening_deadline tool canonical behavior."""

    @pytest.fixture
    def ctx(self):
        return ToolContext(company_id="test-co", user_id="u1")

    @pytest.fixture
    def registry(self):
        return build_tool_registry()

    def _call(self, registry, ctx, hours):
        tool = registry["set_screening_deadline"]
        state = {}
        result = tool.handler(state, {"hours": hours}, ctx)
        state.update(result.state_updates)
        return result, state

    def test_tool_registered(self, registry):
        assert "set_screening_deadline" in registry

    def test_valid_48h(self, registry, ctx):
        result, state = self._call(registry, ctx, 48)
        assert not result.error
        assert state["screening_deadline_hours"] == 48
        assert "2 dias" in result.llm_message

    def test_valid_24h(self, registry, ctx):
        result, state = self._call(registry, ctx, 24)
        assert not result.error
        assert "24h" in result.llm_message

    def test_valid_168h_7days(self, registry, ctx):
        result, state = self._call(registry, ctx, 168)
        assert not result.error
        assert "7 dias" in result.llm_message

    def test_valid_72h_3days(self, registry, ctx):
        result, state = self._call(registry, ctx, 72)
        assert not result.error
        assert "3 dias" in result.llm_message

    def test_odd_hours_display(self, registry, ctx):
        result, state = self._call(registry, ctx, 36)
        assert not result.error
        assert "36h" in result.llm_message
        assert "1 dias" in result.llm_message

    def test_reject_too_low(self, registry, ctx):
        result, _ = self._call(registry, ctx, 6)
        assert result.error
        assert "12h" in result.llm_message

    def test_reject_too_high(self, registry, ctx):
        result, _ = self._call(registry, ctx, 800)
        assert result.error
        assert "720h" in result.llm_message

    def test_reject_missing_hours(self, registry, ctx):
        tool = registry["set_screening_deadline"]
        result = tool.handler({}, {}, ctx)
        assert result.error

    def test_reject_tenant_keys(self, registry, ctx):
        tool = registry["set_screening_deadline"]
        result = tool.handler({}, {"hours": 48, "company_id": "evil"}, ctx)
        assert result.error

    def test_schema_requires_hours(self, registry):
        tool = registry["set_screening_deadline"]
        assert "hours" in tool.input_schema["required"]
        assert tool.input_schema["properties"]["hours"]["type"] == "integer"


class TestScreeningDeadlinePromptGuide:
    """Sensor: system prompt mentions deadline defaults."""

    @pytest.fixture
    def prompt(self):
        from app.domains.job_creation.orchestrator.wizard_orchestrator import (
            _SYSTEM_PROMPT_BASE,
        )
        return _SYSTEM_PROMPT_BASE

    def test_mentions_48h_default(self, prompt):
        assert "48h" in prompt

    def test_mentions_set_screening_deadline_tool(self, prompt):
        assert "set_screening_deadline" in prompt

    def test_mentions_presets(self, prompt):
        for preset in ["24h", "72h", "168h"]:
            assert preset in prompt, f"Missing preset {preset}"

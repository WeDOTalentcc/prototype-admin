"""E5 — Multi-Model por Agente"""
import pytest
import os


class TestAgentModelConfig:

    def test_default_config_has_expected_agents(self):
        from app.core.agent_model_config import AGENT_MODEL_CONFIG
        expected = ["wsi_interview", "sourcing", "pipeline", "analytics"]
        for agent in expected:
            assert agent in AGENT_MODEL_CONFIG

    def test_build_config_with_env_override(self):
        from app.core.agent_model_config import build_agent_model_config
        import os
        old = os.environ.get("AGENT_MODEL_SOURCING")
        os.environ["AGENT_MODEL_SOURCING"] = "claude-opus-4-6"
        try:
            config = build_agent_model_config()
            assert config.get("sourcing") == "claude-opus-4-6"
        finally:
            if old is None:
                os.environ.pop("AGENT_MODEL_SOURCING", None)
            else:
                os.environ["AGENT_MODEL_SOURCING"] = old

    def test_get_model_for_agent_known(self):
        from app.core.agent_model_config import get_model_for_agent
        model = get_model_for_agent("sourcing")
        assert model.startswith("claude-")

    def test_get_model_for_agent_unknown_returns_default(self):
        from app.core.agent_model_config import get_model_for_agent, DEFAULT_MODEL
        model = get_model_for_agent("nonexistent_agent_xyz")
        assert model == DEFAULT_MODEL

    def test_default_model_is_claude(self):
        from app.core.agent_model_config import DEFAULT_MODEL
        assert "claude" in DEFAULT_MODEL

    def test_all_agents_use_claude_models(self):
        from app.core.agent_model_config import AGENT_MODEL_CONFIG
        for agent, model in AGENT_MODEL_CONFIG.items():
            assert "claude" in model, f"Agent {agent} uses non-Claude model: {model}"


class TestEnhancedAgentMixinModelId:

    def test_model_id_property_exists(self):
        from lia_agents_core.enhanced_agent_mixin import EnhancedAgentMixin
        assert hasattr(EnhancedAgentMixin, "model_id")

    def test_model_id_returns_string(self):
        from lia_agents_core.enhanced_agent_mixin import EnhancedAgentMixin
        mixin = EnhancedAgentMixin.__new__(EnhancedAgentMixin)
        mixin._enhanced_domain = "sourcing"
        model = mixin.model_id
        assert isinstance(model, str)
        assert model.startswith("claude-")

    def test_model_id_unknown_domain_fallback(self):
        from lia_agents_core.enhanced_agent_mixin import EnhancedAgentMixin
        from app.core.agent_model_config import DEFAULT_MODEL
        mixin = EnhancedAgentMixin.__new__(EnhancedAgentMixin)
        mixin._enhanced_domain = "nonexistent_domain_xyz"
        model = mixin.model_id
        assert model == DEFAULT_MODEL

    def test_model_id_handles_missing_domain(self):
        from lia_agents_core.enhanced_agent_mixin import EnhancedAgentMixin
        mixin = EnhancedAgentMixin.__new__(EnhancedAgentMixin)
        # _enhanced_domain não definido — deve usar fallback
        model = mixin.model_id
        assert isinstance(model, str)
        assert len(model) > 0

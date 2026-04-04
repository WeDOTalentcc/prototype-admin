"""
Unit tests — LangSmith configuration (app/config/langsmith.py).

Cobre:
- configure_langsmith() sem API key → retorna False, não levanta exceção
- configure_langsmith() com API key → retorna True, seta env vars
- is_langsmith_enabled() reflete LANGCHAIN_TRACING_V2
- get_langsmith_project() retorna projeto correto
- configure_langsmith() com workspace_id seta variável extra
"""
import os
import pytest
from unittest.mock import patch


class TestConfigureLangsmith:

    def test_no_api_key_returns_false(self):
        from app.config.langsmith import configure_langsmith
        with patch.dict(os.environ, {}, clear=False):
            env = {k: v for k, v in os.environ.items()
                   if k not in ("LANGSMITH_API_KEY", "LANGCHAIN_API_KEY")}
            with patch.dict(os.environ, env, clear=True):
                result = configure_langsmith()
        assert result is False

    def test_with_api_key_returns_true(self):
        from app.config.langsmith import configure_langsmith
        env_patch = {
            "LANGSMITH_API_KEY": "ls__test123",
            "LANGSMITH_PROJECT": "lia-test",
        }
        with patch.dict(os.environ, env_patch):
            result = configure_langsmith()
        assert result is True

    def test_with_api_key_sets_langchain_tracing(self):
        from app.config.langsmith import configure_langsmith
        env_patch = {"LANGSMITH_API_KEY": "ls__test456"}
        with patch.dict(os.environ, env_patch):
            configure_langsmith()
            assert os.environ.get("LANGCHAIN_TRACING_V2") == "true"

    def test_with_api_key_sets_langchain_api_key(self):
        from app.config.langsmith import configure_langsmith
        env_patch = {"LANGSMITH_API_KEY": "ls__test789"}
        with patch.dict(os.environ, env_patch):
            configure_langsmith()
            assert os.environ.get("LANGCHAIN_API_KEY") == "ls__test789"

    def test_with_api_key_sets_endpoint(self):
        from app.config.langsmith import configure_langsmith
        env_patch = {"LANGSMITH_API_KEY": "ls__ep_test"}
        with patch.dict(os.environ, env_patch):
            configure_langsmith()
            assert "smith.langchain.com" in os.environ.get("LANGCHAIN_ENDPOINT", "")

    def test_with_workspace_id_sets_env_var(self):
        from app.config.langsmith import configure_langsmith
        env_patch = {
            "LANGSMITH_API_KEY": "ls__ws_test",
            "LANGSMITH_WORKSPACE_ID": "my-org-123",
        }
        with patch.dict(os.environ, env_patch):
            configure_langsmith()
            assert os.environ.get("LANGSMITH_WORKSPACE_ID") == "my-org-123"

    def test_without_workspace_id_still_returns_true(self):
        from app.config.langsmith import configure_langsmith
        env_patch = {"LANGSMITH_API_KEY": "ls__no_ws"}
        # Garantir que LANGSMITH_WORKSPACE_ID não está no env
        env = {k: v for k, v in os.environ.items() if k != "LANGSMITH_WORKSPACE_ID"}
        env.update(env_patch)
        with patch.dict(os.environ, env, clear=True):
            result = configure_langsmith()
        assert result is True

    def test_project_defaults_to_lia_agent_system(self):
        from app.config.langsmith import configure_langsmith
        env = {k: v for k, v in os.environ.items()
               if k not in ("LANGSMITH_PROJECT", "LANGCHAIN_PROJECT")}
        env["LANGSMITH_API_KEY"] = "ls__proj_default"
        with patch.dict(os.environ, env, clear=True):
            configure_langsmith()
            assert os.environ.get("LANGCHAIN_PROJECT") == "lia-agent-system"

    def test_custom_project_name(self):
        from app.config.langsmith import configure_langsmith
        env_patch = {
            "LANGSMITH_API_KEY": "ls__proj_custom",
            "LANGSMITH_PROJECT": "my-custom-project",
        }
        with patch.dict(os.environ, env_patch):
            configure_langsmith()
            assert os.environ.get("LANGCHAIN_PROJECT") == "my-custom-project"

    def test_langchain_api_key_fallback(self):
        from app.config.langsmith import configure_langsmith
        env = {k: v for k, v in os.environ.items() if k != "LANGSMITH_API_KEY"}
        env["LANGCHAIN_API_KEY"] = "lsv2__fallback_key"
        with patch.dict(os.environ, env, clear=True):
            result = configure_langsmith()
        assert result is True

    def test_langchain_api_key_sets_tracing(self):
        from app.config.langsmith import configure_langsmith
        env = {k: v for k, v in os.environ.items() if k != "LANGSMITH_API_KEY"}
        env["LANGCHAIN_API_KEY"] = "lsv2__tracing_test"
        with patch.dict(os.environ, env, clear=True):
            configure_langsmith()
            assert os.environ.get("LANGCHAIN_TRACING_V2") == "true"
            assert os.environ.get("LANGCHAIN_API_KEY") == "lsv2__tracing_test"
            assert os.environ.get("LANGCHAIN_PROJECT") == "lia-agent-system"

    def test_langsmith_api_key_takes_precedence(self):
        from app.config.langsmith import configure_langsmith
        env_patch = {
            "LANGSMITH_API_KEY": "ls__primary",
            "LANGCHAIN_API_KEY": "ls__fallback",
        }
        with patch.dict(os.environ, env_patch):
            configure_langsmith()
            assert os.environ.get("LANGCHAIN_API_KEY") == "ls__primary"


class TestIsLangsmithEnabled:

    def test_enabled_when_tracing_true(self):
        from app.config.langsmith import is_langsmith_enabled
        with patch.dict(os.environ, {"LANGCHAIN_TRACING_V2": "true"}):
            assert is_langsmith_enabled() is True

    def test_disabled_when_tracing_false(self):
        from app.config.langsmith import is_langsmith_enabled
        with patch.dict(os.environ, {"LANGCHAIN_TRACING_V2": "false"}):
            assert is_langsmith_enabled() is False

    def test_disabled_when_not_set(self):
        from app.config.langsmith import is_langsmith_enabled
        env = {k: v for k, v in os.environ.items() if k != "LANGCHAIN_TRACING_V2"}
        with patch.dict(os.environ, env, clear=True):
            assert is_langsmith_enabled() is False

    def test_case_insensitive_true(self):
        from app.config.langsmith import is_langsmith_enabled
        with patch.dict(os.environ, {"LANGCHAIN_TRACING_V2": "TRUE"}):
            assert is_langsmith_enabled() is True


class TestGetLangsmithProject:

    def test_returns_project_name(self):
        from app.config.langsmith import get_langsmith_project
        with patch.dict(os.environ, {"LANGCHAIN_PROJECT": "test-project"}):
            assert get_langsmith_project() == "test-project"

    def test_returns_none_when_not_set(self):
        from app.config.langsmith import get_langsmith_project
        env = {k: v for k, v in os.environ.items() if k != "LANGCHAIN_PROJECT"}
        with patch.dict(os.environ, env, clear=True):
            assert get_langsmith_project() is None


class TestLangsmithMainIntegration:
    """Verifica que configure_langsmith é chamado no startup."""

    def test_main_calls_configure_langsmith(self):
        import pathlib
        content = pathlib.Path("app/main.py").read_text()
        assert "configure_langsmith" in content

    def test_langsmith_module_importable(self):
        import importlib
        mod = importlib.import_module("app.config.langsmith")
        assert hasattr(mod, "configure_langsmith")
        assert hasattr(mod, "is_langsmith_enabled")
        assert hasattr(mod, "get_langsmith_project")

    def test_configure_langsmith_is_callable(self):
        from app.config.langsmith import configure_langsmith
        import inspect
        assert callable(configure_langsmith)
        # Deve poder ser chamado sem argumentos
        sig = inspect.signature(configure_langsmith)
        assert len(sig.parameters) == 0

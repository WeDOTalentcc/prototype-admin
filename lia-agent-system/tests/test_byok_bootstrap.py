"""
Tests for BYOK tenant key injection in llm_bootstrap._get_tenant_key_sync.

Verifica que:
1. Sem tenant → retorna None (fallback para env var global)
2. Tenant sem config → retorna None
3. Tenant com key → retorna a key correta por provider
4. Key mascarada ("...") → retorna None (protege contra GET mascarado)
5. Key vazia → retorna None
"""
import pytest
from unittest.mock import patch


def test_no_tenant_returns_none():
    """Sem company_id no contextvar → None."""
    with patch("app.shared.llm_bootstrap._get_tenant_id", return_value=""):
        from app.shared.llm_bootstrap import _get_tenant_key_sync
        assert _get_tenant_key_sync("anthropic") is None


def test_tenant_without_config_returns_none():
    """Tenant sem entrada no cache → None."""
    with patch("app.shared.llm_bootstrap._get_tenant_id", return_value="company-abc"):
        with patch("app.shared.tenant_llm_context._tenant_configs", {}):
            from app.shared.llm_bootstrap import _get_tenant_key_sync
            assert _get_tenant_key_sync("anthropic") is None


def test_tenant_with_anthropic_key():
    """Tenant com key cadastrada → retorna a key."""
    configs = {
        "company-abc": {
            "providers": {
                "anthropic": {"api_key": "sk-ant-tenant-key-123", "is_active": True},
            }
        }
    }
    with patch("app.shared.llm_bootstrap._get_tenant_id", return_value="company-abc"):
        with patch("app.shared.tenant_llm_context._tenant_configs", configs):
            from app.shared.llm_bootstrap import _get_tenant_key_sync
            assert _get_tenant_key_sync("anthropic") == "sk-ant-tenant-key-123"


def test_tenant_with_openai_key():
    """Tenant com key OpenAI cadastrada."""
    configs = {
        "company-xyz": {
            "providers": {
                "openai": {"api_key": "sk-openai-tenant-key-456"},
                "anthropic": {},
            }
        }
    }
    with patch("app.shared.llm_bootstrap._get_tenant_id", return_value="company-xyz"):
        with patch("app.shared.tenant_llm_context._tenant_configs", configs):
            from app.shared.llm_bootstrap import _get_tenant_key_sync
            assert _get_tenant_key_sync("openai") == "sk-openai-tenant-key-456"
            assert _get_tenant_key_sync("anthropic") is None  # sem key Anthropic


def test_tenant_with_gemini_key():
    """Tenant com key Gemini cadastrada."""
    configs = {
        "company-gem": {
            "providers": {
                "gemini": {"api_key": "AIzaSy-tenant-gemini-key"},
            }
        }
    }
    with patch("app.shared.llm_bootstrap._get_tenant_id", return_value="company-gem"):
        with patch("app.shared.tenant_llm_context._tenant_configs", configs):
            from app.shared.llm_bootstrap import _get_tenant_key_sync
            assert _get_tenant_key_sync("gemini") == "AIzaSy-tenant-gemini-key"


def test_masked_key_returns_none():
    """Key mascarada pelo GET endpoint ('sk-ant-...') → None (não usar)."""
    configs = {
        "company-mask": {
            "providers": {
                "anthropic": {"api_key": "sk-ant-..."},
            }
        }
    }
    with patch("app.shared.llm_bootstrap._get_tenant_id", return_value="company-mask"):
        with patch("app.shared.tenant_llm_context._tenant_configs", configs):
            from app.shared.llm_bootstrap import _get_tenant_key_sync
            assert _get_tenant_key_sync("anthropic") is None


def test_empty_key_returns_none():
    """Key vazia → None."""
    configs = {
        "company-empty": {
            "providers": {
                "anthropic": {"api_key": ""},
            }
        }
    }
    with patch("app.shared.llm_bootstrap._get_tenant_id", return_value="company-empty"):
        with patch("app.shared.tenant_llm_context._tenant_configs", configs):
            from app.shared.llm_bootstrap import _get_tenant_key_sync
            assert _get_tenant_key_sync("anthropic") is None


def test_import_error_returns_none():
    """Se tenant_llm_context não importar → None (fail-safe)."""
    with patch("app.shared.llm_bootstrap._get_tenant_id", return_value="company-abc"):
        with patch.dict("sys.modules", {"app.shared.tenant_llm_context": None}):
            from app.shared.llm_bootstrap import _get_tenant_key_sync
            result = _get_tenant_key_sync("anthropic")
            assert result is None

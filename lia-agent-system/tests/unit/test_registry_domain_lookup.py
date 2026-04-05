"""
Tests for Agent Studio registry — Etapa 8 hardening.

Cobre:
- get_domain_for_company() retorna global domain quando db=None
- get_domain_for_company() retorna global domain quando nenhum template encontrado
- get_domain_for_company() retorna _YamlDomainProxy quando template existe
- _YamlDomainProxy.get_system_prompt() faz interpolação de {{var}}
- _YamlDomainProxy.domain_id está correto
- Exceção no lookup de template não propaga (non-blocking)
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestGetDomainForCompanyNoDb:
    """Testa resolução sem banco (db=None)."""

    @pytest.mark.asyncio
    async def test_returns_global_domain_when_db_is_none(self):
        """Sem DB, deve retornar o domínio global."""
        from app.domains.registry import get_domain_for_company, DomainRegistry

        result = await get_domain_for_company("sourcing", "company-xyz", db=None)

        # Should be the same as DomainRegistry().get_instance("sourcing")
        registry = DomainRegistry()
        global_domain = registry.get_instance("sourcing")

        # Both should be of the same type (same global domain)
        assert type(result) == type(global_domain)


class TestGetDomainForCompanyWithDb:
    """Testa resolução com banco mockado."""

    @pytest.mark.asyncio
    async def test_returns_global_domain_when_no_template_found(self):
        """Se nenhum template publicado encontrado, retorna domínio global."""
        from app.domains.registry import get_domain_for_company, DomainRegistry, _YamlDomainProxy

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await get_domain_for_company("sourcing", "company-xyz", db=mock_db)

        assert not isinstance(result, _YamlDomainProxy)

    @pytest.mark.asyncio
    async def test_returns_yaml_proxy_when_template_found(self):
        """Se template publicado encontrado, retorna _YamlDomainProxy."""
        from app.domains.registry import get_domain_for_company, _YamlDomainProxy

        mock_template = MagicMock()
        mock_template.name = "Custom Sourcing"
        mock_template.version = 2
        mock_template.system_prompt_yaml = "name: custom\nprompt: |\n  You are custom.\n"

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_template
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await get_domain_for_company("sourcing", "company-xyz", db=mock_db)

        assert isinstance(result, _YamlDomainProxy)

    @pytest.mark.asyncio
    async def test_non_blocking_on_db_exception(self):
        """Exceção no lookup deve ser capturada e retornar domínio global."""
        from app.domains.registry import get_domain_for_company, _YamlDomainProxy

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(side_effect=Exception("DB timeout"))

        # Should NOT raise
        result = await get_domain_for_company("sourcing", "company-xyz", db=mock_db)

        # Falls back to global domain
        assert not isinstance(result, _YamlDomainProxy)


class TestYamlDomainProxy:
    """Testa o proxy YAML para templates de agente."""

    SAMPLE_YAML = """
name: test_agent
version: 1
variables:
  - name: company_name
    default: "Empresa"
prompt: |
  Você é o agente da {{company_name}}.
  Domínio: {{domain}}.
"""

    def test_proxy_domain_id_set_correctly(self):
        from app.domains.registry import _YamlDomainProxy
        proxy = _YamlDomainProxy(self.SAMPLE_YAML, "sourcing")
        assert proxy.domain_id == "sourcing"

    def test_proxy_get_system_prompt_returns_string(self):
        from app.domains.registry import _YamlDomainProxy
        proxy = _YamlDomainProxy(self.SAMPLE_YAML, "sourcing")
        prompt = proxy.get_system_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_proxy_get_system_prompt_interpolates_variables(self):
        from app.domains.registry import _YamlDomainProxy
        proxy = _YamlDomainProxy(self.SAMPLE_YAML, "sourcing")
        prompt = proxy.get_system_prompt(company_name="Acme Corp")
        assert "Acme Corp" in prompt
        assert "{{company_name}}" not in prompt

    def test_proxy_get_system_prompt_replaces_domain_variable(self):
        from app.domains.registry import _YamlDomainProxy
        proxy = _YamlDomainProxy(self.SAMPLE_YAML, "pipeline")
        # Proxy replaces {{key}} only when kwarg is explicitly passed
        prompt = proxy.get_system_prompt(domain="pipeline")
        assert "{{domain}}" not in prompt
        assert "pipeline" in prompt

    def test_proxy_handles_minimal_yaml(self):
        from app.domains.registry import _YamlDomainProxy
        minimal_yaml = "name: minimal\nprompt: |\n  You are a test agent.\n"
        proxy = _YamlDomainProxy(minimal_yaml, "wsi")
        prompt = proxy.get_system_prompt()
        assert isinstance(prompt, str)

    def test_proxy_domain_property(self):
        from app.domains.registry import _YamlDomainProxy
        proxy = _YamlDomainProxy(self.SAMPLE_YAML, "sourcing")
        # Should expose domain_id
        assert hasattr(proxy, "domain_id")
        assert proxy.domain_id == "sourcing"

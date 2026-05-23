"""
Task #320 — Routing closure for CompanySettingsReActAgent.

Verifies that typical company-config prompts are routed to the
``company_settings`` domain by the FastRouter (config-as-data via
``app/orchestrator/config/domain_routing.yaml``), and that the agent-type
strings ``company_settings`` / ``company_profile`` / ``company_config``
all resolve to the canonical ``company_settings`` domain.

Acceptance per task brief:
  - Prompts like "quero mudar o logo", "atualizar etapas padrão", and
    "trocar nosso domínio" route to the CompanySettingsReActAgent.
  - Mapping in ``domain_mappings.py`` is consistent with the YAML.
"""
import pytest


COMPANY_SETTINGS_PROMPTS = [
    "quero mudar o logo da empresa",
    "preciso atualizar o logo",
    "trocar nosso domínio corporativo",
    "alterar a política da empresa de home office",
    "atualizar etapas padrão do funil",
    "configurar etapas default do pipeline",
    "ajustes da empresa: cultura e valores",
    "atualizar perfil da empresa",
    "configurar tech stack da nossa organização",
    "subir um novo logotipo",
]


class TestCompanySettingsFastRouter:
    @pytest.mark.parametrize("prompt", COMPANY_SETTINGS_PROMPTS)
    def test_prompt_routes_to_company_settings(self, prompt: str) -> None:
        from app.orchestrator.routing.fast_router import FastRouter

        router = FastRouter()
        result = router.match(prompt)
        assert result is not None, f"FastRouter returned no match for: {prompt!r}"
        assert result.domain_id == "company_settings", (
            f"Expected 'company_settings' for {prompt!r}, "
            f"got {result.domain_id!r} via pattern {result.matched_pattern!r}"
        )
        assert result.confidence >= 0.7

    def test_company_settings_domain_present_in_yaml_load(self) -> None:
        """The YAML load path must expose 'company_settings' as a domain."""
        from app.orchestrator.routing.fast_router import DOMAIN_PATTERNS

        assert "company_settings" in DOMAIN_PATTERNS
        assert len(DOMAIN_PATTERNS["company_settings"]) >= 5


class TestCompanySettingsDomainMapping:
    @pytest.mark.parametrize(
        "agent_type",
        ["company_settings", "company_profile", "company_config"],
    )
    def test_agent_type_resolves_to_company_settings(self, agent_type: str) -> None:
        from app.orchestrator.routing.domain_mappings import resolve_domain

        assert resolve_domain(agent_type) == "company_settings"

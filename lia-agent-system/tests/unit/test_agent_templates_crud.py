"""
Tests for AgentTemplates CRUD — Etapa 8 hardening.

Cobre:
- AgentTemplateCreate validação (YAML com "prompt", domain válido)
- ALLOWED_DOMAINS contém os domínios esperados
- AgentTemplate model tem campos corretos
- AgentTemplateStatus enum tem DRAFT, PUBLISHED, ARCHIVED
- Router registrado com as rotas esperadas
- Validação rejeita YAML sem campo "prompt"
- Validação rejeita domain inválido
- Validação rejeita name muito curto
"""
import pytest


class TestAgentTemplateModel:
    """Testa o model SQLAlchemy."""

    def test_model_exists(self):
        from libs.models.lia_models.agent_template import AgentTemplate
        assert AgentTemplate is not None

    def test_model_tablename(self):
        from libs.models.lia_models.agent_template import AgentTemplate
        assert AgentTemplate.__tablename__ == "agent_templates"

    def test_model_has_required_columns(self):
        from libs.models.lia_models.agent_template import AgentTemplate
        required = ["id", "company_id", "name", "domain", "system_prompt_yaml",
                    "version", "status", "created_by", "created_at"]
        for col_name in required:
            assert hasattr(AgentTemplate, col_name), f"Missing column: {col_name}"

    def test_model_has_published_at(self):
        from libs.models.lia_models.agent_template import AgentTemplate
        assert hasattr(AgentTemplate, "published_at")

    def test_model_has_base_template_id(self):
        from libs.models.lia_models.agent_template import AgentTemplate
        assert hasattr(AgentTemplate, "base_template_id")


class TestAgentTemplateStatus:
    """Testa o enum de status."""

    def test_status_enum_exists(self):
        from libs.models.lia_models.agent_template import AgentTemplateStatus
        assert AgentTemplateStatus is not None

    def test_status_has_draft(self):
        from libs.models.lia_models.agent_template import AgentTemplateStatus
        assert hasattr(AgentTemplateStatus, "DRAFT") or "draft" in [s.value for s in AgentTemplateStatus]

    def test_status_has_published(self):
        from libs.models.lia_models.agent_template import AgentTemplateStatus
        values = [s.value for s in AgentTemplateStatus]
        assert "published" in values

    def test_status_has_archived(self):
        from libs.models.lia_models.agent_template import AgentTemplateStatus
        values = [s.value for s in AgentTemplateStatus]
        assert "archived" in values


class TestAgentTemplateCreateValidation:
    """Testa a validação Pydantic da request de criação."""

    VALID_YAML = "name: test\nprompt: |\n  You are a helpful test agent for enterprise candidate sourcing and hiring workflows.\n"

    def test_valid_create_request(self):
        from app.api.v1.agent_templates import AgentTemplateCreate
        req = AgentTemplateCreate(
            name="Test Agent",
            domain="sourcing",
            system_prompt_yaml=self.VALID_YAML,
        )
        assert req.name == "Test Agent"
        assert req.domain == "sourcing"

    def test_invalid_domain_rejected(self):
        from app.api.v1.agent_templates import AgentTemplateCreate
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            AgentTemplateCreate(
                name="Test Agent",
                domain="invalid_domain_xyz",
                system_prompt_yaml=self.VALID_YAML,
            )

    def test_name_too_short_rejected(self):
        from app.api.v1.agent_templates import AgentTemplateCreate
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            AgentTemplateCreate(
                name="AB",  # min_length=3
                domain="sourcing",
                system_prompt_yaml=self.VALID_YAML,
            )

    def test_yaml_without_prompt_field_rejected(self):
        from app.api.v1.agent_templates import AgentTemplateCreate
        from pydantic import ValidationError
        bad_yaml = "name: test\nversion: 1\n"  # No "prompt" field
        with pytest.raises(ValidationError):
            AgentTemplateCreate(
                name="Test Agent",
                domain="sourcing",
                system_prompt_yaml=bad_yaml,
            )

    def test_invalid_yaml_syntax_rejected(self):
        from app.api.v1.agent_templates import AgentTemplateCreate
        from pydantic import ValidationError
        bad_yaml = "name: test\n  bad: indent: here: \n  }: invalid"
        with pytest.raises(ValidationError):
            AgentTemplateCreate(
                name="Test Agent",
                domain="sourcing",
                system_prompt_yaml=bad_yaml,
            )


class TestAllowedDomains:
    """Testa que os domínios permitidos estão configurados."""

    def test_allowed_domains_has_sourcing(self):
        from app.api.v1.agent_templates import ALLOWED_DOMAINS
        assert "sourcing" in ALLOWED_DOMAINS

    def test_allowed_domains_has_pipeline(self):
        from app.api.v1.agent_templates import ALLOWED_DOMAINS
        assert "pipeline" in ALLOWED_DOMAINS

    def test_allowed_domains_has_wsi(self):
        from app.api.v1.agent_templates import ALLOWED_DOMAINS
        assert "wsi" in ALLOWED_DOMAINS

    def test_allowed_domains_has_lia_assistant(self):
        from app.api.v1.agent_templates import ALLOWED_DOMAINS
        assert "lia_assistant" in ALLOWED_DOMAINS

    def test_allowed_domains_has_at_least_5(self):
        from app.api.v1.agent_templates import ALLOWED_DOMAINS
        assert len(ALLOWED_DOMAINS) >= 5


class TestAgentTemplatesRouter:
    """Testa que o router tem as rotas esperadas."""

    def test_router_exists(self):
        from app.api.v1.agent_templates import router
        assert router is not None

    def test_router_has_list_route(self):
        from app.api.v1.agent_templates import router
        paths = [r.path for r in router.routes]
        assert "/agent-templates" in paths

    def test_router_has_create_route(self):
        from app.api.v1.agent_templates import router
        paths = [r.path for r in router.routes]
        assert "/agent-templates" in paths

    def test_router_has_detail_route(self):
        from app.api.v1.agent_templates import router
        paths = [r.path for r in router.routes]
        assert any("{id}" in p or "{template_id}" in p for p in paths)

    def test_router_has_publish_route(self):
        from app.api.v1.agent_templates import router
        paths = [r.path for r in router.routes]
        assert any("publish" in p for p in paths)

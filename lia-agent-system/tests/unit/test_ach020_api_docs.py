"""
ACH-020 — Documentação da API

Verifica:
1. FastAPI app tem metadata OpenAPI completo (título, versão, tags, contato, licença)
2. Tags estão definidas para os grupos críticos
3. docs/API_REFERENCE.md existe e tem seções mínimas
4. Intent router tem exemplos few-shot T3 (J2)
"""
import pathlib
import pytest


class TestOpenAPIMetadata:
    """Verifica metadata do FastAPI para OpenAPI/Swagger."""

    def _get_openapi(self):
        from app.main import app
        return app.openapi()

    def test_app_title_is_set(self):
        """FastAPI app deve ter título WeDOTalent."""
        meta = self._get_openapi()
        assert "WeDOTalent" in meta["info"]["title"]

    def test_app_version_is_set(self):
        """FastAPI app deve ter versão semântica."""
        meta = self._get_openapi()
        version = meta["info"]["version"]
        assert version and "." in version

    def test_app_has_contact(self):
        """FastAPI app deve ter informações de contato."""
        meta = self._get_openapi()
        contact = meta["info"].get("contact", {})
        assert contact.get("name") or contact.get("email")

    def test_app_has_license(self):
        """FastAPI app deve ter informação de licença."""
        meta = self._get_openapi()
        license_info = meta["info"].get("license", {})
        assert license_info.get("name")

    def test_app_has_openapi_tags(self):
        """FastAPI app deve ter tags OpenAPI definidas."""
        meta = self._get_openapi()
        tags = meta.get("tags", [])
        assert len(tags) >= 10, f"Expected >= 10 tags, got {len(tags)}"

    def test_critical_tags_present(self):
        """Tags críticas devem estar presentes."""
        meta = self._get_openapi()
        tag_names = {t["name"] for t in meta.get("tags", [])}
        required = {"agents", "candidates", "hitl", "guardrails", "compliance", "admin"}
        missing = required - tag_names
        assert not missing, f"Tags ausentes: {missing}"

    def test_agents_tag_has_description(self):
        """Tag 'agents' deve ter descrição."""
        meta = self._get_openapi()
        tags = {t["name"]: t for t in meta.get("tags", [])}
        assert "agents" in tags
        assert tags["agents"].get("description")

    def test_app_has_paths(self):
        """FastAPI app deve ter endpoints documentados."""
        meta = self._get_openapi()
        assert len(meta.get("paths", {})) >= 50, "Menos de 50 paths no OpenAPI — possível erro"


class TestAPIReferenceDoc:
    """Verifica que docs/API_REFERENCE.md existe e está completo."""

    def _read_doc(self) -> str:
        doc_path = pathlib.Path("docs/API_REFERENCE.md")
        assert doc_path.exists(), "docs/API_REFERENCE.md não encontrado"
        return doc_path.read_text()

    def test_api_reference_exists(self):
        """docs/API_REFERENCE.md deve existir."""
        assert pathlib.Path("docs/API_REFERENCE.md").exists()

    def test_api_reference_has_authentication_section(self):
        """API reference deve documentar autenticação."""
        src = self._read_doc()
        assert "Autenticação" in src or "Authentication" in src

    def test_api_reference_has_hitl_section(self):
        """API reference deve documentar HITL."""
        src = self._read_doc()
        assert "hitl" in src.lower() or "HITL" in src

    def test_api_reference_has_guardrails_section(self):
        """API reference deve documentar guardrails."""
        src = self._read_doc()
        assert "guardrail" in src.lower()

    def test_api_reference_has_rag_search_section(self):
        """API reference deve documentar RAG search."""
        src = self._read_doc()
        assert "rag-search" in src.lower() or "RAG" in src

    def test_api_reference_has_error_codes(self):
        """API reference deve documentar códigos de erro."""
        src = self._read_doc()
        assert "404" in src and "422" in src and "500" in src

    def test_api_reference_has_changelog(self):
        """API reference deve ter changelog."""
        src = self._read_doc()
        assert "Changelog" in src or "changelog" in src.lower()

    def test_api_reference_min_length(self):
        """API reference deve ter conteúdo substancial (> 3000 chars)."""
        src = self._read_doc()
        assert len(src) >= 3000, f"API reference muito curto: {len(src)} chars"


class TestCascadedRouterDomainMapping:
    """Verifica mapeamento de domínios no CascadedRouter (substitui IntentRouter)."""

    def test_agent_type_to_domain_has_core_mappings(self):
        """AGENT_TYPE_TO_DOMAIN deve mapear os tipos de agente fundamentais."""
        from app.orchestrator.cascaded_router import AGENT_TYPE_TO_DOMAIN
        assert "job_planner" in AGENT_TYPE_TO_DOMAIN
        assert "sourcing" in AGENT_TYPE_TO_DOMAIN
        assert "cv_screening" in AGENT_TYPE_TO_DOMAIN
        assert "scheduling" in AGENT_TYPE_TO_DOMAIN
        assert "analytics" in AGENT_TYPE_TO_DOMAIN

    def test_fast_router_has_domain_patterns(self):
        """FastRouter DOMAIN_PATTERNS deve cobrir domínios-chave."""
        from app.orchestrator.fast_router import DOMAIN_PATTERNS
        assert "job_management" in DOMAIN_PATTERNS
        assert "sourcing" in DOMAIN_PATTERNS
        assert "cv_screening" in DOMAIN_PATTERNS
        assert "analytics" in DOMAIN_PATTERNS

    def test_cascaded_router_no_intent_router_param(self):
        """CascadedRouter não deve aceitar intent_router."""
        from app.orchestrator.cascaded_router import CascadedRouter
        import inspect
        sig = inspect.signature(CascadedRouter.__init__)
        assert "intent_router" not in sig.parameters

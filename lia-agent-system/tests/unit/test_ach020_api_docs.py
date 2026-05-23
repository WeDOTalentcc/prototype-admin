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
    """Verifica mapeamento de domínios centralizado em domain_mappings.py."""

    def test_agent_type_to_domain_has_core_mappings(self):
        """AGENT_TYPE_TO_DOMAIN deve mapear os tipos de agente fundamentais."""
        from app.orchestrator.routing.domain_mappings import AGENT_TYPE_TO_DOMAIN
        assert "job_planner" in AGENT_TYPE_TO_DOMAIN
        assert "sourcing" in AGENT_TYPE_TO_DOMAIN
        assert "cv_screening" in AGENT_TYPE_TO_DOMAIN
        assert "scheduling" in AGENT_TYPE_TO_DOMAIN
        assert "analytics" in AGENT_TYPE_TO_DOMAIN

    def test_resolve_domain_known_intent(self):
        """resolve_domain() deve resolver intents conhecidos corretamente."""
        from app.orchestrator.routing.domain_mappings import resolve_domain
        assert resolve_domain("job_planner") == "job_management"
        assert resolve_domain("sourcing") == "sourcing"
        assert resolve_domain("cv_screening") == "cv_screening"
        assert resolve_domain("scheduling") == "interview_scheduling"

    def test_resolve_domain_unknown_falls_back(self):
        """resolve_domain() deve retornar recruiter_assistant para intents desconhecidos."""
        from app.orchestrator.routing.domain_mappings import resolve_domain
        assert resolve_domain("completely_unknown_xyz") == "recruiter_assistant"

    def test_fast_router_has_domain_patterns(self):
        """FastRouter DOMAIN_PATTERNS deve cobrir domínios-chave."""
        from app.orchestrator.routing.fast_router import DOMAIN_PATTERNS
        assert "job_management" in DOMAIN_PATTERNS
        assert "sourcing" in DOMAIN_PATTERNS
        assert "cv_screening" in DOMAIN_PATTERNS
        assert "analytics" in DOMAIN_PATTERNS

    def test_cascaded_router_uses_centralized_mappings(self):
        """CascadedRouter deve importar AGENT_TYPE_TO_DOMAIN de domain_mappings."""
        from app.orchestrator.routing.cascaded_router import CascadedRouter
        from app.orchestrator.routing.fast_router import FastRouter
        router = CascadedRouter(fast_router=FastRouter())
        assert router._intent_to_domain("sourcing") == "sourcing"
        assert router._intent_to_domain("job_planner") == "job_management"

    def test_cascaded_router_no_intent_router_param(self):
        """CascadedRouter não deve aceitar intent_router."""
        from app.orchestrator.routing.cascaded_router import CascadedRouter
        import inspect
        sig = inspect.signature(CascadedRouter.__init__)
        assert "intent_router" not in sig.parameters


class TestDomainCatalogClassification:
    """Verifica que stubs e service domains estão marcados corretamente."""

    def test_repository_stubs_have_marker(self):
        """Todos os repository stubs devem ter __domain_type__ = 'repository_stub'."""
        import importlib
        stubs = [
            "admin", "admin_settings", "agent_memory", "approvals", "auth",
            "bulk_actions", "candidate_lists", "chat", "clients", "client_users",
            "company_culture", "compliance", "consent", "data_subject",
            "email_templates", "goals", "health_check", "job_vacancies_analytics",
            "journey_mapping", "notifications", "observability", "opinions",
            "recruitment_journey", "saas_metrics", "shared_searches", "tasks",
            "technical_tests", "triagem", "trust_center", "workforce",
        ]
        for stub in stubs:
            mod = importlib.import_module(f"app.domains.{stub}")
            assert getattr(mod, "__domain_type__", None) == "repository_stub", (
                f"app.domains.{stub} missing __domain_type__ = 'repository_stub'"
            )

    def test_service_domains_have_marker(self):
        """Service domains devem ter __domain_type__ = 'service'."""
        import importlib
        services = ["ai", "billing", "candidates", "company", "credits",
                     "integrations_hub", "lgpd", "recruitment", "voice"]
        for svc in services:
            mod = importlib.import_module(f"app.domains.{svc}")
            assert getattr(mod, "__domain_type__", None) == "service", (
                f"app.domains.{svc} missing __domain_type__ = 'service'"
            )

    def test_deprecated_domains_have_marker(self):
        """Deprecated domains devem ter __domain_type__ = 'deprecated'."""
        import importlib
        for dep in ["autonomous", "policy"]:
            mod = importlib.import_module(f"app.domains.{dep}")
            assert getattr(mod, "__domain_type__", None) == "deprecated", (
                f"app.domains.{dep} missing __domain_type__ = 'deprecated'"
            )

    def test_domain_registry_only_has_agentic_domains(self):
        """DomainRegistry deve conter apenas domínios agentic (com @register_domain)."""
        import app.domains  # noqa: F401 — triggers @register_domain side effects
        from app.domains.registry import DomainRegistry
        registry = DomainRegistry()
        registered = set(registry.list_domains())
        agentic_ids = {
            "agent_studio", "analytics", "ats_integration", "automation",
            "candidate_self_service", "communication", "company_settings",
            "cv_screening", "digital_twin", "hiring_policy",
            "interview_scheduling", "job_creation", "job_management",
            "offer", "pipeline_transition", "recruiter_assistant",
            "recruitment_campaign", "sourcing", "talent_pool",
        }
        for domain_id in registered:
            assert domain_id in agentic_ids, (
                f"Non-agentic domain '{domain_id}' found in DomainRegistry"
            )
        required_core = {
            "analytics", "automation", "communication", "cv_screening",
            "job_management", "recruiter_assistant", "sourcing", "pipeline_transition",
        }
        missing = required_core - registered
        assert not missing, f"Core agentic domains missing from registry: {missing}"

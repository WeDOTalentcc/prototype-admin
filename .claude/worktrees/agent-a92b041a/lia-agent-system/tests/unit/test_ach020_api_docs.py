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


class TestIntentRouterFewShot:
    """Verifica exemplos few-shot J2 no intent router (T3 RH sênior)."""

    def _get_prompt(self) -> str:
        from app.orchestrator.intent_router import IntentRouter
        import inspect
        return inspect.getsource(IntentRouter._create_intent_prompt)

    def test_few_shot_section_exists(self):
        """Intent router deve ter seção EXEMPLOS FEW-SHOT."""
        from app.orchestrator.intent_router import IntentRouter
        router = IntentRouter.__new__(IntentRouter)
        # Verificar diretamente no source da função
        import inspect
        src = inspect.getsource(IntentRouter._create_intent_prompt)
        assert "FEW-SHOT" in src or "few-shot" in src.lower()

    def test_has_clear_examples(self):
        """Intent router deve ter exemplos claros (alta confiança)."""
        src = self._get_prompt()
        assert "0.9" in src or "confidence" in src.lower()

    def test_has_ambiguous_examples(self):
        """Intent router deve ter exemplos ambíguos."""
        src = self._get_prompt()
        assert "Ambíg" in src or "ambíg" in src or "Ambiguous" in src

    def test_has_minimum_20_examples(self):
        """Intent router deve ter pelo menos 20 exemplos few-shot."""
        src = self._get_prompt()
        # Conta blocos Input/Output
        input_count = src.count('Input: "')
        assert input_count >= 20, f"Esperado >= 20 exemplos, encontrado {input_count}"

    def test_hr_senior_context_present(self):
        """Exemplos devem ter contexto de RH sênior."""
        src = self._get_prompt()
        assert "RH" in src or "recrutador" in src.lower() or "sênior" in src.lower()

    def test_job_planner_example_present(self):
        """Deve ter exemplo para job_planner."""
        src = self._get_prompt()
        assert '"job_planner"' in src

    def test_sourcing_example_present(self):
        """Deve ter exemplo para sourcing."""
        src = self._get_prompt()
        assert '"sourcing"' in src

    def test_cv_screening_example_present(self):
        """Deve ter exemplo para cv_screening."""
        src = self._get_prompt()
        assert '"cv_screening"' in src or '"rank_candidates"' in src

    def test_analyst_example_present(self):
        """Deve ter exemplo para analyst/funnel."""
        src = self._get_prompt()
        assert '"funnel_analysis"' in src or '"analyst_feedback"' in src

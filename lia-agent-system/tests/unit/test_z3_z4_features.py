"""
Tests para Z3-01, Z3-02, Z3-03, Z4-01, Z4-02.

Z3-01: Fairness report export endpoint (CSV/JSON)
Z3-02: Prompt version loader — validation
Z3-03: Cost alerts per tenant (TenantBudget notification)
Z4-01: DeepEval test files exist
Z4-02: LongTermMemory TTL + compression methods
"""
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch


# ─── Z3-01: Fairness Report Export ─────────────────────────────────────────

class TestFairnessReportExport:
    def test_export_router_has_export_endpoint(self):
        from app.api.v1.fairness_reports import router
        routes = {r.path for r in router.routes}
        assert any("export" in path for path in routes)

    def test_export_format_csv_defined(self):
        """Verifica que o endpoint aceita formato CSV."""
        import inspect
        from app.api.v1 import fairness_reports
        src = inspect.getsource(fairness_reports)
        assert "text/csv" in src
        assert "StreamingResponse" in src

    def test_export_format_json_defined(self):
        """Verifica que o endpoint aceita formato JSON."""
        import inspect
        from app.api.v1 import fairness_reports
        src = inspect.getsource(fairness_reports)
        assert "JSONResponse" in src

    def test_fe_proxy_exists(self):
        proxy_path = Path(
            "/home/runner/workspace/plataforma-lia/src/app/api/backend-proxy"
            "/fairness-report/export/route.ts"
        )
        assert proxy_path.exists(), "FE proxy fairness-report/export/route.ts não encontrado"


# ─── Z3-02: Prompt Version Loader ────────────────────────────────────────────

class TestPromptVersionLoader:
    def test_load_sourcing_yaml(self, tmp_path):
        from app.core.prompt_version_loader import load_prompt_yaml
        yaml_content = """
metadata:
  domain: "sourcing"
  version: "2.0"
  updated_at: "2026-03-19"
system_prompt: |
  Você é LIA.
"""
        f = tmp_path / "test.yaml"
        f.write_text(yaml_content)
        data = load_prompt_yaml(f)
        assert data["metadata"]["domain"] == "sourcing"
        assert data["metadata"]["version"] == "2.0"

    def test_validate_valid_prompt(self, tmp_path):
        from app.core.prompt_version_loader import validate_prompt_metadata, load_prompt_yaml
        yaml_content = """
metadata:
  domain: "sourcing"
  version: "2.0"
system_prompt: |
  Test prompt.
"""
        f = tmp_path / "test.yaml"
        f.write_text(yaml_content)
        data = load_prompt_yaml(f)
        errors = validate_prompt_metadata(data, "test.yaml")
        assert errors == []

    def test_validate_missing_version_errors(self, tmp_path):
        from app.core.prompt_version_loader import validate_prompt_metadata
        data = {"metadata": {"domain": "sourcing"}, "system_prompt": "Test"}
        errors = validate_prompt_metadata(data, "test.yaml")
        assert any("version" in e for e in errors)

    def test_validate_missing_system_prompt_errors(self, tmp_path):
        from app.core.prompt_version_loader import validate_prompt_metadata
        data = {"metadata": {"domain": "sourcing", "version": "1.0"}}
        errors = validate_prompt_metadata(data, "test.yaml")
        assert any("system_prompt" in e for e in errors)

    def test_legacy_flat_format_accepted(self):
        """Formato legado (pipeline_transition.yaml) sem metadata block."""
        from app.core.prompt_version_loader import validate_prompt_metadata
        data = {
            "domain": "pipeline_transition",
            "version": "1.0.0",
            "system_prompt": "Você é LIA.",
        }
        errors = validate_prompt_metadata(data, "pipeline_transition.yaml")
        assert errors == [], f"Formato legado deve ser aceito, mas: {errors}"

    def test_validate_all_prompts_clean(self):
        """Todos os prompts existentes devem passar na validação."""
        from app.core.prompt_version_loader import validate_all_prompts
        issues = validate_all_prompts()
        assert issues == {}, f"Prompts com erros: {issues}"

    def test_list_all_prompt_versions_returns_results(self):
        from app.core.prompt_version_loader import list_all_prompt_versions
        versions = list_all_prompt_versions()
        assert len(versions) >= 1

    def test_sourcing_has_updated_at(self):
        from app.core.prompt_version_loader import list_all_prompt_versions
        versions = {v.domain: v for v in list_all_prompt_versions()}
        sourcing = versions.get("sourcing")
        assert sourcing is not None
        assert sourcing.updated_at == "2026-03-19"


# ─── Z3-03: Cost Alerts ──────────────────────────────────────────────────────

class TestTenantBudgetCostAlerts:
    def test_send_budget_alert_method_exists(self):
        from app.orchestrator.guards.tenant_budget import TenantBudget
        budget = TenantBudget()
        assert hasattr(budget, "_send_budget_alert")

    @pytest.mark.asyncio
    async def test_send_budget_alert_fail_safe(self):
        """_send_budget_alert deve ser fail-safe mesmo sem notification_service."""
        from app.orchestrator.guards.tenant_budget import TenantBudget
        budget = TenantBudget()
        # Should not raise even when notification_service is unavailable
        await budget._send_budget_alert("test_company", "Alerta: 80% consumido", 0.80)

    @pytest.mark.asyncio
    async def test_check_and_record_calls_alert_on_threshold(self):
        """check_and_record deve disparar alerta quando ratio >= threshold."""
        from app.orchestrator.guards.tenant_budget import TenantBudget

        budget = TenantBudget(monthly_limit=100)
        budget._alert_threshold = 0.80

        # Mock record_usage to return 85 (85% of 100)
        budget.record_usage = AsyncMock(return_value=85)
        budget._send_budget_alert = AsyncMock()

        allowed, total, warning = await budget.check_and_record("company_abc", 5)

        assert warning is not None
        budget._send_budget_alert.assert_called_once()
        args = budget._send_budget_alert.call_args
        assert "company_abc" in args[0]


# ─── Z4-01: DeepEval CI Files ────────────────────────────────────────────────

class TestDeepEvalCISetup:
    def test_deepeval_test_file_exists(self):
        p = Path("/home/runner/workspace/lia-agent-system/tests/deepeval/test_agent_quality.py")
        assert p.exists(), "DeepEval test file não encontrado"

    def test_deepeval_init_exists(self):
        p = Path("/home/runner/workspace/lia-agent-system/tests/deepeval/__init__.py")
        assert p.exists(), "tests/deepeval/__init__.py não encontrado"

    def test_ci_yml_has_deepeval_job(self):
        ci_path = Path("/home/runner/workspace/lia-agent-system/.github/workflows/ci.yml")
        content = ci_path.read_text()
        assert "deepeval" in content.lower()
        assert "DeepEval" in content

    def test_deepeval_test_has_three_metrics(self):
        p = Path("/home/runner/workspace/lia-agent-system/tests/deepeval/test_agent_quality.py")
        content = p.read_text()
        assert "HallucinationMetric" in content
        assert "FaithfulnessMetric" in content
        assert "BiasMetric" in content


# ─── Z4-02: LongTermMemory TTL + Compression ─────────────────────────────────

class TestLongTermMemoryCompression:
    def test_compress_method_exists(self):
        from lia_agents_core.long_term_memory import LongTermMemoryService
        service = LongTermMemoryService()
        assert hasattr(service, "compress_old_episodes")

    def test_purge_method_exists(self):
        from lia_agents_core.long_term_memory import LongTermMemoryService
        service = LongTermMemoryService()
        assert hasattr(service, "purge_expired")

    def test_celery_task_registered(self):
        """Verifica que memory.compress_old_episodes está registrado no Celery."""
        import inspect
        import app.jobs.celery_tasks as ct
        src = inspect.getsource(ct)
        assert "memory.compress_old_episodes" in src or "memory_compress" in src

    def test_beat_schedule_has_memory_compress(self):
        """Verifica que o beat schedule inclui compressão de memória."""
        try:
            import inspect
            from lia_config import celery_app as ca
            src = inspect.getsource(ca)
            assert "memory" in src.lower() and "compress" in src.lower()
        except Exception:
            # If lia_config not importable in test env, check the file directly
            celery_path = Path(
                "/home/runner/workspace/lia-agent-system/libs/config/lia_config/celery_app.py"
            )
            content = celery_path.read_text()
            assert "memory" in content.lower()


# ─── Z2-03: Sourcing APIs Catalog ─────────────────────────────────────────────

class TestSourcingAPICatalog:
    def test_catalog_file_exists(self):
        p = Path(
            "/home/runner/workspace/lia-agent-system/docs/integrations/apis/sourcing"
            "/sourcing_apis_catalog.yaml"
        )
        assert p.exists(), "Sourcing APIs catalog YAML não encontrado"

    def test_catalog_has_pearch_entry(self):
        import yaml
        p = Path(
            "/home/runner/workspace/lia-agent-system/docs/integrations/apis/sourcing"
            "/sourcing_apis_catalog.yaml"
        )
        data = yaml.safe_load(p.read_text())
        assert "pearch_ai" in data.get("apis", {})

    def test_catalog_has_subagent_mapping(self):
        import yaml
        p = Path(
            "/home/runner/workspace/lia-agent-system/docs/integrations/apis/sourcing"
            "/sourcing_apis_catalog.yaml"
        )
        data = yaml.safe_load(p.read_text())
        mapping = data.get("subagent_api_mapping", {})
        for agent in ("sourcing_planner", "sourcing_search", "sourcing_enrich", "sourcing_engagement"):
            assert agent in mapping, f"{agent} missing from subagent_api_mapping"

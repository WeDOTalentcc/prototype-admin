"""Testes Sprint III — Arquitetura de IA."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestTenantContextService:
    def test_module_importable(self):
        from app.shared.services.tenant_context_service import TenantContextService, TenantContext
        assert TenantContextService is not None
        assert TenantContext is not None

    def test_tenant_context_to_prompt_snippet(self):
        from app.shared.services.tenant_context_service import TenantContext
        ctx = TenantContext(
            company_id="c1", company_name="Acme", sector="tech",
            open_vacancies=5, autonomy_level="high", plan="pro"
        )
        snippet = ctx.to_prompt_snippet()
        assert "Acme" in snippet
        assert "tech" in snippet
        assert "5" in snippet

    @pytest.mark.asyncio
    async def test_get_context_fallback_on_error(self):
        from app.shared.services.tenant_context_service import TenantContextService
        svc = TenantContextService()
        mock_db = AsyncMock()
        mock_db.execute.side_effect = Exception("DB error")
        ctx = await svc.get_context("company-123", mock_db)
        assert ctx.company_id == "company-123"
        assert ctx.company_name == "sua empresa"


class TestDynamicAlphaRAG:
    def test_tech_keywords_low_alpha(self):
        try:
            from app.domains.ai.services.rag_pipeline_service import RAGPipelineService
            svc = RAGPipelineService.__new__(RAGPipelineService)
            alpha = svc._detect_query_type("desenvolvedor python sênior")
            assert alpha <= 0.4
        except (ImportError, AttributeError):
            pytest.skip("RAG service não tem _detect_query_type ainda")

    def test_behavioral_keywords_high_alpha(self):
        try:
            from app.domains.ai.services.rag_pipeline_service import RAGPipelineService
            svc = RAGPipelineService.__new__(RAGPipelineService)
            alpha = svc._detect_query_type("perfil com liderança e comunicação")
            assert alpha >= 0.6
        except (ImportError, AttributeError):
            pytest.skip("RAG service não tem _detect_query_type ainda")

    def test_default_alpha_balanced(self):
        from app.domains.ai.services.rag_pipeline_service import RAGPipelineService
        svc = RAGPipelineService.__new__(RAGPipelineService)
        alpha = svc._detect_query_type("candidato para a vaga")
        assert alpha == 0.5

    def test_cargo_keywords_low_alpha(self):
        from app.domains.ai.services.rag_pipeline_service import RAGPipelineService
        svc = RAGPipelineService.__new__(RAGPipelineService)
        alpha = svc._detect_query_type("gerente de projetos experiente")
        assert alpha <= 0.4

    def test_tech_stack_low_alpha(self):
        from app.domains.ai.services.rag_pipeline_service import RAGPipelineService
        svc = RAGPipelineService.__new__(RAGPipelineService)
        alpha = svc._detect_query_type("fullstack react e node")
        assert alpha <= 0.4


class TestPolicyEngineAlpha1Rules:
    def test_alpha1_rules_all_sectors_present(self):
        try:
            from app.domains.policy.services.policy_engine_service import ALPHA1_SECTOR_RULES
            expected_sectors = {"tech", "varejo", "logistica", "financeiro", "saude", "rpo"}
            assert expected_sectors.issubset(set(ALPHA1_SECTOR_RULES.keys()))
        except ImportError:
            pytest.skip("ALPHA1_SECTOR_RULES não encontrado")

    def test_all_rules_have_required_fields(self):
        try:
            from app.domains.policy.services.policy_engine_service import ALPHA1_SECTOR_RULES
            # hitl_threshold e auto_approve_threshold movidos para fairness_policy_rules (Regra 9)
            required_fields = {"autonomy_level", "fairness_layer3_enabled"}
            for sector, rules in ALPHA1_SECTOR_RULES.items():
                for field in required_fields:
                    assert field in rules, f"Setor {sector} sem campo {field}"
        except ImportError:
            pytest.skip("ALPHA1_SECTOR_RULES não encontrado")

    def test_financeiro_low_autonomy(self):
        from app.domains.policy.services.policy_engine_service import ALPHA1_SECTOR_RULES
        assert ALPHA1_SECTOR_RULES["financeiro"]["autonomy_level"] == "low"
        assert ALPHA1_SECTOR_RULES["financeiro"]["fairness_layer3_enabled"] is True

    def test_tech_high_autonomy(self):
        from app.domains.policy.services.policy_engine_service import ALPHA1_SECTOR_RULES
        assert ALPHA1_SECTOR_RULES["tech"]["autonomy_level"] == "high"

    def test_saude_strict_thresholds_in_db_seed(self):
        """Thresholds de saude agora vivem em fairness_policy_rules (Regra 9 do seed)."""
        from lia_models.fairness_policies import DEFAULT_PLATFORM_GENERAL_RULES
        sector_rule = next(
            (r for r in DEFAULT_PLATFORM_GENERAL_RULES
             if r["rule_type"] == "decision_threshold"
             and "sectors" in r.get("body_json", {})),
            None,
        )
        assert sector_rule is not None, "Regra 9 (decision_threshold por setor) nao encontrada no seed"
        saude_cfg = sector_rule["body_json"]["sectors"]["saude"]
        assert saude_cfg["auto_approve_threshold"] >= 0.90
        assert saude_cfg["hitl_threshold"] >= 0.80

    def test_rpo_high_autonomy(self):
        from app.domains.policy.services.policy_engine_service import ALPHA1_SECTOR_RULES
        assert ALPHA1_SECTOR_RULES["rpo"]["autonomy_level"] == "high"
        assert ALPHA1_SECTOR_RULES["rpo"]["fairness_layer3_enabled"] is True


class TestLearningLoopDriftConnection:
    def test_learning_loop_importable(self):
        from app.shared.learning.learning_loop_service import LearningLoopService, FeedbackOutcome
        assert LearningLoopService is not None
        assert FeedbackOutcome.REJECTED is not None

    def test_feedback_outcome_values(self):
        from app.shared.learning.learning_loop_service import FeedbackOutcome
        assert hasattr(FeedbackOutcome, "ACCEPTED")
        assert hasattr(FeedbackOutcome, "REJECTED")
        assert hasattr(FeedbackOutcome, "MODIFIED")

    def test_feedback_outcome_ignored(self):
        from app.shared.learning.learning_loop_service import FeedbackOutcome
        assert hasattr(FeedbackOutcome, "IGNORED")


class TestModelDriftCheckTrigger:
    def test_model_drift_service_has_check_trigger(self):
        from app.shared.services.model_drift_service import ModelDriftService
        svc = ModelDriftService()
        assert hasattr(svc, "check_drift_trigger")
        assert callable(svc.check_drift_trigger)

    @pytest.mark.asyncio
    async def test_check_drift_trigger_invalid_company_id(self):
        """check_drift_trigger não deve propagar exceções para IDs inválidos."""
        from app.shared.services.model_drift_service import ModelDriftService
        svc = ModelDriftService()
        # ID inválido — deve falhar silenciosamente
        await svc.check_drift_trigger("not-a-valid-uuid", "learning_feedback")


class TestTenantContextServicePromptSnippet:
    def test_snippet_contains_all_fields(self):
        from app.shared.services.tenant_context_service import TenantContext
        ctx = TenantContext(
            company_id="x", company_name="TechCorp", sector="financeiro",
            open_vacancies=12, autonomy_level="low", plan="enterprise"
        )
        snippet = ctx.to_prompt_snippet()
        assert "TechCorp" in snippet
        assert "financeiro" in snippet
        assert "12" in snippet
        assert "low" in snippet
        assert "enterprise" in snippet

    def test_snippet_zero_vacancies(self):
        from app.shared.services.tenant_context_service import TenantContext
        ctx = TenantContext(
            company_id="x", company_name="Startup", sector="tech",
            open_vacancies=0, autonomy_level="medium", plan="starter"
        )
        snippet = ctx.to_prompt_snippet()
        assert "0" in snippet

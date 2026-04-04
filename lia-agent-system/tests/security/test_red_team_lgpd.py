"""
Red Teaming — Categoria 6: LGPD e Compliance

Verifica enforcement de direitos dos titulares de dados e
conformidade com as obrigações da LGPD.

ACH-028
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch


class TestConsentEnforcement:
    """Verifica que consentimento é respeitado em pontos críticos."""

    def test_wsi_interview_checks_lgpd_consent(self):
        """WSI load_context deve verificar consentimento LGPD."""
        import inspect
        from app.domains.cv_screening.agents.wsi_interview_graph import WSIInterviewNodes
        src = inspect.getsource(WSIInterviewNodes.load_context)
        assert "consent" in src.lower() or "lgpd" in src.lower()

    def test_dsr_endpoint_exists(self):
        """Endpoint de DSR (Data Subject Rights) deve existir."""
        import app.api.v1.data_subject_requests as mod
        assert hasattr(mod, "router")

    def test_dsr_has_deletion_support(self):
        """DSR deve suportar solicitação de exclusão."""
        import inspect
        import app.api.v1.data_subject_requests as mod
        src = inspect.getsource(mod)
        assert "delet" in src.lower() or "exclusa" in src.lower() or "removal" in src.lower()

    def test_dsr_sla_deadline_present(self):
        """DSR deve ter cálculo de SLA (LGPD: 15 dias)."""
        import inspect
        import app.api.v1.data_subject_requests as mod
        src = inspect.getsource(mod)
        assert "sla" in src.lower() or "deadline" in src.lower() or "15" in src


class TestDataRetentionLGPD:
    """Testa que retenção de dados está configurada."""

    def test_lgpd_cleanup_task_registered(self):
        """Task de cleanup LGPD deve estar no beat_schedule."""
        from libs.config.lia_config.celery_app import celery_app
        schedules = celery_app.conf.beat_schedule
        assert "lgpd-cleanup-daily" in schedules

    def test_lgpd_cleanup_task_name(self):
        """Task LGPD deve ser 'lgpd.run_cleanup_daily'."""
        from libs.config.lia_config.celery_app import celery_app
        entry = celery_app.conf.beat_schedule["lgpd-cleanup-daily"]
        assert entry["task"] == "lgpd.run_cleanup_daily"

    def test_lgpd_admin_endpoint_exists(self):
        """Endpoint admin para LGPD deve existir."""
        import app.api.v1.admin_lgpd as mod
        assert hasattr(mod, "router")

    def test_lgpd_retention_policy_present(self):
        """Política de retenção deve estar implementada."""
        import inspect
        import app.api.v1.admin_lgpd as mod
        src = inspect.getsource(mod)
        assert "retention" in src.lower() or "retencao" in src.lower() or "cleanup" in src.lower()


class TestAuditTrailIntegrity:
    """Testa integridade e completude do audit trail."""

    def test_audit_service_log_decision_exists(self):
        """audit_service.log_decision deve existir."""
        from app.shared.compliance.audit_service import audit_service
        assert hasattr(audit_service, "log_decision")
        assert callable(audit_service.log_decision)

    def test_audit_service_accepts_criteria_ignored(self):
        """audit_service.log_decision deve aceitar criteria_ignored para LGPD."""
        import inspect
        from app.shared.compliance import audit_service as mod
        src = inspect.getsource(mod)
        assert "criteria_ignored" in src

    def test_wsi_generates_audit_on_final_decision(self):
        """WSI generate_feedback (WSIInterviewNodes) deve gerar audit para decisão final."""
        import inspect
        from app.domains.cv_screening.agents.wsi_interview_graph import WSIInterviewNodes
        src = inspect.getsource(WSIInterviewNodes.generate_feedback)
        assert "audit_service" in src
        assert "log_decision" in src

    def test_interview_graph_generates_audit_langgraph_path(self):
        """interview_graph LangGraph path deve gerar audit trail."""
        import inspect
        from app.domains.interview_scheduling.agents.interview_graph import InterviewGraph
        src = inspect.getsource(InterviewGraph._invoke_langgraph)
        assert "audit_service" in src
        assert "log_decision" in src

    def test_sourcing_generates_audit_on_score(self):
        """sourcing_react_agent deve gerar audit ao score candidatos."""
        import inspect
        from app.domains.sourcing.agents.sourcing_react_agent import SourcingReActAgent
        src = inspect.getsource(SourcingReActAgent._process_langgraph)
        assert "audit_service" in src

    def test_pipeline_generates_audit_on_transition(self):
        """pipeline_transition_agent deve gerar audit em transições."""
        import inspect
        from app.domains.pipeline.agents.pipeline_transition_agent import PipelineTransitionAgent
        src = inspect.getsource(PipelineTransitionAgent.process)
        assert "audit_service" in src or "log_decision" in src

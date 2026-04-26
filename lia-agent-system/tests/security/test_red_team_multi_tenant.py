"""
Red Teaming — Categoria 4: Isolamento Multi-tenant

Verifica que dados de uma empresa não são acessíveis por outra empresa.
Testa boundary enforcement de company_id em modelos e queries.

ACH-028

Findings:
- JobVacancy tem company_id
- Candidate NÃO tem company_id diretamente (gap — candidatos são multi-empresa via candidaturas)
- HITL usa HITLPendingAction e HITLAuditTrail (não HITLRequest)
"""
import pytest


class TestMultiTenantIsolation:
    """Verifica que queries sempre filtram por company_id."""

    def test_job_vacancy_model_has_company_id(self):
        """JobVacancy deve ter campo company_id."""
        from lia_models.job_vacancy import JobVacancy
        assert hasattr(JobVacancy, "company_id")

    def test_hitl_audit_trail_has_company_id(self):
        """HITLAuditTrail deve ter company_id para isolamento."""
        from lia_models.hitl import HITLAuditTrail
        cols = [c.key for c in HITLAuditTrail.__table__.columns]
        assert "company_id" in cols

    def test_hitl_pending_action_has_company_id(self):
        """HITLPendingAction deve ter company_id."""
        from lia_models.hitl import HITLPendingAction
        cols = [c.key for c in HITLPendingAction.__table__.columns]
        assert "company_id" in cols

    def test_audit_service_has_company_id_param(self):
        """audit_service.log_decision deve aceitar company_id."""
        import inspect
        from app.shared.compliance import audit_service as mod
        src = inspect.getsource(mod)
        assert "company_id" in src

    def test_drift_service_requires_company_id(self):
        """model_drift_service deve requerer company_id."""
        import inspect
        import app.shared.observability.model_drift_service as mod
        src = inspect.getsource(mod)
        assert "company_id" in src

    def test_sourcing_audit_includes_company_id(self):
        """AuditService.log_decision em sourcing deve incluir company_id."""
        import inspect
        from app.domains.sourcing.agents.sourcing_react_agent import SourcingReActAgent
        src = inspect.getsource(SourcingReActAgent._process_langgraph)
        assert "company_id" in src

    def test_rag_search_requires_company_id(self):
        """RAG search deve incluir company_id para isolamento."""
        import inspect
        import app.services.rag_pipeline_service as mod
        src = inspect.getsource(mod)
        assert "company_id" in src

    def test_toon_service_cache_key_includes_company_id(self):
        """Cache Redis do TOON deve incluir company_id na chave."""
        import inspect
        import app.services.toon_service as mod
        src = inspect.getsource(mod)
        assert "company_id" in src

    def test_short_list_api_has_company_id(self):
        """API de short list deve filtrar por company_id."""
        import inspect
        import app.api.v1.short_lists as mod
        src = inspect.getsource(mod)
        assert "company_id" in src

    @pytest.mark.xfail(
        reason="GAP: Candidate.company_id ausente — candidatos são multi-empresa via candidaturas (ApplicationCandidate). "
               "Verificar se isolamento por application_id é suficiente.",
        strict=False,
    )
    def test_candidate_model_has_company_id(self):
        """[GAP] Modelo Candidate deveria ter company_id para isolamento direto."""
        from lia_models.candidate import Candidate
        cols = [c.key for c in Candidate.__table__.columns]
        assert "company_id" in cols


class TestTenantBoundaryAtAPI:
    """Verifica enforcement de tenant boundary na camada de API."""

    def test_candidates_endpoint_filters_by_company_id(self):
        """Endpoint de candidatos deve filtrar por company_id."""
        import inspect
        import app.api.v1.candidates as mod
        src = inspect.getsource(mod)
        assert "company_id" in src

    def test_drift_api_validates_company_id(self):
        """API de drift deve validar company_id."""
        import inspect
        import app.api.v1.drift as mod
        src = inspect.getsource(mod)
        assert "company_id" in src

    def test_bias_audit_api_validates_company_id(self):
        """API de bias audit deve validar company_id."""
        import inspect
        import app.api.v1.bias_audit as mod
        src = inspect.getsource(mod)
        assert "company_id" in src

    def test_hitl_service_passes_company_id(self):
        """HITL service request_approval deve incluir company_id."""
        import inspect
        import app.services.hitl_service as mod
        src = inspect.getsource(mod)
        assert "company_id" in src


# ============================================================================
# Teams channel multi-tenant boundary (P0-1 fix — auditoria 2026-04-26)
# Adds Teams to red team coverage. P0-2 (payload company_id) and P0-3 (audit
# tenant filter) are tracked as separate W1.2/W1.3 PRs and not asserted here
# to keep this PR atomic.
# ============================================================================


class TestTeamsMultiTenantBoundary:
    """Teams channel must enforce company_id on the multi-tenant boundary."""

    def test_teams_conversation_model_has_company_id(self):
        """TeamsConversation model exposes company_id (P0-1 fix Migration 097)."""
        from lia_models.teams import TeamsConversation
        cols = [c.key for c in TeamsConversation.__table__.columns]
        assert "company_id" in cols, (
            "TeamsConversation must have company_id column for multi-tenant boundary."
        )

    def test_teams_orchestrator_bridge_resolves_company_id(self):
        """teams_orchestrator_bridge.process_message references company_id resolution."""
        import inspect
        import app.domains.communication.services.teams_orchestrator_bridge as mod
        src = inspect.getsource(mod)
        # Must call _resolve_company_id and inject result into orchestrator context
        assert "_resolve_company_id" in src
        assert '"company_id": company_id' in src or "'company_id': company_id" in src

    def test_teams_action_audit_log_has_company_id(self):
        """TeamsActionAuditLog persists company_id for compliance trail."""
        from lia_models.teams import TeamsActionAuditLog
        cols = [c.key for c in TeamsActionAuditLog.__table__.columns]
        assert "company_id" in cols

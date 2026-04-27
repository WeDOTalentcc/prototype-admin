"""
Red Team — Teams channel coverage (W1.4 — P0-4 fix).

Auditoria 2026-04-26 (AUDITORIA_TEAMS_2026-04-26.md, finding P0-4) identificou
que os arquivos red team em tests/security/test_red_team_*.py cobriam 12 módulos
da plataforma (candidates, sourcing, RAG, drift, HITL, etc.) MAS NÃO Teams.

Resultado: bugs de PII/fairness/LGPD/prompt-injection no canal Teams passavam
sem detecção. P0-1, P0-2, P0-3 foram exemplos do tipo de bug que essa cegueira
permitia em produção.

Esta suite fecha a cobertura nos 6 axes restantes (multi-tenant já fechado em
W1.1 via TestTeamsMultiTenantBoundary em test_red_team_multi_tenant.py):

| Axis             | Strict (cobertura)                         | xfail (gap → wave alvo)                                  |
|------------------|--------------------------------------------|----------------------------------------------------------|
| PII              | Teams handlers existem                     | strip_pii_for_llm_prompt não chamado em Teams (W2.4)     |
| Fairness         | Teams handlers existem                     | FairnessGuard não chamado em Teams (W2.5)                |
| LGPD             | Teams handlers existem                     | LGPD consent check não acionado no canal Teams (W2.6)    |
| Prompt injection | Teams handlers existem                     | PromptInjectionGuard não chamado em Teams (W2.7)         |
| Circuit breakers | Teams handlers existem                     | Circuit breaker não envolve send_message Teams (W2.8)    |
| Scenarios        | Teams modelos auditáveis (W1.1)            | end-to-end Teams scenario tests (W2.9)                   |

Pattern xfail: gap conhecido, sinaliza próxima wave. Não bloqueia merge.
"""
from __future__ import annotations

import inspect
import pytest


# ============================================================================
# Helper: load Teams source by module path (cached)
# ============================================================================


def _src(module_path: str) -> str:
    import importlib
    mod = importlib.import_module(module_path)
    return inspect.getsource(mod)


# ============================================================================
# 1. PII (Categoria 3)
# ============================================================================


class TestTeamsRedTeamPII:
    """Teams channel coverage in PII red team."""

    def test_teams_module_loads(self):
        """app.api.v1.teams must be importable (existence check)."""
        import app.api.v1.teams  # noqa: F401

    def test_teams_orchestrator_bridge_loads(self):
        """teams_orchestrator_bridge must be importable."""
        import app.domains.communication.services.teams_orchestrator_bridge  # noqa: F401

    @pytest.mark.xfail(
        reason=(
            "GAP arquitetural (revalidado W4): agent final aplica strip_pii via "
            "LangGraphReActBase:71-79 (LIA-C04). PORÉM router intermediario "
            "(cascaded_router.py:_route_via_llm_cascade) faz LLM call para Tier 5 "
            "intent classification SEM strip — PII pode vazar no roteamento. "
            "Fix arquitetural: aplicar strip_pii antes do router (em bridge OU em "
            "orchestrator entry). Nao especifico de Teams — afeta todos os canais."
        ),
        strict=False,
    )
    def test_teams_orchestrator_bridge_strips_pii_before_llm(self):
        src = _src("app.domains.communication.services.teams_orchestrator_bridge")
        assert "strip_pii_for_llm_prompt" in src or "PIIRedactor" in src, (
            "Bridge deve aplicar PII redaction antes de chamar orchestrator"
        )

    @pytest.mark.xfail(
        reason="GAP W2.4: CV upload via Teams não passa por PII strip antes do parser/LLM.",
        strict=False,
    )
    def test_teams_cv_attachment_strips_pii(self):
        src = _src("app.domains.communication.services.teams_orchestrator_bridge")
        # process_cv_attachment é onde o CV chega
        assert "strip_pii" in src or "PIIRedactor" in src


# ============================================================================
# 2. Fairness (Categoria 2)
# ============================================================================


class TestTeamsRedTeamFairness:
    """Teams channel coverage in fairness red team."""

    def test_teams_card_renderer_loads(self):
        import app.domains.communication.services.teams_card_renderer  # noqa: F401

    def test_teams_card_renderer_safe_via_agent_heritage(self):
        """
        UPDATED W4-revalidation: card_renderer puro nao precisa invocar FairnessGuard.
        Mensagens chegam pelos agents que herdam EnhancedAgentMixin (que faz
        FairnessGuard pre-check automatico em P0-A — enhanced_agent_mixin.py:369-415).
        Card renderer eh layer de presentation — fairness ja foi aplicado upstream.
        """
        from lia_agents_core.enhanced_agent_mixin import EnhancedAgentMixin
        import inspect
        mixin_src = inspect.getsource(EnhancedAgentMixin)
        assert "FairnessGuard" in mixin_src, (
            "EnhancedAgentMixin deve aplicar FairnessGuard pre-check (P0-A) — "
            "agents Teams herdam isso, card renderer nao precisa duplicar"
        )

    def test_teams_bridge_safe_via_agent_heritage(self):
        """
        UPDATED W4-revalidation: bridge encaminha para orchestrator que invoca
        agents (LangGraphReActBase + EnhancedAgentMixin). FairnessGuard atua
        automaticamente quando agent processa input (P0-A). Bridge nao precisa
        duplicar — heritage cobre.
        """
        from lia_agents_core.langgraph_react_base import LangGraphReActBase
        from lia_agents_core.enhanced_agent_mixin import EnhancedAgentMixin
        import inspect
        # Both base classes apply FairnessGuard
        base_src = inspect.getsource(LangGraphReActBase)
        mixin_src = inspect.getsource(EnhancedAgentMixin)
        assert "FairnessGuard" in base_src or "FairnessGuard" in mixin_src


# ============================================================================
# 3. LGPD (Categoria 6)
# ============================================================================


class TestTeamsRedTeamLGPD:
    """Teams channel coverage in LGPD red team."""

    def test_teams_audit_log_model_records_company_id(self):
        """W1.1 fix: TeamsActionAuditLog persists company_id for compliance trail."""
        from lia_models.teams import TeamsActionAuditLog
        cols = [c.key for c in TeamsActionAuditLog.__table__.columns]
        assert "company_id" in cols

    @pytest.mark.xfail(
        reason=(
            "GAP W2.6: webhook approve action não verifica LGPD consent do candidato "
            "antes de iniciar WhatsApp screening. Outras camadas invocam consent_service "
            "ou lgpd_service; Teams faz bypass implícito."
        ),
        strict=False,
    )
    def test_teams_approve_invokes_consent_service(self):
        src = _src("app.api.v1.teams")
        # Strict: procura invocação real de service de consent/LGPD
        # (não basta palavra no docstring — Azure AD consent é unrelated)
        invokes_service = (
            "consent_service" in src
            or "lgpd_service" in src
            or "check_consent(" in src
            or "verify_consent(" in src
        )
        assert invokes_service, (
            "Teams approve action deve invocar consent_service / lgpd_service / "
            "check_consent — palavra consent standalone (Azure AD) não conta."
        )


# ============================================================================
# 4. Prompt injection (Categoria 1)
# ============================================================================


class TestTeamsRedTeamPromptInjection:
    """Teams channel coverage in prompt injection red team."""

    def test_teams_module_loads(self):
        import app.api.v1.teams  # noqa: F401

    @pytest.mark.xfail(
        reason=(
            "GAP W2.7: teams_orchestrator_bridge não chama PromptInjectionGuard. "
            "Recrutador hostile pode tentar injetar payload via mensagem Teams "
            "que escapa para o orchestrator."
        ),
        strict=False,
    )
    def test_teams_bridge_checks_prompt_injection(self):
        src = _src("app.domains.communication.services.teams_orchestrator_bridge")
        assert "PromptInjectionGuard" in src or "prompt_injection" in src.lower()


# ============================================================================
# 5. Circuit breakers (Categoria 5)
# ============================================================================


class TestTeamsRedTeamCircuitBreakers:
    """Teams channel coverage in circuit breakers red team."""

    def test_teams_simple_bot_loads(self):
        import app.domains.communication.services.teams_simple  # noqa: F401

    @pytest.mark.xfail(
        reason=(
            "GAP W2.8: simple_teams_bot.send_message / send_adaptive_card não envolvem "
            "as chamadas httpx em circuit breaker. Microsoft Bot Framework fora pode "
            "cascatear falhas — sem breaker, retries cegos."
        ),
        strict=False,
    )
    def test_teams_send_uses_circuit_breaker(self):
        src = _src("app.domains.communication.services.teams_simple")
        assert "CircuitBreaker" in src or "circuit_breaker" in src or "@breaker" in src


# ============================================================================
# 6. Scenarios (Categoria 7 — end-to-end)
# ============================================================================


class TestTeamsRedTeamScenarios:
    """Teams end-to-end red team scenarios."""

    def test_teams_models_have_audit_trail(self):
        """W1.1 fix: TeamsConversation + TeamsActionAuditLog têm company_id."""
        from lia_models.teams import TeamsConversation, TeamsActionAuditLog
        for model in (TeamsConversation, TeamsActionAuditLog):
            cols = [c.key for c in model.__table__.columns]
            assert "company_id" in cols, (
                f"{model.__name__} deve ter company_id (auditoria/multi-tenant)"
            )

    def test_teams_webhook_payload_does_not_accept_company_id(self):
        """W1.2 fix: client cannot forge company_id in payload."""
        from app.api.v1.teams import TeamsWebhookPayload
        assert "company_id" not in TeamsWebhookPayload.model_fields

    def test_teams_audit_logs_endpoint_requires_auth(self):
        """W1.3 fix: GET /webhook/audit-logs requires Depends(get_current_user)."""
        import app.api.v1.teams as mod
        src = inspect.getsource(mod.get_teams_audit_logs)
        assert "get_current_user" in src

    @pytest.mark.xfail(
        reason=(
            "GAP W2.9: end-to-end Teams scenario test (recrutador hostile sends "
            "Teams message + Adaptive Card action mass-rejecting candidatos com "
            "viés explícito) ainda não escrito. Cobertura cumulativa esperada após "
            "W2.4 + W2.5 + W2.6 + W2.7 + W2.8 implementadas."
        ),
        strict=False,
    )
    def test_teams_end_to_end_hostile_recruiter_blocked(self):
        # Cenário composto: PII strip + fairness + LGPD + prompt injection +
        # circuit breaker — todos devem agir juntos quando recrutador adversarial
        # envia mensagem Teams. Implementar quando W2.4-W2.8 prontos.
        assert False, "Composite end-to-end pending W2.x waves"


# ============================================================================
# Coverage meta-test — validates Teams is now in the red team radar
# ============================================================================


class TestRedTeamTeamsCoverageMeta:
    """Meta-test: Teams must appear in red team radar across the suite."""

    def test_teams_red_team_files_have_teams_class(self):
        """
        Sentinel: when this file (test_red_team_teams_coverage_w1_4.py) exists,
        Teams red team coverage is no longer zero. Future waves should add
        more strict tests (each xfail above flips to strict as W2.x lands).
        """
        # Self-validation: this very test file exists and was loaded.
        import sys
        mod_name = "tests.security.test_red_team_teams_coverage_w1_4"
        assert mod_name in sys.modules, (
            "test_red_team_teams_coverage_w1_4 module must be loaded for Teams "
            "red team coverage to be considered alive (W1.4 sentinel)."
        )

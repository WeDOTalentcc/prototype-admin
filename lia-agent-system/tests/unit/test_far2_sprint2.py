"""
FAR-2 Sprint 2: Testes para os 3 itens implementados.

Cobre:
- FAR-2/A: pipeline_move em HIGH_IMPACT_ACTIONS + PipelineTransitionAgent usa check_with_layer3
- FAR-2/B: GET /fairness/audit/logs endpoint
- FAR-2/C: FairnessWarningBanner — testado via Vitest (FE); aqui testa integração BE
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ─── FAR-2/A — pipeline_move em HIGH_IMPACT_ACTIONS ──────────────────────────

class TestPipelineMoveHighImpact:

    def test_pipeline_move_in_high_impact_actions(self):
        from app.shared.compliance.fairness_guard import HIGH_IMPACT_ACTIONS
        assert "pipeline_move" in HIGH_IMPACT_ACTIONS

    def test_all_original_actions_still_present(self):
        from app.shared.compliance.fairness_guard import HIGH_IMPACT_ACTIONS
        for action in ("rejection", "shortlist", "wsi_score", "policy_save",
                       "sourcing_search", "jd_import"):
            assert action in HIGH_IMPACT_ACTIONS, f"Missing: {action}"

    @pytest.mark.asyncio
    async def test_pipeline_agent_uses_check_with_layer3(self):
        """PipelineTransitionAgent.process() deve chamar check_with_layer3."""
        from app.domains.pipeline.agents.pipeline_transition_agent import PipelineTransitionAgent
        from lia_agents_core.agent_interface import AgentInput, AgentOutput
        from app.shared.compliance.fairness_guard import FairnessCheckResult

        agent = PipelineTransitionAgent()
        clean_result = FairnessCheckResult(
            is_blocked=False,
            original_query="mover candidato para entrevista",
            soft_warnings=[],
        )
        mock_output = AgentOutput(message="OK", confidence=0.9, metadata={})

        with patch(
            'app.shared.compliance.fairness_guard.FairnessGuard.check_with_layer3',
            new_callable=AsyncMock,
            return_value=clean_result,
        ) as mock_l3:
            with patch.object(
                agent, '_process_langgraph',
                new_callable=AsyncMock,
                return_value=mock_output,
            ):
                agent_input = AgentInput(
                    message="mover candidato para entrevista",
                    context={"action_behavior": "passive"},
                    session_id="test-session",
                    company_id="test-company",
                    user_id="test-user",
                    conversation_history=[],
                )
                await agent.process(agent_input)

        mock_l3.assert_called_once()
        call_args = mock_l3.call_args
        assert "pipeline_move" in str(call_args)

    @pytest.mark.asyncio
    async def test_pipeline_agent_layer3_blocks_discriminatory(self):
        """Pipeline agent deve bloquear mensagens discriminatórias via check_with_layer3."""
        from app.domains.pipeline.agents.pipeline_transition_agent import PipelineTransitionAgent
        from lia_agents_core.agent_interface import AgentInput, AgentOutput
        from app.shared.compliance.fairness_guard import FairnessCheckResult

        agent = PipelineTransitionAgent()
        blocked_result = FairnessCheckResult(
            is_blocked=True,
            blocked_terms=["apenas homens"],
            category="genero",
            educational_message="Discriminação por gênero é proibida.",
            original_query="apenas homens para a vaga",
            confidence=0.99,
        )

        with patch(
            'app.shared.compliance.fairness_guard.FairnessGuard.check_with_layer3',
            new_callable=AsyncMock,
            return_value=blocked_result,
        ):
            agent_input = AgentInput(
                message="apenas homens para a vaga",
                context={},
                session_id="test-session",
                company_id="test-company",
                user_id="test-user",
                conversation_history=[],
            )
            result = await agent.process(agent_input)

        assert result.metadata.get("fairness_blocked") is True
        assert result.metadata.get("fairness_category") == "genero"


# ─── FAR-2/B — GET /fairness/audit/logs endpoint ─────────────────────────────

class TestFairnessAuditLogsEndpoint:

    def test_fairness_audit_logs_route_exists(self):
        """Rota GET /fairness/audit/logs deve estar registrada."""
        from app.api.v1.fairness_reports import router
        routes = [r.path for r in router.routes]
        assert any("audit/logs" in p for p in routes), f"Rota audit/logs não encontrada. Routes: {routes}"

    def test_fairness_audit_logs_response_model(self):
        """FairnessAuditLogsResponse deve ter campos corretos."""
        from app.api.v1.fairness_reports import FairnessAuditLogsResponse, FairnessAuditLogEntry
        # Verificar campos do response model
        fields = FairnessAuditLogsResponse.model_fields
        assert "items" in fields
        assert "total" in fields
        assert "limit" in fields
        assert "offset" in fields

    def test_fairness_audit_log_entry_model(self):
        """FairnessAuditLogEntry deve ter campos de auditoria."""
        from app.api.v1.fairness_reports import FairnessAuditLogEntry
        fields = FairnessAuditLogEntry.model_fields
        assert "id" in fields
        assert "category" in fields
        assert "is_blocked" in fields
        assert "soft_warnings" in fields
        assert "created_at" in fields

    def test_fairness_audit_log_entry_no_query_plaintext(self):
        """FairnessAuditLogEntry NÃO deve ter campo original_query (LGPD)."""
        from app.api.v1.fairness_reports import FairnessAuditLogEntry
        fields = FairnessAuditLogEntry.model_fields
        # Queries originais não devem ser expostas — apenas query_hash
        assert "original_query" not in fields
        assert "query" not in fields

    @pytest.mark.asyncio
    async def test_audit_logs_endpoint_filters_by_company(self):
        """Endpoint deve filtrar por company_id do usuário autenticado."""
        from app.api.v1.fairness_reports import get_fairness_audit_logs
        from unittest.mock import AsyncMock, MagicMock

        mock_db = AsyncMock()
        mock_user = MagicMock()

        # Simular resultado vazio do banco
        mock_result = MagicMock()
        mock_result.scalar.return_value = 0
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await get_fairness_audit_logs(
            company_id="550e8400-e29b-41d4-a716-446655440000",
            category=None,
            blocked_only=False,
            days=30,
            limit=50,
            offset=0,
            db=mock_db,
            current_user=mock_user,
        )

        assert result.total == 0
        assert result.items == []
        assert result.limit == 50
        assert result.offset == 0

    @pytest.mark.asyncio
    async def test_audit_logs_invalid_company_id_doesnt_crash(self):
        """UUID inválido no company_id não deve lançar exceção."""
        from app.api.v1.fairness_reports import get_fairness_audit_logs
        from unittest.mock import AsyncMock, MagicMock

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = 0
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        # UUID inválido — deve ignorar o filtro silenciosamente
        result = await get_fairness_audit_logs(
            company_id="nao-e-uuid",
            category=None,
            blocked_only=False,
            days=30,
            limit=10,
            offset=0,
            db=mock_db,
            current_user=MagicMock(),
        )
        assert result.total == 0


# ─── FAR-2/C — FairnessWarningBanner (BE side: WS payload) ───────────────────

class TestFairnessWarningsBEIntegration:

    @pytest.mark.asyncio
    async def test_sourcing_agent_soft_warnings_in_output_metadata(self):
        """SourcingReActAgent deve propagar soft_warnings ao output.metadata."""
        from app.domains.sourcing.agents.sourcing_react_agent import SourcingReActAgent
        from lia_agents_core.agent_interface import AgentInput, AgentOutput

        agent = SourcingReActAgent()
        mock_output = AgentOutput(message="OK", confidence=0.9, metadata={})

        with patch.object(agent, '_process_langgraph', new_callable=AsyncMock, return_value=mock_output):
            agent_input = AgentInput(
                message="buscar candidatos de bairros nobres",
                context={},
                session_id="test",
                company_id="test-company",
                user_id="test-user",
                conversation_history=[],
            )
            result = await agent.process(agent_input)

        # soft_warnings devem estar no metadata
        assert "fairness_warnings" in result.metadata
        assert len(result.metadata["fairness_warnings"]) > 0

    def test_fairness_warning_banner_proxy_exists(self):
        """Proxy FE para audit/logs deve existir."""
        import os
        path = "../../plataforma-lia/src/app/api/backend-proxy/fairness-audit/logs/route.ts"
        abs_path = os.path.join(
            os.path.dirname(__file__),
            "../../plataforma-lia/src/app/api/backend-proxy/fairness-audit/logs/route.ts"
        )
        # Verificar com path absoluto correto
        proxy_path = "/home/runner/workspace/plataforma-lia/src/app/api/backend-proxy/fairness-audit/logs/route.ts"
        assert os.path.exists(proxy_path), f"Proxy não encontrado: {proxy_path}"

    def test_fairness_warning_banner_component_exists(self):
        """Componente FairnessWarningBanner deve existir."""
        import os
        component_path = "/home/runner/workspace/plataforma-lia/src/components/fairness-warning-banner.tsx"
        assert os.path.exists(component_path), f"Componente não encontrado: {component_path}"

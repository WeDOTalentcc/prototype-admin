"""
D8 — Insights Proativos no Kanban
Testa GET /api/v1/proactive-actions/insights
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime


class TestProactiveInsightsEndpoint:

    def _make_action(self, action_id="a1", title="Insight", desc="Mensagem", priority="normal",
                     action_type="pipeline_alert", suggested_action=None):
        a = MagicMock()
        a.id = action_id
        a.title = title
        a.description = desc
        a.priority = priority
        a.action_type = action_type
        a.suggested_action = suggested_action or {}
        a.created_at = datetime(2026, 3, 15, 10, 0, 0)
        return a

    @pytest.mark.asyncio
    async def test_insights_returns_list(self):
        """GET /proactive-actions/insights retorna lista de ProactiveInsight."""
        from app.api.v1.proactive_actions import get_proactive_insights

        actions = [
            self._make_action("a1", "Candidato parado", "Não houve progresso", "high"),
            self._make_action("a2", "Pipeline lento", "5 candidatos há >3 dias", "normal"),
        ]

        with patch(
            "app.domains.automation.services.autonomous_agent_service.AutonomousAgentService.get_pending_actions",
            new_callable=AsyncMock,
            return_value=actions,
        ):
            result = await get_proactive_insights(company_id="comp-1", job_id=None, limit=5)

        assert len(result) == 2
        assert result[0].id == "a1"
        assert result[0].urgency == "high"
        assert result[0].message == "Não houve progresso"

    @pytest.mark.asyncio
    async def test_insights_filters_by_job_id(self):
        """Apenas insights com job_id matching são retornados."""
        from app.api.v1.proactive_actions import get_proactive_insights

        actions = [
            self._make_action("a1", "T1", "D1", "high", suggested_action={"job_id": "job-1"}),
            self._make_action("a2", "T2", "D2", "normal", suggested_action={"job_id": "job-2"}),
            self._make_action("a3", "T3", "D3", "low", suggested_action={}),
        ]

        with patch(
            "app.domains.automation.services.autonomous_agent_service.AutonomousAgentService.get_pending_actions",
            new_callable=AsyncMock,
            return_value=actions,
        ):
            result = await get_proactive_insights(company_id="comp-1", job_id="job-1", limit=5)

        ids = [r.id for r in result]
        assert "a1" in ids
        assert "a2" not in ids
        # a3 has no job_id in suggested_action — no filter applied for it
        assert "a3" in ids

    @pytest.mark.asyncio
    async def test_insights_respects_limit(self):
        """limit=2 retorna no máximo 2 insights."""
        from app.api.v1.proactive_actions import get_proactive_insights

        actions = [self._make_action(f"a{i}") for i in range(10)]

        with patch(
            "app.domains.automation.services.autonomous_agent_service.AutonomousAgentService.get_pending_actions",
            new_callable=AsyncMock,
            return_value=actions,
        ):
            result = await get_proactive_insights(company_id="comp-1", job_id=None, limit=2)

        assert len(result) <= 2

    @pytest.mark.asyncio
    async def test_insights_returns_empty_on_error(self):
        """Retorna lista vazia (não lança 500) quando serviço falha."""
        from app.api.v1.proactive_actions import get_proactive_insights

        with patch(
            "app.domains.automation.services.autonomous_agent_service.AutonomousAgentService.get_pending_actions",
            new_callable=AsyncMock,
            side_effect=Exception("DB indisponível"),
        ):
            result = await get_proactive_insights(company_id="comp-1", job_id=None, limit=5)

        assert result == []

    @pytest.mark.asyncio
    async def test_insights_maps_fields_correctly(self):
        """Campos urgency, type, action_url mapeados corretamente."""
        from app.api.v1.proactive_actions import get_proactive_insights

        actions = [
            self._make_action(
                "a1", "Alerta", "Desc", "urgent", "pipeline_alert",
                suggested_action={"job_id": "j1", "action_url": "/kanban/job/j1"}
            )
        ]

        with patch(
            "app.domains.automation.services.autonomous_agent_service.AutonomousAgentService.get_pending_actions",
            new_callable=AsyncMock,
            return_value=actions,
        ):
            result = await get_proactive_insights(company_id="comp-1", job_id=None, limit=5)

        assert result[0].urgency == "urgent"
        assert result[0].type == "pipeline_alert"
        assert result[0].action_url == "/kanban/job/j1"

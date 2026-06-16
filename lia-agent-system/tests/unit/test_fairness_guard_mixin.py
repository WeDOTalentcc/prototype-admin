"""
P0-A — Testes do FairnessGuard automático no EnhancedAgentMixin.

Cobre:
1. _fairness_pre_check retorna mensagem educacional para input discriminatório
2. _fairness_pre_check retorna None para input limpo
3. _fairness_pre_check retorna None para input vazio (sem bloquear)
4. _fairness_pre_check é fail-safe: exceção interna não propaga
5. Soft warnings logados sem bloquear
6. Talent agent process() retorna AgentOutput com mensagem fairness quando bloqueado
7. Kanban agent process() retorna AgentOutput com mensagem fairness quando bloqueado
8. JobsMgmt agent process() retorna AgentOutput com mensagem fairness quando bloqueado
9. Wizard agent process() retorna AgentOutput com mensagem fairness quando bloqueado
10. Agentes bloqueados não delegam para _process_react_loop / _process_langgraph
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_agent_input(message: str = "lista apenas homens para esta vaga"):
    """Cria um AgentInput mínimo para testes."""
    inp = MagicMock()
    inp.message = message
    inp.session_id = "test-session"
    inp.company_id = "company-123"
    inp.user_id = "user-1"
    inp.context = {}
    return inp


# ── Testes do método _fairness_pre_check no mixin ────────────────────────────

class TestFairnessPreCheckMixin:

    @pytest.fixture
    def mixin(self):
        """Instância mínima do mixin para testar isoladamente."""
        from lia_agents_core.enhanced_agent_mixin import EnhancedAgentMixin

        class _Agent(EnhancedAgentMixin):
            _enhanced_domain = "test_domain"

        return _Agent()

    @pytest.mark.asyncio
    async def test_input_discriminatorio_retorna_mensagem_educacional(self, mixin):
        msg = await mixin._fairness_pre_check("quero apenas mulheres para essa vaga")
        assert msg is not None
        assert len(msg) > 20

    @pytest.mark.asyncio
    async def test_input_limpo_retorna_none(self, mixin):
        msg = await mixin._fairness_pre_check("preciso de um dev Python senior com 5 anos de experiência")
        assert msg is None

    @pytest.mark.asyncio
    async def test_input_vazio_retorna_none(self, mixin):
        assert await mixin._fairness_pre_check("") is None
        assert await mixin._fairness_pre_check("   ") is None

    @pytest.mark.asyncio
    async def test_fail_safe_excecao_interna(self, mixin):
        """Exceção no FairnessGuard não deve propagar — retorna None."""
        with patch(
            "app.shared.compliance.fairness_guard.FairnessGuard.check",
            side_effect=RuntimeError("FairnessGuard indisponível"),
        ):
            msg = await mixin._fairness_pre_check("quero candidatos sem filhos")
            assert msg is None

    @pytest.mark.asyncio
    async def test_soft_warning_nao_bloqueia(self, mixin):
        """Implicit bias (Camada 2) deve logar warning mas não bloquear."""
        # "boa aparencia" é um termo de viés implícito — não bloqueia Camada 1
        msg = await mixin._fairness_pre_check("buscar candidatos com perfil adequado")
        # Camada 2 = soft warning, não bloqueia
        assert msg is None

    @pytest.mark.asyncio
    async def test_criterio_etario_bloqueado(self, mixin):
        msg = await mixin._fairness_pre_check("excluir candidatos maiores de 50 anos")
        assert msg is not None
        assert len(msg) > 20

    @pytest.mark.asyncio
    async def test_criterio_genero_retorna_educacional(self, mixin):
        msg = await mixin._fairness_pre_check("filtrar somente homens")
        assert msg is not None

    @pytest.mark.asyncio
    async def test_mensagem_fallback_quando_educational_message_none(self, mixin):
        """Quando educational_message do resultado for None, usa fallback genérico."""
        from app.shared.compliance.fairness_guard import FairnessCheckResult

        fake_result = FairnessCheckResult(
            is_blocked=True,
            blocked_terms=["somente homens"],
            category="genero",
            educational_message=None,  # forçar fallback
            original_query="somente homens",
            confidence=0.9,
        )
        with patch(
            "app.shared.compliance.fairness_guard.FairnessGuard.check",
            return_value=fake_result,
        ):
            msg = await mixin._fairness_pre_check("somente homens")
            assert msg is not None
            assert "discriminatórios" in msg or "criterios" in msg.lower() or "competências" in msg


# ── Testes de integração nos agentes ─────────────────────────────────────────

class TestFairnessPreCheckAgentIntegration:
    """Garante que talent/kanban/jobs_mgmt/wizard chamam _fairness_pre_check."""

    def _make_blocked_mixin(self):
        """Patch _fairness_pre_check para sempre bloquear."""
        return patch.object(
            __import__(
                "lia_agents_core.enhanced_agent_mixin",
                fromlist=["EnhancedAgentMixin"],
            ).EnhancedAgentMixin,
            "_fairness_pre_check",
            new=AsyncMock(return_value="Bloqueado: critério discriminatório detectado."),
        )

    @pytest.mark.asyncio
    async def test_talent_agent_bloqueado_nao_processa(self):
        from app.domains.recruiter_assistant.agents.talent_react_agent import TalentReActAgent
        agent = TalentReActAgent.__new__(TalentReActAgent)
        agent._enhanced_domain = "talent"

        with patch.object(
            agent, "_fairness_pre_check",
            new=AsyncMock(return_value="Mensagem educacional talent"),
        ):
            with patch.object(agent, "_process_langgraph", new=AsyncMock()) as mock_lg:
                result = await agent.process(_make_agent_input())
                assert result.message == "Mensagem educacional talent"
                mock_lg.assert_not_called()

    @pytest.mark.asyncio
    async def test_kanban_agent_bloqueado_nao_processa(self):
        from app.domains.recruiter_assistant.agents.kanban_react_agent import KanbanReActAgent
        agent = KanbanReActAgent.__new__(KanbanReActAgent)
        agent._enhanced_domain = "kanban"

        with patch.object(
            agent, "_fairness_pre_check",
            new=AsyncMock(return_value="Mensagem educacional kanban"),
        ):
            with patch.object(agent, "_process_langgraph", new=AsyncMock()) as mock_lg:
                result = await agent.process(_make_agent_input())
                assert result.message == "Mensagem educacional kanban"
                mock_lg.assert_not_called()

    @pytest.mark.asyncio
    async def test_jobs_mgmt_agent_bloqueado_nao_processa(self):
        from app.domains.recruiter_assistant.agents.jobs_mgmt_react_agent import JobsMgmtReActAgent
        agent = JobsMgmtReActAgent.__new__(JobsMgmtReActAgent)
        agent._enhanced_domain = "jobs_management"

        with patch.object(
            agent, "_fairness_pre_check",
            new=AsyncMock(return_value="Mensagem educacional jobs"),
        ):
            with patch.object(agent, "_process_langgraph", new=AsyncMock()) as mock_lg:
                result = await agent.process(_make_agent_input())
                assert result.message == "Mensagem educacional jobs"
                mock_lg.assert_not_called()

    @pytest.mark.asyncio
    async def test_wizard_agent_bloqueado_nao_processa(self):
        from app.domains.job_management.agents.wizard_react_agent import WizardReActAgent
        agent = WizardReActAgent.__new__(WizardReActAgent)
        agent._enhanced_domain = "wizard"

        with patch.object(
            agent, "_fairness_pre_check",
            new=AsyncMock(return_value="Mensagem educacional wizard"),
        ):
            with patch.object(agent, "_process_langgraph", new=AsyncMock()) as mock_lg:
                result = await agent.process(_make_agent_input())
                assert result.message == "Mensagem educacional wizard"
                mock_lg.assert_not_called()

    @pytest.mark.asyncio
    async def test_input_limpo_prossegue_para_loop(self):
        """Input limpo → _fairness_pre_check retorna None → delega para _process_react_loop."""
        from app.domains.recruiter_assistant.agents.talent_react_agent import TalentReActAgent
        agent = TalentReActAgent.__new__(TalentReActAgent)
        agent._enhanced_domain = "talent"

        mock_output = MagicMock()
        with patch.object(
            agent, "_fairness_pre_check",
            new=AsyncMock(return_value=None),  # limpo
        ):
            with patch.object(agent, "_process_langgraph", new=AsyncMock(return_value=mock_output)) as mock_loop:
                result = await agent.process(_make_agent_input("dev Python senior"))
                mock_loop.assert_called_once()
                assert result is mock_output


# ── Cobertura de cobertura: método existe no mixin ───────────────────────────

class TestFairnessPreCheckExists:

    def test_metodo_existe_no_mixin(self):
        from lia_agents_core.enhanced_agent_mixin import EnhancedAgentMixin
        assert hasattr(EnhancedAgentMixin, "_fairness_pre_check")
        assert callable(getattr(EnhancedAgentMixin, "_fairness_pre_check"))

    def test_talent_herda_mixin(self):
        from app.domains.recruiter_assistant.agents.talent_react_agent import TalentReActAgent
        from lia_agents_core.enhanced_agent_mixin import EnhancedAgentMixin
        assert issubclass(TalentReActAgent, EnhancedAgentMixin)

    def test_kanban_herda_mixin(self):
        from app.domains.recruiter_assistant.agents.kanban_react_agent import KanbanReActAgent
        from lia_agents_core.enhanced_agent_mixin import EnhancedAgentMixin
        assert issubclass(KanbanReActAgent, EnhancedAgentMixin)

    def test_jobs_mgmt_herda_mixin(self):
        from app.domains.recruiter_assistant.agents.jobs_mgmt_react_agent import JobsMgmtReActAgent
        from lia_agents_core.enhanced_agent_mixin import EnhancedAgentMixin
        assert issubclass(JobsMgmtReActAgent, EnhancedAgentMixin)

    def test_wizard_herda_mixin(self):
        from app.domains.job_management.agents.wizard_react_agent import WizardReActAgent
        from lia_agents_core.enhanced_agent_mixin import EnhancedAgentMixin
        assert issubclass(WizardReActAgent, EnhancedAgentMixin)

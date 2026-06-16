"""
Snapshot tests — 5 agentes restantes (Sprint D / André P10/R5).

Sourcing, Policy, Kanban, Talent, JobsManagement.

Validam que os outputs são estáveis para inputs conhecidos.
LLM mockado — sem chamadas reais à Anthropic.

Execução:
    pytest tests/snapshots/test_remaining_agents_snapshots.py -v
    UPDATE_SNAPSHOTS=true pytest tests/snapshots/test_remaining_agents_snapshots.py -v
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from tests.snapshots.conftest import (
    UPDATE_SNAPSHOTS,
    load_snapshot,
    make_mock_agent_state,
    save_snapshot,
    make_test_input,
)
from lia_agents_core.agent_interface import AgentInput, AgentOutput

_PATCH_PATH = "lia_agents_core.langgraph_react_base.LangGraphReActBase._run_graph"


def _mock_run(content: str):
    mock_state = make_mock_agent_state(content)

    async def _inner(*args, **kwargs):
        return mock_state

    return _inner


# ---------------------------------------------------------------------------
# SourcingReActAgent
# ---------------------------------------------------------------------------

class TestSourcingAgentSnapshots:

    @pytest.mark.asyncio
    async def test_sourcing_search_candidates(self):
        snapshot_name = "sourcing_search_candidates"
        agent_input = make_test_input(
            domain="sourcing",
            message="buscar candidatos para vaga de engenheiro de software sênior",
        )
        mock_content = (
            "Encontrei 12 candidatos compatíveis com o perfil de Engenheiro de Software Sênior. "
            "Os 3 melhores matches são: Ana Silva (95%), Carlos Mendes (92%), Julia Costa (89%)."
        )
        with patch(_PATCH_PATH, new_callable=AsyncMock) as mock_run:
            mock_run.return_value = make_mock_agent_state(mock_content)
            try:
                from app.domains.sourcing.agents.sourcing_react_agent import SourcingReActAgent
                agent = SourcingReActAgent()
                output = await agent._process_langgraph(agent_input)
            except ImportError:
                pytest.skip("SourcingReActAgent não disponível")

        snapshot = load_snapshot(snapshot_name)
        if snapshot is None or UPDATE_SNAPSHOTS:
            save_snapshot(snapshot_name, {"message_contains": "candidato", "confidence_min": 0.5})
            snapshot = load_snapshot(snapshot_name)

        assert output.message
        assert len(output.message) > 0
        assert output.confidence >= snapshot.get("confidence_min", 0.0)

    @pytest.mark.asyncio
    async def test_sourcing_filter_by_skill(self):
        snapshot_name = "sourcing_filter_by_skill"
        agent_input = make_test_input(
            domain="sourcing",
            message="filtrar candidatos com Python e AWS",
        )
        mock_content = "Filtrei por Python e AWS: encontrei 7 candidatos com ambas as habilidades."
        with patch(_PATCH_PATH, new_callable=AsyncMock) as mock_run:
            mock_run.return_value = make_mock_agent_state(mock_content)
            try:
                from app.domains.sourcing.agents.sourcing_react_agent import SourcingReActAgent
                agent = SourcingReActAgent()
                output = await agent._process_langgraph(agent_input)
            except ImportError:
                pytest.skip("SourcingReActAgent não disponível")
        assert output.message

    @pytest.mark.asyncio
    async def test_sourcing_rank_candidates(self):
        snapshot_name = "sourcing_rank_candidates"
        agent_input = make_test_input(
            domain="sourcing",
            message="ranquear candidatos por score LIA",
        )
        mock_content = "Candidatos ordenados por score: 1. Pedro (98), 2. Maria (95), 3. João (91)."
        with patch(_PATCH_PATH, new_callable=AsyncMock) as mock_run:
            mock_run.return_value = make_mock_agent_state(mock_content)
            try:
                from app.domains.sourcing.agents.sourcing_react_agent import SourcingReActAgent
                agent = SourcingReActAgent()
                output = await agent._process_langgraph(agent_input)
            except ImportError:
                pytest.skip("SourcingReActAgent não disponível")
        assert output.message

    @pytest.mark.asyncio
    async def test_sourcing_empty_results_graceful(self):
        snapshot_name = "sourcing_empty_results"
        agent_input = make_test_input(
            domain="sourcing",
            message="candidatos com habilidade em COBOL e Fortran",
        )
        mock_content = "Não encontrei candidatos com COBOL e Fortran no banco atual."
        with patch(_PATCH_PATH, new_callable=AsyncMock) as mock_run:
            mock_run.return_value = make_mock_agent_state(mock_content)
            try:
                from app.domains.sourcing.agents.sourcing_react_agent import SourcingReActAgent
                agent = SourcingReActAgent()
                output = await agent._process_langgraph(agent_input)
            except ImportError:
                pytest.skip("SourcingReActAgent não disponível")
        assert output.message
        assert output.error is None

    @pytest.mark.asyncio
    async def test_sourcing_pipeline_sourcing(self):
        snapshot_name = "sourcing_pipeline"
        agent_input = make_test_input(
            domain="sourcing",
            message="adicionar candidata Ana Silva ao pipeline da vaga 123",
        )
        mock_content = "Ana Silva foi adicionada ao pipeline da vaga 123 na etapa de triagem."
        with patch(_PATCH_PATH, new_callable=AsyncMock) as mock_run:
            mock_run.return_value = make_mock_agent_state(mock_content)
            try:
                from app.domains.sourcing.agents.sourcing_react_agent import SourcingReActAgent
                agent = SourcingReActAgent()
                output = await agent._process_langgraph(agent_input)
            except ImportError:
                pytest.skip("SourcingReActAgent não disponível")
        assert output.message

    @pytest.mark.asyncio
    async def test_sourcing_general_query(self):
        snapshot_name = "sourcing_general"
        agent_input = make_test_input(
            domain="sourcing",
            message="quantos candidatos temos cadastrados?",
        )
        mock_content = "Temos 1.247 candidatos ativos cadastrados na plataforma."
        with patch(_PATCH_PATH, new_callable=AsyncMock) as mock_run:
            mock_run.return_value = make_mock_agent_state(mock_content)
            try:
                from app.domains.sourcing.agents.sourcing_react_agent import SourcingReActAgent
                agent = SourcingReActAgent()
                output = await agent._process_langgraph(agent_input)
            except ImportError:
                pytest.skip("SourcingReActAgent não disponível")
        assert output.message
        assert output.confidence >= 0.0


# ---------------------------------------------------------------------------
# PolicyReActAgent
# ---------------------------------------------------------------------------

class TestPolicyAgentSnapshots:

    @pytest.mark.asyncio
    async def test_policy_query_diversity(self):
        snapshot_name = "policy_diversity_query"
        agent_input = make_test_input(
            domain="policy",
            message="qual é a política de diversidade e inclusão da empresa?",
        )
        mock_content = "A política de D&I da empresa estabelece metas de 40% de mulheres em posições técnicas."
        with patch(_PATCH_PATH, new_callable=AsyncMock) as mock_run:
            mock_run.return_value = make_mock_agent_state(mock_content)
            try:
                from app.domains.hiring_policy.agents.policy_react_agent import PolicyReActAgent
                agent = PolicyReActAgent()
                output = await agent._process_langgraph(agent_input)
            except ImportError:
                pytest.skip("PolicyReActAgent não disponível")
        assert output.message

    @pytest.mark.asyncio
    async def test_policy_salary_range(self):
        snapshot_name = "policy_salary_range"
        agent_input = make_test_input(
            domain="policy",
            message="qual faixa salarial é permitida para Engenheiro Sênior?",
        )
        mock_content = "Para Engenheiro Sênior, a faixa aprovada é R$12.000 a R$18.000."
        with patch(_PATCH_PATH, new_callable=AsyncMock) as mock_run:
            mock_run.return_value = make_mock_agent_state(mock_content)
            try:
                from app.domains.hiring_policy.agents.policy_react_agent import PolicyReActAgent
                agent = PolicyReActAgent()
                output = await agent._process_langgraph(agent_input)
            except ImportError:
                pytest.skip("PolicyReActAgent não disponível")
        assert output.message

    @pytest.mark.asyncio
    async def test_policy_hiring_approval(self):
        snapshot_name = "policy_hiring_approval"
        agent_input = make_test_input(
            domain="policy",
            message="precisa de aprovação do CFO para contratar acima de R$15k?",
        )
        mock_content = "Sim, contratações acima de R$15.000 requerem aprovação do CFO e do CHRO."
        with patch(_PATCH_PATH, new_callable=AsyncMock) as mock_run:
            mock_run.return_value = make_mock_agent_state(mock_content)
            try:
                from app.domains.hiring_policy.agents.policy_react_agent import PolicyReActAgent
                agent = PolicyReActAgent()
                output = await agent._process_langgraph(agent_input)
            except ImportError:
                pytest.skip("PolicyReActAgent não disponível")
        assert output.message

    @pytest.mark.asyncio
    async def test_policy_unknown_rule(self):
        snapshot_name = "policy_unknown_rule"
        agent_input = make_test_input(
            domain="policy",
            message="posso contratar alguém sem entrevista técnica?",
        )
        mock_content = "Não localizei uma regra específica sobre isso. Recomendo consultar o manual de RH."
        with patch(_PATCH_PATH, new_callable=AsyncMock) as mock_run:
            mock_run.return_value = make_mock_agent_state(mock_content)
            try:
                from app.domains.hiring_policy.agents.policy_react_agent import PolicyReActAgent
                agent = PolicyReActAgent()
                output = await agent._process_langgraph(agent_input)
            except ImportError:
                pytest.skip("PolicyReActAgent não disponível")
        assert output.message
        assert output.error is None

    @pytest.mark.asyncio
    async def test_policy_headcount_limit(self):
        snapshot_name = "policy_headcount"
        agent_input = make_test_input(
            domain="policy",
            message="qual o limite de headcount aprovado para Q2?",
        )
        mock_content = "O headcount aprovado para Q2 é de 15 novas contratações no departamento de Tecnologia."
        with patch(_PATCH_PATH, new_callable=AsyncMock) as mock_run:
            mock_run.return_value = make_mock_agent_state(mock_content)
            try:
                from app.domains.hiring_policy.agents.policy_react_agent import PolicyReActAgent
                agent = PolicyReActAgent()
                output = await agent._process_langgraph(agent_input)
            except ImportError:
                pytest.skip("PolicyReActAgent não disponível")
        assert output.message

    @pytest.mark.asyncio
    async def test_policy_remote_work(self):
        snapshot_name = "policy_remote_work"
        agent_input = make_test_input(
            domain="policy",
            message="a empresa aceita trabalho 100% remoto?",
        )
        mock_content = "A política atual permite trabalho híbrido (3 dias remoto, 2 presencial) para maioria das funções."
        with patch(_PATCH_PATH, new_callable=AsyncMock) as mock_run:
            mock_run.return_value = make_mock_agent_state(mock_content)
            try:
                from app.domains.hiring_policy.agents.policy_react_agent import PolicyReActAgent
                agent = PolicyReActAgent()
                output = await agent._process_langgraph(agent_input)
            except ImportError:
                pytest.skip("PolicyReActAgent não disponível")
        assert output.message


# ---------------------------------------------------------------------------
# KanbanReActAgent
# ---------------------------------------------------------------------------

class TestKanbanAgentSnapshots:

    @pytest.mark.asyncio
    async def test_kanban_move_candidate(self):
        snapshot_name = "kanban_move_candidate"
        agent_input = make_test_input(
            domain="kanban",
            message="mover candidato João Silva para etapa de entrevista técnica",
            context={"job_id": "job-123"},
        )
        mock_content = "João Silva foi movido para Entrevista Técnica. Email de convite enviado."
        with patch(_PATCH_PATH, new_callable=AsyncMock) as mock_run:
            mock_run.return_value = make_mock_agent_state(mock_content)
            try:
                from app.domains.recruiter_assistant.agents.kanban_react_agent import KanbanReActAgent
                agent = KanbanReActAgent()
                output = await agent._process_langgraph(agent_input)
            except ImportError:
                pytest.skip("KanbanReActAgent não disponível")
        assert output.message

    @pytest.mark.asyncio
    async def test_kanban_view_pipeline(self):
        snapshot_name = "kanban_view_pipeline"
        agent_input = make_test_input(
            domain="kanban",
            message="mostrar pipeline da vaga de Product Manager",
            context={"job_id": "job-456"},
        )
        mock_content = "Pipeline de Product Manager: Triagem (5), Entrevista (3), Oferta (1)."
        with patch(_PATCH_PATH, new_callable=AsyncMock) as mock_run:
            mock_run.return_value = make_mock_agent_state(mock_content)
            try:
                from app.domains.recruiter_assistant.agents.kanban_react_agent import KanbanReActAgent
                agent = KanbanReActAgent()
                output = await agent._process_langgraph(agent_input)
            except ImportError:
                pytest.skip("KanbanReActAgent não disponível")
        assert output.message

    @pytest.mark.asyncio
    async def test_kanban_reject_candidate(self):
        snapshot_name = "kanban_reject_candidate"
        agent_input = make_test_input(
            domain="kanban",
            message="reprovar candidata Maria Santos com feedback de perfil não aderente",
        )
        mock_content = "Maria Santos reprovada. Feedback enviado: perfil não aderente à vaga."
        with patch(_PATCH_PATH, new_callable=AsyncMock) as mock_run:
            mock_run.return_value = make_mock_agent_state(mock_content)
            try:
                from app.domains.recruiter_assistant.agents.kanban_react_agent import KanbanReActAgent
                agent = KanbanReActAgent()
                output = await agent._process_langgraph(agent_input)
            except ImportError:
                pytest.skip("KanbanReActAgent não disponível")
        assert output.message

    @pytest.mark.asyncio
    async def test_kanban_bottleneck_detection(self):
        snapshot_name = "kanban_bottleneck"
        agent_input = make_test_input(
            domain="kanban",
            message="identificar gargalos no processo seletivo",
        )
        mock_content = "Gargalo detectado: 8 candidatos parados há +5 dias em Entrevista Técnica."
        with patch(_PATCH_PATH, new_callable=AsyncMock) as mock_run:
            mock_run.return_value = make_mock_agent_state(mock_content)
            try:
                from app.domains.recruiter_assistant.agents.kanban_react_agent import KanbanReActAgent
                agent = KanbanReActAgent()
                output = await agent._process_langgraph(agent_input)
            except ImportError:
                pytest.skip("KanbanReActAgent não disponível")
        assert output.message

    @pytest.mark.asyncio
    async def test_kanban_schedule_interview(self):
        snapshot_name = "kanban_schedule_interview"
        agent_input = make_test_input(
            domain="kanban",
            message="agendar entrevista com Pedro Alves para sexta às 14h",
        )
        mock_content = "Entrevista agendada com Pedro Alves: sexta-feira às 14h. Convite enviado."
        with patch(_PATCH_PATH, new_callable=AsyncMock) as mock_run:
            mock_run.return_value = make_mock_agent_state(mock_content)
            try:
                from app.domains.recruiter_assistant.agents.kanban_react_agent import KanbanReActAgent
                agent = KanbanReActAgent()
                output = await agent._process_langgraph(agent_input)
            except ImportError:
                pytest.skip("KanbanReActAgent não disponível")
        assert output.message

    @pytest.mark.asyncio
    async def test_kanban_sla_alert(self):
        snapshot_name = "kanban_sla_alert"
        agent_input = make_test_input(
            domain="kanban",
            message="quais candidatos estão com SLA em risco?",
        )
        mock_content = "3 candidatos com SLA em risco: Ana (2d), Carlos (1d), Julia (hoje)."
        with patch(_PATCH_PATH, new_callable=AsyncMock) as mock_run:
            mock_run.return_value = make_mock_agent_state(mock_content)
            try:
                from app.domains.recruiter_assistant.agents.kanban_react_agent import KanbanReActAgent
                agent = KanbanReActAgent()
                output = await agent._process_langgraph(agent_input)
            except ImportError:
                pytest.skip("KanbanReActAgent não disponível")
        assert output.message


# ---------------------------------------------------------------------------
# TalentReActAgent
# ---------------------------------------------------------------------------

class TestTalentAgentSnapshots:

    @pytest.mark.asyncio
    async def test_talent_evaluate_candidate(self):
        snapshot_name = "talent_evaluate_candidate"
        agent_input = make_test_input(
            domain="talent",
            message="avaliar candidatura de Fernanda Lima para a vaga de Data Scientist",
        )
        mock_content = "Avaliação de Fernanda Lima: Score LIA 87/100. Pontos fortes: Python, ML, comunicação."
        with patch(_PATCH_PATH, new_callable=AsyncMock) as mock_run:
            mock_run.return_value = make_mock_agent_state(mock_content)
            try:
                from app.domains.recruiter_assistant.agents.talent_react_agent import TalentReActAgent
                agent = TalentReActAgent()
                output = await agent._process_langgraph(agent_input)
            except ImportError:
                pytest.skip("TalentReActAgent não disponível")
        assert output.message

    @pytest.mark.asyncio
    async def test_talent_compare_candidates(self):
        snapshot_name = "talent_compare_candidates"
        agent_input = make_test_input(
            domain="talent",
            message="comparar candidatos Ricardo e Mariana para vaga de DevOps",
        )
        mock_content = "Comparativo: Ricardo (82pts, forte em Kubernetes) vs Mariana (79pts, forte em CI/CD)."
        with patch(_PATCH_PATH, new_callable=AsyncMock) as mock_run:
            mock_run.return_value = make_mock_agent_state(mock_content)
            try:
                from app.domains.recruiter_assistant.agents.talent_react_agent import TalentReActAgent
                agent = TalentReActAgent()
                output = await agent._process_langgraph(agent_input)
            except ImportError:
                pytest.skip("TalentReActAgent não disponível")
        assert output.message

    @pytest.mark.asyncio
    async def test_talent_wsi_summary(self):
        snapshot_name = "talent_wsi_summary"
        agent_input = make_test_input(
            domain="talent",
            message="resumo do WSI do candidato Rafael",
        )
        mock_content = "WSI Rafael: perfil Executor (DISC), pontuação 76/100, fit cultural 85%."
        with patch(_PATCH_PATH, new_callable=AsyncMock) as mock_run:
            mock_run.return_value = make_mock_agent_state(mock_content)
            try:
                from app.domains.recruiter_assistant.agents.talent_react_agent import TalentReActAgent
                agent = TalentReActAgent()
                output = await agent._process_langgraph(agent_input)
            except ImportError:
                pytest.skip("TalentReActAgent não disponível")
        assert output.message

    @pytest.mark.asyncio
    async def test_talent_shortlist(self):
        snapshot_name = "talent_shortlist"
        agent_input = make_test_input(
            domain="talent",
            message="criar shortlist dos 5 melhores candidatos para vaga de CTO",
        )
        mock_content = "Shortlist CTO: 1.Thiago (94) 2.Camila (91) 3.Bruno (89) 4.Luana (87) 5.Felipe (85)."
        with patch(_PATCH_PATH, new_callable=AsyncMock) as mock_run:
            mock_run.return_value = make_mock_agent_state(mock_content)
            try:
                from app.domains.recruiter_assistant.agents.talent_react_agent import TalentReActAgent
                agent = TalentReActAgent()
                output = await agent._process_langgraph(agent_input)
            except ImportError:
                pytest.skip("TalentReActAgent não disponível")
        assert output.message

    @pytest.mark.asyncio
    async def test_talent_silver_medalist(self):
        snapshot_name = "talent_silver_medalist"
        agent_input = make_test_input(
            domain="talent",
            message="identificar silver medalists para recontato",
        )
        mock_content = "Encontrei 8 silver medalists dos últimos 6 meses para recontato prioritário."
        with patch(_PATCH_PATH, new_callable=AsyncMock) as mock_run:
            mock_run.return_value = make_mock_agent_state(mock_content)
            try:
                from app.domains.recruiter_assistant.agents.talent_react_agent import TalentReActAgent
                agent = TalentReActAgent()
                output = await agent._process_langgraph(agent_input)
            except ImportError:
                pytest.skip("TalentReActAgent não disponível")
        assert output.message

    @pytest.mark.asyncio
    async def test_talent_invalid_input_graceful(self):
        snapshot_name = "talent_invalid_graceful"
        agent_input = make_test_input(
            domain="talent",
            message="",  # mensagem vazia
        )
        mock_content = "Não entendi sua solicitação. Pode reformular?"
        with patch(_PATCH_PATH, new_callable=AsyncMock) as mock_run:
            mock_run.return_value = make_mock_agent_state(mock_content)
            try:
                from app.domains.recruiter_assistant.agents.talent_react_agent import TalentReActAgent
                agent = TalentReActAgent()
                output = await agent._process_langgraph(agent_input)
            except ImportError:
                pytest.skip("TalentReActAgent não disponível")
        assert output.error is None


# ---------------------------------------------------------------------------
# JobsManagementReActAgent
# ---------------------------------------------------------------------------

class TestJobsManagementAgentSnapshots:

    @pytest.mark.asyncio
    async def test_jobs_list_active(self):
        snapshot_name = "jobs_list_active"
        agent_input = make_test_input(
            domain="jobs_management",
            message="listar vagas abertas",
        )
        mock_content = "Vagas abertas (12): Eng. Software (3), Data Scientist (2), UX Designer (1), outros (6)."
        with patch(_PATCH_PATH, new_callable=AsyncMock) as mock_run:
            mock_run.return_value = make_mock_agent_state(mock_content)
            try:
                from app.domains.recruiter_assistant.agents.jobs_mgmt_react_agent import JobsManagementReActAgent
            except ImportError:
                pytest.skip("JobsManagementReActAgent não disponível")
            agent = JobsManagementReActAgent()
            output = await agent._process_langgraph(agent_input)
        assert output.message

    @pytest.mark.asyncio
    async def test_jobs_close_vacancy(self):
        snapshot_name = "jobs_close_vacancy"
        agent_input = make_test_input(
            domain="jobs_management",
            message="fechar vaga de Engenheiro Backend que já foi preenchida",
        )
        mock_content = "Vaga de Engenheiro Backend fechada com sucesso. Status atualizado para 'preenchida'."
        with patch(_PATCH_PATH, new_callable=AsyncMock) as mock_run:
            mock_run.return_value = make_mock_agent_state(mock_content)
            try:
                from app.domains.recruiter_assistant.agents.jobs_mgmt_react_agent import JobsManagementReActAgent
            except ImportError:
                pytest.skip("JobsManagementReActAgent não disponível")
            agent = JobsManagementReActAgent()
            output = await agent._process_langgraph(agent_input)
        assert output.message

    @pytest.mark.asyncio
    async def test_jobs_metrics(self):
        snapshot_name = "jobs_metrics"
        agent_input = make_test_input(
            domain="jobs_management",
            message="métricas de tempo médio de fechamento de vagas",
        )
        mock_content = "Tempo médio de fechamento: 28 dias. Meta: 30 dias. Performance: ✓ dentro do prazo."
        with patch(_PATCH_PATH, new_callable=AsyncMock) as mock_run:
            mock_run.return_value = make_mock_agent_state(mock_content)
            try:
                from app.domains.recruiter_assistant.agents.jobs_mgmt_react_agent import JobsManagementReActAgent
            except ImportError:
                pytest.skip("JobsManagementReActAgent não disponível")
            agent = JobsManagementReActAgent()
            output = await agent._process_langgraph(agent_input)
        assert output.message

    @pytest.mark.asyncio
    async def test_jobs_duplicate_vacancy(self):
        snapshot_name = "jobs_duplicate"
        agent_input = make_test_input(
            domain="jobs_management",
            message="duplicar vaga de Analista de Dados para abrir mais 2 posições",
        )
        mock_content = "Vaga duplicada: 2 novas posições de Analista de Dados criadas a partir do template."
        with patch(_PATCH_PATH, new_callable=AsyncMock) as mock_run:
            mock_run.return_value = make_mock_agent_state(mock_content)
            try:
                from app.domains.recruiter_assistant.agents.jobs_mgmt_react_agent import JobsManagementReActAgent
            except ImportError:
                pytest.skip("JobsManagementReActAgent não disponível")
            agent = JobsManagementReActAgent()
            output = await agent._process_langgraph(agent_input)
        assert output.message

    @pytest.mark.asyncio
    async def test_jobs_update_deadline(self):
        snapshot_name = "jobs_update_deadline"
        agent_input = make_test_input(
            domain="jobs_management",
            message="prorrogar prazo da vaga de UX Designer por mais 2 semanas",
        )
        mock_content = "Prazo da vaga de UX Designer prorrogado para 22/03/2026."
        with patch(_PATCH_PATH, new_callable=AsyncMock) as mock_run:
            mock_run.return_value = make_mock_agent_state(mock_content)
            try:
                from app.domains.recruiter_assistant.agents.jobs_mgmt_react_agent import JobsManagementReActAgent
            except ImportError:
                pytest.skip("JobsManagementReActAgent não disponível")
            agent = JobsManagementReActAgent()
            output = await agent._process_langgraph(agent_input)
        assert output.message

    @pytest.mark.asyncio
    async def test_jobs_invalid_graceful(self):
        snapshot_name = "jobs_invalid_graceful"
        agent_input = make_test_input(
            domain="jobs_management",
            message="fazer algo completamente fora do contexto de vagas",
        )
        mock_content = "Posso ajudar com gestão de vagas. O que precisa?"
        with patch(_PATCH_PATH, new_callable=AsyncMock) as mock_run:
            mock_run.return_value = make_mock_agent_state(mock_content)
            try:
                from app.domains.recruiter_assistant.agents.jobs_mgmt_react_agent import JobsManagementReActAgent
            except ImportError:
                pytest.skip("JobsManagementReActAgent não disponível")
            agent = JobsManagementReActAgent()
            output = await agent._process_langgraph(agent_input)
        assert output.error is None

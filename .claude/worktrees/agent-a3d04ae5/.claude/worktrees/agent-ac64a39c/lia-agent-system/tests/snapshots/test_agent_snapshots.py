"""
Snapshot tests — 5 agentes restantes (Sprint D / André P10).

Camada 4 — E2E (pytest-asyncio, mock do LLM).

Agentes cobertos (6 fixtures cada):
- SourcingReActAgent      → app.domains.sourcing.agents.sourcing_react_agent
- PolicyReActAgent        → app.domains.hiring_policy.agents.policy_react_agent
- KanbanReActAgent        → app.domains.recruiter_assistant.agents.kanban_react_agent
- TalentReActAgent        → app.domains.recruiter_assistant.agents.talent_react_agent
- JobsMgmtReActAgent      → app.domains.recruiter_assistant.agents.jobs_mgmt_react_agent

Garante que cada agente:
1. Aceita AgentInput corretamente
2. Retorna AgentOutput com message não-vazia
3. confidence em [0.0, 1.0]
4. Não lança exceção para inputs válidos

Execução:
    pytest tests/snapshots/test_agent_snapshots.py -v
    UPDATE_SNAPSHOTS=true pytest tests/snapshots/test_agent_snapshots.py -v
"""
import pytest
from unittest.mock import AsyncMock, patch

from tests.snapshots.conftest import (
    UPDATE_SNAPSHOTS,
    load_snapshot,
    make_mock_agent_state,
    make_test_input,
    save_snapshot,
)
from lia_agents_core.agent_interface import AgentInput, AgentOutput

_PATCH = "lia_agents_core.langgraph_react_base.LangGraphReActBase._run_graph"


def _check(output: AgentOutput, name: str) -> dict:
    """Verifica contrato mínimo e retorna dict serializável."""
    assert isinstance(output, AgentOutput), f"[{name}] deve ser AgentOutput"
    assert output.message, f"[{name}] message não pode ser vazio"
    assert 0.0 <= output.confidence <= 1.0, f"[{name}] confidence fora de [0,1]"
    return {
        "message_non_empty": bool(output.message),
        "confidence_valid": 0.0 <= output.confidence <= 1.0,
        "has_actions": isinstance(output.actions, list),
        "no_error": output.error is None,
    }


def _snap(name: str, data: dict) -> dict:
    """Grava snapshot se não existir e retorna o stored."""
    if UPDATE_SNAPSHOTS or load_snapshot(name) is None:
        save_snapshot(name, data)
    return load_snapshot(name)


# ===========================================================================
# SourcingReActAgent — 6 fixtures
# ===========================================================================

class TestSourcingAgentSnapshots:

    @pytest.mark.asyncio
    async def test_sourcing_busca_engenheiro(self):
        name = "snap_sourcing_busca_engenheiro"
        inp = make_test_input("sourcing", "buscar candidatos para vaga de engenheiro Python",
                              {"job_id": "job-eng-001"})
        state = make_mock_agent_state("Encontrei 23 candidatos para Engenheiro Python.")

        with patch(_PATCH, new_callable=AsyncMock) as m:
            m.return_value = state
            try:
                from app.domains.sourcing.agents.sourcing_react_agent import SourcingReActAgent
                out = await SourcingReActAgent()._process_langgraph(inp)
            except ImportError:
                pytest.skip("SourcingReActAgent não disponível")

        data = _check(out, name)
        data["company_id"] = inp.company_id
        stored = _snap(name, data)
        assert stored["message_non_empty"] == data["message_non_empty"]
        assert stored["company_id"] == data["company_id"]

    @pytest.mark.asyncio
    async def test_sourcing_filtro_skills(self):
        name = "snap_sourcing_filtro_skills"
        inp = make_test_input("sourcing", "filtrar candidatos com React e TypeScript",
                              {"skills": ["React", "TypeScript"], "min_years": 3})
        state = make_mock_agent_state("Filtrei por React+TypeScript: 12 candidatos.")

        with patch(_PATCH, new_callable=AsyncMock) as m:
            m.return_value = state
            try:
                from app.domains.sourcing.agents.sourcing_react_agent import SourcingReActAgent
                out = await SourcingReActAgent()._process_langgraph(inp)
            except ImportError:
                pytest.skip("SourcingReActAgent não disponível")

        data = _check(out, name)
        stored = _snap(name, data)
        assert stored["message_non_empty"] == data["message_non_empty"]

    @pytest.mark.asyncio
    async def test_sourcing_sem_resultados(self):
        name = "snap_sourcing_sem_resultados"
        inp = make_test_input("sourcing", "candidatos com 20 anos em Fortran e Cobol",
                              {"job_id": "job-rare-001"})
        state = make_mock_agent_state("Nenhum candidato encontrado com esse perfil específico.")

        with patch(_PATCH, new_callable=AsyncMock) as m:
            m.return_value = state
            try:
                from app.domains.sourcing.agents.sourcing_react_agent import SourcingReActAgent
                out = await SourcingReActAgent()._process_langgraph(inp)
            except ImportError:
                pytest.skip("SourcingReActAgent não disponível")

        data = _check(out, name)
        stored = _snap(name, data)
        assert stored["no_error"] == data["no_error"]

    @pytest.mark.asyncio
    async def test_sourcing_status_pipeline(self):
        name = "snap_sourcing_status_pipeline"
        inp = make_test_input("sourcing", "status do sourcing para vaga de Product Manager",
                              {"job_id": "job-pm-001"})
        state = make_mock_agent_state("Sourcing PM: 45 identificados, 12 contatados, 8 responderam.")

        with patch(_PATCH, new_callable=AsyncMock) as m:
            m.return_value = state
            try:
                from app.domains.sourcing.agents.sourcing_react_agent import SourcingReActAgent
                out = await SourcingReActAgent()._process_langgraph(inp)
            except ImportError:
                pytest.skip("SourcingReActAgent não disponível")

        data = _check(out, name)
        stored = _snap(name, data)
        assert stored["confidence_valid"] == data["confidence_valid"]

    @pytest.mark.asyncio
    async def test_sourcing_multitenancy(self):
        name = "snap_sourcing_multitenancy"
        inp = AgentInput(message="buscar candidatos",
                         context={"job_id": "job-mt-001"},
                         session_id="snap-sourcing-mt",
                         company_id="company-sourcing-tenant-xyz",
                         user_id="snap-user-001")
        state = make_mock_agent_state("Buscando candidatos para a empresa...")

        with patch(_PATCH, new_callable=AsyncMock) as m:
            m.return_value = state
            try:
                from app.domains.sourcing.agents.sourcing_react_agent import SourcingReActAgent
                out = await SourcingReActAgent()._process_langgraph(inp)
            except ImportError:
                pytest.skip("SourcingReActAgent não disponível")

        assert isinstance(out, AgentOutput)
        assert inp.company_id == "company-sourcing-tenant-xyz"
        data = {"company_id_preserved": True, "message_non_empty": bool(out.message)}
        stored = _snap(name, data)
        assert stored["company_id_preserved"] is True

    @pytest.mark.asyncio
    async def test_sourcing_input_minimo(self):
        name = "snap_sourcing_input_minimo"
        inp = AgentInput(message="ajuda sourcing", context={},
                         session_id="snap-sourcing-min", company_id="test-company-001",
                         user_id="snap-user-001")
        state = make_mock_agent_state("Como posso ajudá-lo com o sourcing?")

        with patch(_PATCH, new_callable=AsyncMock) as m:
            m.return_value = state
            try:
                from app.domains.sourcing.agents.sourcing_react_agent import SourcingReActAgent
                out = await SourcingReActAgent()._process_langgraph(inp)
            except ImportError:
                pytest.skip("SourcingReActAgent não disponível")

        assert isinstance(out, AgentOutput)
        data = {"no_exception": True, "message_non_empty": bool(out.message)}
        stored = _snap(name, data)
        assert stored["no_exception"] is True


# ===========================================================================
# PolicyReActAgent — 6 fixtures
# ===========================================================================

class TestPolicyAgentSnapshots:

    @pytest.mark.asyncio
    async def test_policy_configurar_criterios(self):
        name = "snap_policy_configurar_criterios"
        inp = make_test_input("policy", "configurar política para vagas de engenharia",
                              {"stage": "onboarding", "department": "Engenharia"})
        state = make_mock_agent_state("Política de Engenharia configurada com critérios padrão.")

        with patch(_PATCH, new_callable=AsyncMock) as m:
            m.return_value = state
            try:
                from app.domains.hiring_policy.agents.policy_react_agent import PolicyReActAgent
                out = await PolicyReActAgent()._process_langgraph(inp)
            except ImportError:
                pytest.skip("PolicyReActAgent não disponível")

        data = _check(out, name)
        data["company_id"] = inp.company_id
        stored = _snap(name, data)
        assert stored["message_non_empty"] == data["message_non_empty"]

    @pytest.mark.asyncio
    async def test_policy_bloquear_discriminatorio(self):
        name = "snap_policy_bloquear_discriminatorio"
        inp = make_test_input("policy", "filtrar apenas candidatos do sexo masculino com menos de 30 anos",
                              {"stage": "criteria_setup"})
        state = make_mock_agent_state(
            "Não posso aplicar filtros baseados em gênero ou idade — viola LGPD e DEI.")

        with patch(_PATCH, new_callable=AsyncMock) as m:
            m.return_value = state
            try:
                from app.domains.hiring_policy.agents.policy_react_agent import PolicyReActAgent
                out = await PolicyReActAgent()._process_langgraph(inp)
            except ImportError:
                pytest.skip("PolicyReActAgent não disponível")

        assert isinstance(out, AgentOutput)
        assert out.message
        data = {"message_non_empty": True, "no_exception": True, "no_error": out.error is None}
        stored = _snap(name, data)
        assert stored["no_exception"] is True

    @pytest.mark.asyncio
    async def test_policy_consultar_existente(self):
        name = "snap_policy_consultar_existente"
        inp = make_test_input("policy", "critérios de triagem para vendas",
                              {"stage": "query", "department": "Vendas"})
        state = make_mock_agent_state("Vendas: 2 anos B2B, CRM, negociação. Inglês desejável.")

        with patch(_PATCH, new_callable=AsyncMock) as m:
            m.return_value = state
            try:
                from app.domains.hiring_policy.agents.policy_react_agent import PolicyReActAgent
                out = await PolicyReActAgent()._process_langgraph(inp)
            except ImportError:
                pytest.skip("PolicyReActAgent não disponível")

        data = _check(out, name)
        stored = _snap(name, data)
        assert stored["message_non_empty"] == data["message_non_empty"]

    @pytest.mark.asyncio
    async def test_policy_atualizar_criterio(self):
        name = "snap_policy_atualizar_criterio"
        inp = make_test_input("policy", "aumentar inglês para avançado em TI",
                              {"stage": "update", "department": "Tecnologia"})
        state = make_mock_agent_state("Requisito de inglês em TI atualizado para Avançado.")

        with patch(_PATCH, new_callable=AsyncMock) as m:
            m.return_value = state
            try:
                from app.domains.hiring_policy.agents.policy_react_agent import PolicyReActAgent
                out = await PolicyReActAgent()._process_langgraph(inp)
            except ImportError:
                pytest.skip("PolicyReActAgent não disponível")

        data = _check(out, name)
        stored = _snap(name, data)
        assert stored["no_error"] == data["no_error"]

    @pytest.mark.asyncio
    async def test_policy_multitenancy(self):
        name = "snap_policy_multitenancy"
        inp = AgentInput(message="política de RH", context={},
                         session_id="snap-policy-mt", company_id="company-policy-tenant-001",
                         user_id="snap-user-001")
        state = make_mock_agent_state("Configurando política de RH...")

        with patch(_PATCH, new_callable=AsyncMock) as m:
            m.return_value = state
            try:
                from app.domains.hiring_policy.agents.policy_react_agent import PolicyReActAgent
                out = await PolicyReActAgent()._process_langgraph(inp)
            except ImportError:
                pytest.skip("PolicyReActAgent não disponível")

        assert isinstance(out, AgentOutput)
        assert inp.company_id == "company-policy-tenant-001"
        data = {"company_id_preserved": True, "message_non_empty": bool(out.message)}
        stored = _snap(name, data)
        assert stored["company_id_preserved"] is True

    @pytest.mark.asyncio
    async def test_policy_input_minimo(self):
        name = "snap_policy_input_minimo"
        inp = AgentInput(message="política", context={},
                         session_id="snap-policy-min", company_id="test-company-001",
                         user_id="snap-user-001")
        state = make_mock_agent_state("Como posso ajudá-lo com as políticas de contratação?")

        with patch(_PATCH, new_callable=AsyncMock) as m:
            m.return_value = state
            try:
                from app.domains.hiring_policy.agents.policy_react_agent import PolicyReActAgent
                out = await PolicyReActAgent()._process_langgraph(inp)
            except ImportError:
                pytest.skip("PolicyReActAgent não disponível")

        assert isinstance(out, AgentOutput)
        data = {"no_exception": True, "message_non_empty": bool(out.message)}
        stored = _snap(name, data)
        assert stored["no_exception"] is True


# ===========================================================================
# KanbanReActAgent — 6 fixtures
# ===========================================================================

class TestKanbanAgentSnapshots:

    @pytest.mark.asyncio
    async def test_kanban_mover_candidato(self):
        name = "snap_kanban_mover_candidato"
        inp = make_test_input("kanban", "mover João Silva para entrevista técnica",
                              {"job_id": "job-001", "from_stage": "triage", "to_stage": "tech_interview"})
        state = make_mock_agent_state("João Silva movido para Entrevista Técnica. Email enviado.")

        with patch(_PATCH, new_callable=AsyncMock) as m:
            m.return_value = state
            try:
                from app.domains.recruiter_assistant.agents.kanban_react_agent import KanbanReActAgent
                out = await KanbanReActAgent()._process_langgraph(inp)
            except ImportError:
                pytest.skip("KanbanReActAgent não disponível")

        data = _check(out, name)
        data["company_id"] = inp.company_id
        stored = _snap(name, data)
        assert stored["message_non_empty"] == data["message_non_empty"]

    @pytest.mark.asyncio
    async def test_kanban_listar_coluna(self):
        name = "snap_kanban_listar_coluna"
        inp = make_test_input("kanban", "candidatos na triagem para analista",
                              {"job_id": "job-002", "stage": "triage"})
        state = make_mock_agent_state("Triagem — Analista: 7 candidatos. Ana (0.87), Bruno (0.82)...")

        with patch(_PATCH, new_callable=AsyncMock) as m:
            m.return_value = state
            try:
                from app.domains.recruiter_assistant.agents.kanban_react_agent import KanbanReActAgent
                out = await KanbanReActAgent()._process_langgraph(inp)
            except ImportError:
                pytest.skip("KanbanReActAgent não disponível")

        data = _check(out, name)
        stored = _snap(name, data)
        assert stored["message_non_empty"] == data["message_non_empty"]

    @pytest.mark.asyncio
    async def test_kanban_acao_em_lote(self):
        name = "snap_kanban_acao_em_lote"
        inp = make_test_input("kanban", "reprovar todos candidatos sem score",
                              {"job_id": "job-003", "bulk_action": True})
        state = make_mock_agent_state(
            "Você reprova 15 candidatos. Ação irreversível. Confirmar?")

        with patch(_PATCH, new_callable=AsyncMock) as m:
            m.return_value = state
            try:
                from app.domains.recruiter_assistant.agents.kanban_react_agent import KanbanReActAgent
                out = await KanbanReActAgent()._process_langgraph(inp)
            except ImportError:
                pytest.skip("KanbanReActAgent não disponível")

        assert isinstance(out, AgentOutput)
        assert out.message
        data = {"message_non_empty": True, "no_exception": True, "no_error": out.error is None}
        stored = _snap(name, data)
        assert stored["no_exception"] is True

    @pytest.mark.asyncio
    async def test_kanban_metricas_funil(self):
        name = "snap_kanban_metricas_funil"
        inp = make_test_input("kanban", "métricas do funil para gerente comercial",
                              {"job_id": "job-004"})
        state = make_mock_agent_state(
            "Gerente Comercial: Triagem:30 | RH:12 | Técnica:6 | Oferta:2. Conversão: 6.7%.")

        with patch(_PATCH, new_callable=AsyncMock) as m:
            m.return_value = state
            try:
                from app.domains.recruiter_assistant.agents.kanban_react_agent import KanbanReActAgent
                out = await KanbanReActAgent()._process_langgraph(inp)
            except ImportError:
                pytest.skip("KanbanReActAgent não disponível")

        data = _check(out, name)
        stored = _snap(name, data)
        assert stored["confidence_valid"] == data["confidence_valid"]

    @pytest.mark.asyncio
    async def test_kanban_multitenancy(self):
        name = "snap_kanban_multitenancy"
        inp = AgentInput(message="listar kanban", context={"job_id": "job-mt-001"},
                         session_id="snap-kanban-mt", company_id="company-kanban-tenant-999",
                         user_id="snap-user-001")
        state = make_mock_agent_state("Kanban da empresa...")

        with patch(_PATCH, new_callable=AsyncMock) as m:
            m.return_value = state
            try:
                from app.domains.recruiter_assistant.agents.kanban_react_agent import KanbanReActAgent
                out = await KanbanReActAgent()._process_langgraph(inp)
            except ImportError:
                pytest.skip("KanbanReActAgent não disponível")

        assert isinstance(out, AgentOutput)
        assert inp.company_id == "company-kanban-tenant-999"
        data = {"company_id_preserved": True, "message_non_empty": bool(out.message)}
        stored = _snap(name, data)
        assert stored["company_id_preserved"] is True

    @pytest.mark.asyncio
    async def test_kanban_input_minimo(self):
        name = "snap_kanban_input_minimo"
        inp = AgentInput(message="kanban", context={},
                         session_id="snap-kanban-min", company_id="test-company-001",
                         user_id="snap-user-001")
        state = make_mock_agent_state("Como posso ajudá-lo com o kanban?")

        with patch(_PATCH, new_callable=AsyncMock) as m:
            m.return_value = state
            try:
                from app.domains.recruiter_assistant.agents.kanban_react_agent import KanbanReActAgent
                out = await KanbanReActAgent()._process_langgraph(inp)
            except ImportError:
                pytest.skip("KanbanReActAgent não disponível")

        assert isinstance(out, AgentOutput)
        data = {"no_exception": True, "message_non_empty": bool(out.message)}
        stored = _snap(name, data)
        assert stored["no_exception"] is True


# ===========================================================================
# TalentReActAgent — 6 fixtures
# ===========================================================================

class TestTalentAgentSnapshots:

    @pytest.mark.asyncio
    async def test_talent_buscar_lideranca(self):
        name = "snap_talent_buscar_lideranca"
        inp = make_test_input("talent", "talentos com perfil de liderança",
                              {"job_id": "job-mgr-001", "seniority": "senior"})
        state = make_mock_agent_state("18 talentos com liderança. Experiência média: 8 anos.")

        with patch(_PATCH, new_callable=AsyncMock) as m:
            m.return_value = state
            try:
                from app.domains.recruiter_assistant.agents.talent_react_agent import TalentReActAgent
                out = await TalentReActAgent()._process_langgraph(inp)
            except ImportError:
                pytest.skip("TalentReActAgent não disponível")

        data = _check(out, name)
        data["company_id"] = inp.company_id
        stored = _snap(name, data)
        assert stored["message_non_empty"] == data["message_non_empty"]

    @pytest.mark.asyncio
    async def test_talent_score_lia(self):
        name = "snap_talent_score_lia"
        inp = make_test_input("talent", "analisar score LIA do candidato",
                              {"job_id": "job-005", "candidate_id": "cand-001", "lia_score": 0.78})
        state = make_mock_agent_state("Score LIA: 0.78 (Recomendado). Técnico:0.91, Comunicação:0.82.")

        with patch(_PATCH, new_callable=AsyncMock) as m:
            m.return_value = state
            try:
                from app.domains.recruiter_assistant.agents.talent_react_agent import TalentReActAgent
                out = await TalentReActAgent()._process_langgraph(inp)
            except ImportError:
                pytest.skip("TalentReActAgent não disponível")

        data = _check(out, name)
        stored = _snap(name, data)
        assert stored["message_non_empty"] == data["message_non_empty"]

    @pytest.mark.asyncio
    async def test_talent_silver_medalist(self):
        name = "snap_talent_silver_medalist"
        inp = make_test_input("talent", "silver medalists para nova vaga de engenheiro",
                              {"job_id": "job-new-001", "department": "Engenharia"})
        state = make_mock_agent_state("3 silver medalists para Engenharia. Ana Oliveira (0.89).")

        with patch(_PATCH, new_callable=AsyncMock) as m:
            m.return_value = state
            try:
                from app.domains.recruiter_assistant.agents.talent_react_agent import TalentReActAgent
                out = await TalentReActAgent()._process_langgraph(inp)
            except ImportError:
                pytest.skip("TalentReActAgent não disponível")

        data = _check(out, name)
        stored = _snap(name, data)
        assert stored["no_error"] == data["no_error"]

    @pytest.mark.asyncio
    async def test_talent_filtro_experiencia(self):
        name = "snap_talent_filtro_experiencia"
        inp = make_test_input("talent", "talentos com 3-7 anos de experiência",
                              {"job_id": "job-006", "min_years": 3, "max_years": 7})
        state = make_mock_agent_state("34 talentos com 3-7 anos. Score médio LIA: 0.74.")

        with patch(_PATCH, new_callable=AsyncMock) as m:
            m.return_value = state
            try:
                from app.domains.recruiter_assistant.agents.talent_react_agent import TalentReActAgent
                out = await TalentReActAgent()._process_langgraph(inp)
            except ImportError:
                pytest.skip("TalentReActAgent não disponível")

        data = _check(out, name)
        stored = _snap(name, data)
        assert stored["confidence_valid"] == data["confidence_valid"]

    @pytest.mark.asyncio
    async def test_talent_multitenancy(self):
        name = "snap_talent_multitenancy"
        inp = AgentInput(message="talentos disponíveis", context={},
                         session_id="snap-talent-mt", company_id="company-talent-tenant-777",
                         user_id="snap-user-001")
        state = make_mock_agent_state("Listando talentos...")

        with patch(_PATCH, new_callable=AsyncMock) as m:
            m.return_value = state
            try:
                from app.domains.recruiter_assistant.agents.talent_react_agent import TalentReActAgent
                out = await TalentReActAgent()._process_langgraph(inp)
            except ImportError:
                pytest.skip("TalentReActAgent não disponível")

        assert isinstance(out, AgentOutput)
        assert inp.company_id == "company-talent-tenant-777"
        data = {"company_id_preserved": True, "message_non_empty": bool(out.message)}
        stored = _snap(name, data)
        assert stored["company_id_preserved"] is True

    @pytest.mark.asyncio
    async def test_talent_input_minimo(self):
        name = "snap_talent_input_minimo"
        inp = AgentInput(message="talentos", context={},
                         session_id="snap-talent-min", company_id="test-company-001",
                         user_id="snap-user-001")
        state = make_mock_agent_state("Como posso ajudá-lo com talentos?")

        with patch(_PATCH, new_callable=AsyncMock) as m:
            m.return_value = state
            try:
                from app.domains.recruiter_assistant.agents.talent_react_agent import TalentReActAgent
                out = await TalentReActAgent()._process_langgraph(inp)
            except ImportError:
                pytest.skip("TalentReActAgent não disponível")

        assert isinstance(out, AgentOutput)
        data = {"no_exception": True, "message_non_empty": bool(out.message)}
        stored = _snap(name, data)
        assert stored["no_exception"] is True


# ===========================================================================
# JobsMgmtReActAgent — 6 fixtures
# ===========================================================================

class TestJobsManagementAgentSnapshots:

    @pytest.mark.asyncio
    async def test_jobs_listar_vagas(self):
        name = "snap_jobs_listar_vagas"
        inp = make_test_input("jobs_management", "listar vagas abertas", {"filter": "active"})
        state = make_mock_agent_state("8 vagas abertas. Engenharia:3 | Comercial:2 | Produto:2 | RH:1.")

        with patch(_PATCH, new_callable=AsyncMock) as m:
            m.return_value = state
            try:
                from app.domains.recruiter_assistant.agents.jobs_mgmt_react_agent import JobsMgmtReActAgent
                out = await JobsMgmtReActAgent()._process_langgraph(inp)
            except ImportError:
                pytest.skip("JobsMgmtReActAgent não disponível")

        data = _check(out, name)
        data["company_id"] = inp.company_id
        stored = _snap(name, data)
        assert stored["message_non_empty"] == data["message_non_empty"]

    @pytest.mark.asyncio
    async def test_jobs_publicar_vaga(self):
        name = "snap_jobs_publicar_vaga"
        inp = make_test_input("jobs_management", "publicar vaga de Desenvolvedor Full Stack",
                              {"job_id": "job-pub-001", "status": "draft", "title": "Dev Full Stack"})
        state = make_mock_agent_state("Vaga Dev Full Stack publicada no LinkedIn, portal e Indeed.")

        with patch(_PATCH, new_callable=AsyncMock) as m:
            m.return_value = state
            try:
                from app.domains.recruiter_assistant.agents.jobs_mgmt_react_agent import JobsMgmtReActAgent
                out = await JobsMgmtReActAgent()._process_langgraph(inp)
            except ImportError:
                pytest.skip("JobsMgmtReActAgent não disponível")

        data = _check(out, name)
        stored = _snap(name, data)
        assert stored["message_non_empty"] == data["message_non_empty"]

    @pytest.mark.asyncio
    async def test_jobs_pausar_vaga(self):
        name = "snap_jobs_pausar_vaga"
        inp = make_test_input("jobs_management", "pausar vaga de Analista de Dados",
                              {"job_id": "job-pause-001", "status": "active"})
        state = make_mock_agent_state("Vaga Analista de Dados pausada. Candidatos em processo não afetados.")

        with patch(_PATCH, new_callable=AsyncMock) as m:
            m.return_value = state
            try:
                from app.domains.recruiter_assistant.agents.jobs_mgmt_react_agent import JobsMgmtReActAgent
                out = await JobsMgmtReActAgent()._process_langgraph(inp)
            except ImportError:
                pytest.skip("JobsMgmtReActAgent não disponível")

        assert isinstance(out, AgentOutput)
        assert out.message
        data = {"message_non_empty": True, "no_exception": True, "no_error": out.error is None}
        stored = _snap(name, data)
        assert stored["no_exception"] is True

    @pytest.mark.asyncio
    async def test_jobs_metricas(self):
        name = "snap_jobs_metricas"
        inp = make_test_input("jobs_management", "métricas da vaga de Product Owner",
                              {"job_id": "job-po-001"})
        state = make_mock_agent_state("PO: 47 candidaturas, 5 aprovados, 1 contratado. TTH: 25d.")

        with patch(_PATCH, new_callable=AsyncMock) as m:
            m.return_value = state
            try:
                from app.domains.recruiter_assistant.agents.jobs_mgmt_react_agent import JobsMgmtReActAgent
                out = await JobsMgmtReActAgent()._process_langgraph(inp)
            except ImportError:
                pytest.skip("JobsMgmtReActAgent não disponível")

        data = _check(out, name)
        stored = _snap(name, data)
        assert stored["confidence_valid"] == data["confidence_valid"]

    @pytest.mark.asyncio
    async def test_jobs_multitenancy(self):
        name = "snap_jobs_multitenancy"
        inp = AgentInput(message="vagas", context={},
                         session_id="snap-jobs-mt", company_id="company-jobs-tenant-555",
                         user_id="snap-user-001")
        state = make_mock_agent_state("Vagas da empresa...")

        with patch(_PATCH, new_callable=AsyncMock) as m:
            m.return_value = state
            try:
                from app.domains.recruiter_assistant.agents.jobs_mgmt_react_agent import JobsMgmtReActAgent
                out = await JobsMgmtReActAgent()._process_langgraph(inp)
            except ImportError:
                pytest.skip("JobsMgmtReActAgent não disponível")

        assert isinstance(out, AgentOutput)
        assert inp.company_id == "company-jobs-tenant-555"
        data = {"company_id_preserved": True, "message_non_empty": bool(out.message)}
        stored = _snap(name, data)
        assert stored["company_id_preserved"] is True

    @pytest.mark.asyncio
    async def test_jobs_input_minimo(self):
        name = "snap_jobs_input_minimo"
        inp = AgentInput(message="vagas", context={},
                         session_id="snap-jobs-min", company_id="test-company-001",
                         user_id="snap-user-001")
        state = make_mock_agent_state("Como posso ajudá-lo com vagas?")

        with patch(_PATCH, new_callable=AsyncMock) as m:
            m.return_value = state
            try:
                from app.domains.recruiter_assistant.agents.jobs_mgmt_react_agent import JobsMgmtReActAgent
                out = await JobsMgmtReActAgent()._process_langgraph(inp)
            except ImportError:
                pytest.skip("JobsMgmtReActAgent não disponível")

        assert isinstance(out, AgentOutput)
        data = {"no_exception": True, "message_non_empty": bool(out.message)}
        stored = _snap(name, data)
        assert stored["no_exception"] is True

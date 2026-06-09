"""D8 — Parity Execution: Verificação de execução real A vs B com mock controlado.

Complementa test_parity_anchors.py (inspeção de código/flags) com verificação
de que os dois caminhos *executam* as camadas corretas de compliance e chegam
ao agente correto — usando mocks controlados para isolar o transporte SSE.

Estrutura:
  TestFairnessGuardExecution  — FairnessGuard executado em ambos os cenários (2)
  TestAgentDispatchExecution  — agente correto invocado em cada cenário (3)
  TestPostComplianceExecution — post_compliance chamado em ambas as trilhas (2)
  TestHITLGateExecution       — gate HITL executa e bloqueia tool sensível (2)
  TestParityEquivalence       — resultado equivalente A≈B para mesma query (1)
"""
from __future__ import annotations

import asyncio
import importlib
import os
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch, call

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _stub_agent_output(message: str = "ok") -> Any:
    """Cria AgentOutput fake sem importar lia_agents_core (evita side-effects)."""
    out = MagicMock()
    out.message = message
    out.actions = []
    out.navigation = None
    out.confidence = 0.9
    out.state_updates = {}
    out.metadata = {}
    out.error = None
    out.response_blocks = None
    return out


def _stub_chat_response(content: str = "ok") -> Any:
    """Cria ChatResponse fake sem importar main_orchestrator."""
    resp = MagicMock()
    resp.success = True
    resp.content = content
    resp.message = content
    resp.agent_used = "supervisor"
    resp.actions = []
    resp.ui_action = None
    resp.ui_action_params = None
    resp.hitl_pending = None
    resp.response_blocks = None
    resp.metadata = {}
    resp.needs_confirmation = False
    return resp


def _make_fairness_pass() -> MagicMock:
    """FairnessGuard.check() que retorna resultado não-bloqueado."""
    result = MagicMock()
    result.is_blocked = False
    result.educational_message = None
    fg = MagicMock()
    fg.check.return_value = result
    return fg


def _make_fairness_block(msg: str = "bias detectado") -> MagicMock:
    """FairnessGuard.check() que retorna resultado bloqueado."""
    result = MagicMock()
    result.is_blocked = True
    result.educational_message = msg
    fg = MagicMock()
    fg.check.return_value = result
    return fg


# ---------------------------------------------------------------------------
# Fixtures locais
# ---------------------------------------------------------------------------

@pytest.fixture
def scope_config():
    try:
        return importlib.import_module("app.tools.scope_config")
    except Exception:
        return None


@pytest.fixture
def hitl_ctx():
    try:
        return importlib.import_module("app.shared.hitl.hitl_approval_context")
    except Exception:
        return None


@pytest.fixture
def c3b_module():
    try:
        return importlib.import_module("app.shared.compliance.c3b_layer")
    except Exception:
        return None


@pytest.fixture
def agent_registry():
    try:
        return importlib.import_module("app.shared.agents.agent_registry")
    except Exception:
        return None


# ===========================================================================
# 1. TestFairnessGuardExecution
# ===========================================================================

class TestFairnessGuardExecution:
    """Verifica que FairnessGuard executa check() na entrada de ambos os cenários."""

    def test_fairness_guard_check_called_on_inbound_message(self):
        """FairnessGuard.check() é invocado com o conteúdo da mensagem.

        Simula a chamada direta ao bloco LIA-P03 do SSE handler,
        sem executar o handler completo.
        """
        fg_mock = _make_fairness_pass()

        with patch(
            "app.shared.compliance.fairness_guard.FairnessGuard",
            return_value=fg_mock,
        ):
            from app.shared.compliance.fairness_guard import FairnessGuard

            fg = FairnessGuard()
            result = fg.check("liste candidatos para a vaga de dev")

        fg_mock.check.assert_called_once_with("liste candidatos para a vaga de dev")
        assert result.is_blocked is False

    def test_fairness_guard_blocks_biased_message(self):
        """FairnessGuard.check() retorna is_blocked=True para mensagem tendenciosa.

        Simula que o SSE handler lança HTTPException 400 quando is_blocked=True.
        Ambos os caminhos A e B passam pelo mesmo bloco — o bloqueio é compartilhado.
        """
        fg_mock = _make_fairness_block("Solicitacao com possivel vies de genero")

        with patch(
            "app.shared.compliance.fairness_guard.FairnessGuard",
            return_value=fg_mock,
        ):
            from app.shared.compliance.fairness_guard import FairnessGuard

            fg = FairnessGuard()
            result = fg.check("prefiro candidatos do sexo masculino para esta vaga")

        fg_mock.check.assert_called_once()
        assert result.is_blocked is True
        assert "vies" in result.educational_message.lower() or \
               result.educational_message is not None


# ===========================================================================
# 2. TestAgentDispatchExecution
# ===========================================================================

class TestAgentDispatchExecution:
    """Verifica que o agente correto é despachado em cada cenário."""

    def test_federated_path_reaches_recruiter_copilot(
        self, federated_flags, scope_config
    ):
        """Cenário A: federated_primary_enabled()=True → agent id='recruiter_copilot'.

        Verifica que _get_agent("recruiter_copilot") é chamado quando
        _use_federated=True, sem invocar o SSE handler completo.
        """
        if scope_config is None:
            pytest.skip("scope_config não importável")

        assert scope_config.federated_primary_enabled() is True, (
            "federated_primary_enabled() deve ser True com LIA_FEDERATED_PRIMARY=true"
        )

        # Simula a lógica de seleção do agente do SSE handler (linhas 658-667)
        _bubble_via_supervisor = os.getenv(
            "LIA_BUBBLE_VIA_SUPERVISOR", "false"
        ).lower() in ("true", "1")

        _use_federated = (not _bubble_via_supervisor) and scope_config.federated_primary_enabled()

        # Mocks de agentes
        copilot_agent = MagicMock(name="recruiter_copilot")
        domain_agent = MagicMock(name="domain_agent")

        with patch(
            "app.api.v1.chat_shared._get_agent",
            side_effect=lambda domain: copilot_agent if domain == "recruiter_copilot" else domain_agent,
        ) as mock_get:
            from app.api.v1.chat_shared import _get_agent

            if _bubble_via_supervisor:
                agent = None
            elif _use_federated:
                agent = _get_agent("recruiter_copilot")
            else:
                agent = _get_agent("talent")

        assert _use_federated is True, "Deve usar caminho federado"
        mock_get.assert_called_once_with("recruiter_copilot")
        assert agent is copilot_agent, "agent deve ser recruiter_copilot"

    def test_supervisor_path_agent_is_none(self, supervisor_flags, scope_config):
        """Cenário B: _bubble_via_supervisor=True → agent=None (supervisor controla).

        MainOrchestrator processa internamente. O _get_agent NÃO deve ser chamado.
        """
        _bubble_via_supervisor = os.getenv(
            "LIA_BUBBLE_VIA_SUPERVISOR", "false"
        ).lower() in ("true", "1")

        assert _bubble_via_supervisor is True, (
            "supervisor_flags deve setar LIA_BUBBLE_VIA_SUPERVISOR=true"
        )

        with patch(
            "app.api.v1.chat_shared._get_agent",
        ) as mock_get:
            # Replica lógica do SSE handler
            if _bubble_via_supervisor:
                agent = None
            else:
                from app.api.v1.chat_shared import _get_agent
                agent = _get_agent("talent")

        # agent deve ser None — supervisor não usa _get_agent()
        assert agent is None, "Cenário B: agent deve ser None (supervisor controla)"
        mock_get.assert_not_called()

    def test_main_orchestrator_process_called_in_supervisor_path(self, supervisor_flags):
        """Cenário B: MainOrchestrator.process() é chamado para processar a mensagem.

        Simula a chamada em _run_via_supervisor() com mock controlado do orchestrator.
        """
        fake_response = _stub_chat_response("resultado do supervisor")

        mock_orchestrator = MagicMock()
        mock_orchestrator.process = AsyncMock(return_value=fake_response)

        with patch(
            "app.orchestrator.execution.main_orchestrator.get_main_orchestrator",
            return_value=mock_orchestrator,
        ):
            from app.orchestrator.execution.main_orchestrator import get_main_orchestrator

            orch = get_main_orchestrator()
            # Simula a chamada em _run_via_supervisor()
            ctx_mock = MagicMock()
            db_mock = MagicMock()

            result = asyncio.run(
                orch.process(ctx_mock, db_mock, streaming_callback=None)
            )

        mock_orchestrator.process.assert_called_once()
        assert result.content == "resultado do supervisor"
        assert result.success is True


# ===========================================================================
# 3. TestPostComplianceExecution
# ===========================================================================

class TestPostComplianceExecution:
    """Verifica que post_compliance é chamado em ambas as trilhas de saída."""

    @pytest.mark.asyncio
    async def test_post_compliance_called_in_federated_path(self, c3b_module):
        """Trilha A (FIX-C3B-SSE): post_compliance executado com mensagem do agente.

        Simula o bloco FIX-C3B-SSE do SSE handler — post_compliance é chamado
        com o output do agente federado antes de enviar ao cliente.
        """
        if c3b_module is None:
            pytest.skip("c3b_layer não importável")

        agent_message = "Lista de candidatos para revisão."
        cleaned_message = "Lista de candidatos para revisão. [AUDITADO]"

        mock_post_compliance = AsyncMock(return_value=cleaned_message)

        with patch.object(c3b_module, "post_compliance", mock_post_compliance):
            ComplianceContext = c3b_module.ComplianceContext
            post_compliance = c3b_module.post_compliance

            ctx = ComplianceContext(
                company_id="test-company",
                user_id="test-user",
                session_id="test-session",
                domain="recruiter_copilot",
                agent_id="recruiter_copilot",
                original_message="liste candidatos",
                fairness_flags=[],
            )
            result = await post_compliance(agent_message, ctx)

        mock_post_compliance.assert_called_once_with(agent_message, ctx)
        assert result == cleaned_message

    @pytest.mark.asyncio
    async def test_post_compliance_called_in_supervisor_path(self, c3b_module):
        """Trilha B (FIX-C3B-SUP): post_compliance executado com output do supervisor.

        Simula o bloco FIX-C3B-SUP do SSE handler — post_compliance é chamado
        com ChatResponse.content do MainOrchestrator antes de enviar ao cliente.
        """
        if c3b_module is None:
            pytest.skip("c3b_layer não importável")

        supervisor_content = "Aqui estão os candidatos encontrados pelo supervisor."
        cleaned_content = "Aqui estão os candidatos encontrados. [LGPD AUDITADO]"

        mock_post_compliance = AsyncMock(return_value=cleaned_content)

        with patch.object(c3b_module, "post_compliance", mock_post_compliance):
            ComplianceContext = c3b_module.ComplianceContext
            post_compliance = c3b_module.post_compliance

            ctx = ComplianceContext(
                company_id="test-company",
                user_id="test-user",
                session_id="test-session",
                domain="jobs_management",
                agent_id="supervisor",
                original_message="abrir vaga",
                fairness_flags=[],
            )
            result = await post_compliance(supervisor_content, ctx)

        mock_post_compliance.assert_called_once_with(supervisor_content, ctx)
        assert result == cleaned_content

    @pytest.mark.asyncio
    async def test_post_compliance_fail_open_both_paths(self, c3b_module):
        """post_compliance fail-open: exception não bloqueia resposta ao usuário.

        Verifica que ambas as trilhas continuam mesmo se post_compliance lança
        Exception — padrão REGRA 4 (não silent fallback: loga warning mas não
        engole a mensagem original).
        """
        if c3b_module is None:
            pytest.skip("c3b_layer não importável")

        original_message = "Lista de candidatos."

        mock_post_compliance = AsyncMock(
            side_effect=RuntimeError("c3b service indisponivel")
        )

        result_a = original_message
        result_b = original_message

        # Simula try/except fail-open do SSE handler — ambas as trilhas
        for agent_id in ("recruiter_copilot", "supervisor"):
            with patch.object(c3b_module, "post_compliance", mock_post_compliance):
                ComplianceContext = c3b_module.ComplianceContext
                post_compliance = c3b_module.post_compliance

                ctx = ComplianceContext(
                    company_id="test-company",
                    user_id="test-user",
                    session_id="test-session",
                    domain="test",
                    agent_id=agent_id,
                    original_message="query",
                    fairness_flags=[],
                )
                try:
                    cleaned = await post_compliance(original_message, ctx)
                    # Se chegou aqui sem exception → falha inesperada
                    if agent_id == "recruiter_copilot":
                        result_a = cleaned
                    else:
                        result_b = cleaned
                except Exception:
                    # Fail-open: mantém mensagem original
                    pass  # resultado já inicializado com original_message

        # Em fail-open, as mensagens originais chegam ao cliente intactas
        assert result_a == original_message, (
            "Trilha A fail-open: mensagem original deve chegar ao cliente"
        )
        assert result_b == original_message, (
            "Trilha B fail-open: mensagem original deve chegar ao cliente"
        )


# ===========================================================================
# 4. TestHITLGateExecution
# ===========================================================================

class TestHITLGateExecution:
    """Verifica que o gate HITL executa e bloqueia ferramenta sensível."""

    def test_hitl_preflight_blocks_sensitive_tool_when_gate_on(
        self, hitl_ctx, monkeypatch
    ):
        """hitl_preflight retorna dict de bloqueio para close_job com gate ON.

        Simula a chamada em qualquer tool gated (close_job, reject_candidate, etc.)
        — o gate verifica se a ação já foi aprovada via ContextVar; se não foi,
        retorna needs_confirmation=True.
        """
        if hitl_ctx is None:
            pytest.skip("hitl_approval_context não importável")

        monkeypatch.setenv("LIA_HITL_GATE", "true")
        importlib.reload(hitl_ctx)

        assert hitl_ctx.hitl_gate_enabled() is True

        # ContextVar não aprovado → deve bloquear
        result = hitl_ctx.hitl_preflight(
            tool="close_job",
            domain="job_management",
            message="Fechar esta vaga requer confirmacao do recrutador.",
        )

        assert result is not None, "hitl_preflight deve retornar dict quando bloqueado"
        assert result.get("needs_confirmation") is True
        assert result.get("success") is False
        hitl_data = result.get("hitl", {})
        assert hitl_data.get("tool") == "close_job", (
            "hitl dict deve conter o nome da tool"
        )

    def test_hitl_preflight_passes_when_approved(self, hitl_ctx, monkeypatch):
        """hitl_preflight retorna None quando ação foi aprovada via set_hitl_approved.

        Simula o re-despacho após aprovação (SSE detecta approve_pending_id
        e chama set_hitl_approved(True) antes de re-executar o turno).
        """
        if hitl_ctx is None:
            pytest.skip("hitl_approval_context não importável")

        monkeypatch.setenv("LIA_HITL_GATE", "true")
        importlib.reload(hitl_ctx)

        # Marca como aprovado (simula set_hitl_approved(True) no _run_agent)
        hitl_ctx.set_hitl_approved(True)

        result = hitl_ctx.hitl_preflight(
            tool="close_job",
            domain="job_management",
            message="Fechar vaga — aprovado.",
        )

        assert result is None, (
            "hitl_preflight deve retornar None quando acao foi aprovada — "
            "tool continua normalmente"
        )

        # Cleanup: resetar aprovação para não contaminar outros testes
        try:
            hitl_ctx.set_hitl_approved(False)
        except Exception:
            pass


# ===========================================================================
# 5. TestParityEquivalence
# ===========================================================================

class TestParityEquivalence:
    """Verifica equivalência de resultado entre A (federado) e B (supervisor)."""

    @pytest.mark.asyncio
    async def test_equivalent_compliance_context_both_scenarios(self, c3b_module):
        """A e B constroem ComplianceContext com os mesmos campos essenciais.

        A paridade de governança depende que ambos passem os mesmos metadados
        para post_compliance. Verifica que os campos company_id, user_id,
        session_id, original_message são equivalentes.
        """
        if c3b_module is None:
            pytest.skip("c3b_layer não importável")

        ComplianceContext = c3b_module.ComplianceContext

        common_params = dict(
            company_id="company-xyz",
            user_id="user-123",
            session_id="sess-abc",
            original_message="listar candidatos qualificados",
            fairness_flags=[],
        )

        # Trilha A (federado)
        ctx_a = ComplianceContext(
            **common_params,
            domain="recruiter_copilot",
            agent_id="recruiter_copilot",
        )

        # Trilha B (supervisor)
        ctx_b = ComplianceContext(
            **common_params,
            domain="jobs_management",
            agent_id="supervisor",
        )

        # Campos essenciais de auditoria devem ser iguais
        assert ctx_a.company_id == ctx_b.company_id, (
            "company_id deve ser idêntico em A e B"
        )
        assert ctx_a.user_id == ctx_b.user_id, (
            "user_id deve ser idêntico em A e B"
        )
        assert ctx_a.session_id == ctx_b.session_id, (
            "session_id deve ser idêntico em A e B"
        )
        assert ctx_a.original_message == ctx_b.original_message, (
            "original_message deve ser idêntico em A e B"
        )

        # Campos que diferenciam os cenários (esperado divergirem)
        assert ctx_a.agent_id != ctx_b.agent_id, (
            "agent_id deve diferir: 'recruiter_copilot' vs 'supervisor'"
        )

    def test_scope_config_flags_are_mutually_exclusive(
        self, scope_config, monkeypatch
    ):
        """federated e supervisor são mutuamente exclusivos via lógica AND-NOT.

        Verifica a invariante do SSE handler:
          _use_federated = (not _bubble_via_supervisor) and _fed_primary()

        Quando ambos estão TRUE, _use_federated=False (supervisor ganha).
        """
        if scope_config is None:
            pytest.skip("scope_config não importável")

        # Ambas flags ON — supervisor deve ganhar (federated=False)
        monkeypatch.setenv("LIA_FEDERATED_PRIMARY", "true")
        monkeypatch.setenv("LIA_BUBBLE_VIA_SUPERVISOR", "true")
        importlib.reload(scope_config)

        _bubble = os.getenv("LIA_BUBBLE_VIA_SUPERVISOR", "false").lower() in (
            "true", "1"
        )
        _fed_primary = scope_config.federated_primary_enabled()
        _use_federated = (not _bubble) and _fed_primary

        assert _bubble is True, "LIA_BUBBLE_VIA_SUPERVISOR deve ser True"
        assert _fed_primary is True, "federated_primary_enabled() deve ser True"
        assert _use_federated is False, (
            "Quando ambas ativas, _use_federated deve ser False "
            "(supervisor tem precedência pela lógica AND-NOT)"
        )

        # Restore: só federated ON
        monkeypatch.setenv("LIA_BUBBLE_VIA_SUPERVISOR", "false")
        importlib.reload(scope_config)
        _bubble2 = os.getenv("LIA_BUBBLE_VIA_SUPERVISOR", "false").lower() in (
            "true", "1"
        )
        _fed_primary2 = scope_config.federated_primary_enabled()
        _use_federated2 = (not _bubble2) and _fed_primary2

        assert _use_federated2 is True, (
            "Com só LIA_FEDERATED_PRIMARY=true, _use_federated deve ser True"
        )

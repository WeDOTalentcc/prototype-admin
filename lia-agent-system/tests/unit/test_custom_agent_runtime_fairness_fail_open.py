"""TDD P0-4: FairnessGuard fail-closed no CustomAgentRuntime + audit trail.

Dois problemas confirmados em custom_agent_runtime.py (2026-06-14):

  Camada 3A (input, execute() linhas 824-835):
    except Exception: pass
    — silencia crash do guard, execução continua, log_check() nunca chamado.

  Camada 3B (output tool, _tenant_safe_wrapper linhas 322-323):
    except Exception as _fg_exc: logger.warning(...)
    — fail-open quando guard crasha, log_check() nunca chamado mesmo quando
    result.is_blocked=True.

Fix canônico: espelhar Fix A de 2026-06-14 em agent_chat_sse.py:
  - Crash do guard → logger.error + retorno de bloqueio (fail-closed)
  - result.is_blocked → log_check() com company_id/agent_id/session_id
"""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ─── Fixture canônica: previne RuntimeError do checkpointer em production ───

@pytest.fixture(autouse=True)
def _patch_checkpointer_and_tenant():
    """Padrão canônico: substitui get_checkpointer() + _get_tenant_context_snippet.

    Em APP_ENV=production, get_checkpointer() levanta RuntimeError antes de
    initialize_checkpointer_async(). Testes unitários mocam _process_langgraph
    separadamente — o checkpointer real não é exercido.
    """
    from unittest.mock import patch as _patch, AsyncMock as _AsyncMock
    with (
        _patch("lia_agents_core.langgraph_base.get_checkpointer", return_value=None),
        _patch(
            "app.shared.agents.tenant_aware_agent.TenantAwareAgentMixin._get_tenant_context_snippet",
            new_callable=_AsyncMock,
            return_value="",
        ),
    ):
        yield


# ─── helpers ────────────────────────────────────────────────────────────────

def _make_runtime(company_id: str = "comp-1"):
    from app.domains.agent_studio.custom_agent_runtime import CustomAgentRuntime
    return CustomAgentRuntime(
        agent_id="ag-test",
        agent_name="TestAgent",
        system_prompt="Você é um assistente.",
        allowed_tools=[],
        company_id=company_id,
    )


def _make_ok_agent_output():
    out = MagicMock()
    out.message = "Resposta normal."
    out.confidence = 0.9
    out.metadata = {}
    out.actions = []
    out.reasoning_trace = None
    return out


def _make_blocked_fg_result(category: str = "gender"):
    r = MagicMock()
    r.is_blocked = True
    r.category = category
    r.educational_message = "Critério discriminatório detectado."
    return r


def _make_ok_fg_result():
    r = MagicMock()
    r.is_blocked = False
    r.category = None
    r.educational_message = None
    return r


# ─── Camada 3A (input, execute()) ───────────────────────────────────────────

class TestFairnessGuard3AInputFailClosed:
    """FairnessGuard no caminho de input em execute() deve ser fail-closed."""

    @pytest.mark.asyncio
    async def test_guard_crash_blocks_execution(self):
        """Se FairnessGuard.check() lança RuntimeError, execute() deve
        ser BLOQUEADO (fail-closed) — não continuar silenciosamente."""
        runtime = _make_runtime()

        mock_output = _make_ok_agent_output()

        with patch(
            "app.shared.compliance.fairness_guard.FairnessGuard.check",
            side_effect=RuntimeError("guard_crash"),
        ), patch.object(
            runtime, "_process_langgraph",
            new=AsyncMock(return_value=mock_output),
        ):
            output = await runtime.execute(
                message="teste",
                user_id="u1",
                company_id="comp-1",
                session_id="sess-1",
            )

        # _process_langgraph NÃO deve ter sido chamado (guard falhou antes)
        # OU output deve indicar bloqueio/erro
        assert (
            output.metadata.get("blocked") is True
            or output.metadata.get("error") is not None
            or output.metadata.get("compliance_check_failed") is True
        ), (
            "execute() deve ser fail-closed quando FairnessGuard crasha. "
            f"Metadata atual: {output.metadata}"
        )

    @pytest.mark.asyncio
    async def test_guard_crash_logs_error_not_silent(self):
        """Crash do FairnessGuard deve ser logado com logger.error —
        o padrão 'except Exception: pass' silencia o erro (P0-4)."""
        runtime = _make_runtime()

        mock_output = _make_ok_agent_output()

        with patch(
            "app.shared.compliance.fairness_guard.FairnessGuard.check",
            side_effect=RuntimeError("guard_crash_test"),
        ), patch.object(
            runtime, "_process_langgraph",
            new=AsyncMock(return_value=mock_output),
        ), patch(
            "app.domains.agent_studio.custom_agent_runtime.logger",
        ) as mock_logger:
            await runtime.execute(
                message="teste",
                user_id="u1",
                company_id="comp-1",
                session_id="sess-1",
            )

        # Deve chamar logger.error (não apenas warning ou silence)
        assert mock_logger.error.called, (
            "Crash do FairnessGuard deve gerar logger.error — "
            "'except Exception: pass' silencia o crash (P0-4)"
        )

    @pytest.mark.asyncio
    async def test_guard_blocked_returns_blocked_output(self):
        """Quando FairnessGuard.is_blocked=True, execute() deve retornar
        AgentOutput com metadata.blocked=True e não continuar o processamento."""
        runtime = _make_runtime()

        blocked = _make_blocked_fg_result()
        mock_output = _make_ok_agent_output()
        mock_process = AsyncMock(return_value=mock_output)

        with patch(
            "app.shared.compliance.fairness_guard.FairnessGuard.check",
            return_value=blocked,
        ), patch.object(
            runtime, "_process_langgraph",
            new=mock_process,
        ):
            output = await runtime.execute(
                message="prefiro candidatos homens",
                user_id="u1",
                company_id="comp-1",
                session_id="sess-1",
            )

        # execute() já fazia isso corretamente — não deve ter regredido
        assert output.metadata.get("blocked") is True, (
            "execute() deve retornar metadata.blocked=True quando FairnessGuard bloqueia"
        )
        # _process_langgraph NÃO deve ter sido chamado
        assert not mock_process.called, (
            "_process_langgraph não deve ser chamado quando FairnessGuard bloqueia"
        )

    @pytest.mark.asyncio
    async def test_guard_blocked_calls_log_check_for_audit_trail(self):
        """Quando FairnessGuard.is_blocked=True, log_check() DEVE ser chamado
        com company_id e session_id para popular o FairnessAuditLog.

        Atualmente NÃO é chamado — este teste deve FALHAR (Red) antes do fix."""
        runtime = _make_runtime(company_id="comp-audit-3a")
        blocked = _make_blocked_fg_result(category="race")

        mock_log_check = AsyncMock()
        mock_output = _make_ok_agent_output()

        with patch(
            "app.shared.compliance.fairness_guard.FairnessGuard.check",
            return_value=blocked,
        ), patch(
            "app.shared.compliance.fairness_guard.FairnessGuard.log_check",
            new=mock_log_check,
        ), patch.object(
            runtime, "_process_langgraph",
            new=AsyncMock(return_value=mock_output),
        ):
            output = await runtime.execute(
                message="prefiro candidatos brancos",
                user_id="u1",
                company_id="comp-audit-3a",
                session_id="sess-audit-3a",
            )

        assert output.metadata.get("blocked") is True, (
            "Pré-condição: execute() deve bloquear"
        )
        assert mock_log_check.called, (
            "log_check() DEVE ser chamado quando FairnessGuard bloqueia na camada 3A — "
            "sem isso o bloqueio não fica no FairnessAuditLog (Fix A espelhado, P0-4)"
        )
        # Verificar que company_id foi passado
        all_args = str(mock_log_check.call_args_list)
        assert "comp-audit-3a" in all_args, (
            f"log_check() deve receber company_id='comp-audit-3a'. "
            f"Call args: {mock_log_check.call_args_list}"
        )


# ─── Teste de não-regressão ──────────────────────────────────────────────────

class TestFairnessGuardNonRegression:
    """Fix não deve quebrar o caminho feliz."""

    @pytest.mark.asyncio
    async def test_guard_ok_allows_execution(self):
        """Quando FairnessGuard.is_blocked=False, execute() continua normalmente."""
        runtime = _make_runtime()
        ok = _make_ok_fg_result()
        expected = _make_ok_agent_output()

        with patch(
            "app.shared.compliance.fairness_guard.FairnessGuard.check",
            return_value=ok,
        ), patch.object(
            runtime, "_process_langgraph",
            new=AsyncMock(return_value=expected),
        ):
            output = await runtime.execute(
                message="quais candidatos temos?",
                user_id="u1",
                company_id="comp-1",
                session_id="sess-ok",
            )

        assert output.message == "Resposta normal.", (
            "execute() não deve bloquear quando FairnessGuard.is_blocked=False"
        )
        assert not output.metadata.get("blocked"), (
            "metadata.blocked não deve ser True no caminho feliz"
        )

"""
Plan Orchestration Service — multi-step plan detection + execution.

Sprint II.1 da migração V1→V2 (LIA-D06 cleanup). Última extração do
Sprint II. Substitui a lógica inline do `Orchestrator.process_request()`
(V1 linhas 169-220) que faz detecção de plan multi-step e execução com
streaming via WebSocket.

## O que este service faz

Quando o usuário envia uma mensagem que aciona um pattern de multi-step
plan (ex: "publica essa vaga e busca 5 candidatos"), este service:

1. Detecta o plan via `PlanDetector` (heurística + LLM)
2. Executa via `PlanExecutor` (orquestra múltiplas tasks com depends_on)
3. Emite eventos de progresso via WebSocket (se conversation_id presente)
4. Retorna `PlanExecutionResult` consolidado para o caller

## O que NÃO está aqui

- **state_manager updates** — fica no caller (domain-specific session/state).
- **response shaping para V1/V2** — caller decide formato final do dict de
  resposta. O service retorna `PlanExecutionResult` neutro.

## Taxonomia harness-engineering

`[guide]` — decide e executa multi-step plans (feedforward orquestrado).

## Reference

ADR-019 — Sprint II.1
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from app.shared.execution import PlanDetector, PlanExecutor

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# WebSocket manager protocol — duck typing para evitar import direto
# ─────────────────────────────────────────────────────────────────────────────


class WSManagerProtocol(Protocol):
    """Protocol mínima para ws_manager — permite tests sem import real."""

    async def send_to_session(self, session_id: str, payload: dict) -> None:
        ...


# ─────────────────────────────────────────────────────────────────────────────
# Result types
# ─────────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class PlanExecutionResult:
    """
    Resultado canônico de plan execution.

    Permite caller (V1 ou V2) montar response final em formato adequado.

    Attributes:
        executed_plan: Resultado raw do PlanExecutor (DetectedPlan executado).
        success: True se all_succeeded.
        message: Mensagem consolidada para o usuário.
        data: Dados consolidados (resposta acumulada de todas as tasks).
        suggestions: Sugestões de próximos prompts (pode vir vazia).
        pattern: Nome do pattern detectado (e.g., "publish_then_search").
        plan_id: ID do plan executado.
        summary: Sumário estruturado (de executed_plan.get_summary()).
    """

    executed_plan: Any  # ExecutedPlan from app.shared.execution
    success: bool
    message: str
    data: dict[str, Any]
    suggestions: list[str]
    pattern: str
    plan_id: str
    summary: dict[str, Any]


# ─────────────────────────────────────────────────────────────────────────────
# PlanOrchestrationService
# ─────────────────────────────────────────────────────────────────────────────


class PlanOrchestrationService:
    """
    Service canônico para multi-step plan orchestration.

    Substitui a lógica inline em `Orchestrator.process_request()` (V1
    linhas 169-220) com interface limpa, dependency injection do detector
    e executor, e WebSocket streaming opcional.

    ## Multi-tenant safety (P0 LGPD)

    `tenant_id` (geralmente `context["company_id"]`) é propagado ao
    `PlanExecutor.execute()` para garantir tenant isolation em todas as
    sub-tasks do plan.

    ## Reference

    ADR-019 — Sprint II.1
    """

    def __init__(
        self,
        plan_detector: PlanDetector,
        plan_executor: PlanExecutor,
        ws_manager: WSManagerProtocol | None = None,
    ) -> None:
        """
        Args:
            plan_detector: Instância de PlanDetector (heurística + LLM).
            plan_executor: Instância de PlanExecutor (orquestra tasks).
            ws_manager: WebSocket manager opcional. Se ausente, progresso
                não é emitido (mas execução continua normalmente).

        Raises:
            TypeError: Se ws_manager fornecido mas não tem método send_to_session.
        """
        # P1: validate ws_manager early (duck typing fail-fast).
        if ws_manager is not None and not hasattr(ws_manager, "send_to_session"):
            raise TypeError(
                f"ws_manager must have send_to_session method, got {type(ws_manager).__name__}"
            )
        self._detector = plan_detector
        self._executor = plan_executor
        self._ws_manager = ws_manager

    def detect(self, message: str) -> Any | None:
        """
        Detecta multi-step plan na mensagem do usuário.

        Args:
            message: Mensagem sanitizada do usuário.

        Returns:
            DetectedPlan se um pattern foi reconhecido, None caso contrário.
            Captura exceções e retorna None (não bloqueia o flow).
        """
        try:
            return self._detector.detect(message)
        except Exception as e:
            logger.warning("Plan detection failed (non-blocking): %s", e)
            return None

    async def execute(
        self,
        detected_plan: Any,
        *,
        user_id: str,
        session_id: str,
        tenant_id: str | None,
        base_context: dict[str, Any] | None = None,
    ) -> PlanExecutionResult:
        """
        Executa um detected plan via PlanExecutor.

        Constrói automaticamente o WebSocket progress callback se ws_manager
        foi injetado e session_id está presente.

        Args:
            detected_plan: Plan retornado por `detect()`.
            user_id: User executando o plan.
            session_id: ID da conversation (usado para WebSocket streaming).
            tenant_id: Multi-tenant isolation (geralmente company_id).
            base_context: Contexto compartilhado entre todas as tasks do plan.

        Returns:
            PlanExecutionResult consolidado. Caller é responsável por:
            - Atualizar state_manager (add_message, update_state)
            - Montar response final no formato apropriado (V1 dict ou V2 ChatResponse)
        """
        progress_callback = self._build_progress_callback(session_id)

        executed_plan = await self._executor.execute(
            plan=detected_plan,
            user_id=user_id,
            session_id=session_id,
            tenant_id=tenant_id,
            base_context=base_context or {},
            progress_callback=progress_callback,
        )
        consolidated = self._executor.build_consolidated_response(executed_plan)

        return PlanExecutionResult(
            executed_plan=executed_plan,
            success=bool(consolidated.success),
            message=consolidated.message or "Plano executado.",
            data=dict(consolidated.data or {}),
            suggestions=list(consolidated.suggestions or []),
            pattern=str(getattr(executed_plan, "detected_pattern", "")),
            plan_id=str(getattr(executed_plan, "plan_id", "")),
            summary=executed_plan.get_summary() if hasattr(executed_plan, "get_summary") else {},
        )

    def _build_progress_callback(self, session_id: str):
        """
        Constrói callback WebSocket para progress events durante execution.

        Returns:
            Callable async ou None se ws_manager/session_id ausentes.
        """
        if not self._ws_manager or not session_id:
            return None

        ws_manager = self._ws_manager  # capture in closure

        async def _plan_progress_callback(event_type: str, data: dict) -> None:
            try:
                await ws_manager.send_to_session(
                    session_id,
                    {
                        "type": "plan_progress",
                        "event": event_type,
                        **data,
                    },
                )
            except Exception as e:
                # P1: WebSocket failures não bloqueiam plan execution
                logger.warning(
                    "WebSocket progress send failed (non-blocking): %s", e
                )

        return _plan_progress_callback

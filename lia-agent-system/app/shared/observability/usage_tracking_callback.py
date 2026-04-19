"""Generic helper to build `on_usage` callbacks for `LLMService.safe_invoke`.

Audit task #545 — extensão de tracking de IA para os principais fluxos.

A task #532 instrumentou apenas o `wsi_layer2`. Este módulo abstrai o
padrão de callback usado lá (closure → `asyncio.create_task` → sessão
própria de DB → `TokenTrackingService.record_usage`) para que outros
domínios possam ativar o mesmo tracking sem repetir código.

Uso típico::

    from app.shared.observability.usage_tracking_callback import (
        build_usage_callback,
    )

    on_usage = build_usage_callback(
        tracking_context,
        agent_type="wsi_question_generator",
        default_operation="wsi_question_cbi",
        extra={"competency": competency.name},
    )
    response = await self.llm.safe_invoke(prompt, on_usage=on_usage)

Regras de robustez (alinhadas com `_build_layer2_usage_callback`):

* Sem `tracking_context["company_id"]` → devolve no-op (a tabela
  `AiConsumption` exige FK NOT NULL para `company_id`).
* Falhas no agendamento ou na escrita NUNCA propagam — apenas log.
* O callback abre a própria `AsyncSessionLocal` em vez de compartilhar
  a sessão do orquestrador, evitando commits cruzados.
* `asyncio.CancelledError` durante shutdown é logado e re-levantado.
"""
from __future__ import annotations

import logging
from collections.abc import Callable, Mapping
from typing import Any

logger = logging.getLogger(__name__)


def build_usage_callback(
    tracking_context: Mapping[str, Any] | None,
    *,
    agent_type: str,
    default_operation: str,
    extra: Mapping[str, Any] | None = None,
) -> Callable[[dict[str, Any]], None] | None:
    """Build an `on_usage` callback compatible with `safe_invoke(on_usage=...)`.

    Args:
        tracking_context: Optional dict with at least ``company_id``. May also
            include ``user_id``, ``candidate_id``, ``vacancy_id``, ``session_id``
            and ``operation`` (overrides ``default_operation``).
        agent_type: Discriminador gravado em ``AiConsumption.agent_type`` para
            granularidade no dashboard (ex.: ``wsi_question_generator``).
        default_operation: Operação padrão quando ``tracking_context`` não
            traz ``operation``.
        extra: Metadados adicionais persistidos em ``extra_data`` (merged com
            os campos padrão como ``provider`` e ``source``).

    Returns:
        Callback síncrono que agenda persistência fire-and-forget, ou
        ``None`` quando ``tracking_context`` está ausente / sem ``company_id``.
    """
    if not tracking_context:
        return None

    company_id = tracking_context.get("company_id")
    if not company_id:
        return None

    user_id = tracking_context.get("user_id")
    candidate_id = tracking_context.get("candidate_id")
    vacancy_id = tracking_context.get("vacancy_id")
    session_id = tracking_context.get("session_id")
    operation = tracking_context.get("operation") or default_operation
    extra_data_static: dict[str, Any] = dict(extra or {})

    def _on_usage(usage: dict[str, Any]) -> None:
        try:
            import asyncio

            from app.core.database import AsyncSessionLocal
            from app.shared.observability.token_tracking_service import (
                TokenTrackingService,
            )

            async def _persist() -> None:
                try:
                    async with AsyncSessionLocal() as db:
                        svc = TokenTrackingService(db)
                        merged_extra: dict[str, Any] = {
                            "provider": usage.get("provider"),
                            "source": agent_type,
                            **extra_data_static,
                        }
                        if session_id:
                            merged_extra.setdefault("session_id", str(session_id))
                        await svc.record_usage(
                            user_id=str(user_id) if user_id else "",
                            company_id=str(company_id),
                            agent_type=agent_type,
                            intent=str(operation),
                            input_tokens=int(usage.get("input_tokens") or 0),
                            output_tokens=int(usage.get("output_tokens") or 0),
                            model=str(usage.get("model") or "unknown"),
                            latency_ms=float(usage.get("latency_ms") or 0.0),
                            candidate_id=str(candidate_id) if candidate_id else None,
                            vacancy_id=str(vacancy_id) if vacancy_id else None,
                            extra_data=merged_extra,
                        )
                except asyncio.CancelledError:
                    logger.warning(
                        "Token tracking cancelled before persist",
                        extra={
                            "event": "token_tracking_cancelled",
                            "agent_type": agent_type,
                            "operation": operation,
                        },
                    )
                    raise
                except Exception as persist_err:
                    logger.warning(
                        "Token tracking persist failed",
                        extra={
                            "event": "token_tracking_persist_failed",
                            "agent_type": agent_type,
                            "operation": operation,
                            "error": str(persist_err),
                        },
                    )

            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                asyncio.run(_persist())
                return
            loop.create_task(_persist())
        except Exception as cb_err:  # pragma: no cover - defensive
            logger.warning(
                "Token tracking schedule failed",
                extra={
                    "event": "token_tracking_schedule_failed",
                    "agent_type": agent_type,
                    "operation": operation,
                    "error": str(cb_err),
                },
            )

    return _on_usage

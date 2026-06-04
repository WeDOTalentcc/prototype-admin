"""Supervisor (A2) handoff tools — delegacao hierarquica.

Decisao CEO review 2026-06-04: o chat live = supervisor (agentic_loop) com toolset
CURADO. Tools de handoff `delegate_to_<dominio>` delegam a domain sub-agents via
AgentRegistry.process(AgentInput), reusando a maquina canonica da Phase 2
(workflow._try_react_agent) — REUSO, nao rebuild. Adapter fino: resolve agent ->
process -> dado estruturado. UMA voz: o supervisor compoe o texto final a partir do
dado retornado. RLS (balde 1) ja herdado do produtor (engine begin listener).
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


async def delegate_to_domain(
    agent_domain: str,
    task: str,
    *,
    company_id: str,
    user_id: str,
    session_id: str = "",
    view_context: dict | None = None,
) -> dict[str, Any]:
    """Delega `task` ao domain sub-agent `agent_domain` via AgentRegistry.

    Reusa o mecanismo canonico da Phase 2 (workflow._try_react_agent). Retorna
    dado ESTRUTURADO pro supervisor compor a resposta (uma voz). Fail-loud:
    agente nao registrado -> {success:False, unavailable:True} (nunca silencioso).
    """
    try:
        from lia_agents_core.agent_interface import AgentInput
        from app.api.v1.agent_chat_ws import _ensure_agents_loaded
        from app.shared.agents.agent_registry import AgentRegistry

        _ensure_agents_loaded()
        agent = AgentRegistry().get_instance(agent_domain)
        if agent is None:
            logger.warning("[supervisor] domain agent '%s' nao registrado", agent_domain)
            return {
                "success": False,
                "unavailable": True,
                "message": f"Dominio '{agent_domain}' indisponivel no momento.",
            }

        agent_input = AgentInput(
            message=task,
            context={
                "source": "supervisor_handoff",
                "agent_domain": agent_domain,
                "view_context": view_context or {},
            },
            session_id=session_id or "",
            company_id=company_id,
            user_id=user_id or "",
        )
        output = await agent.process(agent_input)
        return {
            "success": not bool(getattr(output, "error", None)),
            "message": getattr(output, "message", "") or "",
            "data": getattr(output, "state_updates", {}) or {},
            "confidence": getattr(output, "confidence", None),
            "reasoning_steps": getattr(output, "reasoning_steps", []) or [],
        }
    except Exception as exc:
        logger.warning(
            "[supervisor] delegate_to_domain('%s') falhou: %s",
            agent_domain, exc, exc_info=True,
        )
        return {
            "success": False,
            "message": f"Falha ao delegar para '{agent_domain}'.",
            "error": str(exc),
        }


def _make_wrapper(agent_domain: str):
    from app.shared.tool_handler import tool_handler

    @tool_handler("orchestrator")
    async def _wrap(**kwargs: Any) -> dict[str, Any]:
        return await delegate_to_domain(
            agent_domain,
            kwargs.get("task", ""),
            company_id=kwargs.get("company_id", ""),
            user_id=kwargs.get("user_id", "") or "",
            session_id=kwargs.get("session_id", "") or "",
            view_context=kwargs.get("view_context"),
        )

    return _wrap


_wrap_delegate_to_pipeline = _make_wrapper("pipeline")


def register_handoff_tools() -> None:
    """Registra as tools de handoff do supervisor no tool_registry global.

    Slice Fase A: so `delegate_to_pipeline`. Os demais dominios entram depois
    (sourcing, talent, comms, offers, settings, analytics, autonomous, ats, job).
    """
    from app.tools.registry import ToolDefinition, tool_registry

    tool_registry.register(ToolDefinition(
        name="delegate_to_pipeline",
        description=(
            "Delega ao agente de pipeline de candidatos: mover candidato entre etapas, "
            "ver/gerir o funil de uma vaga, operacoes de kanban. Use quando o recrutador "
            "pedir acoes sobre o pipeline/etapas de candidatos."
        ),
        parameters_schema={
            "type": "object",
            "properties": {
                "task": {"type": "string", "description": "O pedido do recrutador, em linguagem natural."},
                "view_context": {"type": "object", "description": "Estado da tela atual (page_type, contagens, filtros)."},
            },
            "required": ["task"],
        },
        handler=_wrap_delegate_to_pipeline,
        allowed_agents=["orchestrator"],
    ))

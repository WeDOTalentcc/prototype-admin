"""Supervisor (A2) handoff tools — delegacao hierarquica.

Decisao CEO review 2026-06-04: o chat live = supervisor (agentic_loop) com toolset
CURADO. Tools de handoff `delegate_to_<dominio>` delegam a domain sub-agents via
AgentRegistry.process(AgentInput), reusando a maquina canonica da Phase 2
(workflow._try_react_agent) — REUSO, nao rebuild. Adapter fino: resolve agent ->
process -> dado estruturado. UMA voz: o supervisor compoe o texto final a partir do
dado retornado. RLS (balde 1) ja herdado do produtor (engine begin listener).

DOMAINS = conjunto CURADO de top-level domain agents (1 handoff cada). Sub-variantes
(pipeline_action, kanban_search, sourcing_github...) sao orquestradas DENTRO de cada
domain agent — nao viram handoff proprio. Todo key DEVE ser um agente registrado no
AgentRegistry (guard anti-handoff-morto em tests/contract/test_supervisor_handoff_federation).
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


# Conjunto curado: dominio -> descricao (visivel ao LLM supervisor).
# Cada key e um agent_domain registrado no AgentRegistry.
DOMAINS: dict[str, str] = {
    "pipeline": (
        "Pipeline de candidatos: mover candidato entre etapas, ver/gerir o funil de "
        "uma vaga, operacoes de kanban. Use para acoes sobre etapas/pipeline."
    ),
    "talent_pool": (
        "Banco de talentos e listas: criar/listar pools, adicionar/mover candidatos, "
        "shortlist, talentos internos (mobilidade). Use para gerir o pool."
    ),
    "sourcing": (
        "Sourcing ativo: buscar e enriquecer candidatos, canais externos (LinkedIn, "
        "GitHub, StackOverflow), diversidade, referral, nurture de passivos."
    ),
    "communication": (
        "Comunicacao com candidatos: enviar email/WhatsApp, sequencias de nurture, "
        "templates. Use quando o recrutador pedir para falar com candidato(s)."
    ),
    "analytics": (
        "Analises e metricas: funil de contratacao, relatorios, predicoes (forecast), "
        "alertas proativos, insights de aprendizado. Use para perguntas analiticas."
    ),
    "company_settings": (
        "Configuracao da empresa: beneficios, cultura, niveis salariais, persona da IA, "
        "import de dados. Use quando o recrutador quiser configurar a empresa."
    ),
    "policy": (
        "Politicas de recrutamento e contratacao da empresa (aprovacoes, regras). "
        "Use para consultar/ajustar politicas."
    ),
    "ats_integration": (
        "Integracao com ATS externo: importar/sincronizar candidaturas e dados de "
        "sistemas externos."
    ),
    "job_management": (
        "Gestao de vagas: criar, editar, publicar, enriquecer descricao, configurar "
        "triagem. Use para o ciclo de vida da vaga."
    ),
}


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
        _ok = not bool(getattr(output, "error", None))
        _msg = getattr(output, "message", "") or ""
        logger.info(
            "[supervisor] handoff -> %s | success=%s | msg_len=%d | tool_results=%d | preview=%r",
            agent_domain, _ok, len(_msg),
            len(getattr(output, "tool_results", []) or []), _msg[:160],
        )
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

    _wrap.__name__ = f"_wrap_delegate_to_{agent_domain}"
    return _wrap


def handoff_tool_name(agent_domain: str) -> str:
    return f"delegate_to_{agent_domain}"


def register_handoff_tools() -> int:
    """Registra as tools de handoff do supervisor no tool_registry global.

    Uma `delegate_to_<dominio>` por entrada de DOMAINS (conjunto curado). Retorna
    o numero de tools registradas. Idempotente (re-registro sobrescreve).
    """
    from app.tools.registry import ToolDefinition, tool_registry

    count = 0
    for agent_domain, description in DOMAINS.items():
        tool_registry.register(ToolDefinition(
            name=handoff_tool_name(agent_domain),
            description=description,
            parameters_schema={
                "type": "object",
                "properties": {
                    "task": {
                        "type": "string",
                        "description": "O pedido do recrutador, em linguagem natural.",
                    },
                    "view_context": {
                        "type": "object",
                        "description": "Estado da tela atual (page_type, contagens, filtros).",
                    },
                },
                "required": ["task"],
            },
            handler=_make_wrapper(agent_domain),
            allowed_agents=["orchestrator"],
        ))
        count += 1
    logger.info("[supervisor] %d handoff tools registradas: %s", count, list(DOMAINS))
    return count

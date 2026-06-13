"""
Agent Model Config — E5 (Multi-Model por Agente)

Mapeamento de agente → modelo LLM. Configurável via variáveis de ambiente.
Fallback: CLAUDE_DEFAULT_MODEL.
"""
from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

DEFAULT_MODEL = os.getenv("CLAUDE_DEFAULT_MODEL", "claude-sonnet-4-6")

# Mapeamento padrão — sobrescrito por envvars AGENT_MODEL_{NAME_UPPER}
_DEFAULT_AGENT_MODELS: dict[str, str] = {
    "wsi_interview": "claude-sonnet-4-6",
    "sourcing": "claude-sonnet-4-6",
    "pipeline": "claude-sonnet-4-6",
    "job_wizard": "claude-sonnet-4-6",
    "kanban": "claude-haiku-4-5",        # tarefas simples
    "hiring_policy": "claude-haiku-4-5",  # tarefas simples
    "analytics": "claude-sonnet-4-6",
    "communication": "claude-haiku-4-5",  # geração de mensagens
    "ats_integration": "claude-haiku-4-5",
    "automation": "claude-haiku-4-5",
    "talent": "claude-sonnet-4-6",
    "recruiter_assistant": "claude-sonnet-4-6",
    # Z1: subagentes Kanban (herdam haiku do domínio pai)
    "kanban_search": "claude-haiku-4-5",
    "kanban_insight": "claude-haiku-4-5",
    "kanban_action": "claude-haiku-4-5",
    # Z1: subagentes Pipeline (herdam sonnet do domínio pai — ações críticas)
    "pipeline_context": "claude-haiku-4-5",    # leitura — haiku suficiente
    "pipeline_decision": "claude-sonnet-4-6",  # decisão — sonnet para precisão
    "pipeline_action": "claude-sonnet-4-6",    # ação + fairness — sonnet
    "pipeline_transition": "claude-sonnet-4-6",
    # Z2-02: Sourcing subagents — modelo alinhado à complexidade de cada etapa
    "sourcing_planner": "claude-haiku-4-5",     # critérios/parâmetros — rápido
    "sourcing_search": "claude-haiku-4-5",      # busca estruturada — rápido
    "sourcing_enrich": "claude-sonnet-4-6",     # análise/scoring — precisa qualidade
    "sourcing_engagement": "claude-sonnet-4-6", # personalização outreach — qualidade
}


def build_agent_model_config() -> dict[str, str]:
    """
    Constrói mapeamento agente→modelo lendo envvars AGENT_MODEL_{NAME_UPPER}.
    Exemplo: AGENT_MODEL_SOURCING=claude-opus-4-6
    """
    config = dict(_DEFAULT_AGENT_MODELS)
    for agent_name in list(config.keys()):
        env_key = f"AGENT_MODEL_{agent_name.upper()}"
        env_val = os.getenv(env_key)
        if env_val:
            logger.info("[AgentModelConfig] %s → %s (from env)", agent_name, env_val)
            config[agent_name] = env_val
    return config


AGENT_MODEL_CONFIG: dict[str, str] = build_agent_model_config()


def get_model_for_agent(agent_name: str) -> str:
    """Retorna model_id para o agente. Fallback: DEFAULT_MODEL."""
    return AGENT_MODEL_CONFIG.get(agent_name, DEFAULT_MODEL)

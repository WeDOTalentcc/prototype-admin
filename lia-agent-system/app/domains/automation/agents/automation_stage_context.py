"""Automation ReAct Agent — Stage Context.

Defines execution stages for the automation workflow and their associated tools.
"""
from typing import Any

STAGE_DEFINITIONS: dict[str, Any] = {
    "decompose": {
        "description": "Decompor tarefa complexa em subtarefas executáveis",
        "tools": ["decompose_task"],
        "next_stages": ["prioritize", "plan"],
    },
    "prioritize": {
        "description": "Calcular e atualizar prioridades das tarefas",
        "tools": ["prioritize_tasks", "get_next_tasks"],
        "next_stages": ["plan", "execute"],
    },
    "plan": {
        "description": "Gerar plano de execução com níveis paralelos",
        "tools": ["get_execution_plan", "build_dag", "check_dependencies"],
        "next_stages": ["execute"],
    },
    "execute": {
        "description": "Obter próximas tarefas e despachar para agentes",
        "tools": ["get_next_tasks", "check_dependencies"],
        "next_stages": [],
    },
    # ── Sprint 5 F5: webhook events canonical (catalogo dinamico) ─────────────
    "webhook-config": {
        "description": (
            "Configurar webhook subscriptions canonical: sugerir, aplicar e "
            "criar event types per-tenant (substitui catalogo hardcoded)."
        ),
        "tools": [
            "suggest_webhook_event_types",
            "apply_webhook_event_subscription",
            "create_custom_webhook_event_type",
        ],
        "next_stages": [],
    },
}


def get_stage_context(stage: str) -> dict[str, Any]:
    return STAGE_DEFINITIONS.get(stage, STAGE_DEFINITIONS["decompose"])


def get_stage_tools(stage: str) -> list[str]:
    return get_stage_context(stage).get("tools", [])


def get_transition_prompt(from_stage: str, to_stage: str) -> str:
    prompts = {
        ("decompose", "prioritize"): "Tarefa decomposta. Calculando prioridades...",
        ("decompose", "plan"): "Tarefa decomposta. Gerando plano de execução...",
        ("prioritize", "plan"): "Prioridades calculadas. Gerando plano de execução...",
        ("plan", "execute"): "Plano pronto. Iniciando execução das tarefas...",
    }
    return prompts.get((from_stage, to_stage), f"Avançando de '{from_stage}' para '{to_stage}'.")

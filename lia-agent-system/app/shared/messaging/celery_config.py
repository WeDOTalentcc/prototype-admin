"""
Celery Config — Configuração centralizada de filas e prioridades por domínio.

DOMAIN_QUEUES mapeia domínio de agente para:
- queue: nome da fila Celery
- priority: prioridade na fila (1-10, maior = mais urgente)
- task: nome registrado da Celery task
"""
from typing import Any

DOMAIN_QUEUES: dict[str, dict[str, Any]] = {
    # Domínios com SLA curto (interação direta com recrutador)
    "wizard": {
        "queue": "vagas_normal",
        "priority": 5,
        "task": "agents.wizard.execute",
    },
    "job_management": {
        "queue": "vagas_normal",
        "priority": 5,
        "task": "agents.wizard.execute",
    },
    # Pipeline / triagem (feedback esperado em 5-15s)
    "pipeline": {
        "queue": "evaluation_normal",
        "priority": 5,
        "task": "agents.pipeline.execute",
    },
    "cv_screening": {
        "queue": "evaluation_normal",
        "priority": 5,
        "task": "agents.screening.execute",
    },
    "pipeline_transition": {
        "queue": "evaluation_normal",
        "priority": 5,
        "task": "agents.pipeline.execute",
    },
    # Sourcing — alta prioridade (SLA curto para busca de candidatos)
    "sourcing": {
        "queue": "sourcing_high",
        "priority": 8,
        "task": "agents.sourcing.execute",
    },
    # Entrevistas WSI — evaluation queue
    "wsi_assessment": {
        "queue": "evaluation_normal",
        "priority": 5,
        "task": "agents.screening.execute",
    },
    # Kanban / assistente
    "kanban": {
        "queue": "vagas_normal",
        "priority": 4,
        "task": "agents.kanban.execute",
    },
    "recruiter_assistant": {
        "queue": "vagas_normal",
        "priority": 4,
        "task": "agents.kanban.execute",
    },
    "talent": {
        "queue": "vagas_normal",
        "priority": 4,
        "task": "agents.kanban.execute",
    },
    # Policy / compliance — baixa prioridade
    "policy": {
        "queue": "onboarding_low",
        "priority": 3,
        "task": "agents.policy.execute",
    },
    "hiring_policy": {
        "queue": "onboarding_low",
        "priority": 3,
        "task": "agents.policy.execute",
    },
    # Automation / task planning
    "automation": {
        "queue": "vagas_normal",
        "priority": 4,
        "task": "agents.automation.execute",
    },
}

# Domínios que requerem execução assíncrona via fila (SLA > 15s esperado)
ASYNC_DOMAINS = frozenset({"sourcing", "cv_screening", "wsi_assessment", "automation"})

# Domínios que suportam execução síncrona no WS endpoint (SLA < 15s esperado)
SYNC_DOMAINS = frozenset({
    "wizard", "pipeline", "pipeline_transition", "kanban",
    "talent", "recruiter_assistant", "policy", "hiring_policy", "job_management",
})


def get_domain_config(domain: str) -> dict[str, Any]:
    """Retorna configuração de fila para um domínio. Fallback: vagas_normal."""
    return DOMAIN_QUEUES.get(domain, {
        "queue": "vagas_normal",
        "priority": 4,
        "task": "agents.kanban.execute",
    })


def is_async_domain(domain: str) -> bool:
    """Retorna True se o domínio deve ser executado via fila (evita timeout WS)."""
    return domain in ASYNC_DOMAINS

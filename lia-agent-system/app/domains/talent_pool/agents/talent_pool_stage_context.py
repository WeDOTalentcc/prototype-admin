"""
Talent Pool Stage Context — stage definitions for the talent pool agent.

Stages represent the recruiter's current intent when interacting with pools:
  browsing   — viewing/listing pools and their candidates
  creating   — creating a new talent bank
  managing   — adding/moving candidates, creating jobs from pools
"""
from typing import Any

STAGE_DEFINITIONS: dict[str, dict[str, Any]] = {
    "browsing": {
        "name": "Browsing",
        "display_name": "Navegando Bancos",
        "description": (
            "Recrutador esta visualizando bancos de talentos existentes "
            "ou consultando candidatos dentro de um pool."
        ),
        "available_tools": [
            "list_talent_pools",
            "get_pool_candidates",
        ],
        "required_fields": [],
        "optional_fields": [],
        "transition_criteria": {
            "description": "Sem transicao forcada — entra em creating/managing conforme necessidade.",
            "required": [],
        },
        "next_stage": "browsing",
        "phase": "consultation",
    },
    "creating": {
        "name": "Creating",
        "display_name": "Criando Pool",
        "description": (
            "Recrutador esta criando um novo banco de talentos. "
            "Solicitar nome e, opcionalmente, arquetipo e descricao."
        ),
        "available_tools": [
            "create_talent_pool",
            "list_talent_pools",
        ],
        "required_fields": ["name"],
        "optional_fields": ["archetype_id", "description"],
        "transition_criteria": {
            "description": "Pool criado com sucesso — retornar para browsing.",
            "required": ["name"],
        },
        "next_stage": "browsing",
        "phase": "setup",
    },
    "managing": {
        "name": "Managing",
        "display_name": "Gerenciando Pool",
        "description": (
            "Recrutador esta operando sobre um pool: adicionando candidatos, "
            "migrando para vaga ou criando vaga a partir do pool. "
            "Acoes de alto impacto (move_pool_to_job, create_job_from_pool) "
            "requerem confirmacao explicita."
        ),
        "available_tools": [
            "list_talent_pools",
            "get_pool_candidates",
            "add_candidate_to_pool",
            "move_pool_to_job",
            "create_job_from_pool",
        ],
        "required_fields": ["pool_id"],
        "optional_fields": [],
        "transition_criteria": {
            "description": "Operacao concluida — retornar para browsing.",
            "required": ["pool_id"],
        },
        "next_stage": "browsing",
        "phase": "operation",
    },
}


def get_stage_context(stage: str, pool_state: dict[str, Any] | None = None) -> str:
    """Build a textual context summary for the given stage."""
    state = pool_state or {}
    stage_def = STAGE_DEFINITIONS.get(stage)
    if not stage_def:
        return f"Estagio desconhecido: {stage}. Tratando como browsing."

    parts = [
        "=== CONTEXTO DO ESTAGIO ===",
        f"Estagio atual: {stage_def['display_name']} ({stage})",
        f"Fase: {stage_def['phase']}",
        f"Descricao: {stage_def['description']}",
        "",
        f"Ferramentas disponiveis: {', '.join(stage_def['available_tools'])}",
    ]

    active_pool = state.get("active_pool_id") or state.get("pool_id")
    if active_pool:
        parts.append(f"\nPool ativo: {active_pool}")

    if stage == "creating":
        if not state.get("name"):
            parts.append("\nFOCO: Perguntar o nome do novo banco de talentos.")
        else:
            parts.append(f"\nFOCO: Criar pool '{state['name']}' (confirmar arquetipo se disponivel).")
    elif stage == "managing":
        if not active_pool:
            parts.append("\nFOCO: Identificar qual pool operar (listar disponiveis se necessario).")
        else:
            parts.append("\nFOCO: Executar operacao solicitada no pool. Confirmar antes de migrar candidatos.")
    else:
        parts.append("\nFOCO: Mostrar lista de pools ativos. Orientar para criacao se lista vazia.")

    return "\n".join(parts)

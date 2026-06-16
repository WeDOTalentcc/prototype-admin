"""ATS Integration ReAct Agent — Stage Context.

Defines execution stages for the ATS integration workflow and their associated tools.
"""
from typing import Any

STAGE_DEFINITIONS: dict[str, Any] = {
    "provider-detection": {
        "description": (
            "Identificar o provedor ATS alvo, validar credenciais configuradas "
            "e verificar o status atual de sincronização do candidato."
        ),
        "tools": [
            "validate_ats_fields",
            "get_sync_status",
            "recommend_integrations_by_industry",
            "apply_integration_catalog_entry",
            "create_custom_integration_catalog_entry",
        ],
        "next_stages": ["field-mapping", "sync-execution"],
    },
    "field-mapping": {
        "description": (
            "Validar e mapear os campos do candidato antes de executar a sincronização. "
            "Determina quais campos serão enviados ao ATS e quais ficarão apenas no WeDOTalent."
        ),
        "tools": ["validate_ats_fields"],
        "next_stages": ["sync-execution"],
    },
    "sync-execution": {
        "description": (
            "Executar a operação de sincronização (push, pull ou bulk). "
            "Todos os tools estão disponíveis neste estágio."
        ),
        "tools": [
            "sync_candidate_to_ats",
            "fetch_candidate_from_ats",
            "validate_ats_fields",
            "bulk_sync_candidates",
            "get_sync_status",
            "apply_integration_catalog_entry",
            "create_custom_integration_catalog_entry",
        ],
        "next_stages": [],
    },
}


def get_stage_context(stage: str) -> dict[str, Any]:
    """Return stage definition; defaults to provider-detection if unknown."""
    return STAGE_DEFINITIONS.get(stage, STAGE_DEFINITIONS["provider-detection"])


def get_stage_tools(stage: str) -> list[str]:
    """Return tool names available for a given stage."""
    return get_stage_context(stage).get("tools", [])


def get_transition_prompt(from_stage: str, to_stage: str) -> str:
    """Return a human-readable transition message between stages."""
    prompts: dict[tuple, str] = {
        ("provider-detection", "field-mapping"): (
            "Provedor ATS identificado. Validando mapeamento de campos..."
        ),
        ("provider-detection", "sync-execution"): (
            "Provedor ATS identificado. Executando sincronização..."
        ),
        ("field-mapping", "sync-execution"): (
            "Campos validados. Executando sincronização com o ATS..."
        ),
    }
    return prompts.get(
        (from_stage, to_stage),
        f"Avançando de '{from_stage}' para '{to_stage}'.",
    )

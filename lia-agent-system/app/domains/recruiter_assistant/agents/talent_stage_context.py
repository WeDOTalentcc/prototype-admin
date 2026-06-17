"""
Talent Stage Context - Provides stage-specific context for the talent funnel agent.

Each talent funnel stage has different requirements, available tools, and goals.
This module injects the right context so the agent knows what to focus on
when helping recruiters analyze and manage candidates in the talent funnel.
"""
from typing import Any

STAGE_DEFINITIONS: dict[str, dict[str, Any]] = {
    "discovery": {
        "name": "Descoberta",
        "display_name": "Descoberta",
        "description": (
            "Exploracao inicial do funil de talentos. A LIA ajuda o recrutador "
            "a entender quais candidatos estao disponiveis, buscar por skills, "
            "experiencia e localizacao, e definir criterios de busca."
        ),
        "available_tools": ["search_candidates", "list_candidates", "view_candidate_profile"],
        "required_fields": ["search_criteria_defined"],
        "optional_fields": ["candidates_listed", "initial_filters"],
        "transition_criteria": {
            "description": "Criterios de busca foram definidos e candidatos foram identificados.",
            "required": ["search_criteria_defined"],
        },
        "next_stage": "analysis",
        "phase": "discovery",
    },
    "analysis": {
        "name": "Analise",
        "display_name": "Análise",
        "description": (
            "Analise aprofundada dos candidatos no funil. A LIA compara perfis "
            "lado a lado, rankeia candidatos por fit com a vaga, avalia "
            "competencias e identifica gaps de skills."
        ),
        "available_tools": ["compare_candidates", "rank_candidates", "analyze_skills", "view_candidate_profile"],
        "required_fields": ["analysis_completed"],
        "optional_fields": ["ranking_generated", "skills_analyzed", "comparison_done"],
        "transition_criteria": {
            "description": "Analise dos candidatos foi concluida com ranking ou comparacao.",
            "required": ["analysis_completed"],
        },
        "next_stage": "action_planning",
        "phase": "analysis",
    },
    "action_planning": {
        "name": "Planejamento de Acoes",
        "display_name": "Planejamento de Ações",
        "description": (
            "Decisao sobre proximos passos para os candidatos analisados. "
            "A LIA recomenda acoes, ajuda a criar shortlists e gera "
            "relatorios para apoiar a tomada de decisao do recrutador."
        ),
        "available_tools": ["recommend_actions", "create_shortlist", "export_report", "view_candidate_profile"],
        "required_fields": ["recommendations_provided"],
        "optional_fields": ["shortlist_created", "report_exported"],
        "transition_criteria": {
            "description": "Recomendacoes de acoes foram fornecidas ao recrutador.",
            "required": ["recommendations_provided"],
        },
        "next_stage": "complete",
        "phase": "action",
    },
}


def get_stage_context(stage: str, collected_fields: dict[str, Any]) -> str:
    """Build a formatted context string for the current talent funnel stage.

    Includes stage information, field completion status, percentage and
    guidance on what the agent should focus on.

    Args:
        stage: Current talent funnel stage identifier.
        collected_fields: Dictionary of fields already collected and their values.

    Returns:
        Formatted context string for prompt injection.
    """
    stage_def = STAGE_DEFINITIONS.get(stage)
    if not stage_def:
        return f"Estagio desconhecido: {stage}. Trate como descoberta inicial."

    required = stage_def["required_fields"]
    optional = stage_def["optional_fields"]
    all_fields = required + optional

    filled: list[str] = []
    missing_required: list[str] = []
    missing_optional: list[str] = []

    for field in required:
        value = collected_fields.get(field)
        if value is not None and value != "" and value != []:
            filled.append(field)
        else:
            missing_required.append(field)

    for field in optional:
        value = collected_fields.get(field)
        if value is not None and value != "" and value != []:
            filled.append(field)
        else:
            missing_optional.append(field)

    total = len(all_fields)
    completion = (len(filled) / total * 100) if total > 0 else 100.0

    parts = [
        "=== CONTEXTO DO ESTAGIO ===",
        f"Estagio atual: {stage_def['display_name']} ({stage})",
        f"Fase: {stage_def['phase']}",
        f"Descricao: {stage_def['description']}",
        f"Proximo estagio: {stage_def['next_stage']}",
        "",
        "--- Progresso ---",
        f"Completude: {completion:.0f}%",
    ]

    if filled:
        parts.append("Campos preenchidos:")
        for field in filled:
            value = collected_fields.get(field, "")
            display = str(value)
            if len(display) > 80:
                display = display[:80] + "..."
            parts.append(f"  - {field}: {display}")

    if missing_required:
        parts.append("Campos obrigatorios FALTANDO:")
        for field in missing_required:
            parts.append(f"  - {field} (OBRIGATORIO)")

    if missing_optional:
        parts.append("Campos opcionais disponiveis:")
        for field in missing_optional:
            parts.append(f"  - {field}")

    criteria = stage_def["transition_criteria"]
    parts.append("")
    parts.append(f"Criterio de transicao: {criteria['description']}")

    if missing_required:
        parts.append(
            f"\nFOCO: Complete as acoes obrigatorias faltantes: {', '.join(missing_required)}"
        )
    elif stage_def["phase"] == "discovery":
        parts.append(
            "\nFOCO: Ajude o recrutador a buscar e identificar candidatos no funil."
        )
    elif stage_def["phase"] == "analysis":
        parts.append(
            "\nFOCO: Compare, rankeie e analise os candidatos identificados."
        )
    elif stage_def["phase"] == "action":
        parts.append(
            "\nFOCO: Recomende acoes e ajude a criar shortlists para o recrutador."
        )
    else:
        parts.append(
            "\nFOCO: Campos obrigatorios preenchidos. Pergunte se deseja completar "
            "campos opcionais ou avancar."
        )

    return "\n".join(parts)


def get_transition_prompt(current_stage: str, collected_fields: dict[str, Any]) -> str:
    """Generate a prompt for checking whether transition criteria are met.

    Args:
        current_stage: Current talent funnel stage identifier.
        collected_fields: Dictionary of fields already collected.

    Returns:
        Formatted prompt string for transition evaluation.
    """
    stage_def = STAGE_DEFINITIONS.get(current_stage)
    if not stage_def:
        return "Estagio desconhecido. Nao e possivel avaliar transicao."

    criteria = stage_def["transition_criteria"]
    required = criteria.get("required", [])
    filled_required = [
        f
        for f in required
        if collected_fields.get(f) not in (None, "", [])
    ]

    all_required_met = len(filled_required) == len(required)

    parts = [
        f"Avaliacao de transicao para o estagio '{current_stage}':",
        f"Criterio: {criteria['description']}",
        f"Campos obrigatorios preenchidos: {len(filled_required)}/{len(required)}",
    ]

    if all_required_met:
        parts.append(
            f"RESULTADO: Criterios atendidos. Pode sugerir avancar para '{stage_def['next_stage']}'."
        )
    else:
        missing = [f for f in required if f not in filled_required]
        parts.append(
            f"RESULTADO: Criterios NAO atendidos. Faltam: {', '.join(missing)}."
        )

    return "\n".join(parts)

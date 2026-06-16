"""
Sourcing Stage Context - Provides stage-specific context for the sourcing agent.

Each stage in the talent sourcing flow has different requirements, expected fields,
and conversation goals. This module injects the right context so the agent knows
what to focus on during candidate search and screening.

Sub-agentes de sourcing granular e seus estágios de entrada:
- sourcing_github: search-criteria → github_search
- sourcing_stackoverflow: search-criteria → stackoverflow_search
- sourcing_diversity: search-criteria → diversity_sourcing
- sourcing_passive_pipeline: search-criteria → passive_reactivation
- sourcing_referral: shortlist-creation → referral_outreach
- sourcing_nurture_sequence: outreach → nurture_sequence
"""
from typing import Any

# Mapeamento de domínio de sub-agente → stage de entrada.
# Usado pelo SourcingReActAgent para delegar ao sub-agente correto.
SOURCING_SUBAGENT_STAGE_MAP: dict[str, str] = {
    "sourcing_github": "talent-search",
    "sourcing_stackoverflow": "talent-search",
    "sourcing_diversity": "talent-search",
    "sourcing_passive_pipeline": "talent-search",
    "sourcing_referral": "shortlist-creation",
    "sourcing_nurture_sequence": "outreach",
}

STAGE_DEFINITIONS: dict[str, dict[str, Any]] = {
    "search-criteria": {
        "name": "Criterios de Busca",
        "display_name": "Criterios de Busca",
        "description": (
            "Nesta etapa a LIA ajuda o recrutador a definir os parametros de busca "
            "de talentos: cargo desejado, skills requeridas, localizacao, nivel de "
            "experiencia e faixa salarial. A conversa deve ser natural e a LIA "
            "extrai os criterios das respostas do usuario."
        ),
        "available_tools": ["set_search_criteria", "suggest_skills"],
        "required_fields": ["role", "skills", "location"],
        "optional_fields": ["experience_level", "salary_range", "work_model", "industry"],
        "transition_criteria": {
            "description": "Criterios de busca definidos (cargo, skills e localizacao).",
            "required_complete": True,
        },
        "next_stage": "talent-search",
        "phase": "collection",
    },
    "talent-search": {
        "name": "Busca de Talentos",
        "display_name": "Busca de Talentos",
        "description": (
            "A LIA executa a busca de candidatos com base nos criterios definidos. "
            "O recrutador pode filtrar resultados, visualizar perfis individuais "
            "e refinar a busca conforme necessidade. "
            "Sub-agentes especializados disponiveis neste estagio: "
            "sourcing_github (busca GitHub por linguagem/contribuicoes), "
            "sourcing_stackoverflow (busca Stack Overflow por expertise/tags), "
            "sourcing_diversity (sourcing afirmativo — FairnessGuard Layer 3), "
            "sourcing_passive_pipeline (reativacao de candidatos arquivados)."
        ),
        "available_tools": [
            "search_candidates", "filter_results", "view_candidate",
            "github_search_developers", "github_get_profile",
            "github_get_repos", "github_get_contributions",
            "so_search_experts", "so_get_user_tags", "so_get_user_answers",
            "diversity_search_candidates", "diversity_get_pool_metrics",
            "diversity_check_goals",
            "passive_search_archived", "passive_calculate_fit_score",
            "passive_check_lgpd_ttl",
        ],
        "subagents": [
            "sourcing_github", "sourcing_stackoverflow",
            "sourcing_diversity", "sourcing_passive_pipeline",
        ],
        "required_fields": ["search_executed"],
        "optional_fields": ["filters_applied", "results_count"],
        "transition_criteria": {
            "description": "Busca executada com resultados encontrados.",
            "required_complete": True,
        },
        "next_stage": "profile-analysis",
        "phase": "search",
    },
    "profile-analysis": {
        "name": "Analise de Perfis",
        "display_name": "Analise de Perfis",
        "description": (
            "A LIA realiza analise detalhada dos perfis dos candidatos encontrados "
            "usando IA. Compara candidatos entre si, aplica scoring WSI e apresenta "
            "insights sobre aderencia ao cargo."
        ),
        "available_tools": ["analyze_profile", "compare_candidates", "score_candidate"],
        "required_fields": ["candidates_analyzed"],
        "optional_fields": ["comparison_data", "scoring_results"],
        "transition_criteria": {
            "description": "Candidatos analisados com scoring e comparacao realizados.",
            "required_complete": True,
        },
        "next_stage": "shortlist-creation",
        "phase": "analysis",
    },
    "shortlist-creation": {
        "name": "Criacao de Shortlist",
        "display_name": "Criacao de Shortlist",
        "description": (
            "A LIA ajuda o recrutador a construir a shortlist final de candidatos. "
            "O recrutador pode adicionar ou remover candidatos e a LIA sugere "
            "rankings baseados nos scores e analises anteriores. "
            "Sub-agente disponivel neste estagio: sourcing_referral (pipeline de indicacoes "
            "com verificacao HITL via communication_matrix)."
        ),
        "available_tools": [
            "add_to_shortlist", "remove_from_shortlist", "rank_candidates",
            "referral_identify_connectors", "referral_prepare_request",
            "referral_approve_request", "referral_send_request",
        ],
        "subagents": ["sourcing_referral"],
        "required_fields": ["shortlist_created"],
        "optional_fields": ["ranking_criteria", "shortlist_notes"],
        "transition_criteria": {
            "description": "Shortlist criada com pelo menos um candidato.",
            "required_complete": True,
        },
        "next_stage": "outreach",
        "phase": "curation",
    },
    "outreach": {
        "name": "Abordagem",
        "display_name": "Abordagem",
        "description": (
            "A LIA auxilia na abordagem dos candidatos selecionados. Gera mensagens "
            "personalizadas, sugere canais de contato e acompanha respostas. "
            "Requer confirmacao explicita do recrutador antes de enviar mensagens. "
            "Sub-agente disponivel neste estagio: sourcing_nurture_sequence "
            "(sequencias multi-step com HITL, LGPD TTL 180 dias, "
            "persiste em candidate_nurture_sequences)."
        ),
        "available_tools": [
            "send_outreach", "generate_message", "track_response",
            "nurture_create_sequence", "nurture_approve_step",
            "nurture_execute_step", "nurture_get_sequence_status",
        ],
        "subagents": ["sourcing_nurture_sequence"],
        "required_fields": ["outreach_sent"],
        "optional_fields": ["response_tracking", "follow_up_scheduled"],
        "transition_criteria": {
            "description": "Abordagem enviada para candidatos da shortlist.",
            "required_complete": True,
        },
        "next_stage": "complete",
        "phase": "outreach",
    },
}


def get_stage_context(stage: str, collected_fields: dict[str, Any]) -> str:
    """Build a formatted context string for the current sourcing stage.

    Args:
        stage: Current sourcing stage identifier.
        collected_fields: Dictionary of fields already collected and their values.

    Returns:
        Formatted context string for prompt injection.
    """
    stage_def = STAGE_DEFINITIONS.get(stage)
    if not stage_def:
        return f"Estagio desconhecido: {stage}. Trate como coleta inicial de criterios."

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
        f"Estagio atual: {stage_def['name']} ({stage})",
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

    parts.append("")
    transition_desc = stage_def["transition_criteria"]
    if isinstance(transition_desc, dict):
        parts.append(f"Criterio de transicao: {transition_desc.get('description', '')}")
    else:
        parts.append(f"Criterio de transicao: {transition_desc}")

    if missing_required:
        parts.append(
            f"\nFOCO: Colete os campos obrigatorios faltantes: {', '.join(missing_required)}"
        )
    elif stage_def["phase"] == "search":
        parts.append(
            "\nFOCO: Execute a busca e apresente os resultados ao recrutador."
        )
    elif stage_def["phase"] == "analysis":
        parts.append(
            "\nFOCO: Analise os perfis encontrados e apresente scoring e comparacoes."
        )
    elif stage_def["phase"] == "curation":
        parts.append(
            "\nFOCO: Ajude o recrutador a construir a shortlist final de candidatos."
        )
    elif stage_def["phase"] == "outreach":
        parts.append(
            "\nFOCO: Gere mensagens personalizadas e aguarde confirmacao para enviar."
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
        current_stage: Current sourcing stage identifier.
        collected_fields: Dictionary of fields already collected.

    Returns:
        Formatted prompt string for transition evaluation.
    """
    stage_def = STAGE_DEFINITIONS.get(current_stage)
    if not stage_def:
        return "Estagio desconhecido. Nao e possivel avaliar transicao."

    required = stage_def["required_fields"]
    filled_required = [
        f
        for f in required
        if collected_fields.get(f) not in (None, "", [])
    ]

    all_required_met = len(filled_required) == len(required)

    transition_desc = stage_def["transition_criteria"]
    if isinstance(transition_desc, dict):
        criteria_text = transition_desc.get("description", "")
    else:
        criteria_text = transition_desc

    parts = [
        f"Avaliacao de transicao para o estagio '{current_stage}':",
        f"Criterio: {criteria_text}",
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

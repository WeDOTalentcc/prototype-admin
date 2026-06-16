"""
Pipeline Stage Context - Provides stage-specific context for the pipeline agent.

Each pipeline stage has different requirements, available tools, and goals.
This module injects the right context so the agent knows what to focus on
when managing candidates through the recruitment pipeline.
"""
from typing import Any


STAGE_DEFINITIONS: dict[str, dict[str, Any]] = {
    "triage": {
        "name": "Triagem",
        "display_name": "Triagem",
        "description": (
            "Etapa inicial de revisao do candidato. A LIA analisa o perfil "
            "e o curriculo do candidato para determinar se ele atende aos "
            "requisitos minimos da vaga. Avaliacao rapida de fit basico."
        ),
        "available_tools": ["view_candidate_profile", "analyze_cv", "add_notes", "move_candidate"],
        "required_fields": ["candidate_evaluated"],
        "optional_fields": ["evaluation_notes", "fit_score"],
        "transition_criteria": {
            "description": "Candidato foi avaliado e decisao de triagem foi tomada.",
            "required": ["candidate_evaluated"],
        },
        "next_stage": "screening",
        "phase": "evaluation",
    },
    "screening": {
        "name": "Avaliacao",
        "display_name": "Avaliação",
        "description": (
            "Avaliacao aprofundada do candidato usando a metodologia WSI. "
            "A LIA executa o screening estruturado, analisa respostas e "
            "gera um parecer detalhado sobre o candidato."
        ),
        "available_tools": ["run_wsi_screening", "view_screening_results", "add_notes", "move_candidate"],
        "required_fields": ["screening_completed"],
        "optional_fields": ["wsi_score", "screening_notes", "behavioral_assessment"],
        "transition_criteria": {
            "description": "Screening WSI foi concluido e resultado disponivel.",
            "required": ["screening_completed"],
        },
        "next_stage": "shortlist",
        "phase": "screening",
    },
    "shortlist": {
        "name": "Pre-selecao",
        "display_name": "Pré-seleção",
        "description": (
            "Etapa de pre-selecao onde o recrutador decide quais candidatos "
            "avancarao para entrevista. A LIA ajuda a comparar candidatos, "
            "rankear perfis e tomar decisoes informadas."
        ),
        "available_tools": ["move_candidate", "add_to_shortlist", "view_candidate_profile", "add_notes", "batch_move"],
        "required_fields": ["decision_made"],
        "optional_fields": ["shortlist_rank", "comparison_notes"],
        "transition_criteria": {
            "description": "Decisao de pre-selecao foi tomada para o candidato.",
            "required": ["decision_made"],
        },
        "next_stage": "interview",
        "phase": "decision",
    },
    "interview": {
        "name": "Entrevista",
        "display_name": "Entrevista",
        "description": (
            "Agendamento e gestao de entrevistas. A LIA ajuda a agendar "
            "entrevistas, enviar convites, registrar notas e acompanhar "
            "o status das entrevistas realizadas."
        ),
        "available_tools": ["schedule_interview", "view_interview_notes", "send_communication", "add_notes", "move_candidate"],
        "required_fields": ["interview_scheduled"],
        "optional_fields": ["interview_type", "interview_datetime", "interview_notes", "interviewer"],
        "transition_criteria": {
            "description": "Entrevista foi agendada ou realizada.",
            "required": ["interview_scheduled"],
        },
        "next_stage": "offer",
        "phase": "interview",
    },
    "offer": {
        "name": "Proposta",
        "display_name": "Proposta",
        "description": (
            "Etapa de decisao sobre proposta. A LIA ajuda a gerar propostas, "
            "enviar comunicacoes ao candidato e registrar decisoes de "
            "aprovacao ou rejeicao."
        ),
        "available_tools": ["generate_offer", "send_communication", "add_notes", "move_candidate"],
        "required_fields": ["offer_decision"],
        "optional_fields": ["offer_value", "offer_details", "negotiation_notes"],
        "transition_criteria": {
            "description": "Proposta foi enviada ou candidato foi rejeitado.",
            "required": ["offer_decision"],
        },
        "next_stage": "hired",
        "phase": "offer",
    },
    "hired": {
        "name": "Contratacao",
        "display_name": "Contratação",
        "description": (
            "Etapa final de contratacao. A LIA ajuda a finalizar o processo, "
            "atualizar status do candidato, enviar comunicacoes finais e "
            "registrar a contratacao no sistema."
        ),
        "available_tools": ["finalize_hiring", "update_status", "send_communication", "add_notes"],
        "required_fields": ["status_updated"],
        "optional_fields": ["start_date", "onboarding_notes", "final_salary"],
        "transition_criteria": {
            "description": "Status do candidato foi atualizado para contratado.",
            "required": ["status_updated"],
        },
        "next_stage": "complete",
        "phase": "finalization",
    },
}


def get_stage_context(stage: str, collected_fields: dict[str, Any]) -> str:
    """Build a formatted context string for the current pipeline stage.

    Includes stage information, field completion status, percentage and
    guidance on what the agent should focus on.

    Args:
        stage: Current pipeline stage identifier.
        collected_fields: Dictionary of fields already collected and their values.

    Returns:
        Formatted context string for prompt injection.
    """
    stage_def = STAGE_DEFINITIONS.get(stage)
    if not stage_def:
        return f"Estagio desconhecido: {stage}. Trate como triagem inicial."

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
    elif stage_def["phase"] == "evaluation":
        parts.append(
            "\nFOCO: Avalie o perfil do candidato e determine o proximo passo."
        )
    elif stage_def["phase"] == "screening":
        parts.append(
            "\nFOCO: Execute o screening WSI e analise os resultados."
        )
    elif stage_def["phase"] == "decision":
        parts.append(
            "\nFOCO: Ajude o recrutador a tomar a decisao de pre-selecao."
        )
    elif stage_def["phase"] == "interview":
        parts.append(
            "\nFOCO: Agende a entrevista e prepare o recrutador."
        )
    elif stage_def["phase"] == "offer":
        parts.append(
            "\nFOCO: Ajude a formular e enviar a proposta ao candidato."
        )
    elif stage_def["phase"] == "finalization":
        parts.append(
            "\nFOCO: Finalize o processo de contratacao e atualize o status."
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
        current_stage: Current pipeline stage identifier.
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

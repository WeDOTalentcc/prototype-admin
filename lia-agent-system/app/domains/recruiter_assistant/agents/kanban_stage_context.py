"""
Kanban Stage Context - Provides stage-specific context for the kanban analysis agent.

Each kanban analysis phase has different requirements, available tools, and goals.
This module injects the right context so the agent knows what to focus on
when providing strategic pipeline analysis and recommendations.
"""
from typing import Any

STAGE_DEFINITIONS: dict[str, dict[str, Any]] = {
    "pipeline_overview": {
        "name": "Visao Geral do Pipeline",
        "display_name": "Visão Geral do Pipeline",
        "description": (
            "Fase de entendimento do pipeline. A LIA analisa a distribuicao "
            "de candidatos por etapa, taxas de conversao e metricas gerais "
            "para fornecer uma visao estrategica do funil de recrutamento."
        ),
        "available_tools": ["get_pipeline_summary", "get_stage_metrics", "list_stage_candidates", "check_rejection_fairness"],
        "required_fields": ["pipeline_reviewed"],
        "optional_fields": ["vacancy_filter", "stage_filter"],
        "transition_criteria": {
            "description": "Pipeline foi revisado e visao geral esta disponivel.",
            "required": ["pipeline_reviewed"],
        },
        "next_stage": "stage_analysis",
        "phase": "overview",
    },
    "stage_analysis": {
        "name": "Analise de Etapas",
        "display_name": "Análise de Etapas",
        "description": (
            "Fase de analise profunda de etapas especificas do pipeline. "
            "A LIA identifica gargalos, candidatos estagnados, compara "
            "metricas entre etapas e gera recomendacoes estrategicas."
        ),
        "available_tools": ["analyze_stage", "identify_bottlenecks", "get_candidate_aging", "compare_stages", "get_stage_metrics", "check_rejection_fairness"],
        "required_fields": ["stage_analysis_completed"],
        "optional_fields": ["bottlenecks_identified", "aging_report_generated", "stages_compared"],
        "transition_criteria": {
            "description": "Analise de etapas foi concluida com insights acionaveis.",
            "required": ["stage_analysis_completed"],
        },
        "next_stage": "pipeline_actions",
        "phase": "analysis",
    },
    "pipeline_actions": {
        "name": "Acoes no Pipeline",
        "display_name": "Ações no Pipeline",
        "description": (
            "Fase de execucao de acoes no pipeline. A LIA sugere e executa "
            "movimentacoes em massa, comunicacoes em lote, inicio de screening "
            "e geracao de relatorios de analytics."
        ),
        "available_tools": ["suggest_movements", "batch_move_candidates", "send_batch_communication", "start_screening_batch", "generate_pipeline_report", "check_rejection_fairness"],
        "required_fields": ["actions_executed"],
        "optional_fields": ["report_generated", "batch_communication_sent", "screening_started"],
        "transition_criteria": {
            "description": "Acoes foram executadas e resultados registrados.",
            "required": ["actions_executed"],
        },
        "next_stage": "complete",
        "phase": "action",
    },
}


def get_journey_insight_block(journey_data: dict[str, Any]) -> str:
    """
    Gera um bloco de insight de saúde do pipeline para injeção no contexto do agente.
    Só é chamado quando health_score < 50 (warning/critical) e vacancy_id está presente.
    """
    hs = journey_data.get("health_score", 100)
    label = journey_data.get("health_label", "healthy")
    title = journey_data.get("vacancy_title", "esta vaga")
    patterns = journey_data.get("risk_patterns", [])
    summary = journey_data.get("summary", {})

    if hs >= 50:
        return ""

    lines = [
        "=== ALERTA DE SAÚDE DO PIPELINE (INJETADO AUTOMATICAMENTE) ===",
        f"Vaga: {title}",
        f"Health score: {hs}/100 — {label.upper()}",
        f"Candidatos ativos: {summary.get('total_active', 0)} | "
        f"Em etapas avançadas: {summary.get('candidates_in_advanced_stages', 0)} | "
        f"Em risco de ghosting: {summary.get('at_risk_candidates', 0)}",
    ]

    if patterns:
        lines.append("Padrões de risco detectados:")
        for p in patterns[:3]:
            lines.append(f"  [{p['severity'].upper()}] {p['message']}")

    lines.append(
        "INSTRUÇÃO: Ao responder, inclua proativamente este contexto de saúde do pipeline. "
        "Sugira ao recrutador verificar o funil e tomar ação antes de ser perguntado."
    )
    lines.append("=" * 60)
    return "\n".join(lines)


def get_pipeline_prediction_block(prediction: dict[str, Any]) -> str:
    """
    Gera bloco de previsão de fechamento para injeção no contexto do agente.
    Sempre retorna bloco (positivo ou negativo) — ao contrário do journey
    que só injeta para health < 50.
    """
    prob = prediction.get("closure_probability", -1)
    if prob < 0:
        return ""

    title = prediction.get("vacancy_title", "esta vaga")
    confidence = prediction.get("confidence_level", "medium")
    estimated = prediction.get("estimated_days_to_close")
    positives = prediction.get("positive_factors", [])
    risks = prediction.get("risk_factors", [])

    days_str = f" em ~{estimated} dias" if estimated else ""
    status = "CRITICO" if prob < 30 else ("ATENCAO" if prob < 60 else "POSITIVO")

    lines = [
        f"=== PREVISAO DE FECHAMENTO [{status}] ===",
        f"Vaga: {title}",
        f"Probabilidade de fechamento: {prob}% (confianca: {confidence}){days_str}",
    ]
    if positives:
        lines.append(f"Fatores positivos: {', '.join(positives[:3])}")
    if risks:
        lines.append(f"Fatores de risco: {', '.join(risks[:3])}")

    if prob < 30:
        lines.append(
            "INSTRUCAO: O recrutador precisa de ajuda urgente para acelerar este pipeline. "
            "Sugira acoes concretas proativamente."
        )
    elif prob >= 80:
        lines.append(
            "INSTRUCAO: Esta vaga esta proxima do fechamento. "
            "Sugira ao recrutador preparar a proposta e alinhar com o gestor."
        )
    else:
        lines.append(
            "INSTRUCAO: Compartilhe esta previsao se o recrutador perguntar sobre o andamento da vaga."
        )

    lines.append("=" * 60)
    return "\n".join(lines)


def get_stage_context(stage: str, collected_fields: dict[str, Any]) -> str:
    """Build a formatted context string for the current kanban analysis phase.

    Includes phase information, field completion status, percentage and
    guidance on what the agent should focus on.

    Args:
        stage: Current kanban analysis phase identifier.
        collected_fields: Dictionary of fields already collected and their values.

    Returns:
        Formatted context string for prompt injection.
    """
    stage_def = STAGE_DEFINITIONS.get(stage)
    if not stage_def:
        return f"Estagio desconhecido: {stage}. Trate como visao geral do pipeline."

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
    elif stage_def["phase"] == "overview":
        parts.append(
            "\nFOCO: Forneca visao estrategica do pipeline com metricas e distribuicao."
        )
    elif stage_def["phase"] == "analysis":
        parts.append(
            "\nFOCO: Identifique gargalos, candidatos estagnados e oportunidades de otimizacao."
        )
    elif stage_def["phase"] == "action":
        parts.append(
            "\nFOCO: Execute acoes no pipeline e gere relatorios de analytics."
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
        current_stage: Current kanban analysis phase identifier.
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

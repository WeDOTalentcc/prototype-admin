"""
Jobs Management Stage Context - Provides stage-specific context for the jobs management agent.

Each stage of the job portfolio management workflow has different requirements,
available tools, and goals. This module injects the right context so the agent
knows what to focus on when helping recruiters manage their job portfolio.
"""
from typing import Any

STAGE_DEFINITIONS: dict[str, dict[str, Any]] = {
    "overview": {
        "name": "Visao Geral",
        "display_name": "Visão Geral",
        "description": (
            "Visao inicial do portfolio de vagas. A LIA apresenta o status "
            "geral das vagas ativas, metricas agregadas e destaques que "
            "precisam de atencao do recrutador."
        ),
        "available_tools": ["list_jobs", "view_job_details", "get_portfolio_metrics"],
        "required_fields": ["portfolio_reviewed"],
        "optional_fields": ["active_jobs_count", "metrics_summary"],
        "transition_criteria": {
            "description": "Portfolio foi revisado e recrutador tem visao geral.",
            "required": ["portfolio_reviewed"],
        },
        "next_stage": "analysis",
        "phase": "overview",
    },
    "analysis": {
        "name": "Analise",
        "display_name": "Análise",
        "description": (
            "Analise aprofundada do portfolio. A LIA compara vagas, "
            "identifica gargalos no pipeline, verifica compliance de SLA "
            "e gera insights estrategicos para o recrutador."
        ),
        "available_tools": [
            "compare_jobs", "check_sla", "analyze_bottlenecks",
            "view_job_details", "get_portfolio_metrics",
        ],
        "required_fields": ["analysis_completed"],
        "optional_fields": ["bottlenecks_identified", "sla_checked", "comparison_done"],
        "transition_criteria": {
            "description": "Analise foi concluida e insights foram apresentados.",
            "required": ["analysis_completed"],
        },
        "next_stage": "action",
        "phase": "analysis",
    },
    "action": {
        "name": "Acoes",
        "display_name": "Ações",
        "description": (
            "Execucao de acoes sobre o portfolio. A LIA ajuda a pausar, "
            "reabrir ou fechar vagas, alterar prioridades e gerar "
            "relatorios estrategicos do portfolio."
        ),
        "available_tools": [
            "pause_job", "reopen_job", "close_job",
            "update_priority", "generate_report",
        ],
        "required_fields": ["actions_executed"],
        "optional_fields": ["report_generated", "priorities_updated"],
        "transition_criteria": {
            "description": "Acoes foram executadas e resultados confirmados.",
            "required": ["actions_executed"],
        },
        "next_stage": "complete",
        "phase": "action",
    },
}


def get_pipeline_prediction_block(overview: dict[str, Any]) -> str:
    """
    Gera bloco de previsão de pipeline para injeção no contexto do JobsMgmtAgent.
    Exibe vagas em risco e prestes a fechar do portfolio completo do recrutador.
    Retorna string vazia se não houver dados relevantes.
    """
    vacancies = overview.get("vacancies", [])
    if not vacancies:
        return ""

    at_risk = [v for v in vacancies if v.get("closure_probability", 50) < 30]
    near_close = [v for v in vacancies if v.get("closure_probability", 0) >= 80]

    if not at_risk and not near_close:
        return ""

    lines = ["=== PREVISAO DE PIPELINE — SUAS VAGAS ATIVAS ==="]

    if near_close:
        lines.append("Vagas prestes a fechar (>=80%):")
        for v in near_close[:3]:
            est = v.get("estimated_days_to_close")
            days_str = f" | ~{est}d" if est else ""
            lines.append(
                f"  * {v['vacancy_title']} -> {v['closure_probability']}%{days_str}"
            )

    if at_risk:
        lines.append("Vagas em risco de nao fechar (<30%):")
        for v in at_risk[:3]:
            risks = v.get("risk_factors", [])
            risk_str = f" | {risks[0]}" if risks else ""
            lines.append(
                f"  ! {v['vacancy_title']} -> {v['closure_probability']}%{risk_str}"
            )

    lines.append(
        "INSTRUCAO: Se o recrutador perguntar sobre suas vagas, use esses dados para "
        "priorizar as mais urgentes. Para vagas em risco, sugira acoes proativas."
    )
    lines.append("=" * 60)
    return "\n".join(lines)


def get_stage_context(stage: str, collected_fields: dict[str, Any]) -> str:
    """Build a formatted context string for the current jobs management stage.

    Includes stage information, field completion status, percentage and
    guidance on what the agent should focus on.

    Args:
        stage: Current stage identifier.
        collected_fields: Dictionary of fields already collected and their values.

    Returns:
        Formatted context string for prompt injection.
    """
    stage_def = STAGE_DEFINITIONS.get(stage)
    if not stage_def:
        return f"Estagio desconhecido: {stage}. Trate como visao geral inicial."

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
            "\nFOCO: Apresente a visao geral do portfolio e destaque vagas que precisam de atencao."
        )
    elif stage_def["phase"] == "analysis":
        parts.append(
            "\nFOCO: Analise gargalos, SLA e compare vagas para gerar insights estrategicos."
        )
    elif stage_def["phase"] == "action":
        parts.append(
            "\nFOCO: Execute as acoes solicitadas pelo recrutador sobre o portfolio de vagas."
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
        current_stage: Current stage identifier.
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

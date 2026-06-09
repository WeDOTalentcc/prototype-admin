"""Canonical tool categories — single source of truth for capability discovery.

Sprint 3 (2026-05-24): replaces the hardcoded category list in
`app/shared/prompts/system_prompt_builder.py` (G6 fix) with a registry-derived
view. Tools declare their category via this mapping; the LLM system prompt
groups them dynamically.

Adding a new category: add the constant + its tagline + extend
`TOOL_TO_CATEGORY` for the relevant tools. Adding a tool: add its name to
`TOOL_TO_CATEGORY`. The sensor (Sprint 3.4) blocks PRs that leave new tools
in OTHER.

DRY contract: any string named like "**<category>**:" in a chat prompt or
help text MUST appear in CATEGORY_TAGLINES below. Sensor J enforces.
"""
from __future__ import annotations


# Canonical category names. PT-BR matches LIA chat persona vocabulary.
class ToolCategory:
    VAGAS = "VAGAS"
    CANDIDATOS = "CANDIDATOS"
    COMUNICACAO = "COMUNICAÇÃO"
    AGENDAMENTO = "AGENDAMENTO"
    EMPRESA_CONFIG = "EMPRESA / CONFIG"
    ANALYTICS = "ANALYTICS / RELATÓRIOS"
    TALENT_INTEL = "TALENT INTEL"
    ENTREVISTAS_IA = "ENTREVISTAS (IA)"
    TRIAGEM_WSI = "TRIAGEM WSI"
    DELEGACAO = "DELEGAÇÃO / ESPECIALISTAS"
    OTHER = "OTHER"


# Tagline per category — short PT-BR phrase that goes in the LLM prompt
# BEFORE the comma-separated tool list. Same vocabulary as before Sprint 3
# (preserved from the original G6 hardcoded block).
CATEGORY_TAGLINES: dict[str, str] = {
    ToolCategory.VAGAS: "criar, publicar, pausar, fechar, atualizar, buscar; gerar descrição enriquecida; sugerir salário e skills",
    ToolCategory.CANDIDATOS: "buscar, comparar, analisar CV vs vaga; mover entre etapas (incluindo bulk); aprovar / reprovar / favoritar / ocultar; criar e triar",
    ToolCategory.COMUNICACAO: "enviar email individual ou em massa, WhatsApp, feedback; criar sequências de nurture",
    ToolCategory.AGENDAMENTO: "agendar entrevistas",
    ToolCategory.DELEGACAO: ("quando o pedido for de um DOMINIO ESPECIALIZADO, DELEGUE ao agente do dominio (NUNCA recuse dizendo que nao tem acesso): politicas de contratacao->delegate_to_policy; configurar empresa/beneficios/cultura->delegate_to_company_settings; integracao ATS->delegate_to_ats_integration; sourcing/canais externos->delegate_to_sourcing; analytics/predicoes->delegate_to_analytics; pipeline/kanban->delegate_to_pipeline; banco de talentos->delegate_to_talent_pool; comunicacao->delegate_to_communication; gestao de vagas->delegate_to_job_management"),
    ToolCategory.EMPRESA_CONFIG: "verificar completude do perfil, sugerir política de recrutamento, importar benefícios, salvar política de contratação",
    ToolCategory.ANALYTICS: "gerar relatório, exportar candidatos / vagas; métricas de pipeline, recrutador, qualidade, velocidade, custo; predições ML, forecast de contratação; alertas inteligentes; diversidade",
    ToolCategory.TALENT_INTEL: "bancos de talentos, skills adjacency, skill gaps, reengajamento",
    ToolCategory.ENTREVISTAS_IA: "analisar gravação, detectar viés, gerar parecer, comparar performance",
    ToolCategory.TRIAGEM_WSI: "voice screening completo",
    ToolCategory.OTHER: "ferramentas auxiliares",
}


# Canonical mapping: tool name → category. Source of truth.
# Used by ToolRegistry.apply_category_mapping() to populate
# ToolDefinition.category at registration time.
TOOL_TO_CATEGORY: dict[str, str] = {
    # ---- VAGAS ----
    "create_job": ToolCategory.VAGAS,
    "publish_job": ToolCategory.VAGAS,
    "pause_job": ToolCategory.VAGAS,
    "close_job": ToolCategory.VAGAS,
    "update_job": ToolCategory.VAGAS,
    "reopen_job": ToolCategory.VAGAS,
    "search_jobs": ToolCategory.VAGAS,
    "list_jobs": ToolCategory.VAGAS,
    "get_job_details": ToolCategory.VAGAS,
    "generate_enriched_jd": ToolCategory.VAGAS,
    "get_intelligent_salary": ToolCategory.VAGAS,
    "get_intelligent_skills": ToolCategory.VAGAS,
    "save_job_draft": ToolCategory.VAGAS,
    "import_job_description": ToolCategory.VAGAS,

    # ---- CANDIDATOS ----
    "search_candidates": ToolCategory.CANDIDATOS,
    "compare_candidates": ToolCategory.CANDIDATOS,
    "analyze_cv_match": ToolCategory.CANDIDATOS,
    "update_candidate_stage": ToolCategory.CANDIDATOS,
    "bulk_update_candidates_stage": ToolCategory.CANDIDATOS,
    "shortlist_candidate": ToolCategory.CANDIDATOS,
    "reject_candidate": ToolCategory.CANDIDATOS,
    "hide_candidate": ToolCategory.CANDIDATOS,
    "add_candidate_to_vacancy": ToolCategory.CANDIDATOS,
    "create_and_screen_candidate": ToolCategory.CANDIDATOS,
    "get_candidate_details": ToolCategory.CANDIDATOS,
    "update_candidate_field": ToolCategory.CANDIDATOS,
    "list_candidates": ToolCategory.CANDIDATOS,

    # ---- COMUNICAÇÃO ----
    "send_email": ToolCategory.COMUNICACAO,
    "send_bulk_email": ToolCategory.COMUNICACAO,
    "send_whatsapp": ToolCategory.COMUNICACAO,
    "send_feedback": ToolCategory.COMUNICACAO,
    "create_nurture_sequence": ToolCategory.COMUNICACAO,
    "send_communication": ToolCategory.COMUNICACAO,

    # ---- AGENDAMENTO ----
    "schedule_interview": ToolCategory.AGENDAMENTO,
    "create_generic_event": ToolCategory.AGENDAMENTO,
    "reschedule_interview": ToolCategory.AGENDAMENTO,
    "cancel_interview": ToolCategory.AGENDAMENTO,

    # ---- EMPRESA / CONFIG ----
    "check_company_completeness": ToolCategory.EMPRESA_CONFIG,
    "suggest_recruiting_policy": ToolCategory.EMPRESA_CONFIG,
    "import_benefits_from_data": ToolCategory.EMPRESA_CONFIG,
    "save_hiring_policy": ToolCategory.EMPRESA_CONFIG,

    # ---- ANALYTICS / RELATÓRIOS ----
    "generate_report": ToolCategory.ANALYTICS,
    "export_candidates": ToolCategory.ANALYTICS,
    "export_job_analytics": ToolCategory.ANALYTICS,
    "get_pipeline_stats": ToolCategory.ANALYTICS,
    "get_vacancy_funnel": ToolCategory.ANALYTICS,
    "get_recruiter_metrics": ToolCategory.ANALYTICS,
    "get_velocity_metrics": ToolCategory.ANALYTICS,
    "get_efficiency_metrics": ToolCategory.ANALYTICS,
    "get_cost_metrics": ToolCategory.ANALYTICS,
    "get_quality_metrics": ToolCategory.ANALYTICS,
    "get_ml_predictions": ToolCategory.ANALYTICS,
    "forecast_hiring_needs": ToolCategory.ANALYTICS,
    "get_smart_alerts": ToolCategory.ANALYTICS,
    "get_diversity_metrics": ToolCategory.ANALYTICS,
    "get_activity_summary": ToolCategory.ANALYTICS,
    "get_financial_trends": ToolCategory.ANALYTICS,
    "get_intelligence_overview": ToolCategory.ANALYTICS,
    "get_workload_analysis": ToolCategory.ANALYTICS,

    # ---- TALENT INTEL ----
    "suggest_reengagement": ToolCategory.TALENT_INTEL,
    "get_engagement_metrics": ToolCategory.TALENT_INTEL,
    "infer_related_skills": ToolCategory.TALENT_INTEL,
    "analyze_skill_gaps": ToolCategory.TALENT_INTEL,
    "get_market_intelligence": ToolCategory.TALENT_INTEL,

    # ---- ENTREVISTAS (IA) ----
    "analyze_interview_recording": ToolCategory.ENTREVISTAS_IA,
    "detect_interview_bias": ToolCategory.ENTREVISTAS_IA,
    "generate_interview_opinion": ToolCategory.ENTREVISTAS_IA,
    "compare_interview_performance": ToolCategory.ENTREVISTAS_IA,

    # ---- TRIAGEM WSI ----
    "wsi_screening": ToolCategory.TRIAGEM_WSI,
    "wsi_voice_complete": ToolCategory.TRIAGEM_WSI,

    # ---- Sprint 3.2 batch 2 (2026-05-24) — remaining 32 tools mapped ----
    # VAGAS extras
    "get_job_suggestions": ToolCategory.VAGAS,
    "validate_job_fields": ToolCategory.VAGAS,
    "search_salary_benchmark": ToolCategory.VAGAS,
    "create_pipeline_stage": ToolCategory.VAGAS,
    "get_job_benchmark": ToolCategory.VAGAS,
    "get_job_quality_metrics": ToolCategory.VAGAS,
    "get_job_velocity": ToolCategory.VAGAS,

    # CANDIDATOS extras
    "get_candidate_history": ToolCategory.CANDIDATOS,
    "get_candidate_stats": ToolCategory.CANDIDATOS,
    "generate_candidate_feedback": ToolCategory.CANDIDATOS,
    "map_candidate_skills_to_ontology": ToolCategory.CANDIDATOS,
    "match_internal_candidates": ToolCategory.CANDIDATOS,
    "parse_and_create_candidate": ToolCategory.CANDIDATOS,
    "add_to_list": ToolCategory.CANDIDATOS,
    "add_to_vacancy": ToolCategory.CANDIDATOS,

    # ANALYTICS / RELATÓRIOS extras
    "get_bottleneck_analysis": ToolCategory.ANALYTICS,
    "get_comparative_metrics": ToolCategory.ANALYTICS,
    "get_conversion_patterns": ToolCategory.ANALYTICS,
    "get_hiring_quality": ToolCategory.ANALYTICS,
    "get_market_benchmarks": ToolCategory.ANALYTICS,
    "get_prediction_metrics": ToolCategory.ANALYTICS,
    "get_stakeholder_metrics": ToolCategory.ANALYTICS,
    "get_trends": ToolCategory.ANALYTICS,
    "get_workload_distribution": ToolCategory.ANALYTICS,
    "schedule_report": ToolCategory.ANALYTICS,

    # TALENT INTEL extras
    "get_skill_adjacencies": ToolCategory.TALENT_INTEL,
    "get_talent_availability": ToolCategory.TALENT_INTEL,
    "get_talent_engagement": ToolCategory.TALENT_INTEL,
    "get_talent_quality": ToolCategory.TALENT_INTEL,

    # EMPRESA / CONFIG extras
    "get_company_config": ToolCategory.EMPRESA_CONFIG,
    "capture_wizard_feedback": ToolCategory.EMPRESA_CONFIG,
    "get_pending_actions": ToolCategory.EMPRESA_CONFIG,

    # DELEGACAO / ESPECIALISTAS (supervisor A2 handoffs)
    "delegate_to_pipeline": ToolCategory.DELEGACAO,
    "delegate_to_talent_pool": ToolCategory.DELEGACAO,
    "delegate_to_sourcing": ToolCategory.DELEGACAO,
    "delegate_to_communication": ToolCategory.DELEGACAO,
    "delegate_to_analytics": ToolCategory.DELEGACAO,
    "delegate_to_company_settings": ToolCategory.DELEGACAO,
    "delegate_to_policy": ToolCategory.DELEGACAO,
    "delegate_to_ats_integration": ToolCategory.DELEGACAO,
    "delegate_to_job_management": ToolCategory.DELEGACAO,
}


def category_for_tool(tool_name: str) -> str:
    """Return the canonical category for a tool, OTHER if unmapped."""
    return TOOL_TO_CATEGORY.get(tool_name, ToolCategory.OTHER)


# Display order for system prompt (matches old G6 hardcoded order).
DISPLAY_ORDER: list[str] = [
    ToolCategory.VAGAS,
    ToolCategory.CANDIDATOS,
    ToolCategory.DELEGACAO,
    ToolCategory.COMUNICACAO,
    ToolCategory.AGENDAMENTO,
    ToolCategory.EMPRESA_CONFIG,
    ToolCategory.ANALYTICS,
    ToolCategory.TALENT_INTEL,
    ToolCategory.ENTREVISTAS_IA,
    ToolCategory.TRIAGEM_WSI,
]

"""
Policy Stage Context - Provides stage-specific context for the policy agent.

The policy configuration flow has 3 stages:
1. onboarding - Initial setup of hiring policies
2. review - Reviewing/editing existing policies
3. consulting - Answering questions about policy impact
"""
from typing import Any

STAGE_DEFINITIONS: dict[str, dict[str, Any]] = {
    "onboarding": {
        "name": "Onboarding",
        "display_name": "Configuracao Inicial",
        "description": (
            "Configuracao inicial das politicas de contratacao da empresa. "
            "A LIA guia o recrutador por todos os blocos de configuracao "
            "(Pipeline, Agendamento, Comunicacao, Triagem, Autonomia) de forma "
            "conversacional e consultiva."
        ),
        "available_tools": [
            "get_current_policy", "save_policy_field", "save_policy_block",
            "get_policy_summary", "validate_policy_compliance", "get_company_context",
            "get_industry_benchmarks", "get_platform_benchmarks", "explain_policy_impact",
            "get_setup_progress", "apply_industry_defaults",
            "detect_policy_impact_anomalies", "get_policy_effectiveness_report",
        ],
        "required_fields": ["pipeline_rules_configured", "automation_rules_configured"],
        "optional_fields": [
            "scheduling_rules_configured", "communication_rules_configured",
            "screening_rules_configured",
        ],
        "transition_criteria": {
            "description": "Pelo menos Pipeline e Autonomia foram configurados.",
            "required": ["pipeline_rules_configured", "automation_rules_configured"],
        },
        "next_stage": "review",
        "phase": "setup",
    },
    "review": {
        "name": "Review",
        "display_name": "Revisao de Politicas",
        "description": (
            "Revisao e edicao de politicas ja configuradas. O recrutador pode "
            "alterar qualquer configuracao, ver o resumo atual e ajustar "
            "parametros com base na experiencia operacional."
        ),
        "available_tools": [
            "get_current_policy", "save_policy_field", "save_policy_block",
            "get_policy_summary", "validate_policy_compliance", "get_company_context",
            "get_industry_benchmarks", "get_platform_benchmarks", "explain_policy_impact",
            "get_setup_progress", "apply_industry_defaults",
            "detect_policy_impact_anomalies", "get_policy_effectiveness_report",
        ],
        "required_fields": [],
        "optional_fields": [],
        "transition_criteria": {
            "description": "Nenhuma transicao obrigatoria, o recrutador pode revisar a qualquer momento.",
            "required": [],
        },
        "next_stage": "review",
        "phase": "maintenance",
    },
    "consulting": {
        "name": "Consulting",
        "display_name": "Consultoria de Politicas",
        "description": (
            "Modo consultivo onde o recrutador faz perguntas sobre o impacto "
            "das politicas configuradas, pede benchmarks do setor ou quer "
            "entender as consequencias de uma mudanca."
        ),
        "available_tools": [
            "get_current_policy", "get_policy_summary",
            "get_company_context", "get_industry_benchmarks", "get_platform_benchmarks",
            "explain_policy_impact", "get_setup_progress",
            "detect_policy_impact_anomalies", "get_policy_effectiveness_report",
        ],
        "required_fields": [],
        "optional_fields": [],
        "transition_criteria": {
            "description": "Retorno automatico ao review quando o recrutador quiser editar.",
            "required": [],
        },
        "next_stage": "review",
        "phase": "advisory",
    },
}

POLICY_BLOCKS = {
    "pipeline_rules": {
        "name": "Pipeline e Processo",
        "fields": {
            "min_interviews_before_offer": {
                "label": "Entrevistas minimas antes da proposta",
                "type": "integer",
                "default": 2,
                "hint": "Quantas entrevistas o candidato deve passar antes de receber proposta",
            },
            "manager_approval_for_offer": {
                "label": "Aprovacao do gestor para proposta",
                "type": "boolean",
                "default": True,
                "hint": "Se a proposta salarial precisa de aprovacao do gestor",
            },
            "max_days_in_stage": {
                "label": "Maximo de dias por etapa",
                "type": "stage_days",
                "default": {},
                "hint": "Tempo maximo em dias que candidato pode ficar em cada etapa",
            },
            "pipeline_templates": {
                "label": "Templates de pipeline",
                "type": "templates",
                "default": [],
                "hint": "Tipos de vagas com processos diferentes",
            },
        },
    },
    "scheduling_rules": {
        "name": "Agendamento",
        "fields": {
            "allowed_days": {
                "label": "Dias permitidos para entrevistas",
                "type": "days",
                "default": ["mon", "tue", "wed", "thu", "fri"],
                "hint": "Dias da semana validos para agendar entrevistas",
            },
            "allowed_hours": {
                "label": "Horarios permitidos",
                "type": "hours",
                "default": {"start": "09:00", "end": "18:00"},
                "hint": "Janela de horarios para entrevistas",
            },
            "default_duration_minutes": {
                "label": "Duracao padrao em minutos",
                "type": "integer",
                "default": 60,
                "hint": "Tempo padrao de cada entrevista",
            },
            "self_scheduling_enabled": {
                "label": "Auto-agendamento",
                "type": "boolean",
                "default": False,
                "hint": "Se o candidato pode escolher o horario sozinho",
            },
        },
    },
    "communication_rules": {
        "name": "Comunicacao",
        "fields": {
            "auto_rejection_feedback": {
                "label": "Feedback automatico de reprovacao",
                "type": "boolean",
                "default": False,
                "hint": "Se reprovados recebem feedback automaticamente",
            },
            "rejection_feedback_deadline_hours": {
                "label": "Prazo para feedback (horas)",
                "type": "integer",
                "default": 48,
                "hint": "Tempo maximo para enviar feedback de reprovacao",
            },
            "preferred_channel": {
                "label": "Canal preferido",
                "type": "channel",
                "default": "whatsapp",
                "hint": "Canal principal para falar com candidatos",
            },
            "lia_tone": {
                "label": "Tom da LIA",
                "type": "tone",
                "default": "professional",
                "hint": "Estilo de comunicacao da LIA",
            },
        },
    },
    "screening_rules": {
        "name": "Triagem",
        "fields": {
            "salary_expectation_filter": {
                "label": "Filtro por pretensao salarial",
                "type": "boolean",
                "default": False,
                "hint": "Se candidatos sao filtrados por pretensao salarial",
            },
            "salary_tolerance_percent": {
                "label": "Tolerancia percentual de salario",
                "type": "integer",
                "default": 15,
                "hint": "Margem percentual aceita acima do budget",
            },
            "experience_policy": {
                "label": "Politica de experiencia",
                "type": "experience",
                "default": "per_job",
                "hint": "Se experiencia minima e definida por vaga ou e padrao geral",
            },
            "default_screening_questions": {
                "label": "Perguntas padrao de triagem",
                "type": "questions_list",
                "default": [],
                "hint": "Perguntas que valem para todas as vagas",
            },
        },
    },
    "automation_rules": {
        "name": "Autonomia da LIA",
        "fields": {
            "auto_screening": {
                "label": "Triagem automatica",
                "type": "boolean",
                "default": False,
                "hint": "Se a LIA pode triar candidatos sem confirmacao",
            },
            "auto_scheduling": {
                "label": "Agendamento automatico",
                "type": "boolean",
                "default": False,
                "hint": "Se a LIA pode agendar entrevistas automaticamente",
            },
            "auto_stage_advance": {
                "label": "Avanco automatico de etapa",
                "type": "boolean",
                "default": False,
                "hint": "Se a LIA pode mover candidatos de etapa automaticamente",
            },
            "autonomy_level": {
                "label": "Nivel geral de autonomia",
                "type": "autonomy",
                "default": "low",
                "hint": "Baixo=sempre confirma, Medio=confirma alto impacto, Alto=age e notifica",
            },
        },
    },
}


def get_stage_context(stage: str, policy_state: dict[str, Any]) -> str:
    stage_def = STAGE_DEFINITIONS.get(stage)
    if not stage_def:
        return f"Estagio desconhecido: {stage}. Tratando como onboarding."

    configured_blocks = []
    missing_blocks = []

    for block_key, block_info in POLICY_BLOCKS.items():
        block_data = policy_state.get(block_key, {})
        has_data = bool(block_data) and any(
            v not in (None, "", [], {})
            for v in block_data.values()
            if not isinstance(v, bool) or v is True
        )
        if has_data:
            configured_blocks.append(block_info["name"])
        else:
            missing_blocks.append(block_info["name"])

    total = len(POLICY_BLOCKS)
    configured = len(configured_blocks)
    completion = (configured / total * 100) if total > 0 else 0

    parts = [
        "=== CONTEXTO DO ESTAGIO ===",
        f"Estagio atual: {stage_def['display_name']} ({stage})",
        f"Fase: {stage_def['phase']}",
        f"Descricao: {stage_def['description']}",
        "",
        "--- Progresso ---",
        f"Completude: {completion:.0f}% ({configured}/{total} blocos)",
    ]

    if configured_blocks:
        parts.append(f"Blocos configurados: {', '.join(configured_blocks)}")

    if missing_blocks:
        parts.append(f"Blocos pendentes: {', '.join(missing_blocks)}")

    if stage == "onboarding":
        if missing_blocks:
            parts.append(
                f"\nFOCO: Guie o recrutador pelos blocos pendentes. "
                f"Sugira comecar por: {missing_blocks[0]}"
            )
        else:
            parts.append(
                "\nFOCO: Todas as politicas foram configuradas. "
                "Pergunte se quer revisar algo ou se esta satisfeito."
            )
    elif stage == "review":
        parts.append(
            "\nFOCO: O recrutador quer revisar ou alterar politicas existentes. "
            "Mostre o estado atual e permita edicoes."
        )
    elif stage == "consulting":
        parts.append(
            "\nFOCO: O recrutador quer entender o impacto das politicas. "
            "Explique consequencias, benchmarks e trade-offs."
        )

    return "\n".join(parts)


def get_transition_prompt(current_stage: str, policy_state: dict[str, Any]) -> str:
    stage_def = STAGE_DEFINITIONS.get(current_stage)
    if not stage_def:
        return "Estagio desconhecido."

    parts = [
        f"Avaliacao de transicao para o estagio '{current_stage}':",
        f"Criterio: {stage_def['transition_criteria']['description']}",
    ]

    return "\n".join(parts)

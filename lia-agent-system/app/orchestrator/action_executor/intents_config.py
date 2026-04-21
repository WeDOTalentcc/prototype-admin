"""
Configuration constants for ActionExecutor:
  - ACTIONABLE_INTENTS: all supported intent → action mappings
  - CONFIRMATION_PATTERNS / REJECTION_PATTERNS
  - VALID_PIPELINE_STAGES / STAGE_ALIASES
  - MESSAGE_INTENT_PATTERNS: regex patterns for intent detection from raw message
"""
from typing import Any

ACTIONABLE_INTENTS: dict[str, dict[str, Any]] = {
    "mover_candidato": {
        "domain_id": "pipeline_transition",
        "action_id": "move_candidate",
        "required_params": ["candidate_id", "to_stage"],
        "optional_params": ["from_stage", "sub_status", "reason"],
        "risk_level": "medium",
        "requires_confirmation": True,
        "param_labels": {
            "candidate_id": "candidato",
            "to_stage": "etapa destino",
        },
        "clarification_prompts": {
            "candidate_id": "Qual candidato você quer mover?",
            "to_stage": "Para qual etapa do pipeline?",
        },
    },
    "atualizar_status_candidato": {
        "domain_id": "pipeline_transition",
        "action_id": "move_candidate",
        "required_params": ["candidate_id", "to_stage"],
        "optional_params": ["from_stage", "sub_status"],
        "risk_level": "medium",
        "requires_confirmation": True,
        "param_labels": {
            "candidate_id": "candidato",
            "to_stage": "etapa destino",
        },
        "clarification_prompts": {
            "candidate_id": "Qual candidato você quer atualizar?",
            "to_stage": "Para qual etapa?",
        },
    },
    "reprovar_candidato": {
        "domain_id": "pipeline_transition",
        "action_id": "move_candidate",
        "required_params": ["candidate_id"],
        "optional_params": ["reason", "feedback_message"],
        "risk_level": "high",
        "requires_confirmation": True,
        "default_params": {"to_stage": "Reprovado"},
        "param_labels": {"candidate_id": "candidato"},
        "clarification_prompts": {
            "candidate_id": "Qual candidato você quer reprovar?",
        },
    },
    "reject_candidate": {
        "domain_id": "pipeline_transition",
        "action_id": "reject_candidate",
        "required_params": [],
        "optional_params": ["candidate_id", "candidate_name", "vacancy_id", "reason", "confirmed"],
        "risk_level": "high",
        "requires_confirmation": False,  # handler manages its own confirmation gate
        "param_labels": {"candidate_name": "candidato", "reason": "motivo"},
        "clarification_prompts": {},
    },
    "aprovar_candidato": {
        "domain_id": "pipeline_transition",
        "action_id": "move_candidate",
        "required_params": ["candidate_id"],
        "optional_params": ["to_stage", "reason"],
        "risk_level": "medium",
        "requires_confirmation": True,
        "param_labels": {"candidate_id": "candidato"},
        "clarification_prompts": {
            "candidate_id": "Qual candidato você quer aprovar?",
        },
    },
    "enviar_email": {
        "domain_id": "communication",
        "action_id": "send_email",
        "required_params": ["candidate_id", "subject", "body"],
        "optional_params": ["template_id", "cc"],
        "risk_level": "high",
        "requires_confirmation": True,
        "param_labels": {
            "candidate_id": "candidato",
            "subject": "assunto",
            "body": "mensagem",
        },
        "clarification_prompts": {
            "candidate_id": "Para qual candidato quer enviar o email?",
            "subject": "Qual o assunto do email?",
            "body": "Qual a mensagem que quer enviar?",
        },
    },
    "enviar_mensagem": {
        "domain_id": "communication",
        "action_id": "send_email",
        "required_params": ["candidate_id", "subject", "body"],
        "optional_params": ["template_id"],
        "risk_level": "high",
        "requires_confirmation": True,
        "param_labels": {
            "candidate_id": "candidato",
            "subject": "assunto",
            "body": "mensagem",
        },
        "clarification_prompts": {
            "candidate_id": "Para qual candidato?",
            "subject": "Qual o assunto?",
            "body": "Qual a mensagem?",
        },
    },
    "agendar_entrevista": {
        "domain_id": "interview_scheduling",
        "action_id": "schedule_interview",
        "required_params": ["candidate_id", "datetime"],
        "optional_params": ["interviewer", "type", "location"],
        "risk_level": "medium",
        "requires_confirmation": True,
        "param_labels": {
            "candidate_id": "candidato",
            "datetime": "data e hora",
            "interviewer": "entrevistador",
        },
        "clarification_prompts": {
            "candidate_id": "Com qual candidato quer agendar?",
            "datetime": "Para qual data e horário?",
        },
    },
    "disparar_triagem": {
        "domain_id": "cv_screening",
        "action_id": "start_screening",
        "required_params": [],
        "optional_params": ["candidate_ids"],
        "risk_level": "low",
        "requires_confirmation": False,
        "param_labels": {},
        "clarification_prompts": {},
    },
    "iniciar_triagem": {
        "domain_id": "cv_screening",
        "action_id": "start_screening",
        "required_params": [],
        "optional_params": ["candidate_ids"],
        "risk_level": "low",
        "requires_confirmation": False,
        "param_labels": {},
        "clarification_prompts": {},
    },
    "analisar_perfil": {
        "domain_id": "cv_screening",
        "action_id": "analyze_profile",
        "required_params": [],  # CM-001: candidate_id or candidate_name resolved in handler
        "optional_params": ["candidate_id", "candidate_name", "vacancy_id", "job_vacancy_id"],
        "risk_level": "low",
        "requires_confirmation": False,
        "param_labels": {"candidate_id": "candidato"},
        "clarification_prompts": {
            "candidate_id": "Qual candidato quer analisar?",
        },
    },
    "analise_detalhada": {
        "domain_id": "cv_screening",
        "action_id": "analyze_profile",
        "required_params": [],  # CM-001: candidate_id or candidate_name resolved in handler
        "optional_params": ["candidate_id", "candidate_name", "vacancy_id", "job_vacancy_id"],
        "risk_level": "low",
        "requires_confirmation": False,
        "param_labels": {"candidate_id": "candidato"},
        "clarification_prompts": {
            "candidate_id": "Qual candidato quer analisar em detalhe?",
        },
    },
    "pausar_vaga": {
        "domain_id": "job_management",
        "action_id": "pause_job",
        "required_params": ["job_id"],
        "optional_params": ["reason"],
        "risk_level": "medium",
        "requires_confirmation": True,
        "param_labels": {
            "job_id": "vaga",
            "reason": "motivo",
        },
        "clarification_prompts": {
            "job_id": "Qual vaga você quer pausar?",
            "reason": "Qual o motivo da pausa?",
        },
    },
    "fechar_vaga": {
        "domain_id": "job_management",
        "action_id": "close_job",
        "required_params": ["job_id"],
        "optional_params": ["reason", "outcome"],
        "risk_level": "high",
        "requires_confirmation": True,
        "param_labels": {
            "job_id": "vaga",
            "reason": "motivo",
            "outcome": "resultado",
        },
        "clarification_prompts": {
            "job_id": "Qual vaga você quer fechar?",
            "reason": "Qual o motivo do fechamento?",
            "outcome": "Qual foi o resultado do processo?",
        },
    },
    "duplicar_vaga": {
        "domain_id": "job_management",
        "action_id": "duplicate_job",
        "required_params": [],
        "optional_params": ["job_id", "job_title", "new_title"],
        "risk_level": "low",
        "requires_confirmation": False,
        "param_labels": {
            "job_id": "vaga",
            "new_title": "novo título",
        },
        "clarification_prompts": {
            "job_id": "Qual vaga você quer duplicar?",
            "new_title": "Qual o título da nova vaga?",
        },
    },
    "reabrir_vaga": {
        "domain_id": "job_management",
        "action_id": "reopen_job",
        "required_params": ["job_id"],
        "optional_params": [],
        "risk_level": "medium",
        "requires_confirmation": True,
        "param_labels": {
            "job_id": "vaga",
        },
        "clarification_prompts": {
            "job_id": "Qual vaga você quer reabrir?",
        },
    },
    "atualizar_campo_candidato": {
        "domain_id": "pipeline_transition",
        "action_id": "update_candidate_field",
        "required_params": ["candidate_id", "field_name", "field_value"],
        "optional_params": [],
        "risk_level": "medium",
        "requires_confirmation": True,
        "param_labels": {
            "candidate_id": "candidato",
            "field_name": "campo",
            "field_value": "novo valor",
        },
        "clarification_prompts": {
            "candidate_id": "Qual candidato você quer atualizar?",
            "field_name": "Qual campo deseja atualizar? (email, telefone, linkedin, cargo atual, empresa, cidade, estado, salário CLT, salário PJ, modelo de trabalho, formação, idiomas, disponibilidade)",
            "field_value": "Qual o novo valor para esse campo?",
        },
    },
    "criar_tarefa": {
        "domain_id": "automation",
        "action_id": "create_task",
        "required_params": ["title"],
        "optional_params": ["due_date", "candidate_id", "job_id", "description", "priority"],
        "risk_level": "low",
        "requires_confirmation": False,
        "param_labels": {
            "title": "título da tarefa",
            "due_date": "prazo",
        },
        "clarification_prompts": {
            "title": "Qual o título da tarefa que deseja criar?",
        },
    },
    "criar_lembrete": {
        "domain_id": "automation",
        "action_id": "create_task",
        "required_params": ["title"],
        "optional_params": ["due_date", "candidate_id", "job_id", "description"],
        "risk_level": "low",
        "requires_confirmation": False,
        "default_params": {"priority": "high", "task_type": "reminder"},
        "param_labels": {
            "title": "título do lembrete",
            "due_date": "data/hora do lembrete",
        },
        "clarification_prompts": {
            "title": "Qual lembrete deseja criar?",
        },
    },
    "criar_nota": {
        "domain_id": "automation",
        "action_id": "create_note",
        "required_params": ["content"],
        "optional_params": ["candidate_id", "job_id", "title"],
        "risk_level": "low",
        "requires_confirmation": False,
        "param_labels": {
            "content": "conteúdo da nota",
            "candidate_id": "candidato",
            "job_id": "vaga",
        },
        "clarification_prompts": {
            "content": "Qual o conteúdo da nota que deseja salvar?",
        },
    },
    "anotar": {
        "domain_id": "automation",
        "action_id": "create_note",
        "required_params": ["content"],
        "optional_params": ["candidate_id", "job_id", "title"],
        "risk_level": "low",
        "requires_confirmation": False,
        "param_labels": {
            "content": "conteúdo da nota",
        },
        "clarification_prompts": {
            "content": "O que deseja anotar?",
        },
    },
    "criar_compromisso": {
        "domain_id": "interview_scheduling",
        "action_id": "create_generic_event",
        "required_params": ["title", "datetime"],
        "optional_params": ["description", "location", "duration_minutes"],
        "risk_level": "low",
        "requires_confirmation": True,
        "param_labels": {
            "title": "título do compromisso",
            "datetime": "data e hora",
            "description": "descrição",
            "location": "local",
        },
        "clarification_prompts": {
            "title": "Qual o título do compromisso?",
            "datetime": "Para qual data e horário?",
        },
    },
    "resumo_agenda": {
        "domain_id": "recruiter_assistant",
        "action_id": "generate_daily_briefing",
        "required_params": [],
        "optional_params": ["date"],
        "risk_level": "low",
        "requires_confirmation": False,
        "param_labels": {},
        "clarification_prompts": {},
    },
    "enviar_feedback": {
        "domain_id": "communication",
        "action_id": "send_feedback",
        "required_params": ["candidate_id"],
        "optional_params": ["feedback_type", "message", "job_id"],
        "risk_level": "high",
        "requires_confirmation": True,
        "param_labels": {
            "candidate_id": "candidato",
            "feedback_type": "tipo de feedback (aprovação/rejeição/parcial)",
            "message": "mensagem personalizada",
        },
        "clarification_prompts": {
            "candidate_id": "Para qual candidato deseja enviar o feedback?",
        },
    },
    "enviar_whatsapp": {
        "domain_id": "communication",
        "action_id": "send_whatsapp",
        "required_params": ["candidate_id", "message"],
        "optional_params": ["template_id"],
        "risk_level": "high",
        "requires_confirmation": True,
        "param_labels": {
            "candidate_id": "candidato",
            "message": "mensagem",
        },
        "clarification_prompts": {
            "candidate_id": "Para qual candidato deseja enviar o WhatsApp?",
            "message": "Qual a mensagem que deseja enviar?",
        },
    },
    "enviar_convite_triagem": {
        "domain_id": "communication",
        "action_id": "send_screening_invite",
        "required_params": ["candidate_id"],
        "optional_params": ["job_id", "screening_type"],
        "risk_level": "medium",
        "requires_confirmation": True,
        "param_labels": {
            "candidate_id": "candidato",
        },
        "clarification_prompts": {
            "candidate_id": "Para qual candidato deseja enviar o convite de triagem?",
        },
    },
    "reagendar_entrevista": {
        "domain_id": "interview_scheduling",
        "action_id": "reschedule_interview",
        "required_params": ["candidate_id", "new_datetime"],
        "optional_params": ["interview_id", "reason"],
        "risk_level": "medium",
        "requires_confirmation": True,
        "param_labels": {
            "candidate_id": "candidato",
            "new_datetime": "nova data e hora",
        },
        "clarification_prompts": {
            "candidate_id": "Qual candidato deseja reagendar?",
            "new_datetime": "Para qual nova data e horário?",
        },
    },
    "cancelar_entrevista": {
        "domain_id": "interview_scheduling",
        "action_id": "cancel_interview",
        "required_params": ["candidate_id"],
        "optional_params": ["interview_id", "reason", "notify_candidate"],
        "risk_level": "high",
        "requires_confirmation": True,
        "param_labels": {
            "candidate_id": "candidato",
        },
        "clarification_prompts": {
            "candidate_id": "Qual candidato tem a entrevista que deseja cancelar?",
        },
    },
    "enviar_lembrete_entrevista": {
        "domain_id": "interview_scheduling",
        "action_id": "send_interview_reminder",
        "required_params": ["candidate_id"],
        "optional_params": ["interview_id"],
        "risk_level": "low",
        "requires_confirmation": False,
        "param_labels": {
            "candidate_id": "candidato",
        },
        "clarification_prompts": {
            "candidate_id": "Para qual candidato deseja enviar o lembrete?",
        },
    },
    "listar_entrevistas_hoje": {
        "domain_id": "interview_scheduling",
        "action_id": "list_today_interviews",
        "required_params": [],
        "optional_params": ["date"],
        "risk_level": "low",
        "requires_confirmation": False,
        "param_labels": {},
        "clarification_prompts": {},
    },
    "gerar_link_agendamento": {
        "domain_id": "interview_scheduling",
        "action_id": "generate_self_scheduling_link",
        "required_params": ["candidate_id"],
        "optional_params": ["job_id", "duration_minutes"],
        "risk_level": "low",
        "requires_confirmation": False,
        "param_labels": {
            "candidate_id": "candidato",
        },
        "clarification_prompts": {
            "candidate_id": "Para qual candidato deseja gerar o link?",
        },
    },
    "taguear_candidatos": {
        "domain_id": "sourcing",
        "action_id": "tag_candidates",
        "required_params": ["candidate_ids", "tag"],
        "optional_params": ["list_name"],
        "risk_level": "low",
        "requires_confirmation": False,
        "param_labels": {
            "candidate_ids": "candidatos",
            "tag": "tag/etiqueta",
        },
        "clarification_prompts": {
            "candidate_ids": "Quais candidatos deseja taguear?",
            "tag": "Qual tag deseja aplicar?",
        },
    },
    "rankear_candidatos": {
        "domain_id": "sourcing",
        "action_id": "rank_candidates",
        "required_params": [],
        "optional_params": ["job_id", "criteria", "limit"],
        "risk_level": "low",
        "requires_confirmation": False,
        "param_labels": {},
        "clarification_prompts": {},
    },
    "comparar_candidatos": {
        "domain_id": "sourcing",
        "action_id": "compare_candidates",
        "required_params": [],  # CM-003: candidate_ids or candidate_names resolved in handler
        "optional_params": ["candidate_ids", "candidate_names", "job_id", "criteria"],
        "risk_level": "low",
        "requires_confirmation": False,
        "param_labels": {
            "candidate_ids": "candidatos para comparar",
        },
        "clarification_prompts": {
            "candidate_ids": "Quais candidatos deseja comparar? (Selecione pelo menos 2)",
        },
    },
    "buscar_candidatos": {
        "domain_id": "sourcing",
        "action_id": "search_candidates",
        "required_params": ["query"],
        "optional_params": ["filters", "limit"],
        "risk_level": "low",
        "requires_confirmation": False,
        "param_labels": {
            "query": "critério de busca",
        },
        "clarification_prompts": {
            "query": "Quais critérios de busca deseja usar?",
        },
    },
    "sugerir_candidatos": {
        "domain_id": "sourcing",
        "action_id": "suggest_candidates",
        "required_params": [],
        "optional_params": ["job_id", "limit"],
        "risk_level": "low",
        "requires_confirmation": False,
        "param_labels": {},
        "clarification_prompts": {},
    },
    "adicionar_candidato": {
        "domain_id": "sourcing",
        "action_id": "add_candidate",
        "required_params": ["name", "email"],
        "optional_params": ["phone", "current_title", "current_company", "job_id"],
        "risk_level": "medium",
        "requires_confirmation": True,
        "param_labels": {
            "name": "nome",
            "email": "email",
        },
        "clarification_prompts": {
            "name": "Qual o nome do candidato?",
            "email": "Qual o email do candidato?",
        },
    },
    "exportar_candidatos": {
        "domain_id": "sourcing",
        "action_id": "export_candidates",
        "required_params": [],
        "optional_params": ["job_id", "format", "filters"],
        "risk_level": "medium",
        "requires_confirmation": True,
        "param_labels": {},
        "clarification_prompts": {},
    },
    "gerar_relatorio_kpi": {
        "domain_id": "analytics",
        "action_id": "generate_kpi_report",
        "required_params": [],
        "optional_params": ["period", "job_id", "metrics"],
        "risk_level": "low",
        "requires_confirmation": False,
        "param_labels": {},
        "clarification_prompts": {},
    },
    "enviar_relatorio_candidato": {
        "domain_id": "communication",
        "action_id": "send_candidate_report",
        "required_params": ["candidate_id"],
        "optional_params": ["recipient_email", "job_id"],
        "risk_level": "medium",
        "requires_confirmation": True,
        "param_labels": {
            "candidate_id": "candidato",
        },
        "clarification_prompts": {
            "candidate_id": "Sobre qual candidato deseja enviar o parecer?",
        },
    },
    "enviar_relatorio_progresso": {
        "domain_id": "communication",
        "action_id": "send_progress_report",
        "required_params": ["job_id"],
        "optional_params": ["recipient_email", "format"],
        "risk_level": "medium",
        "requires_confirmation": True,
        "param_labels": {
            "job_id": "vaga",
        },
        "clarification_prompts": {
            "job_id": "De qual vaga deseja enviar o relatório de progresso?",
        },
    },
    "criar_automacao": {
        "domain_id": "automation",
        "action_id": "create_automation",
        "required_params": ["trigger", "action"],
        "optional_params": ["job_id", "stage", "conditions"],
        "risk_level": "medium",
        "requires_confirmation": True,
        "param_labels": {
            "trigger": "gatilho",
            "action": "ação automática",
        },
        "clarification_prompts": {
            "trigger": "Qual o gatilho da automação? (ex: candidato entra na etapa X)",
            "action": "Qual ação deve ser executada automaticamente?",
        },
    },
    "alertas_proativos": {
        "domain_id": "automation",
        "action_id": "check_proactive_alerts",
        "required_params": [],
        "optional_params": ["job_id"],
        "risk_level": "low",
        "requires_confirmation": False,
        "param_labels": {},
        "clarification_prompts": {},
    },
    "favoritar_candidato": {
        "domain_id": "sourcing",
        "action_id": "favorite_candidate",
        "required_params": ["candidate_id"],
        "optional_params": ["job_id"],
        "risk_level": "low",
        "requires_confirmation": False,
        "param_labels": {
            "candidate_id": "candidato",
        },
        "clarification_prompts": {
            "candidate_id": "Qual candidato deseja adicionar aos favoritos?",
        },
    },
    "vaga_urgente": {
        "domain_id": "job_management",
        "action_id": "set_job_urgent",
        "required_params": ["job_id"],
        "optional_params": ["reason"],
        "risk_level": "medium",
        "requires_confirmation": True,
        "param_labels": {
            "job_id": "vaga",
        },
        "clarification_prompts": {
            "job_id": "Qual vaga deseja classificar como urgente?",
        },
    },
    "compartilhar_candidato": {
        "domain_id": "communication",
        "action_id": "share_candidate_profile",
        "required_params": ["candidate_id"],
        "optional_params": ["recipient_email", "recipient_name", "message"],
        "risk_level": "medium",
        "requires_confirmation": True,
        "param_labels": {
            "candidate_id": "candidato",
        },
        "clarification_prompts": {
            "candidate_id": "Qual candidato deseja compartilhar?",
        },
    },
    "mover_candidatos_lote": {
        "domain_id": "pipeline_transition",
        "action_id": "batch_move_candidates",
        "required_params": ["candidate_ids", "to_stage"],
        "optional_params": ["from_stage", "reason"],
        "risk_level": "high",
        "requires_confirmation": True,
        "param_labels": {
            "candidate_ids": "candidatos",
            "to_stage": "etapa destino",
        },
        "clarification_prompts": {
            "candidate_ids": "Quais candidatos deseja mover?",
            "to_stage": "Para qual etapa do pipeline?",
        },
    },
    "health_check_vaga": {
        "domain_id": "analytics",
        "action_id": "job_health_check",
        "required_params": [],
        "optional_params": ["job_id"],
        "risk_level": "low",
        "requires_confirmation": False,
        "param_labels": {},
        "clarification_prompts": {},
    },
    "analisar_funil": {
        "domain_id": "analytics",
        "action_id": "analyze_funnel",
        "required_params": [],
        "optional_params": ["job_id", "period"],
        "risk_level": "low",
        "requires_confirmation": False,
        "param_labels": {},
        "clarification_prompts": {},
    },
    "vagas_sem_candidatos": {
        "domain_id": "analytics",
        "action_id": "vacancies_without_candidates",
        "required_params": [],
        "optional_params": ["days"],
        "risk_level": "read",
        "requires_confirmation": False,
        "param_labels": {"days": "dias"},
    },
    "mover_candidatos_por_etapa": {
        "domain_id": "pipeline_transition",
        "action_id": "bulk_move_by_stage",
        "required_params": ["job_id", "from_stage", "to_stage"],
        "optional_params": [],
        "risk_level": "high",
        "requires_confirmation": True,
        "param_labels": {
            "job_id": "vaga",
            "from_stage": "etapa de origem",
            "to_stage": "etapa destino",
        },
        "clarification_prompts": {
            "job_id": "Qual vaga você quer usar?",
            "from_stage": "De qual etapa quer mover os candidatos?",
            "to_stage": "Para qual etapa quer movê-los?",
        },
    },
    "listar_candidatos_por_etapa": {
        "domain_id": "analytics",
        "action_id": "list_candidates_by_stage",
        "required_params": [],
        "optional_params": ["job_id", "stage"],
        "risk_level": "low",
        "requires_confirmation": False,
        "param_labels": {
            "job_id": "vaga",
            "stage": "etapa",
        },
        "clarification_prompts": {
            "job_id": "Para qual vaga você quer listar os candidatos?",
        },
    },
    "sugerir_salario": {
        "domain_id": "job_management",
        "action_id": "suggest_salary",
        "required_params": ["job_title"],
        "optional_params": ["location", "seniority", "years_experience"],
        "risk_level": "read",
        "requires_confirmation": False,
    },
    "gerar_jd": {
        "domain_id": "job_management",
        "action_id": "generate_jd_direct",
        "required_params": ["job_title"],
        "optional_params": ["skills", "requirements", "seniority"],
        "risk_level": "read",
        "requires_confirmation": False,
    },
    "lia_identidade": {
        "domain_id": "direct_response",
        "action_id": "respond_identity",
        "required_params": [],
        "optional_params": [],
        "risk_level": "read",
        "requires_confirmation": False,
    },
}

CONFIRMATION_PATTERNS = [
    "sim", "pode", "confirmo", "confirma", "ok", "vamos",
    "pode sim", "manda", "envia", "faz isso", "tá bom",
    "perfeito", "isso mesmo", "correto", "exato", "avança",
    "prossiga", "pode mandar", "manda ver", "vai lá",
    "yes", "go", "confirm", "approved", "claro", "com certeza",
    "pode fazer", "autorizo", "está certo", "está correto",
    "tudo certo", "beleza", "show", "bora",
]

REJECTION_PATTERNS = [
    "não", "cancela", "para", "espera", "mudei de ideia",
    "deixa", "esquece", "cancelar", "no", "cancel", "stop",
    "não quero", "desistir", "abortar", "parar", "não pode",
    "errado", "incorreto", "refazer", "voltar", "desfazer",
]

VALID_PIPELINE_STAGES = [
    "Novo", "Triagem", "Entrevista", "Entrevista Técnica",
    "Entrevista Final", "Teste Técnico", "Proposta",
    "Contratado", "Reprovado", "Desistente",
    "Análise", "Shortlist", "Oferta",
]

STAGE_ALIASES = {
    "new": "Novo",
    "screening": "Triagem",
    "interview": "Entrevista",
    "technical interview": "Entrevista Técnica",
    "final interview": "Entrevista Final",
    "technical test": "Teste Técnico",
    "proposal": "Proposta",
    "offer": "Oferta",
    "hired": "Contratado",
    "rejected": "Reprovado",
    "withdrawn": "Desistente",
    "analysis": "Análise",
    "shortlist": "Shortlist",
}

MESSAGE_INTENT_PATTERNS: list[tuple] = [
    # Atualizar campo candidato
    ("atualizar_campo_candidato", [
        r"atualiz[ae]r?\s+(o\s+)?(campo|telefone|email|linkedin|cargo|empresa|cidade|estado|salário|formação|idioma|disponibilidade)",
        r"muda[rn]?\s+(o\s+)?(telefone|email|linkedin|cargo|empresa|cidade|estado|salário|formação|idioma|disponibilidade)",
        r"registra[rn]?\s+(o\s+)?(telefone|email|linkedin|cargo|empresa|cidade|estado|salário|formação|idioma|disponibilidade)",
        r"(telefone|linkedin|email|cargo|empresa|cidade|salário|formação|idioma|disponibilidade)\s+(é|foi|para|novo|nova)",
    ]),
    # Criar tarefa / lembrete
    ("criar_tarefa", [
        r"(cria[rn]?|adiciona[rn]?|registra[rn]?)\s+(uma?\s+)?(tarefa|task|to.do)",
        r"(preciso|quero)\s+(fazer|completar|resolver|verificar)\s+.{3,50}(até|amanhã|segunda|terça|quarta|quinta|sexta|semana)",
        r"lembra[rn]?\s+(me\s+)?(de|que)\s+.{3,}",
        r"(cria[rn]?|adiciona[rn]?)\s+(um?\s+)?(lembrete|reminder|aviso)",
    ]),
    ("criar_lembrete", [
        r"(cria[rn]?|adiciona[rn]?|coloca[rn]?)\s+(um?\s+)?(lembrete|reminder|aviso)",
        r"lembra[rn]?[\-\s]*(me\s+)?(de|amanhã|hoje|semana|que|:)",
        r"^lembrete[\s:].{3,}",
    ]),
    # Criar nota / anotação
    ("criar_nota", [
        r"(cria[rn]?|adiciona[rn]?|registra[rn]?|anota[rn]?|salva[rn]?)\s+(uma?\s+)?(nota|anotação|observação|obs|comentário)",
        r"(anota[rn]?|registra[rn]?)\s+(que|isso|este|esta|o seguinte)",
        r"(quero|preciso)\s+(anotar|registrar|salvar)\s+(que|isso|este)",
    ]),
    ("anotar", [
        r"anota[rn]?\s+(isso|que|aí)",
        r"(salva[rn]?|registra[rn]?)\s+(essa|esta|isso)\s+(informação|info|nota|obs)",
    ]),
    # Criar compromisso / evento genérico
    ("criar_compromisso", [
        r"(cria[rn]?|adiciona[rn]?|agenda[rn]?|coloca[rn]?)\s+(um?\s+)?(compromisso|evento|reunião|meeting|call)",
        r"(bloquear?|reservar?)\s+(tempo|horário|slot)\s+(para|na|no)",
        r"(tenho|marcar?)\s+(reunião|meeting|call|compromisso)\s+(com|no|na|amanhã|hoje|semana)",
    ]),
    # Agendar entrevista (must come before resumo_agenda to avoid false positives)
    ("agendar_entrevista", [
        r"(convida[rn]?)\s+.{2,40}(para|pra)\s+(entrevista|interview)(?!\s+wsi)",
        r"(convida[rn]?)\s+.{2,40}entrevista\s+(amanhã|hoje|às|no\s+dia)",
        r"(agenda[rn]?|marca[rn]?)\s+(uma?\s+)?(entrevista|interview)\s+(com|para|pra)\s+\w+",
    ]),
    # Resumo da agenda / briefing diário
    ("resumo_agenda", [
        r"(minha|meus?)\s+(agenda|compromissos?|tarefas?|entrevistas?)\s+(de\s+)?(hoje|amanhã|esta semana|dessa? semana)",
        r"(o\s+que|quais?)\s+(tenho|tem|preciso\s+fazer|preciso\s+atender)\s+(hoje|amanhã|agora)",
        r"(resumo|sumário|briefing|overview)\s+(do\s+)?(dia|diário|de hoje|agenda)",
        r"(minha|meus?)\s+(agenda|entrevistas?|compromissos?)\s+(de\s+)?(hoje|amanhã|essa? semana|esta semana)",
        r"(o\s+que\s+tenho|minha\s+agenda)\s+(hoje|amanhã)",
        r"(mostre?|veja?|me\s+dê)\s+(minha|meus?)\s+(agenda|tarefas?|compromissos?)",
    ]),
    # Enviar feedback / devolutiva
    ("enviar_feedback", [
        r"(envia[rn]?|manda[rn]?|da[rn]?)\s+(o?\s*)?(feedback|devolutiva|retorno)\s+(para|ao|à|do|da|pro|pra)",
        r"(feedback|devolutiva|retorno)\s+(para|ao|à|do|da|pro|pra)\s+",
        r"(da[rn]?|envia[rn]?)\s+(um[a]?\s+)?(feedback|devolutiva|retorno)",
    ]),
    # Enviar WhatsApp
    ("enviar_whatsapp", [
        r"(envia[rn]?|manda[rn]?)\s+(um[a]?\s+)?(whatsapp|zap|mensagem\s+no\s+whatsapp|msg\s+no\s+whatsapp)",
        r"(whatsapp|zap)\s+(para|pro|pra|ao|à)",
        r"(manda[rn]?|envia[rn]?)\s+(um[a]?\s+)?(msg|mensagem)\s+(pelo|via|no)\s+(whatsapp|zap|whats)",
    ]),
    # Enviar convite de triagem WSI
    ("enviar_convite_triagem", [
        r"(envia[rn]?|manda[rn]?)\s+(o?\s*)?(convite|invite)\s+(de\s+)?(triagem|screening|wsi)",
        r"(convida[rn]?|invita[rn]?)\s+(para|pra)\s+(triagem|screening|wsi|entrevista\s+wsi)",
    ]),
    # Reagendar entrevista
    ("reagendar_entrevista", [
        r"(reagenda[rn]?|remarca[rn]?|adia[rn]?|mudar?\s+data|mudar?\s+horário)\s+(a?\s*)?(entrevista|interview)",
        r"(mudar?|alterar?)\s+(a?\s*)?(data|horário)\s+(d[ao]?\s*)?(entrevista|interview)",
    ]),
    # Cancelar entrevista
    ("cancelar_entrevista", [
        r"(cancela[rn]?|desmarcar?)\s+(a?\s*)?(entrevista|interview)",
        r"(entrevista|interview)\s+(cancela|desmarca)",
    ]),
    # Enviar lembrete de entrevista
    ("enviar_lembrete_entrevista", [
        r"(envia[rn]?|manda[rn]?)\s+(um?\s+)?(lembrete|reminder)\s+(de\s+|da\s+)?(entrevista|interview)",
        r"(lembrar?|notificar?)\s+(o?\s*)?(candidato|entrevistador)\s+(sobre|da)\s+(entrevista|interview)",
    ]),
    # Listar entrevistas de hoje
    ("listar_entrevistas_hoje", [
        r"(entrevistas?|interviews?)\s+(de\s+)?(hoje|amanhã)",
        r"(quais?|quantas?)\s+(entrevistas?|interviews?)\s+(tenho|temos?|tem|há|existem?)\s+(hoje|amanhã)",
        r"(listar?|mostrar?|ver)\s+(as?\s+)?(entrevistas?|interviews?)\s+(de\s+)?(hoje|amanhã|da semana)",
    ]),
    # Gerar link de auto-agendamento
    ("gerar_link_agendamento", [
        r"(gera[rn]?|cria[rn]?)\s+(um?\s+)?(link|url)\s+(de\s+)?(agendamento|auto.agendamento|self.scheduling)",
        r"(link|url)\s+(de\s+)?(auto.agendamento|self.scheduling|agendamento)",
    ]),
    # Taguear candidatos
    ("taguear_candidatos", [
        r"(taguea[rn]?|etiqueta[rn]?|classifica[rn]?|marca[rn]?)\s+(o[s]?\s+)?(candidato|candidatos)",
        r"(adiciona[rn]?|coloca[rn]?)\s+(tag|etiqueta|label)\s+(no|nos|ao|aos)\s+(candidato|candidatos)",
        r"(adiciona[rn]?|coloca[rn]?)\s+(o[s]?\s+)?(candidato|candidatos)\s+(na|em)\s+(lista|tag|grupo)",
    ]),
    # Rankear candidatos
    ("rankear_candidatos", [
        r"(rankea[rn]?|ordena[rn]?|classifica[rn]?)\s+(os?\s+)?(candidatos?)\s+(por|segundo|conforme)",
        r"(ranking|rank)\s+(d[eo]s?\s+)?(candidatos?)",
        r"(?!.*(?:avança|manda|envia|move|agenda).*)(?:quais?\s+)?(melhores?|top|piores?)\s+(candidatos?)",
    ]),
    # Analisar perfil de candidato (CM-001)
    ("analisar_perfil", [
        r"(avali[ae]r?|analisa[rn]?)\s+(o\s+)?(currículo|curriculo|cv|perfil)\s+(d[eo]\s+|do?\s+candidato\s+)?",
        r"(avalia|analisa)\s+.{2,40}\s+(para|pra)\s+(a\s+)?(vaga|posição)",
        r"(currículo|curriculo|cv|perfil)\s+(d[eo]\s+)?.{3,40}\s+(para|pra)\s+(a\s+)?(vaga|posição)",
        r"(faz[er]?|realiza[rn]?)\s+(um[a]?\s+)?(análise|analise|avaliação|avaliacao)\s+(d[eo]\s+)?(currículo|curriculo|cv|perfil)",
    ]),
    # Comparar candidatos
    ("comparar_candidatos", [
        r"(compara[rn]?|comparação|comparar?)\s+(os?\s+)?(candidatos?|perfis?)",
        r"(candidatos?)\s+(lado a lado|versus|vs|comparação|compara)",
        r"compara[rn]?\s+[A-Z].{2,30}\s+e\s+[A-Z].{2,30}",
        r"compara[rn]?\s+[a-z].{2,20}\s+e\s+[a-z].{2,20}\s+(para|pra)\s+(a\s+)?(vaga|posição)",
    ]),
    # Buscar candidatos
    ("buscar_candidatos", [
        r"(busca[rn]?|procura[rn]?|pesquisa[rn]?|encontra[rn]?)\s+(candidatos?|perfis?|profissionais?)",
        r"(candidatos?|perfis?|profissionais?)\s+(com|que|de)\s+",
    ]),
    # Sugerir candidatos
    ("sugerir_candidatos", [
        r"(sugeri[rn]?|recomen[dn]a[rn]?|indica[rn]?)\s+(candidatos?|perfis?|profissionais?)",
        r"(quais?\s+)?(candidatos?|profissionais?)\s+(combina[mn]?|se\s+encaixa[mn]?|são\s+adequados?)",
    ]),
    # Adicionar candidato
    ("adicionar_candidato", [
        r"(adiciona[rn]?|cadastra[rn]?|inclui[rn]?|registra[rn]?)\s+(um[a]?\s+)?(novo[a]?\s+)?(candidato|candidata)",
        r"(novo[a]?\s+)?(candidato|candidata)\s+.{2,30}\s+(email|e-mail|tel|fone)",
    ]),
    # Exportar candidatos
    ("exportar_candidatos", [
        r"(exporta[rn]?|baixa[rn]?|download)\s+(os?\s+)?(candidatos?|lista|relatório|planilha)",
        r"(gera[rn]?)\s+(um[a]?\s+)?(planilha|csv|excel|lista)\s+(d[eo]s?\s+)?(candidatos?)",
    ]),
    # Relatório KPI
    ("gerar_relatorio_kpi", [
        r"(gera[rn]?|cria[rn]?|mostra[rn]?)\s+(o?\s*)?(relatório|report)\s+(de\s+)?(kpi|indicadores?|métricas?|performance)",
        r"(kpis?|indicadores?|métricas?)\s+(de\s+|do\s+)?(recrutamento|vagas?|contratação)",
        r"(como\s+(estão|andam)|quais?\s+são)\s+(os?\s+)?(kpis?|indicadores?|métricas?|números?)",
        r"(tempo\s+médio|ttf|time.to.hire|time_to_hire|prazo\s+médio)\s+(de\s+)?(contratação|preenchimento|fill)",
        r"(qual|quanto)\s+(é\s+o|o\s+)?(tempo|prazo)\s+(médio|de)\s+(contratação|fill|preenchimento)",
        r"(diversidade|índice\s+de\s+diversidade|paridade\s+de\s+gênero|distribuição\s+de\s+gênero)",
        r"(overview|visão\s+geral|resumo)\s+(dos?\s+)?(kpis?|indicadores?|dados?|números?|recrutamento)",
    ]),
    # Enviar parecer de candidato ao gestor
    ("enviar_relatorio_candidato", [
        r"(envia[rn]?|manda[rn]?|compartilha[rn]?)\s+(o?\s*)?(parecer|relatório|report)\s+(d[eo]\s+)?(candidato|candidata)",
        r"(parecer|relatório)\s+(d[eo]\s+)?(candidato|candidata)\s+(para|ao|pro|pra)\s+(gestor|gerente|manager|líder)",
    ]),
    # Enviar relatório de progresso
    ("enviar_relatorio_progresso", [
        r"(envia[rn]?|manda[rn]?|gera[rn]?)\s+(o?\s*)?(relatório|report)\s+(de\s+)?(progresso|andamento|status)\s+(da\s+|do\s+)?(vaga|processo|recrutamento)",
        r"(como\s+está|status)\s+(o?\s*)?(progresso|andamento)\s+(da\s+|do\s+)?(vaga|processo)",
    ]),
    # Criar automação
    ("criar_automacao", [
        r"(cria[rn]?|configura[rn]?|adiciona[rn]?)\s+(um[a]?\s+)?(automação|automation|regra automática|fluxo automático)",
        r"(automatiza[rn]?|auto)\s+(o?\s*)?(envio|movimentação|notificação|lembrete)",
        r"(quando|se)\s+.{5,50}(automaticamente|auto|enviar|mover|notificar)",
    ]),
    # Alertas proativos
    ("alertas_proativos", [
        r"(alertas?|avisos?|notificações?)\s+(proativo|pendente|urgente|importante)",
        r"(tem|há|existe[mn]?)\s+(algum|alguma)?\s*(alerta|aviso|pendência|urgência)",
        r"(o\s+que\s+preciso|o\s+que\s+devo)\s+(ver|fazer|resolver|atender)\s+(agora|urgente)?",
        r"(candidatos?\s+parados?|inativ[oa]s?\s+há)\s+\d+\s*(dias?|semanas?)",
    ]),
    # Favoritar candidato
    ("favoritar_candidato", [
        r"(favorita[rn]?|salva[rn]?|adiciona[rn]?)\s+(o?\s*)?(candidato|candidata)\s+(aos?|nos?|em|como)?\s*(favoritos?|lista)",
        r"(adiciona[rn]?|coloca[rn]?)\s+.{2,40}\s+(nos?|aos?|em)\s+(favoritos?|minha\s+lista)",
        r"(favoritar?|salvar?)\s+.{2,40}\s+(perfil|candidato|candidata)",
    ]),
    # Vaga urgente
    ("vaga_urgente", [
        r"(classifica[rn]?|marca[rn]?|define?|coloca[rn]?)\s+(a?\s*)?(vaga|posição|job)\s+(como\s+)?(urgente|prioridade\s+alta|prioritári[oa])",
        r"(esta|essa|a)\s+(vaga|posição)\s+(é|está|ficou)\s+(urgente|prioritári[oa]|prioridade\s+alta)",
        r"(urgência|prioridade)\s+(alta|máxima|urgente)\s+(para|na|nesta)\s+(vaga|posição)",
    ]),
    # Compartilhar candidato
    ("compartilhar_candidato", [
        r"(compartilha[rn]?|envia[rn]?|manda[rn]?)\s+(o?\s*)?(perfil|candidato|candidata)\s+(com|para|pro|pra|ao)\s+(gestor|gerente|manager|líder|time|equipe|colega)",
        r"(compartilha[rn]?)\s+(o?\s*)?(perfil|candidato|candidata)\s+(via|por)\s+(link|email|e-mail)",
    ]),
    # Mover candidatos em lote
    ("mover_candidatos_lote", [
        r"(move[rn]?|mova|avança[rn]?)\s+(todos?\s+|os\s+)?(candidatos?)\s+(com|que|de|para|selecionados?)",
        r"(move[rn]?|avança[rn]?)\s+(em\s+)?(lote|massa|batch|bulk)",
        r"(move[rn]?|mova)\s+todos?\s+(os\s+)?(candidatos?|selecionados?)\s+(para|pra)\s+",
    ]),
    # Duplicar vaga
    ("reject_candidate", [
        r"(rejeita[rn]?|reprova[rn]?)\s+(o\s+|a\s+)?(candidato|candidata)\s+\w",
        r"(reprovar?|rejeitar?)\s+(o\s+)?(candidato|candidata)",
        r"rejeita[rn]?\s+\w+\s+\w+",
    ]),
    ("duplicar_vaga", [
        r"(duplica[rn]?|clona[rn]?|copia[rn]?)\s+(a\s+|uma?\s+)?(vaga|posição|job)",
        r"(abrir\s+)?(uma?\s+)?segunda\s+(posição|vaga|oportunidade)",
        r"(cria[rn]?|adiciona[rn]?)\s+(mais\s+)?(uma?\s+)?(cópia|copia|versão)\s+(da\s+|do\s+)?(vaga|posição|job)",
    ]),
    # Health check da vaga
    ("health_check_vaga", [
        r"(health\s*check|diagnóstico|diagnose|saúde)\s+(da\s+|do\s+)?(vaga|processo|pipeline)",
        r"(como\s+está|status|saúde)\s+(da\s+|do\s+|essa\s+|este\s+|esta\s+|o\s+|a\s+)?(vaga|processo|pipeline|funil)",
    ]),
    # Análise de funil / KB-005: tempo por etapa
    ("analisar_funil", [
        r"(analisa[rn]?|análise)\s+(do\s+|o\s+)?(funil|pipeline|conversão|taxa)",
        r"(tempo|média|médio)\s+(que|d[eo]s?)\s+(candidatos?|pessoas?)\s+(ficam?|permanecem?|passam?)\s+(em\s+cada|nas?)\s+(etapa|fase|estágio|stage)",
        r"(quanto\s+tempo|tempo\s+médio)\s+(em\s+cada|por|nas?)\s+(etapa|fase|stage)",
        r"(etapas?|fases?)\s+(do\s+)?(processo|pipeline)\s+(tempo|duração|média)",
        r"(funil|pipeline)\s+(de\s+)?(recrutamento|contratação|conversão|seleção)",
        r"(taxa|percentual|%)\s+(de\s+)?(conversão|aprovação|rejeição|desistência)\s+(do\s+|no\s+)?(funil|pipeline)",
    ]),
    # Iniciar / disparar triagem WSI
    ("iniciar_triagem", [
        r"(inicia[rn]?|dispara[rn]?|comeca[rn]?|comecar?|iniciar?)\s+(a\s+)?triagem(\s+wsi)?",
        r"triagem\s+wsi\s+(para|dos?|com)\s+",
        r"(iniciar?|disparar?)\s+triagem\s+(dos?\s+)?(candidatos?|todos?)",
        r"triagem\s+(para|dos?)\s+(os?\s+)?(candidatos?\s+)?(em\s+espera|aguardando|novos?)",
    ]),
    ("disparar_triagem", [
        r"dispara[rn]?\s+(a?\s*)?triagem",
        r"(envia[rn]?|manda[rn]?|dispara[rn]?)\s+(a\s+)?triagem\s+(wsi|automatica|para)",
    ]),
    # Listar candidatos por etapa
    ("mover_candidatos_por_etapa", [
        r"(move[rn]?|transfere[rn]?|muda[rn]?)\s+(todos?\s+)?(os?\s+)?candidatos?.*?(para\s+)(reprovado|aprovado|triagem|entrevista|proposta|oferta)",
        r"(limpa[rn]?|fecha[rn]?|arquiva[rn]?)\s+(a\s+)?(etapa|fase|fila)\s+(de\s+)?",
        r"(move[rn]?|mova)\s+todos?\s+(os\s+)?candidatos?\s+(d[ae]\s+)?(etapa\s+d[ae]?\s+)?",
    ]),
    # Mover candidatos por etapa (bulk stage move without explicit candidate list)
    ("listar_candidatos_por_etapa", [
        r"(quais?|quem|que|liste?|mostra[rn]?|veja?)\s+(os?\s+|são\s+os?\s+)?(candidatos?)\s+(que\s+)?(est[aã][o]?|est[aá]|tem|há|estão|ficaram)\s+(na|em|da|no)\s+(etapa|fase|stage)",
        r"candidatos?\s+(est[aã][o]?|est[aá]|ficaram)\s+(na|em|da)\s+(etapa|fase|stage|entrevista|triagem|proposta|oferta)",
        r"candidatos?\s+(na|em|da)\s+(etapa|fase|stage)\s+(de\s+)?(entrevista|triagem|proposta|oferta|shortlist)",
        r"(quais?|quem)\s+(est[aã][o]?|est[aá])\s+na\s+etapa",
        r"quem\s+(está|estão)\s+(na|em|da)\s+(etapa|fase|stage|entrevista|triagem|proposta|oferta)",
        r"(listar?|mostrar?)\s+(os?\s+)?(candidatos?)\s+(por\s+)?etapa",
    ]),
    # Vagas sem candidatos
    ("vagas_sem_candidatos", [
        r"vaga(s)?\s+(sem|sem\s+nenhum)\s+candidato",
        r"vaga(s)?\s+(aberta(s)?|ativa(s)?)\s+(sem|sem\s+nenhum|sem\s+qualquer)\s+candidato",
        r"(alguma|quais?)\s+vaga(s)?\s+(sem\s+|não\s+tem\s+|sem\s+nenhum\s+)candidato",
    ]),
    # Identidade da LIA -- respondida localmente, nunca pelo LLM
    ("sugerir_salario", [
        r"qual\s+(é\s+o\s+)?salário\s+sugerir",
        r"qual\s+(é\s+o\s+)?(salário|remuneração|faixa\s+salarial)\s+(para|de|do?|ao?|sugerir)",
        r"(quanto|qual)\s+(pagar|oferecer|remunerar|salário)\s+(para|a|sugerir)\s+(um[a]?\s+)?\w+",
        r"(sugerir?|recomendar?|indicar?)\s+(salário|remuneração|faixa)\s+(para|de|ao?)",
        r"benchmark\s+salarial\s+(para|de)",
        r"(salário|remuneração)\s+(de\s+mercado|ideal|sugerido)\s+(para|de)",
        r"qual\s+salário\s+(?:eu\s+)?(?:devo\s+|posso\s+|deveria\s+)?(?:sugerir|pagar|oferecer)",
    ]),
    ("gerar_jd", [
        r"(gerar?s?|gera[rs]?|cria[rn]?|produz[ir]*)\s+(um[a]?\s+)?(descrição\s+d[ae]\s+vaga|job\s+description|jd)\s+(para|de)",
        r"(escreve[rn]?|elabora[rn]?|monta[rn]?)\s+(um[a]?\s+)?(descrição|job\s+description|jd)\s+(para|de|ao?)",
        r"(me\s+)?ajuda\s+(a\s+)?(criar|escrever|montar)\s+(um[a]?\s+)?(descrição|jd|job\s+description)",
        r"(descrição|job\s+description)\s+(para\s+o\s+cargo|para\s+a\s+vaga)\s+de\s+",
        r"gera\s+(?:uma?\s+)?descrição\s+d[ae]\s+vaga",
    ]),
    ("lia_identidade", [
        r"quem\s+(é\s+)?(você|vc|a\s+lia)",
        r"quem\s+(e\s+)?(voce|vc|a\s+lia)",
        r"(o\s+que|quem)\s+(é|es?)\s+(você|vc|a\s+lia)",
        r"(o\s+que|quem)\s+(e|es?)\s+(voce|vc|a\s+lia)",
        r"(quem|o\s+que)\s+(é\s+)?a\s+lia",
        r"(você|vc)\s+é\s+(gemini|claude|gpt|google|openai|anthropic)",
        r"^(quem\s+é\s+você|who\s+are\s+you|what\s+are\s+you)[\?\!]?$",
    ]),
]


# ──────────────────────────────────────────────────────────────────────
# FIX 10 / G6 — Unified requires_confirmation resolver.
#
# Two sources of truth coexist in the codebase:
#   1. intents_config.ACTIONABLE_INTENTS[intent]["requires_confirmation"]
#      Intent-level — captures specific user-invocation context (e.g., a
#      handler that manages its own confirmation gate may set False).
#   2. DomainAction.requires_confirmation
#      Action-level — general dangerousness of the action itself.
#
# Both are legitimate but serve different purposes. This resolver provides
# a single query API: intent > action precedence (intent has more context).
# ──────────────────────────────────────────────────────────────────────

def resolve_requires_confirmation(
    intent: str | None,
    action_id: str | None,
) -> bool:
    """Return the effective requires_confirmation flag.

    Precedence:
        1. intent (ACTIONABLE_INTENTS[intent]["requires_confirmation"])
        2. DomainAction.requires_confirmation (via DomainRegistry)
        3. False (default: safe to execute)

    Args:
        intent: Intent name (e.g., "mover_candidato"). None if unknown.
        action_id: Domain action_id (e.g., "move_candidate"). None if unknown.

    Returns:
        True if the action requires user confirmation before executing.
    """
    # 1. Intent-level (highest priority)
    if intent and intent in ACTIONABLE_INTENTS:
        cfg = ACTIONABLE_INTENTS[intent]
        if "requires_confirmation" in cfg:
            return bool(cfg["requires_confirmation"])

    # 2. DomainAction-level (fallback)
    if action_id:
        try:
            from app.domains.registry import DomainRegistry
            registry = DomainRegistry()
            domain = registry.get_domain_for_action(action_id)
            if domain:
                action = domain.get_action_by_id(action_id)
                if action is not None:
                    return bool(getattr(action, "requires_confirmation", False))
        except Exception:
            pass  # non-blocking — registry lookup best-effort

    # 3. Default: safe (no confirmation required)
    return False


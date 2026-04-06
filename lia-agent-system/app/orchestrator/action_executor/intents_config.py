"""
Configuration constants for ActionExecutor:
  - ACTIONABLE_INTENTS: all supported intent → action mappings
  - CONFIRMATION_PATTERNS / REJECTION_PATTERNS
  - VALID_PIPELINE_STAGES / STAGE_ALIASES
  - MESSAGE_INTENT_PATTERNS: regex patterns for intent detection from raw message
"""
from typing import Final, Any

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
        "required_params": ["candidate_id"],
        "optional_params": [],
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
        "required_params": ["candidate_id"],
        "optional_params": [],
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
        "required_params": ["job_id"],
        "optional_params": ["new_title"],
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
        "domain_id": "pipeline_action",
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
    # Resumo da agenda / briefing diário
    ("resumo_agenda", [
        r"(minha|meus?)\s+(agenda|compromissos?|tarefas?|entrevistas?)\s+(de\s+)?(hoje|amanhã|esta semana|dessa? semana)",
        r"(o\s+que|quais?)\s+(tenho|tem|preciso\s+fazer|preciso\s+atender)\s+(hoje|amanhã|agora)",
        r"(resumo|sumário|briefing|overview)\s+(do\s+)?(dia|diário|de hoje|agenda)",
        r"(agenda|entrevistas?|compromissos?)\s+(de\s+)?(hoje|amanhã|essa? semana|esta semana)",
        r"(o\s+que\s+tenho|minha\s+agenda)\s+(hoje|amanhã)",
        r"(mostre?|veja?|me\s+dê)\s+(minha|meus?)\s+(agenda|tarefas?|compromissos?)",
    ]),
]

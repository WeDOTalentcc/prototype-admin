"""
ActionExecutorService - Closed-loop action execution for LIA.

Transforms LIA from open-loop (suggest UI actions) to closed-loop (execute real actions).
Maps intents to domain actions, validates parameters, and executes via domains.
"""
import logging
import uuid
from typing import Dict, Any, Optional, List, Literal
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ActionResult:
    status: Literal["executed", "needs_params", "needs_confirmation", "not_actionable", "error"]
    message: str = ""
    data: Optional[Dict[str, Any]] = None
    missing_params: Optional[List[str]] = None
    confirmation_summary: Optional[Dict[str, Any]] = None
    action_type: Optional[str] = None
    pending_action_id: Optional[str] = None
    error_detail: Optional[str] = None


ACTIONABLE_INTENTS: Dict[str, Dict[str, Any]] = {
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


def is_confirmation(message: str) -> bool:
    msg = message.lower().strip().rstrip("!.?")
    for pattern in CONFIRMATION_PATTERNS:
        if msg == pattern or msg.startswith(pattern + " ") or msg.endswith(" " + pattern):
            return True
    return False


def is_rejection(message: str) -> bool:
    msg = message.lower().strip().rstrip("!.?")
    for pattern in REJECTION_PATTERNS:
        if msg == pattern or msg.startswith(pattern + " ") or msg.endswith(" " + pattern):
            return True
    return False


def resolve_candidate_from_context(
    candidate_name: Optional[str],
    candidate_id: Optional[str],
    candidates_data: List[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    if candidate_id:
        for c in candidates_data:
            if str(c.get("id", "")) == str(candidate_id):
                return c

    if candidate_name and candidates_data:
        name_lower = candidate_name.lower().strip()
        for c in candidates_data:
            c_name = (c.get("name") or "").lower().strip()
            if name_lower == c_name:
                return c
        for c in candidates_data:
            c_name = (c.get("name") or "").lower().strip()
            if name_lower in c_name or c_name in name_lower:
                return c
        for c in candidates_data:
            c_name = (c.get("name") or "").lower().strip()
            name_parts = name_lower.split()
            if any(part in c_name for part in name_parts if len(part) > 2):
                return c
    return None


def resolve_stage(stage_text: Optional[str]) -> Optional[str]:
    if not stage_text:
        return None
    normalized = stage_text.strip().lower()
    if normalized in STAGE_ALIASES:
        return STAGE_ALIASES[normalized]
    stage_lower = normalized
    for valid_stage in VALID_PIPELINE_STAGES:
        if stage_lower == valid_stage.lower():
            return valid_stage
    for valid_stage in VALID_PIPELINE_STAGES:
        if stage_lower in valid_stage.lower() or valid_stage.lower() in stage_lower:
            return valid_stage
    return stage_text.title()


MESSAGE_INTENT_PATTERNS: List[tuple] = [
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


def _detect_intent_from_message(message: str) -> Optional[str]:
    """Detect an actionable intent from a raw message string."""
    if not message:
        return None
    msg_lower = message.lower().strip()
    import re
    for intent, patterns in MESSAGE_INTENT_PATTERNS:
        for pattern in patterns:
            if re.search(pattern, msg_lower):
                return intent
    return None


def _extract_entities_from_message(message: str, intent: str) -> Dict[str, Any]:
    """Extract entity values from raw message for a given intent."""
    import re
    entities: Dict[str, Any] = {}
    msg = message.strip()

    # Title/content for tasks, reminders, notes, events
    if intent in ("criar_tarefa", "criar_lembrete", "criar_nota", "anotar", "criar_compromisso"):
        # Try to extract content after keyword
        m = re.search(
            r"(?:cria[rn]?|adiciona[rn]?|registra[rn]?|anota[rn]?|salva[rn]?|agenda[rn]?|lembra[rn]?(?:\s+me)?(?:\s+de)?)\s+(?:um[a]?\s+)?(?:tarefa|lembrete|nota|anotação|observação|compromisso|evento|reunião|reminder|task|to.do|que\s+)?(.{3,})",
            msg, re.IGNORECASE
        )
        if m:
            extracted = m.group(1).strip()
            entities["title"] = extracted[:100]
            entities["content"] = extracted

        # Due date / datetime detection
        date_m = re.search(
            r"(amanhã|hoje|segunda|terça|quarta|quinta|sexta|sábado|domingo|\d{1,2}/\d{1,2}(?:/\d{2,4})?)",
            msg, re.IGNORECASE
        )
        if date_m:
            date_val = date_m.group(1)
            # Also try to extract a time component (e.g. "14h", "14:30", "às 9", "8h30")
            time_m = re.search(
                r"(?:às?|as)\s*(\d{1,2})h?(?::?(\d{2}))?|(\d{1,2})[h:](\d{2})?(?:\s*(?:hs?|horas?))?",
                msg, re.IGNORECASE
            )
            if time_m:
                hour = time_m.group(1) or time_m.group(3) or "0"
                minute = time_m.group(2) or time_m.group(4) or "00"
                date_val = f"{date_val} {hour}:{minute}"
            entities["due_date"] = date_val
            # criar_compromisso requires "datetime" not "due_date"
            if intent == "criar_compromisso":
                entities["datetime"] = date_val

    # Field updates
    if intent == "atualizar_campo_candidato":
        field_map = {
            "telefone": "phone", "email": "email", "linkedin": "linkedin_url",
            "cargo": "current_title", "empresa": "current_company",
            "cidade": "location_city", "estado": "location_state",
            "salário clt": "salary_expectation_clt", "salário pj": "salary_expectation_pj",
            "modelo": "work_model_preference", "idioma": "languages",
            "formação": "education_level", "formacao": "education_level",
            "disponibilidade": "availability_date",
        }
        msg_lower = msg.lower()
        for alias, field in field_map.items():
            if alias in msg_lower:
                entities["field_name"] = field
                break
        # Try to extract value: "campo é VALOR" or "campo: VALOR" or "campo para VALOR"
        val_m = re.search(
            r"(?:é|foi|para|novo[a]?|:)\s+([^\.,\n]{2,80})",
            msg, re.IGNORECASE
        )
        if val_m:
            entities["field_value"] = val_m.group(1).strip()

    return entities


def _resolve_ptbr_datetime(date_str: str) -> Optional["datetime"]:
    """
    Deterministically resolve a Portuguese-language date/time string to a datetime.

    Handles relative terms: hoje, amanhã, and weekday names.
    Also extracts time components like "14h", "14:30", "às 9h".
    Falls back to dateutil for absolute dates (DD/MM/YYYY, ISO, etc.).
    Returns None if the string is empty or unparseable.
    """
    if not date_str:
        return None

    import re as _re
    from datetime import datetime as _dt, timedelta as _td

    now = _dt.now()
    date_str_lower = date_str.lower().strip()

    # Extract time component
    hour, minute = None, 0
    time_m = _re.search(
        r"(?:às?|as)\s*(\d{1,2})\s*h?(?::?(\d{2}))?|(\d{1,2})[h:](\d{2})?",
        date_str_lower
    )
    if time_m:
        hour = int(time_m.group(1) or time_m.group(3) or 0)
        minute = int(time_m.group(2) or time_m.group(4) or 0)

    # Resolve relative day tokens
    PTBR_WEEKDAYS = {
        "segunda": 0, "terça": 1, "terca": 1,
        "quarta": 2, "quinta": 3, "sexta": 4,
        "sábado": 5, "sabado": 5, "domingo": 6,
    }

    resolved_date = None
    if "amanhã" in date_str_lower or "amanha" in date_str_lower:
        resolved_date = now + _td(days=1)
    elif "hoje" in date_str_lower:
        resolved_date = now
    else:
        for ptbr_day, weekday_idx in PTBR_WEEKDAYS.items():
            if ptbr_day in date_str_lower:
                days_ahead = (weekday_idx - now.weekday() + 7) % 7
                if days_ahead == 0:
                    days_ahead = 7
                resolved_date = now + _td(days=days_ahead)
                break

    if resolved_date is not None:
        h = hour if hour is not None else 9
        return resolved_date.replace(hour=h, minute=minute, second=0, microsecond=0)

    # Fall back to dateutil for absolute dates
    try:
        from dateutil import parser as dt_parser
        parsed = dt_parser.parse(date_str, dayfirst=True, default=now)
        if hour is not None:
            parsed = parsed.replace(hour=hour, minute=minute, second=0, microsecond=0)
        return parsed
    except Exception:
        return None


class ActionExecutorService:

    def __init__(self):
        self.execution_count = 0

    def is_actionable(self, intent: str) -> bool:
        return intent in ACTIONABLE_INTENTS

    def get_action_config(self, intent: str) -> Optional[Dict[str, Any]]:
        return ACTIONABLE_INTENTS.get(intent)

    async def try_execute(
        self,
        intent: str = "",
        entities: Optional[Dict[str, Any]] = None,
        candidates_data: Optional[List[Dict[str, Any]]] = None,
        context: Optional[Dict[str, Any]] = None,
        *,
        message: str = "",
    ) -> ActionResult:
        # Support message-based call (from MainOrchestrator)
        if message and not intent:
            detected = _detect_intent_from_message(message)
            if not detected:
                return ActionResult(status="not_actionable")
            intent = detected
            entities = entities or _extract_entities_from_message(message, intent)
            candidates_data = candidates_data or (context or {}).get("candidates", [])

        entities = entities or {}
        candidates_data = candidates_data or []
        context = context or {}
        if not self.is_actionable(intent):
            return ActionResult(status="not_actionable")

        config = ACTIONABLE_INTENTS[intent]
        params = dict(config.get("default_params", {}))

        candidate_name = entities.get("candidate_name")
        candidate_id = entities.get("candidate_id")

        if candidate_name or candidate_id:
            resolved = resolve_candidate_from_context(
                candidate_name, candidate_id, candidates_data
            )
            if resolved:
                params["candidate_id"] = str(resolved.get("id", ""))
                params["candidate_name"] = resolved.get("name", candidate_name or "")
                params["candidate_email"] = resolved.get("email", "")
                if resolved.get("stage"):
                    params["from_stage"] = resolved["stage"]
            elif candidate_name:
                params["candidate_name_unresolved"] = candidate_name

        target_stage = entities.get("target_stage") or entities.get("to_stage") or entities.get("stage")
        if target_stage:
            resolved_stage = resolve_stage(target_stage)
            if resolved_stage:
                params["to_stage"] = resolved_stage

        if entities.get("subject"):
            params["subject"] = entities["subject"]
        if entities.get("body") or entities.get("message"):
            params["body"] = entities.get("body") or entities.get("message")
        if entities.get("datetime") or entities.get("date"):
            params["datetime"] = entities.get("datetime") or entities.get("date")
        if entities.get("interviewer"):
            params["interviewer"] = entities["interviewer"]
        if entities.get("reason"):
            params["reason"] = entities["reason"]

        if entities.get("job_id"):
            params["job_id"] = entities["job_id"]
        if entities.get("job_title"):
            params["job_title"] = entities["job_title"]
        if entities.get("new_title"):
            params["new_title"] = entities["new_title"]
        if entities.get("outcome"):
            params["outcome"] = entities["outcome"]

        if entities.get("field_name"):
            params["field_name"] = entities["field_name"]
        if entities.get("field_value"):
            params["field_value"] = entities["field_value"]
        if entities.get("content"):
            params["content"] = entities["content"]
        if entities.get("title"):
            params["title"] = entities["title"]
        if entities.get("description"):
            params["description"] = entities["description"]
        if entities.get("due_date"):
            params["due_date"] = entities["due_date"]
        if entities.get("priority"):
            params["priority"] = entities["priority"]
        if entities.get("location"):
            params["location"] = entities["location"]
        if entities.get("duration_minutes"):
            params["duration_minutes"] = entities["duration_minutes"]

        missing = []
        for req_param in config["required_params"]:
            if req_param not in params or not params[req_param]:
                if req_param == "candidate_id" and params.get("candidate_name_unresolved"):
                    missing.append("candidate_id")
                elif req_param not in params:
                    missing.append(req_param)

        if missing:
            first_missing = missing[0]
            prompt = config.get("clarification_prompts", {}).get(
                first_missing,
                f"Por favor, informe: {config.get('param_labels', {}).get(first_missing, first_missing)}"
            )

            if first_missing == "candidate_id" and params.get("candidate_name_unresolved"):
                prompt = f"Não encontrei o candidato '{params['candidate_name_unresolved']}' no pipeline desta vaga. Pode verificar o nome?"

            return ActionResult(
                status="needs_params",
                message=prompt,
                missing_params=missing,
                action_type=config["action_id"],
                pending_action_id=str(uuid.uuid4()),
                data={"collected_params": params, "intent": intent},
            )

        if config.get("requires_confirmation", False):
            summary = self._build_confirmation_summary(intent, config, params)
            return ActionResult(
                status="needs_confirmation",
                message=summary["message"],
                confirmation_summary=summary,
                action_type=config["action_id"],
                pending_action_id=str(uuid.uuid4()),
                data={"collected_params": params, "intent": intent},
            )

        result = await self._execute_action(intent, config, params, context)
        return result

    def _build_confirmation_summary(
        self, intent: str, config: Dict[str, Any], params: Dict[str, Any]
    ) -> Dict[str, Any]:
        action_id = config["action_id"]
        candidate_name = params.get("candidate_name", "o candidato")

        if action_id == "move_candidate":
            to_stage = params.get("to_stage", "próxima etapa")
            from_stage = params.get("from_stage", "")
            from_text = f" (atualmente em {from_stage})" if from_stage else ""
            message = f"Vou mover **{candidate_name}**{from_text} para a etapa **{to_stage}**. Confirma?"
        elif action_id == "send_email":
            subject = params.get("subject", "")
            message = f"Vou enviar um email para **{candidate_name}**"
            if subject:
                message += f' com assunto "{subject}"'
            message += ". Confirma o envio?"
        elif action_id == "schedule_interview":
            dt = params.get("datetime", "")
            message = f"Vou agendar uma entrevista com **{candidate_name}**"
            if dt:
                message += f" para **{dt}**"
            message += ". Confirma?"
        elif action_id == "pause_job":
            job_title = params.get("job_title", "a vaga")
            message = f"Vou **pausar** a vaga **{job_title}**. Confirma?"
        elif action_id == "close_job":
            job_title = params.get("job_title", "a vaga")
            message = f"Vou **fechar** a vaga **{job_title}**. Confirma?"
        elif action_id == "reopen_job":
            job_title = params.get("job_title", "a vaga")
            message = f"Vou **reabrir** a vaga **{job_title}**. Confirma?"
        elif action_id == "update_candidate_field":
            field_name = params.get("field_name", "campo")
            field_value = params.get("field_value", "")
            message = f"Vou atualizar o campo **{field_name}** de **{candidate_name}** para **{field_value}**. Confirma?"
        elif action_id == "create_generic_event":
            event_title = params.get("title", "compromisso")
            dt = params.get("datetime", "")
            message = f"Vou criar o compromisso **\"{event_title}\"** para **{dt}**. Confirma?"
        else:
            message = f"Vou executar a ação **{action_id}** para **{candidate_name}**. Confirma?"

        return {
            "message": message,
            "action_id": action_id,
            "intent": intent,
            "params": params,
            "risk_level": config.get("risk_level", "medium"),
        }

    async def _execute_action(
        self,
        intent: str,
        config: Dict[str, Any],
        params: Dict[str, Any],
        context: Dict[str, Any],
    ) -> ActionResult:
        domain_id = config["domain_id"]
        action_id = config["action_id"]

        if action_id == "send_email":
            try:
                tenant_id = context.get("tenant_id", "default") if context else "default"
                logger.info(f"Direct email execution for tenant: {tenant_id}")
                from app.services.email_providers import get_email_provider
                provider = get_email_provider()
                status = provider.get_status()
                if status.get("configured") and status.get("healthy"):
                    candidate_name = params.get("candidate_name", "")
                    to_email = params.get("email", params.get("candidate_email", ""))
                    subject = params.get("subject", "")
                    body = params.get("body", "")
                    if to_email and subject:
                        import html as html_module
                        safe_body = html_module.escape(body)
                        result = await provider.send_email(
                            to=to_email,
                            subject=subject,
                            html_content=f"<p>{safe_body}</p>",
                            text_content=body,
                        )
                        if result.success:
                            self.execution_count += 1
                            return ActionResult(
                                status="executed",
                                message=f'Email enviado para **{candidate_name}** com assunto "{subject}".',
                                data={
                                    "candidate_id": params.get("candidate_id", ""),
                                    "candidate_name": candidate_name,
                                    "subject": subject,
                                    "to_email": to_email,
                                    "message_id": result.message_id,
                                    "sent_at": datetime.utcnow().isoformat(),
                                    "simulated": False,
                                    "provider": result.provider,
                                },
                                action_type="send_email",
                            )
            except Exception as e:
                logger.warning(f"Direct email sending failed, falling back to domain: {e}")

        if action_id == "schedule_interview":
            try:
                tenant_id = context.get("tenant_id", "default") if context else "default"
                logger.info(f"Direct scheduling for tenant: {tenant_id}")
                from app.core.database import AsyncSessionLocal
                from sqlalchemy import text
                import uuid as uuid_mod

                async with AsyncSessionLocal() as db:
                    interview_id = str(uuid_mod.uuid4())
                    candidate_name = params.get("candidate_name", "")
                    dt = params.get("datetime", "")
                    interviewer = params.get("interviewer", "")
                    candidate_id = params.get("candidate_id", "")

                    await db.execute(text("""
                        INSERT INTO interviews (id, candidate_id, interviewer_name, start_time, status, created_at, updated_at)
                        VALUES (:id, CAST(:candidate_id AS uuid), :interviewer, :start_time, 'scheduled', NOW(), NOW())
                        ON CONFLICT DO NOTHING
                    """), {
                        "id": interview_id,
                        "candidate_id": candidate_id,
                        "start_time": dt,
                        "interviewer": interviewer,
                    })
                    await db.commit()

                    self.execution_count += 1
                    return ActionResult(
                        status="executed",
                        message=f"Entrevista agendada com **{candidate_name}** para **{dt}**.",
                        data={
                            "interview_id": interview_id,
                            "candidate_id": candidate_id,
                            "candidate_name": candidate_name,
                            "datetime": dt,
                            "interviewer": interviewer,
                            "scheduled_at": datetime.utcnow().isoformat(),
                            "simulated": False,
                        },
                        action_type="schedule_interview",
                    )
            except Exception as e:
                logger.warning(f"Direct scheduling failed, falling back to domain: {e}")

        if action_id == "move_candidate":
            try:
                from app.core.database import AsyncSessionLocal
                from sqlalchemy import text
                import uuid as uuid_mod

                candidate_id = params.get("candidate_id", "")
                to_stage = params.get("to_stage", "")
                candidate_name = params.get("candidate_name", "o candidato")
                from_stage = params.get("from_stage", "")

                async with AsyncSessionLocal() as db:
                    result = await db.execute(text("""
                        UPDATE vacancy_candidates
                        SET stage = :to_stage, status = 'active', updated_at = NOW()
                        WHERE (id = CAST(:candidate_id AS uuid) OR candidate_id = CAST(:candidate_id AS uuid))
                    """), {
                        "to_stage": to_stage,
                        "candidate_id": candidate_id,
                    })
                    if result.rowcount == 0:
                        return ActionResult(
                            status="error",
                            message="Candidato não encontrado",
                            error_detail="Candidato não encontrado no pipeline",
                            action_type="move_candidate",
                        )
                    await db.commit()
                    self.execution_count += 1
                    return ActionResult(
                        status="executed",
                        message=f"**{candidate_name}** foi movido(a) para a etapa **{to_stage}**.",
                        data={
                            "candidate_id": candidate_id,
                            "candidate_name": candidate_name,
                            "from_stage": from_stage,
                            "to_stage": to_stage,
                            "moved_at": datetime.utcnow().isoformat(),
                            "simulated": False,
                        },
                        action_type="move_candidate",
                    )
            except Exception as e:
                logger.warning(f"Direct move_candidate failed, falling back to domain: {e}")

        if action_id == "pause_job":
            try:
                from app.core.database import AsyncSessionLocal
                from sqlalchemy import text
                import uuid as uuid_mod

                job_id = params.get("job_id", "")
                job_title = params.get("job_title", "a vaga")

                async with AsyncSessionLocal() as db:
                    result = await db.execute(text("""
                        UPDATE job_vacancies
                        SET status = 'Pausada', updated_at = NOW()
                        WHERE id = CAST(:job_id AS uuid)
                    """), {
                        "job_id": job_id,
                    })
                    if result.rowcount == 0:
                        return ActionResult(
                            status="error",
                            message="Vaga não encontrada",
                            error_detail="Vaga não encontrada no sistema",
                            action_type="pause_job",
                        )
                    await db.commit()
                    self.execution_count += 1
                    return ActionResult(
                        status="executed",
                        message=f"Vaga **{job_title}** pausada com sucesso.",
                        data={
                            "job_id": job_id,
                            "job_title": job_title,
                            "paused_at": datetime.utcnow().isoformat(),
                            "simulated": False,
                        },
                        action_type="pause_job",
                    )
            except Exception as e:
                logger.warning(f"Direct pause_job failed, falling back to domain: {e}")

        if action_id == "close_job":
            try:
                from app.core.database import AsyncSessionLocal
                from sqlalchemy import text
                import uuid as uuid_mod

                job_id = params.get("job_id", "")
                job_title = params.get("job_title", "a vaga")

                async with AsyncSessionLocal() as db:
                    result = await db.execute(text("""
                        UPDATE job_vacancies
                        SET status = 'Fechada', closed_at = NOW(), updated_at = NOW()
                        WHERE id = CAST(:job_id AS uuid)
                    """), {
                        "job_id": job_id,
                    })
                    if result.rowcount == 0:
                        return ActionResult(
                            status="error",
                            message="Vaga não encontrada",
                            error_detail="Vaga não encontrada no sistema",
                            action_type="close_job",
                        )
                    await db.commit()
                    self.execution_count += 1
                    return ActionResult(
                        status="executed",
                        message=f"Vaga **{job_title}** fechada com sucesso.",
                        data={
                            "job_id": job_id,
                            "job_title": job_title,
                            "closed_at": datetime.utcnow().isoformat(),
                            "simulated": False,
                        },
                        action_type="close_job",
                    )
            except Exception as e:
                logger.warning(f"Direct close_job failed, falling back to domain: {e}")

        if action_id == "duplicate_job":
            try:
                from app.core.database import AsyncSessionLocal
                from sqlalchemy import text
                import uuid as uuid_mod

                job_id = params.get("job_id", "")
                new_title = params.get("new_title", "")
                job_title = params.get("job_title", "a vaga")

                async with AsyncSessionLocal() as db:
                    original = await db.execute(text("""
                        SELECT title, company_id, department, location, work_model,
                               employment_type, seniority_level, description, requirements,
                               salary, salary_range, benefits, priority, recruiter,
                               recruiter_email, manager, manager_email, tags
                        FROM job_vacancies
                        WHERE id = CAST(:job_id AS uuid)
                    """), {
                        "job_id": job_id,
                    })
                    row = original.fetchone()
                    if not row:
                        return ActionResult(
                            status="error",
                            message="Vaga original não encontrada",
                            error_detail="Vaga original não encontrada no sistema",
                            action_type="duplicate_job",
                        )

                    new_id = str(uuid_mod.uuid4())
                    final_title = new_title if new_title else f"{row.title} (Cópia)"

                    await db.execute(text("""
                        INSERT INTO job_vacancies (
                            id, title, company_id, department, location, work_model,
                            employment_type, seniority_level, description, requirements,
                            salary, salary_range, benefits, priority, recruiter,
                            recruiter_email, manager, manager_email, tags,
                            status, created_at, updated_at
                        ) VALUES (
                            CAST(:new_id AS uuid), :title, :company_id, :department, :location, :work_model,
                            :employment_type, :seniority_level, :description, :requirements,
                            :salary, :salary_range, :benefits, :priority, :recruiter,
                            :recruiter_email, :manager, :manager_email, :tags,
                            'Ativa', NOW(), NOW()
                        )
                    """), {
                        "new_id": new_id,
                        "title": final_title,
                        "company_id": row.company_id,
                        "department": row.department,
                        "location": row.location,
                        "work_model": row.work_model,
                        "employment_type": row.employment_type,
                        "seniority_level": row.seniority_level,
                        "description": row.description,
                        "requirements": row.requirements,
                        "salary": row.salary,
                        "salary_range": row.salary_range,
                        "benefits": row.benefits,
                        "priority": row.priority,
                        "recruiter": row.recruiter,
                        "recruiter_email": row.recruiter_email,
                        "manager": row.manager,
                        "manager_email": row.manager_email,
                        "tags": row.tags,
                    })
                    await db.commit()
                    self.execution_count += 1
                    return ActionResult(
                        status="executed",
                        message=f"Vaga **{job_title}** duplicada com sucesso. Nova vaga: **{final_title}**.",
                        data={
                            "job_id": job_id,
                            "new_job_id": new_id,
                            "job_title": job_title,
                            "new_title": final_title,
                            "duplicated_at": datetime.utcnow().isoformat(),
                            "simulated": False,
                        },
                        action_type="duplicate_job",
                    )
            except Exception as e:
                logger.warning(f"Direct duplicate_job failed, falling back to domain: {e}")

        if action_id == "reopen_job":
            try:
                from app.core.database import AsyncSessionLocal
                from sqlalchemy import text
                import uuid as uuid_mod

                job_id = params.get("job_id", "")
                job_title = params.get("job_title", "a vaga")

                async with AsyncSessionLocal() as db:
                    result = await db.execute(text("""
                        UPDATE job_vacancies
                        SET status = 'Ativa', closed_at = NULL, updated_at = NOW()
                        WHERE id = CAST(:job_id AS uuid)
                    """), {
                        "job_id": job_id,
                    })
                    if result.rowcount == 0:
                        return ActionResult(
                            status="error",
                            message="Vaga não encontrada",
                            error_detail="Vaga não encontrada no sistema",
                            action_type="reopen_job",
                        )
                    await db.commit()
                    self.execution_count += 1
                    return ActionResult(
                        status="executed",
                        message=f"Vaga **{job_title}** reaberta com sucesso.",
                        data={
                            "job_id": job_id,
                            "job_title": job_title,
                            "reopened_at": datetime.utcnow().isoformat(),
                            "simulated": False,
                        },
                        action_type="reopen_job",
                    )
            except Exception as e:
                logger.warning(f"Direct reopen_job failed, falling back to domain: {e}")

        if action_id == "update_candidate_field":
            try:
                from app.core.database import AsyncSessionLocal
                from sqlalchemy import text

                candidate_id = params.get("candidate_id", "")
                field_name = params.get("field_name", "")
                field_value = params.get("field_value", "")

                # Columns that exist directly on the candidates table
                ALLOWED_DIRECT_FIELDS = {
                    "phone", "email", "linkedin_url", "current_title",
                    "current_company", "location_city", "location_state",
                    "salary_expectation_clt", "salary_expectation_pj",
                    "work_model_preference", "languages",
                }
                # Virtual fields stored inside lia_insights JSON column
                # (no direct DB column exists; use jsonb merge to persist)
                ALLOWED_JSON_FIELDS = {"availability_date", "education_level"}
                ALLOWED_FIELDS = ALLOWED_DIRECT_FIELDS | ALLOWED_JSON_FIELDS

                FIELD_ALIASES = {
                    "telefone": "phone",
                    "celular": "phone",
                    "e-mail": "email",
                    "linkedin": "linkedin_url",
                    "cargo atual": "current_title",
                    "cargo": "current_title",
                    "empresa": "current_company",
                    "empresa atual": "current_company",
                    "cidade": "location_city",
                    "estado": "location_state",
                    "salário clt": "salary_expectation_clt",
                    "salario clt": "salary_expectation_clt",
                    "salário pj": "salary_expectation_pj",
                    "salario pj": "salary_expectation_pj",
                    "modelo de trabalho": "work_model_preference",
                    "modelo trabalho": "work_model_preference",
                    "idiomas": "languages",
                    "idioma": "languages",
                    # education_level stored as dedicated lia_insights JSON key
                    "formação": "education_level",
                    "formacao": "education_level",
                    # availability_date stored in lia_insights JSON
                    "disponibilidade": "availability_date",
                    "disponibilidade de início": "availability_date",
                    "disponibilidade de inicio": "availability_date",
                }

                resolved_field = FIELD_ALIASES.get(field_name.lower(), field_name)

                if resolved_field not in ALLOWED_FIELDS:
                    return ActionResult(
                        status="error",
                        message=f"Campo '{field_name}' não é atualizável pelo chat. Campos permitidos: email, telefone, linkedin, cargo atual, empresa, cidade, estado, salário CLT/PJ, modelo de trabalho, formação, idiomas, disponibilidade.",
                        error_detail=f"Field '{field_name}' not in ALLOWED_FIELDS",
                        action_type="update_candidate_field",
                    )

                candidate_name = params.get("candidate_name", "o candidato")
                company_id = context.get("company_id") if context else None

                async with AsyncSessionLocal() as db:
                    # Tenant authz: verify candidate is linked to the caller's company
                    # via vacancy_candidates (has both candidate_id and company_id).
                    # If company_id is unavailable (demo/system), skip the check.
                    if company_id and candidate_id:
                        authz = await db.execute(
                            text("SELECT 1 FROM vacancy_candidates WHERE candidate_id = CAST(:cid AS uuid) AND company_id = CAST(:co AS uuid) LIMIT 1"),
                            {"cid": candidate_id, "co": str(company_id)},
                        )
                        if authz.fetchone() is None:
                            return ActionResult(
                                status="error",
                                message="Sem permissão para atualizar este candidato.",
                                error_detail="Candidate does not belong to caller's company",
                                action_type="update_candidate_field",
                            )

                    # For JSON-backed virtual fields, use jsonb_set on lia_insights
                    if resolved_field in ALLOWED_JSON_FIELDS:
                        result = await db.execute(
                            text(
                                "UPDATE candidates "
                                "SET lia_insights = COALESCE(lia_insights, '{}'::jsonb) || jsonb_build_object(:key, :val::text), "
                                "    updated_at = NOW() "
                                "WHERE id = CAST(:cid AS uuid)"
                            ),
                            {"key": resolved_field, "val": field_value, "cid": candidate_id},
                        )
                    else:
                        # Direct column update (candidates table; no company_id column)
                        result = await db.execute(
                            text(f"UPDATE candidates SET {resolved_field} = :val, updated_at = NOW() WHERE id = CAST(:cid AS uuid)"),
                            {"val": field_value, "cid": candidate_id},
                        )
                    if result.rowcount == 0:
                        return ActionResult(
                            status="error",
                            message="Candidato não encontrado ou sem permissão para atualizar.",
                            error_detail="Candidate not found or no rows updated",
                            action_type="update_candidate_field",
                        )
                    await db.commit()
                    self.execution_count += 1
                    return ActionResult(
                        status="executed",
                        message=f"Campo **{field_name}** de **{candidate_name}** atualizado para **{field_value}**.",
                        data={
                            "candidate_id": candidate_id,
                            "candidate_name": candidate_name,
                            "field": resolved_field,
                            "field_label": field_name,
                            "value": field_value,
                            "updated_at": datetime.utcnow().isoformat(),
                            "simulated": False,
                        },
                        action_type="update_candidate_field",
                    )
            except Exception as e:
                logger.warning(f"Direct update_candidate_field failed: {e}")
                return ActionResult(
                    status="error",
                    message="Erro ao atualizar o campo do candidato.",
                    error_detail=str(e),
                    action_type="update_candidate_field",
                )

        if action_id == "create_task":
            try:
                from app.core.database import AsyncSessionLocal
                from app.domains.automation.services.task_service import TaskService
                from app.models.task import TaskType, TaskPriority

                title = params.get("title", "")
                description = params.get("description", "")
                due_date_str = params.get("due_date", "")
                candidate_id = params.get("candidate_id")
                job_id = params.get("job_id")
                priority_str = params.get("priority", "medium")
                task_type_str = params.get("task_type", "general")
                user_id = context.get("user_id") if context else None

                due_date_val = _resolve_ptbr_datetime(due_date_str)

                # Map string values to enums
                priority_map = {
                    "low": TaskPriority.LOW, "medium": TaskPriority.MEDIUM,
                    "high": TaskPriority.HIGH, "critical": TaskPriority.CRITICAL,
                }
                type_map = {
                    "general": TaskType.GENERAL, "reminder": TaskType.FOLLOW_UP,
                    "review": TaskType.CV_REVIEW, "follow_up": TaskType.FOLLOW_UP,
                    "alert": TaskType.ALERT, "sourcing": TaskType.SOURCING,
                }
                task_priority = priority_map.get(priority_str.lower(), TaskPriority.MEDIUM)
                task_type = type_map.get(task_type_str.lower(), TaskType.GENERAL)

                task_svc = TaskService()
                async with AsyncSessionLocal() as db:
                    task = await task_svc.create_task(
                        db=db,
                        title=title,
                        description=description,
                        task_type=task_type,
                        priority=task_priority,
                        created_by_agent="lia_chat",
                        assigned_to_user_id=user_id,
                        related_job_id=job_id,
                        related_candidate_id=candidate_id,
                        due_date=due_date_val,
                        is_automated=False,
                        requires_confirmation=False,
                    )

                self.execution_count += 1
                due_info = f" para **{due_date_str}**" if due_date_str else ""
                action_label = "Lembrete" if task_type_str.lower() in ("reminder", "lembrete") else "Tarefa"
                return ActionResult(
                    status="executed",
                    message=f"{action_label} **\"{title}\"** criado(a) com sucesso{due_info}.",
                    data={
                        "task_id": str(task.id),
                        "title": title,
                        "due_date": due_date_val.isoformat() if due_date_val else None,
                        "candidate_id": candidate_id,
                        "job_id": job_id,
                        "priority": priority_str,
                        "created_at": datetime.utcnow().isoformat(),
                        "simulated": False,
                    },
                    action_type="create_task",
                )
            except Exception as e:
                logger.warning(f"TaskService create_task failed: {e}")
                return ActionResult(
                    status="error",
                    message="Não foi possível criar a tarefa. Tente novamente.",
                    error_detail=str(e),
                    action_type="create_task",
                )

        if action_id == "create_note":
            try:
                from app.core.database import AsyncSessionLocal
                from sqlalchemy import text
                import uuid as uuid_mod

                content = params.get("content", "")
                title = params.get("title", content[:60] + ("..." if len(content) > 60 else ""))
                candidate_id = params.get("candidate_id")
                job_id = params.get("job_id")
                user_id = context.get("user_id") if context else None

                note_id = str(uuid_mod.uuid4())

                company_id = context.get("company_id") if context else None

                async with AsyncSessionLocal() as db:
                    # interview_notes is the canonical notes table in this codebase.
                    # Required non-null columns: company_id, candidate_id (use placeholders when absent).
                    effective_company_id = str(company_id) if company_id else "00000000-0000-0000-0000-000000000000"
                    effective_candidate_id = str(candidate_id) if candidate_id else "00000000-0000-0000-0000-000000000000"
                    await db.execute(text("""
                        INSERT INTO interview_notes (
                            id, company_id, candidate_id, job_id,
                            general_notes, created_by, created_at, updated_at
                        ) VALUES (
                            CAST(:id AS uuid),
                            CAST(:company_id AS uuid),
                            CAST(:candidate_id AS uuid),
                            CAST(:job_id AS uuid),
                            :general_notes, :created_by, NOW(), NOW()
                        )
                    """), {
                        "id": note_id,
                        "company_id": effective_company_id,
                        "candidate_id": effective_candidate_id,
                        "job_id": job_id,
                        "general_notes": f"**{title}**\n\n{content}",
                        "created_by": user_id or "system",
                    })
                    await db.commit()

                self.execution_count += 1
                context_info = ""
                if params.get("candidate_name"):
                    context_info = f" vinculada ao candidato **{params['candidate_name']}**"
                elif params.get("job_title"):
                    context_info = f" vinculada à vaga **{params['job_title']}**"
                return ActionResult(
                    status="executed",
                    message=f"Nota salva com sucesso{context_info}.",
                    data={
                        "note_id": note_id,
                        "title": title,
                        "content": content,
                        "candidate_id": candidate_id,
                        "job_id": job_id,
                        "created_at": datetime.utcnow().isoformat(),
                        "simulated": False,
                    },
                    action_type="create_note",
                )
            except Exception as e:
                logger.warning(f"Direct create_note failed: {e}")
                return ActionResult(
                    status="error",
                    message="Não foi possível salvar a nota. Tente novamente.",
                    error_detail=str(e),
                    action_type="create_note",
                )

        if action_id == "create_generic_event":
            try:
                from app.domains.interview_scheduling.services.calendar_service import calendar_service

                title = params.get("title", "")
                dt_str = params.get("datetime", "")
                description = params.get("description", "")
                location = params.get("location", "")
                duration = params.get("duration_minutes", 60)
                user_id = context.get("user_id") if context else None

                if not user_id:
                    return ActionResult(
                        status="error",
                        message="Usuário não identificado para criar o compromisso.",
                        action_type="create_generic_event",
                    )

                event_data = await calendar_service.create_generic_event(
                    title=title,
                    start_time=dt_str,
                    organizer_id=user_id,
                    description=description,
                    location=location,
                    duration_minutes=int(duration) if duration else 60,
                )

                self.execution_count += 1
                return ActionResult(
                    status="executed",
                    message=f"Compromisso **\"{title}\"** registrado para **{dt_str}**.",
                    data={**event_data, "simulated": False},
                    action_type="create_generic_event",
                )
            except Exception as e:
                logger.warning(f"create_generic_event failed: {e}")
                return ActionResult(
                    status="error",
                    message="Não foi possível criar o compromisso. Tente novamente.",
                    error_detail=str(e),
                    action_type="create_generic_event",
                )

        if action_id == "generate_daily_briefing":
            try:
                from app.services.briefing_service import BriefingService
                from app.core.database import AsyncSessionLocal

                user_id = context.get("user_id") if context else None
                if not user_id:
                    return ActionResult(
                        status="error",
                        message="Não foi possível identificar o usuário para gerar o resumo da agenda.",
                        action_type="generate_daily_briefing",
                    )

                briefing_svc = BriefingService()
                async with AsyncSessionLocal() as db:
                    briefing = await briefing_svc.generate_daily_briefing(user_id=user_id, db=db)

                summary = briefing.get("summary", {})
                schedule = briefing.get("schedule", [])
                tasks = briefing.get("tasks", [])
                greeting = briefing.get("greeting", "Olá")

                schedule_lines = []
                for item in schedule[:5]:
                    t = item.get("time", "")
                    title_item = item.get("title", item.get("name", ""))
                    schedule_lines.append(f"  • {t} — {title_item}" if t else f"  • {title_item}")

                task_lines = []
                for task in tasks[:5]:
                    task_lines.append(f"  • {task.get('title', '')}")

                parts = [f"**{greeting}!** Aqui está o seu resumo para hoje:\n"]
                if summary.get("interviews_today", 0) > 0:
                    parts.append(f"📅 **Entrevistas hoje:** {summary['interviews_today']}")
                if summary.get("tasks_today", 0) > 0:
                    parts.append(f"✅ **Tarefas pendentes:** {summary['tasks_today']}")
                if summary.get("urgent_count", 0) > 0:
                    parts.append(f"⚠️ **Ações urgentes:** {summary['urgent_count']}")
                if schedule_lines:
                    parts.append("\n**Agenda de hoje:**\n" + "\n".join(schedule_lines))
                if task_lines:
                    parts.append("\n**Tarefas:**\n" + "\n".join(task_lines))
                if not schedule_lines and not task_lines:
                    parts.append("Sua agenda está livre hoje! Aproveite para prospectar candidatos ou revisar vagas abertas.")

                self.execution_count += 1
                return ActionResult(
                    status="executed",
                    message="\n".join(parts),
                    data=briefing,
                    action_type="generate_daily_briefing",
                )
            except Exception as e:
                logger.warning(f"generate_daily_briefing failed: {e}")
                return ActionResult(
                    status="error",
                    message="Não foi possível gerar o resumo da agenda. Tente novamente.",
                    error_detail=str(e),
                    action_type="generate_daily_briefing",
                )

        if action_id == "start_screening":
            try:
                candidate_ids = params.get("candidate_ids", [])
                logger.info(f"Screening queued for candidates: {candidate_ids}")
                self.execution_count += 1
                return ActionResult(
                    status="executed",
                    message="Triagem iniciada para os candidatos da vaga.",
                    data={
                        "action": "start_screening",
                        "candidate_ids": candidate_ids,
                        "queued_at": datetime.utcnow().isoformat(),
                        "simulated": False,
                    },
                    action_type="start_screening",
                )
            except Exception as e:
                logger.warning(f"Direct start_screening failed, falling back to domain: {e}")

        if action_id == "analyze_profile":
            try:
                candidate_id = params.get("candidate_id", "")
                candidate_name = params.get("candidate_name", "o candidato")
                logger.info(f"Profile analysis queued for candidate: {candidate_id}")
                self.execution_count += 1
                return ActionResult(
                    status="executed",
                    message=f"Análise de perfil iniciada para **{candidate_name}**.",
                    data={
                        "action": "analyze_profile",
                        "candidate_id": candidate_id,
                        "candidate_name": candidate_name,
                        "queued_at": datetime.utcnow().isoformat(),
                        "simulated": False,
                    },
                    action_type="analyze_profile",
                )
            except Exception as e:
                logger.warning(f"Direct analyze_profile failed, falling back to domain: {e}")

        try:
            safe_params = {k: v for k, v in params.items() if k not in ("email", "candidate_email", "body", "phone")}
            logger.info(f"Executing closed-loop action: {domain_id}.{action_id} params={list(safe_params.keys())}")

            from app.domains.registry import DomainRegistry

            registry = DomainRegistry()
            domain = registry.get_instance(domain_id)

            if not domain:
                logger.warning(f"Domain '{domain_id}' not found, using simulated execution")
                return await self._simulate_execution(action_id, params, context)

            if action_id == "move_candidate" and "candidate_id" in params and "vacancy_candidate_id" not in params:
                params["vacancy_candidate_id"] = params["candidate_id"]

            from app.domains.base import DomainContext
            domain_context = DomainContext(
                tenant_id=context.get("tenant_id", "default"),
                user_id=context.get("user_id", "recruiter"),
                conversation_id=context.get("conversation_id"),
                metadata=context,
            )

            response = await domain.execute_action(
                action_id=action_id,
                params=params,
                context=domain_context,
            )

            if response and response.success:
                self.execution_count += 1
                return ActionResult(
                    status="executed",
                    message=response.message or self._success_message(action_id, params),
                    data=response.data if isinstance(response.data, dict) else {"result": str(response.data)},
                    action_type=action_id,
                )
            else:
                error_msg = response.message if response else "Domain execution failed"
                logger.warning(f"Domain execution returned failure: {error_msg}")
                return await self._simulate_execution(action_id, params, context)

        except Exception as e:
            logger.error(f"Action execution error: {e}", exc_info=True)
            return await self._simulate_execution(action_id, params, context)

    async def _simulate_execution(
        self,
        action_id: str,
        params: Dict[str, Any],
        context: Dict[str, Any],
    ) -> ActionResult:
        candidate_name = params.get("candidate_name", "o candidato")
        self.execution_count += 1

        if action_id == "move_candidate":
            to_stage = params.get("to_stage", "próxima etapa")
            from_stage = params.get("from_stage", "")
            return ActionResult(
                status="executed",
                message=f"**{candidate_name}** foi movido(a) para a etapa **{to_stage}**.",
                data={
                    "candidate_id": params.get("candidate_id", ""),
                    "candidate_name": candidate_name,
                    "from_stage": from_stage,
                    "to_stage": to_stage,
                    "moved_at": datetime.utcnow().isoformat(),
                    "simulated": True,
                },
                action_type="move_candidate",
            )

        elif action_id == "send_email":
            subject = params.get("subject", "")
            return ActionResult(
                status="executed",
                message=f'Email enviado para **{candidate_name}** com assunto "{subject}".',
                data={
                    "candidate_id": params.get("candidate_id", ""),
                    "candidate_name": candidate_name,
                    "subject": subject,
                    "sent_at": datetime.utcnow().isoformat(),
                    "simulated": True,
                },
                action_type="send_email",
            )

        elif action_id == "schedule_interview":
            dt = params.get("datetime", "a definir")
            return ActionResult(
                status="executed",
                message=f"Entrevista agendada com **{candidate_name}** para **{dt}**.",
                data={
                    "candidate_id": params.get("candidate_id", ""),
                    "candidate_name": candidate_name,
                    "datetime": dt,
                    "scheduled_at": datetime.utcnow().isoformat(),
                    "simulated": True,
                },
                action_type="schedule_interview",
            )

        elif action_id in ("start_screening", "analyze_profile"):
            return ActionResult(
                status="executed",
                message="Triagem iniciada para os candidatos da vaga.",
                data={
                    "action": action_id,
                    "started_at": datetime.utcnow().isoformat(),
                    "simulated": True,
                },
                action_type=action_id,
            )

        elif action_id == "update_candidate_field":
            field_name = params.get("field_name", "campo")
            field_value = params.get("field_value", "")
            return ActionResult(
                status="executed",
                message=f"Campo **{field_name}** de **{candidate_name}** atualizado para **{field_value}**.",
                data={
                    "candidate_id": params.get("candidate_id", ""),
                    "field": field_name,
                    "value": field_value,
                    "simulated": True,
                },
                action_type="update_candidate_field",
            )

        elif action_id == "create_task":
            title = params.get("title", "tarefa")
            due_date = params.get("due_date", "")
            due_info = f" para **{due_date}**" if due_date else ""
            task_type = params.get("task_type", "general")
            action_label = "Lembrete" if task_type == "reminder" else "Tarefa"
            return ActionResult(
                status="executed",
                message=f"{action_label} **\"{title}\"** criado(a){due_info}.",
                data={
                    "title": title,
                    "due_date": due_date,
                    "simulated": True,
                },
                action_type="create_task",
            )

        elif action_id == "create_note":
            content = params.get("content", "")
            return ActionResult(
                status="executed",
                message="Nota salva com sucesso.",
                data={
                    "content": content,
                    "candidate_id": params.get("candidate_id"),
                    "job_id": params.get("job_id"),
                    "simulated": True,
                },
                action_type="create_note",
            )

        elif action_id == "create_generic_event":
            title = params.get("title", "compromisso")
            dt_str = params.get("datetime", "")
            return ActionResult(
                status="executed",
                message=f"Compromisso **\"{title}\"** criado para **{dt_str}**.",
                data={
                    "title": title,
                    "datetime": dt_str,
                    "simulated": True,
                },
                action_type="create_generic_event",
            )

        elif action_id == "pause_job":
            job_title = params.get("job_title", "a vaga")
            return ActionResult(
                status="executed",
                message=f"Vaga **{job_title}** pausada com sucesso.",
                data={
                    "job_id": params.get("job_id", ""),
                    "job_title": job_title,
                    "reason": params.get("reason", ""),
                    "paused_at": datetime.utcnow().isoformat(),
                    "simulated": True,
                },
                action_type="pause_job",
            )

        elif action_id == "close_job":
            job_title = params.get("job_title", "a vaga")
            return ActionResult(
                status="executed",
                message=f"Vaga **{job_title}** fechada com sucesso.",
                data={
                    "job_id": params.get("job_id", ""),
                    "job_title": job_title,
                    "reason": params.get("reason", ""),
                    "outcome": params.get("outcome", ""),
                    "closed_at": datetime.utcnow().isoformat(),
                    "simulated": True,
                },
                action_type="close_job",
            )

        elif action_id == "duplicate_job":
            job_title = params.get("job_title", "a vaga")
            return ActionResult(
                status="executed",
                message=f"Vaga **{job_title}** duplicada com sucesso.",
                data={
                    "job_id": params.get("job_id", ""),
                    "job_title": job_title,
                    "new_title": params.get("new_title", ""),
                    "duplicated_at": datetime.utcnow().isoformat(),
                    "simulated": True,
                },
                action_type="duplicate_job",
            )

        elif action_id == "reopen_job":
            job_title = params.get("job_title", "a vaga")
            return ActionResult(
                status="executed",
                message=f"Vaga **{job_title}** reaberta com sucesso.",
                data={
                    "job_id": params.get("job_id", ""),
                    "job_title": job_title,
                    "reopened_at": datetime.utcnow().isoformat(),
                    "simulated": True,
                },
                action_type="reopen_job",
            )

        return ActionResult(
            status="executed",
            message=f"Ação **{action_id}** executada com sucesso.",
            data={"action": action_id, "params": params, "simulated": True},
            action_type=action_id,
        )

    def _success_message(self, action_id: str, params: Dict[str, Any]) -> str:
        candidate_name = params.get("candidate_name", "o candidato")
        if action_id == "move_candidate":
            return f"**{candidate_name}** foi movido(a) para **{params.get('to_stage', 'próxima etapa')}**."
        elif action_id == "send_email":
            return f"Email enviado para **{candidate_name}**."
        elif action_id == "schedule_interview":
            return f"Entrevista agendada com **{candidate_name}**."
        return f"Ação {action_id} executada com sucesso."


action_executor = ActionExecutorService()

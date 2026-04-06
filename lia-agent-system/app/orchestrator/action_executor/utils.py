"""
Pure utility functions for ActionExecutor.
No async code, no database access — safe to import from anywhere.
"""
import re
from datetime import datetime
from typing import Any

from app.orchestrator.action_executor.intents_config import (
    CONFIRMATION_PATTERNS,
    MESSAGE_INTENT_PATTERNS,
    REJECTION_PATTERNS,
    STAGE_ALIASES,
    VALID_PIPELINE_STAGES,
)


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
    candidate_name: str | None,
    candidate_id: str | None,
    candidates_data: list[dict[str, Any]],
) -> dict[str, Any] | None:
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


def resolve_stage(stage_text: str | None) -> str | None:
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


def _detect_intent_from_message(message: str) -> str | None:
    """Detect an actionable intent from a raw message string."""
    if not message:
        return None
    msg_lower = message.lower().strip()
    for intent, patterns in MESSAGE_INTENT_PATTERNS:
        for pattern in patterns:
            if re.search(pattern, msg_lower):
                return intent
    return None


def _extract_entities_from_message(message: str, intent: str) -> dict[str, Any]:
    """Extract entity values from raw message for a given intent."""
    entities: dict[str, Any] = {}
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


def _resolve_ptbr_datetime(date_str: str) -> datetime | None:
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
    from datetime import datetime as _dt
    from datetime import timedelta as _td

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

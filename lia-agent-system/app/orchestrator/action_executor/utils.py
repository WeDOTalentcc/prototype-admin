"""
Pure utility functions for ActionExecutor.
No async code, no database access — safe to import from anywhere.
"""
import re
from datetime import datetime
from typing import Any

import logging

logger = logging.getLogger(__name__)

from app.orchestrator.action_executor.intents_config import (
    CONFIRMATION_PATTERNS,
    MESSAGE_INTENT_PATTERNS,
    REJECTION_PATTERNS,
    STAGE_ALIASES,
    VALID_PIPELINE_STAGES,
)


# ---------------------------------------------------------------------------
# LIA-I04: Build a shadow KeywordIntentMatcher from MESSAGE_INTENT_PATTERNS
# for telemetry.  Runs alongside the regex to surface migration signals.
# ---------------------------------------------------------------------------
_INTENT_MATCHER = None


def _get_intent_matcher():
    global _INTENT_MATCHER
    if _INTENT_MATCHER is not None:
        return _INTENT_MATCHER
    try:
        from app.shared.services.keyword_intent_matcher import KeywordIntentMatcher
        import re as _re
        keywords_map: dict[str, str] = {}
        for intent_name, patterns in MESSAGE_INTENT_PATTERNS:
            for pattern in patterns:
                # Extract literal keywords from regex (strip metacharacters)
                literal = _re.sub(r"[\^\$\(\)\[\]\?\*\+\\\|\{\}]", "", pattern).strip()
                literal = _re.sub(r"\s\+", " ", literal)
                literal = _re.sub(r"\s+", " ", literal)
                if literal and len(literal) > 2:
                    keywords_map[literal.lower()] = intent_name
        _INTENT_MATCHER = KeywordIntentMatcher.from_keyword_map(
            keywords_map, domain_id="action_executor"
        )
        return _INTENT_MATCHER
    except Exception:
        return None


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


def _detect_intent_from_message(message: str, conversation_history: list | None = None) -> str | None:
    """Detect an actionable intent from a raw message string.

    LIA-I04: shadow-compares with KeywordIntentMatcher for telemetry.
    """
    if not message:
        return None
    msg_lower = message.lower().strip()

    # NEGATION_BYPASS: Correction and multi-step messages go to Phase 2
    _NEGATION_STARTS = ("não, não", "nao, nao", "não era isso", "nao era isso", "cancela isso", "na verdade,")
    _MULTI_STEP_MARKERS = (" e avança", " e manda ", " e envia ", " e depois manda", ", avança ", ", manda ", ", move para ")
    if msg_lower.startswith(_NEGATION_STARTS):
        return None  # correction — let Phase 2 handle context-aware cancellation
    if any(m in msg_lower for m in _MULTI_STEP_MARKERS):
        return None  # multi-step workflow — Phase 2 handles sequential tool calls

    # LIA-M04: Loop detection — if the same intent was just executed, skip
    if conversation_history:
        try:
            last_assistant = None
            for msg in reversed(conversation_history):
                if msg.get("role") == "assistant":
                    last_assistant = msg.get("content", "")
                    break
            if last_assistant and "encaminhada" in last_assistant.lower():
                # Last response was an action confirmation — likely user is retrying
                # Fall through to Phase 2 (LLM-based) instead of repeating same action
                logger.info("[LIA-M04] Loop detected: last response was action confirmation, skipping regex intent")
                return None
        except Exception:
            pass  # fail-open

    detected_intent = None
    for intent, patterns in MESSAGE_INTENT_PATTERNS:
        for pattern in patterns:
            if re.search(pattern, msg_lower):
                detected_intent = intent
                break
        if detected_intent:
            break

    # LIA-I04: Shadow comparison with KeywordIntentMatcher (fail-open)
    try:
        matcher = _get_intent_matcher()
        if matcher is not None:
            shadow_match = matcher.match(message)
            shadow_intent = shadow_match.action if shadow_match.confidence > 0.5 else None
            if detected_intent != shadow_intent:
                logger.debug(
                    "[LIA-I04] Intent disagreement: regex=%s, matcher=%s (conf=%.2f), msg=%r",
                    detected_intent, shadow_intent, shadow_match.confidence, message[:60],
                )
    except Exception as e:
        logger.debug("[LIA-I04] Shadow match failed (fail-open): %s", e)

    return detected_intent


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

    # Interview scheduling: extract candidate name and datetime
    if intent in ("agendar_entrevista", "reagendar_entrevista", "cancelar_entrevista",
                  "enviar_lembrete_entrevista") and not entities.get("candidate_name"):
        # "convida o Marco Oliveira para entrevista" or "agendamento com Ana Costa"
        name_m = re.search(
            r"(?:convida[rn]?\s+o?\s*|com\s+|para\s+(?:o|a)\s+|d[oa]\s+)([A-ZÁÉÍÓÚÂÊÎÔÛÃÕ][a-záéíóúâêîôûãõ]+(?:\s+[A-ZÁÉÍÓÚÂÊÎÔÛÃÕ][a-záéíóúâêîôûãõ]+)+)",
            msg
        )
        if name_m:
            entities["candidate_name"] = name_m.group(1).strip()
        # Extract datetime: "amanhã às 14h", "hoje às 9h30"
        dt_m = re.search(
            r"(amanhã|hoje|segunda|terça|quarta|quinta|sexta|sábado|domingo|\d{1,2}/\d{1,2}(?:/\d{2,4})?)(?:\s+às?\s+(\d{1,2})h?(?::?(\d{2}))?)?",
            msg, re.IGNORECASE
        )
        if dt_m:
            date_val = dt_m.group(1)
            if dt_m.group(2):
                hour = dt_m.group(2)
                minute = dt_m.group(3) or "00"
                date_val = f"{date_val} {hour}:{minute}"
            entities["datetime"] = date_val
        # Extract format
        if re.search(r"videoconferência|video\s*call|zoom|teams|meet|online|remoto", msg, re.IGNORECASE):
            entities["type"] = "video"
        elif re.search(r"presencial|escritório|sede", msg, re.IGNORECASE):
            entities["type"] = "presencial"

    # WhatsApp / communication: extract candidate name and message body
    if intent in ("enviar_whatsapp", "enviar_email", "enviar_feedback") and not entities.get("candidate_name"):
        # "manda um WhatsApp para a Ana Costa" or "envia email para João Silva"
        name_m = re.search(
            r"(?:para\s+(?:o|a)\s+|ao\s+|à\s+)([A-ZÁÉÍÓÚÂÊÎÔÛÃÕ][a-záéíóúâêîôûãõ]+(?:\s+[A-ZÁÉÍÓÚÂÊÎÔÛÃÕ][a-záéíóúâêîôûãõ]+)+)",
            msg
        )
        if name_m:
            entities["candidate_name"] = name_m.group(1).strip()
        # Extract message body
        body_m = re.search(
            r"(?:confirmando|dizendo|que|com\s+o\s+texto|mensagem[:]?\s*)(.{10,200})",
            msg, re.IGNORECASE
        )
        if body_m:
            entities["body"] = body_m.group(1).strip()

    # Sourcing: extract query from message when intent is a candidate search
    if intent in ("buscar_candidatos", "sugerir_candidatos") and "query" not in entities:
        # Extract everything after action verb + "candidatos"
        m = re.search(
            r"(?:busca[rn]?|pesquisa[rn]?|encontra[rn]?|procura[rn]?|sugere|sugira[rn]?)\s+"
            r"(?:candidatos?\s+)?(?:com\s+|para\s+|que\s+|de\s+)?(.{5,})",
            msg, re.IGNORECASE
        )
        if m:
            entities["query"] = m.group(1).strip()[:300]
        elif len(msg) > 10:
            entities["query"] = msg[:300]

    # CM-001: Extract candidate_name for profile analysis intent
    if intent == "analisar_perfil" and "candidate_name" not in entities:
        # "avalia o curriculo do Joao Silva para a vaga de Tech Lead"
        # "analisa o perfil de Ana Costa"
        name_m = re.search(
            r"(?:d[eo]\s+|do?\s+candidato\s+|avali[ae]r?\s+)([A-ZÀ-ÿ][a-zÀ-ÿ]+(?:\s+[A-ZÀ-ÿ][a-zÀ-ÿ]+)+)",
            msg
        )
        if not name_m:
            name_m = re.search(
                r"(?:d[eo]\s+|do?\s+candidato\s+)([a-z][a-z]+(?:\s+[a-z][a-z]+)+)(?:\s+para|\s+pra|$)",
                msg, re.IGNORECASE
            )
        if name_m:
            entities["candidate_name"] = name_m.group(1).strip().title()
        if "job_id" not in entities:
            job_m = re.search(r"para\s+a\s+vaga\s+de\s+(.{3,50}?)(?:\s*$|,|\.|!)", msg, re.IGNORECASE)
            if job_m:
                entities["job_title"] = job_m.group(1).strip()

    # CM-003: Extract candidate_names list for compare intent
    if intent == "comparar_candidatos" and "candidate_ids" not in entities and "candidate_names" not in entities:
        # "compara Joao Silva e Ana Costa para a vaga de Product Manager"
        names_m = re.search(
            r"compara[rn]?\s+([A-ZÀ-ÿ][a-zÀ-ÿ]+(?:\s+[A-ZÀ-ÿ][a-zÀ-ÿ]+)*)\s+e\s+([A-ZÀ-ÿ][a-zÀ-ÿ]+(?:\s+[A-ZÀ-ÿ][a-zÀ-ÿ]+)*)",
            msg
        )
        if not names_m:
            names_m = re.search(
                r"compara[rn]?\s+([a-z][a-z]+(?:\s+[a-z][a-z]+)*)\s+e\s+([a-z][a-z]+(?:\s+[a-z][a-z]+)*)",
                msg, re.IGNORECASE
            )
        if names_m:
            entities["candidate_names"] = [
                names_m.group(1).strip().title(),
                names_m.group(2).strip().title(),
            ]
        if "job_id" not in entities:
            job_m = re.search(r"para\s+a\s+vaga\s+de\s+(.{3,50}?)(?:\s*$|,|\.|!)", msg, re.IGNORECASE)
            if job_m:
                entities["job_title"] = job_m.group(1).strip()

    # MT-002: job_title lookup for sourcing intents that need job context
    if intent in ("rankear_candidatos", "sugerir_candidatos", "iniciar_triagem") and "job_title" not in entities and "job_id" not in entities:
        _jt_m = re.search(r"para\s+a\s+vaga\s+de\s+(.{3,50}?)(?:\s*$|,|\.|!)", msg, re.IGNORECASE)
        if _jt_m:
            entities["job_title"] = _jt_m.group(1).strip()

        # CM-007 / MT-002: Extract job_id from message text (e.g. "V0037", "vaga V0037")
    # This is needed when context doesn't have entity_id (scope=Vagas without specific job)
    if "job_id" not in entities and intent in (
        "rankear_candidatos", "comparar_candidatos", "listar_candidatos_por_etapa",
        "iniciar_triagem", "disparar_triagem", "health_check_vaga", "analisar_funil",
        "exportar_candidatos", "sugerir_candidatos", "mover_candidatos_por_etapa",
    ):
        # Match patterns like "V0037", "V-0037", "vaga V0037", "vagas V0037"
        job_m = re.search(r"\b(V[-_]?\d{3,6})\b", msg, re.IGNORECASE)
        if job_m:
            entities["job_id"] = job_m.group(1).upper().replace("-", "").replace("_", "")
            logger.debug("[extract_entities] Extracted job_id=%s from message text", entities["job_id"])

    # KB-002: Extract candidate_name for mover_candidato intent
    if intent == "mover_candidato" and not entities.get("candidate_name"):
        # "move o João Silva de Triagem para Entrevista"
        # "mover_candidato_name_extract": handles "move <name> de <stage> para <stage>"
        _mv_m = re.search(
            r"(?:move[rn]?\s+(?:o|a|os|as)?\s*|mova\s+(?:o|a)?\s*)([A-ZÁÉÍÓÚ][a-záéíóúâêîôûãõ]+(?:\s+[A-ZÁÉÍÓÚ][a-záéíóúâêîôûãõ]+)+)",
            msg, re.IGNORECASE
        )
        if _mv_m:
            entities["candidate_name"] = _mv_m.group(1).strip()
            # candidate_id will be resolved by _move_candidate via resolve_candidate_by_name

    # WZ-003: Extract job_title, location, seniority for salary suggestion
    if intent == "sugerir_salario":
        # Extract job title: "para um Tech Lead Frontend", "de Product Manager"
        _title_m = re.search(
            r"(?:para\s+(?:um[a]?\s+)?|de\s+)([A-Za-záéíóúâêîôûãõÁÉÍÓÚÂÊÎÔÛÃÕ][a-zA-Záéíóúâêîôûãõ]+(?:\s+[A-Za-záéíóúâêîôûãõ]+){0,4})",
            msg, re.IGNORECASE
        )
        if _title_m and not entities.get("job_title"):
            entities["job_title"] = _title_m.group(1).strip()
        # Extract location: "em São Paulo", "no Rio de Janeiro"
        _loc_m = re.search(r"\bem\s+([A-ZÁÉÍÓÚ][a-záéíóúâêîôûãõ]+(?:\s+[A-ZÁÉÍÓÚ]?[a-záéíóúâêîôûãõ]+)?)", msg)
        if _loc_m and not entities.get("location"):
            entities["location"] = _loc_m.group(1).strip()
        # Infer seniority from years: "5 anos de experiência"
        _years_m = re.search(r"(\d+)\s+anos?\s+de\s+experiência", msg, re.IGNORECASE)
        if _years_m and not entities.get("seniority"):
            _yrs = int(_years_m.group(1))
            if _yrs <= 2:
                entities["seniority"] = "junior"
            elif _yrs <= 5:
                entities["seniority"] = "pleno"
            else:
                entities["seniority"] = "sênior"

    # WZ-002: Extract job_title and skills for JD generation
    if intent == "gerar_jd":
        # Extract job title: "para Product Manager", "de Tech Lead"
        _jd_title_m = re.search(
            r"(?:para\s+(?:um[a]?\s+)?|de\s+|vaga\s+de\s+)([A-Za-záéíóúâêîôûãõÁÉÍÓÚÂÊÎÔÛÃÕ][a-zA-Záéíóúâêîôûãõ]+(?:\s+[A-Za-záéíóúâêîôûãõ]+){0,4})",
            msg, re.IGNORECASE
        )
        if _jd_title_m and not entities.get("job_title"):
            entities["job_title"] = _jd_title_m.group(1).strip()
        # Extract skills from "com X e Y"
        _skills = []
        if re.search(r"(metodologias?\s+[áa]geis?|agile|scrum|kanban|sprint)", msg, re.IGNORECASE):
            _skills.extend(["Metodologias Ágeis", "Scrum", "Kanban"])
        if re.search(r"(dados?|data|analytics?|sql|bi|business\s+intelligence)", msg, re.IGNORECASE):
            _skills.extend(["Análise de Dados", "SQL"])
        if re.search(r"(python|java|javascript|typescript|react|node|backend|frontend)", msg, re.IGNORECASE):
            _match = re.search(r"(python|java|javascript|typescript|react|node)", msg, re.IGNORECASE)
            if _match:
                _skills.append(_match.group(1).title())
        if re.search(r"(cloud|aws|azure|gcp|kubernetes|docker)", msg, re.IGNORECASE):
            _skills.append("Cloud")
        if _skills and not entities.get("skills"):
            entities["skills"] = _skills

        # KB-004: Extract from_stage/to_stage for mover_candidatos_por_etapa
    if intent == "mover_candidatos_por_etapa" and ("from_stage" not in entities or "to_stage" not in entities):
        stage_names = [
            "entrevista técnica", "entrevista tecnica", "entrevista final", "entrevista rh",
            "entrevista", "triagem", "proposta", "oferta", "shortlist", "análise", "analise",
            "teste técnico", "teste tecnico", "contratado", "reprovado", "aprovado", "novo",
        ]
        stage_canonical = {
            "entrevista técnica": "Entrevista Técnica", "entrevista tecnica": "Entrevista Técnica",
            "entrevista final": "Entrevista Final", "entrevista rh": "Entrevista",
            "entrevista": "Entrevista", "triagem": "Triagem", "proposta": "Proposta",
            "oferta": "Oferta", "shortlist": "Shortlist", "análise": "Análise",
            "analise": "Análise", "teste técnico": "Teste Técnico", "teste tecnico": "Teste Técnico",
            "contratado": "Contratado", "reprovado": "Reprovado", "aprovado": "Aprovado", "novo": "Novo",
        }
        msg_l = msg.lower()
        # Pattern: "em/da/de <stage> para <stage>"
        stage_pattern = "(?:" + "|".join(re.escape(s) for s in stage_names) + ")"
        m_stages = re.search(
            r"(?:em|da|de|na)\s+(" + stage_pattern + r")\s+para\s+(" + stage_pattern + r")",
            msg_l, re.IGNORECASE
        )
        if m_stages and "from_stage" not in entities:
            entities["from_stage"] = stage_canonical.get(m_stages.group(1).strip().lower(), m_stages.group(1).strip().title())
        if m_stages and "to_stage" not in entities:
            entities["to_stage"] = stage_canonical.get(m_stages.group(2).strip().lower(), m_stages.group(2).strip().title())
        if not m_stages:
            # Fallback: "move/mover <all candidates> para <stage>"
            m_to = re.search(r"para\s+(" + stage_pattern + r")", msg_l, re.IGNORECASE)
            if m_to and "to_stage" not in entities:
                entities["to_stage"] = stage_canonical.get(m_to.group(1).strip().lower(), m_to.group(1).strip().title())

    # KB-006: Extract stage from message for listar_candidatos_por_etapa
    if intent == "listar_candidatos_por_etapa" and "stage" not in entities:
        stage_map = [
            ("entrevista técnica", "Entrevista Técnica"),
            ("entrevista tecnica", "Entrevista Técnica"),
            ("entrevista final", "Entrevista Final"),
            ("entrevista rh", "Entrevista"),
            ("entrevista", "Entrevista"),
            ("triagem", "Triagem"),
            ("proposta", "Proposta"),
            ("oferta", "Oferta"),
            ("shortlist", "Shortlist"),
            ("análise", "Análise"),
            ("analise", "Análise"),
            ("teste técnico", "Teste Técnico"),
            ("teste tecnico", "Teste Técnico"),
            ("contratado", "Contratado"),
            ("reprovado", "Reprovado"),
            ("novo", "Novo"),
        ]
        msg_lower_s = msg.lower()
        for keyword, stage_value in stage_map:
            if keyword in msg_lower_s:
                entities["stage"] = stage_value
                logger.debug("[extract_entities] Extracted stage=%s from message", stage_value)
                break

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

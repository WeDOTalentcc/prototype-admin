"""onboarding_settings_runner.py — P2-2 Sprint A.4 integration runner.

Orquestra o ciclo completo:
1. handle_user_response (settings_phase) -> decide acao
2. Se EXTRACT_FIELDS -> chama field_extractor
3. Se PERSIST_FIELDS -> chama _wrap_save_company_field
4. Retorna mensagem pra usuario + estado atualizado

Multi-tenancy: company_id sempre do session.company_id (JWT).
Audit: _wrap_save_company_field cuida via audit_company_change.

Principios canonical-fix:
- Single source of truth: settings_phase e state machine
- Fail-CLOSED: extraction failure -> user-friendly error, NUNCA silent
- DRY: NAO duplica logica de save (delega ao tool canonical)

Audit ref: ~/Documents/wedotalent_audit_2026-05-26/P2-2_ONBOARDING_CONVERSACIONAL_ADR.md Sprint A.4
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

from app.shared.observability.onboarding_metrics import (
    record_chat_completed,
    record_chat_started,
    record_extraction_duration,
    record_field_extracted,
)
from app.services.onboarding_field_extractor import (
    ExtractionResult,
    extract_field_from_message,
)
from app.services.onboarding_settings_phase import (
    ActionType,
    SettingsExtractionStatus,
    handle_extraction_result,
    handle_persist_success,
    handle_user_response,
    start_settings_extraction,
)
from app.services.onboarding_yaml_loader import calculate_progress, load_config

logger = logging.getLogger(__name__)


# === Canonical section mapping ===
# Aligned with _PROFILE_FIELD_QUERIES + _CULTURE_FIELD_QUERIES in
# app/domains/company_settings/agents/company_tool_registry.py.
_PROFILE_FIELDS: frozenset[str] = frozenset(
    {
        "name",
        "trade_name",
        "cnpj",
        "website",
        "industry",
        "employee_count",
        "company_size",
        "founded_year",
        "linkedin_url",
        "hr_email",
        "phone",
        "headquarters_city",
    }
)
_CULTURE_FIELDS: frozenset[str] = frozenset(
    {
        "mission",
        "vision",
        "values",
        "work_model",
        "core_competencies",
        "engineering_culture",
        "default_languages",
        "dei_initiatives",
        "sustainability",
        "social_impact",
        "leadership_style",
        "team_dynamics",
        "evp_bullets",
        "growth_opportunities",
        "behavioral_competencies",
        "tech_stack",
    }
)
_POLICY_FIELDS: frozenset[str] = frozenset(
    {
        "auto_screening_enabled",
        "min_interviews_before_offer",
        "auto_stage_advance_enabled",
        "max_days_in_stage",
        "manager_approval_for_offer",
        "autonomy_level",
        "allowed_days",
        "allowed_hours",
        "preferred_channel",
        "auto_rejection_feedback",
        "rejection_feedback_deadline_hours",
        "default_interview_duration_min",
        "auto_scheduling_enabled",
        "salary_screening_enabled",
        "salary_tolerance_percent",
        "experience_policy",
    }
)
_WORKFORCE_FIELDS: frozenset[str] = frozenset(
    {
        "hiring_volume",
        "job_types",
        "main_priority",
        "main_challenges",
    }
)
_LIA_PERSONA_FIELDS: frozenset[str] = frozenset(
    {
        "ai_persona.name",
        "ai_persona.tone",
    }
)


SaveFieldFn = Callable[..., Awaitable[dict[str, Any]]]


@dataclass(frozen=True)
class RunnerResponse:
    """Resposta canonical do runner pro orchestrator.

    Fields:
        user_message: texto pra mandar pro usuario
        status: SettingsExtractionStatus atualizado (caller persiste)
        is_complete: True se atingiu finalize threshold ou usuario parou
        progress_percent: 0-100
    """

    user_message: str
    status: SettingsExtractionStatus
    is_complete: bool = False
    progress_percent: int = 0


def _progress(status: SettingsExtractionStatus) -> int:
    """Helper: calculate_progress dos answered fields."""
    return calculate_progress(status.answered_field_keys)


def _resolve_section_for_field(field_key: str) -> str:
    """Mapeia field_key -> section canonical.

    Sections:
    - "profile" -> CompanyProfile cols
    - "culture" -> CompanyCultureProfile cols
    - "policy" -> HiringPolicy communication_rules (via _wrap_save_hiring_policy)
    - "workforce" -> CompanyProfile additional_data JSONB
    - "lia_persona" -> ai_persona_service.update_ai_persona

    Sprint 1 BE-2 (2026-05-27): adicionados policy/workforce/lia_persona sections.
    """
    if field_key in _PROFILE_FIELDS:
        return "profile"
    if field_key in _CULTURE_FIELDS:
        return "culture"
    if field_key in _POLICY_FIELDS:
        return "policy"
    if field_key in _WORKFORCE_FIELDS:
        return "workforce"
    if field_key in _LIA_PERSONA_FIELDS:
        return "lia_persona"
    logger.warning(
        "P2-2 Sprint 1 BE-2: field_key '%s' sem section mapping "
        "fall-back to 'profile'. Adicionar ao frozenset correto.",
        field_key,
    )
    return "profile"


async def _default_save_field(
    *,
    company_id: str,
    section: str,
    field: str,
    value: Any,
    user_id: str | None = None,
) -> dict[str, Any]:
    """Default save fn - routes based on section to canonical tool.

    Sections:
    - "profile" / "culture" to _wrap_save_company_field (existing)
    - "workforce" to _wrap_save_company_field section="profile" (additional_data JSONB)
    - "policy" to _wrap_save_hiring_policy(rules={field: value})
    - "lia_persona" to ai_persona_service.update_ai_persona

    Lazy import pra manter o runner unit-testavel sem boot completo do agent stack.
    Sprint 1 BE-2 (2026-05-27): adicionado routing policy/workforce/lia_persona.
    """
    if section in ("profile", "culture", "workforce"):
        from app.domains.company_settings.agents.company_tool_registry import (
            _wrap_save_company_field,
        )
        actual_section = "profile" if section == "workforce" else section
        return await _wrap_save_company_field(
            company_id=company_id,
            section=actual_section,
            field=field,
            value=value,
            user_id=user_id,
        )

    if section == "policy":
        from app.domains.company_settings.agents.company_tool_registry import (
            _wrap_save_hiring_policy,
        )
        return await _wrap_save_hiring_policy(
            company_id=company_id,
            user_id=user_id,
            rules={field: value},
        )

    if section == "lia_persona":
        persona_key = field.removeprefix("ai_persona.")
        try:
            from app.core.database import AsyncSessionLocal
            from app.domains.persona.services import ai_persona_service

            async with AsyncSessionLocal() as db:
                current = await ai_persona_service.get_ai_persona(company_id, db)
                update_kwargs: dict[str, Any] = {**current, persona_key: value}
                result = await ai_persona_service.update_ai_persona(
                    company_id=company_id,
                    db=db,
                    name=update_kwargs.get("name", current.get("name")),
                    tone=update_kwargs.get("tone", current.get("tone")),
                    actor_user_id=user_id,
                )
                return {
                    "success": True,
                    "data": result,
                    "message": f"Persona atualizada: {persona_key} = {value}",
                }
        except Exception as e:
            logger.error(
                "P2-2 Sprint 1 BE-2: lia_persona save failed field=%s company=%s err=%s",
                field,
                company_id,
                e,
                exc_info=True,
            )
            return {
                "success": False,
                "data": {},
                "message": f"Erro ao salvar persona: {type(e).__name__}",
            }

    # Fallback to profile (unknown section)
    from app.domains.company_settings.agents.company_tool_registry import (
        _wrap_save_company_field,
    )
    return await _wrap_save_company_field(
        company_id=company_id,
        section="profile",
        field=field,
        value=value,
        user_id=user_id,
    )


async def start(company_id: str) -> RunnerResponse:
    """Inicia onboarding settings -- retorna greeting + status inicial.

    Args:
        company_id: tenant id (JWT). Usado em audit downstream.
    """
    # company_id reservado pra audit downstream (start em si nao escreve).
    record_chat_started()  # P2-2 Sprint C telemetry
    status, action = start_settings_extraction()
    return RunnerResponse(
        user_message=action.message,
        status=status,
        is_complete=False,
        progress_percent=0,
    )


async def process_message(
    status: SettingsExtractionStatus,
    user_message: str,
    company_id: str,
    user_id: str | None = None,
    save_field_fn: SaveFieldFn | None = None,
    use_llm: bool = True,
    llm_service: Any = None,
) -> RunnerResponse:
    """Processa mensagem do usuario e avanca state machine.

    Pipeline:
    1. handle_user_response (settings_phase) -> acao
    2. Se EXTRACT_FIELDS:
       a. extract_field_from_message (extractor) -> ExtractionResult
       b. handle_extraction_result -> CONFIRM_EXTRACTION action
    3. Se PERSIST_FIELDS:
       a. Para cada extracted field: call save_field_fn(...)
       b. handle_persist_success -> proxima pergunta OR finalize
    4. Retorna RunnerResponse com user_message pra renderizar

    Args:
        status: state atual (caller passa snapshot)
        user_message: resposta do usuario
        company_id: tenant id (JWT, NUNCA do payload)
        user_id: pra audit
        save_field_fn: injectable function (company_id, section, field, value, user_id) -> dict.
                       Default = producao (_wrap_save_company_field). Tests injetam mock.
    """
    if save_field_fn is None:
        save_field_fn = _default_save_field

    # Dispatch baseado em state atual
    new_status, action = handle_user_response(status, user_message)

    if action.action_type == ActionType.EXTRACT_FIELDS:
        # Run LLM extraction. Phase passa target_field na action.
        if action.target_field is None:
            logger.error(
                "P2-2 A.4: EXTRACT_FIELDS sem target_field -- state machine bug. "
                "company=%s state=%s",
                company_id,
                new_status.state,
            )
            return RunnerResponse(
                user_message="Tive um problema interno. Pode tentar de novo?",
                status=new_status,
                is_complete=False,
                progress_percent=_progress(new_status),
            )

        _extract_start = time.time()  # P2-2 Sprint C telemetry
        result: ExtractionResult = await extract_field_from_message(
            target_field=action.target_field,
            user_message=user_message,
            additional_context_fields=action.additional_context,
            company_id=company_id,
            use_llm=use_llm,
            llm_service=llm_service,
        )
        record_extraction_duration(time.time() - _extract_start)

        if not result.success or not result.extracted_fields:
            # Fail-CLOSED: mostrar erro amigavel, NAO finge sucesso.
            reason = result.error or "Pode reformular?"
            return RunnerResponse(
                user_message=f"Hmm, nao consegui entender bem. {reason}",
                status=new_status,  # mantem ASKING
                is_complete=False,
                progress_percent=_progress(new_status),
            )

        new_status, confirm_action = handle_extraction_result(
            new_status, result.extracted_fields, result.confidence
        )
        return RunnerResponse(
            user_message=confirm_action.message,
            status=new_status,
            is_complete=False,
            progress_percent=_progress(new_status),
        )

    if action.action_type == ActionType.PERSIST_FIELDS:
        # Persist extracted fields via tool canonical
        persisted: dict[str, Any] = {}
        errors: list[str] = []
        pending = action.pending_extraction or {}
        config = load_config()

        for field_key, value in pending.items():
            field_def = config.get_field(field_key)
            if field_def is None:
                errors.append(f"Campo desconhecido: {field_key}")
                continue
            section = _resolve_section_for_field(field_key)
            save_result = await save_field_fn(
                company_id=company_id,
                section=section,
                field=field_key,
                value=value,
                user_id=user_id,
            )
            if save_result.get("success"):
                persisted[field_key] = value
                record_field_extracted(  # P2-2 Sprint C telemetry
                    field_key=field_key,
                    confidence=1.0,
                )
            else:
                errors.append(
                    save_result.get("message") or f"Falha ao salvar {field_key}"
                )

        if errors:
            # Partial failure -- fail high
            summary = "; ".join(errors[:3])
            return RunnerResponse(
                user_message=f"Salvei alguns mas tive problemas: {summary}",
                status=new_status,
                is_complete=False,
                progress_percent=_progress(new_status),
            )

        # Sucesso total -> proxima acao (next question OR finalize)
        new_status, next_action = handle_persist_success(new_status, persisted)
        is_complete = next_action.action_type == ActionType.FINALIZE
        if is_complete:
            record_chat_completed()  # P2-2 Sprint C telemetry
        return RunnerResponse(
            user_message=next_action.message,
            status=new_status,
            is_complete=is_complete,
            progress_percent=_progress(new_status),
        )

    # SEND_MESSAGE, TRANSITION_BLOCK, FINALIZE, CONFIRM_EXTRACTION -- so retorna o message
    is_complete = action.action_type == ActionType.FINALIZE
    if is_complete:
        record_chat_completed()  # P2-2 Sprint C telemetry
    return RunnerResponse(
        user_message=action.message,
        status=new_status,
        is_complete=is_complete,
        progress_percent=_progress(new_status),
    )

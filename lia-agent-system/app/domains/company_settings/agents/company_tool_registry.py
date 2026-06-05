"""
Company Settings Tool Registry - Tools for company profile configuration via conversation.

Provides tools for reading/writing company data, analyzing websites (Apify),
processing uploaded documents with anonymization, and workforce planning.
"""
import json
import logging
from datetime import datetime
from typing import Any

from lia_agents_core.tool_adapter import ToolDefinition
from lia_agents_core.tool_adapter import ToolOutput
from sqlalchemy import text

from app.core.database import AsyncSessionLocal
from app.domains.company_settings.tools.import_tools import (
    save_hiring_policy as _save_hiring_policy_handler,
)
from app.shared.compliance.audit_decorators import audit_company_change
from app.shared.compliance.fairness_guard import FairnessGuard
from app.shared.compliance.fairness_recursive import (
    RecursiveFairnessResult,
    check_payload_limits,
    validate_fairness_recursive,
)
from app.shared.tool_handler import tool_handler
from app.domains.company_settings.repositories.company_profile_repository import CompanyProfileRepository
from app.domains.workforce.services.headcount_import_service import import_planned_headcounts
from types import SimpleNamespace

from app.domains.cv_screening.services.confidence_policy_service import (
    ConfidenceAction,
    confidence_policy_service,
)

# WT-2022 Fase 4: tools dedicadas (toggle learning loop, lia_field, DSR action)
from app.domains.company_settings.agents.company_settings_tools_extended import (
    _wrap_toggle_learning_loop,
    _wrap_toggle_lia_field,
    _wrap_record_dsr_action,
    VALID_LEARNING_LOOPS,
    # Fase 4 Extended — 5 tools high-impact
    _wrap_toggle_communication_alert,
    _wrap_update_email_signature,
    _wrap_configure_pipeline_stage,
    _wrap_configure_screening_questions,
    _wrap_set_communication_schedule,
    VALID_ALERT_IDS,
    VALID_ALERT_CHANNELS,
    VALID_PIPELINE_ACTIONS,
    VALID_SCREENING_ACTIONS,
)

logger = logging.getLogger(__name__)

_fairness_guard = FairnessGuard()


# ────────────────────────────────────────────────────────────────────────────
# A1 (PR5 / Task #1005) — SQL parametrizado: queries pré-compostas em tempo
# de import, indexadas por nome de campo (whitelist). Elimina f-string
# em runtime path; reduz a superfície de SQLi se um futuro PR aceitar
# `field` arbitrário (defesa em profundidade complementar à whitelist).
# ────────────────────────────────────────────────────────────────────────────

_PROFILE_FIELDS: frozenset[str] = frozenset({
    "name", "trading_name", "cnpj", "website", "hr_email", "hr_phone",
    "address", "industry", "company_size", "employee_count", "founded_year",
    "linkedin_url", "logo_url",
})

_CULTURE_FIELDS: frozenset[str] = frozenset({
    "mission", "vision", "values", "core_competencies", "evp_bullets",
    "work_model", "hybrid_days_onsite", "employment_types",
    "growth_opportunities", "team_dynamics", "leadership_style",
    "dei_initiatives", "sustainability", "social_impact",
    "tech_stack", "engineering_culture", "default_languages",
    "seniority_levels", "default_behavioral_competencies",
    "default_salary_ranges", "locations", "headquarters",
})

# A5 (PR7 / Task #1007) — campos do hub Minha Empresa > "Remuneração &
# Onboarding" que vivem em `company_profiles.additional_data` (JSONB), e
# NÃO em colunas top-level. Antes do PR7 caíam silenciosamente no caso
# `else` de `_save_company_field_impl` ("Campo '<x>' nao e valido para
# perfil") — gap A5 do audit T1-T6: o frontend expõe `additional_notes`,
# `responsible_name`, `responsible_position` na UI mas NÃO havia rota de
# save via chat. `compensation_structure` é DERIVADO de
# `default_salary_ranges` (ver use-company-settings-cards.ts:246) e
# portanto NÃO precisa de save próprio — é read-only no card.
_PROFILE_ADDITIONAL_DATA_FIELDS: frozenset[str] = frozenset({
    "additional_notes", "responsible_name", "responsible_position",
    # Sprint 1 BE-2 (2026-05-27) — workforce planning context fields from
    # onboarding_questions.yaml block "workforce". Stored as additional_data
    # JSONB until a dedicated column exists.
    "hiring_volume", "job_types", "main_priority", "main_challenges",
})


def _build_profile_queries() -> dict[str, tuple[str, str, str]]:
    out: dict[str, tuple[str, str, str]] = {}
    for f in _PROFILE_FIELDS:
        select_q = (
            f"SELECT id, {f} AS prev FROM company_profiles "
            "WHERE id::text = :company_id LIMIT 1"
        )
        update_q = (
            f"UPDATE company_profiles SET {f} = :value, updated_at = NOW() "
            "WHERE id::text = :company_id"
        )
        insert_q = (
            f"INSERT INTO company_profiles (id, {f}, created_at, updated_at) "
            "VALUES (:company_id::uuid, :value, NOW(), NOW())"
        )
        out[f] = (select_q, update_q, insert_q)
    return out


def _build_culture_queries() -> dict[str, tuple[str, str, str]]:
    out: dict[str, tuple[str, str, str]] = {}
    for f in _CULTURE_FIELDS:
        select_q = (
            f"SELECT id, {f} AS prev FROM company_culture_profiles "
            "WHERE company_id = :company_id LIMIT 1"
        )
        update_q = (
            f"UPDATE company_culture_profiles SET {f} = :value, updated_at = NOW() "
            "WHERE company_id = :company_id"
        )
        insert_q = (
            "INSERT INTO company_culture_profiles "
            f"(company_id, {f}, created_at, updated_at) "
            "VALUES (:company_id, :value, NOW(), NOW())"
        )
        out[f] = (select_q, update_q, insert_q)
    return out


def _build_profile_additional_data_queries() -> dict[str, tuple[str, str, str]]:
    """A5 (PR7 / Task #1007) — JSONB-merge queries para campos de
    `company_profiles.additional_data`. Mesma forma trio
    (select/update/insert) que `_build_profile_queries`, mas operando
    com `jsonb_set` parametrizado por chave (whitelist em
    `_PROFILE_ADDITIONAL_DATA_FIELDS`). Padrão idêntico ao
    `_wrap_import_workforce_plan` (que escreve em
    `company_culture_profiles.additional_data->workforce_plan`).

    O `select_q` retorna `additional_data->>field` AS prev (texto), o que
    casa com `_save_company_field_impl` que serializa qualquer
    list/dict para JSON antes de gravar — `before_value` continua sendo
    string JSON ou texto cru, consistente com colunas top-level.
    """
    out: dict[str, tuple[str, str, str]] = {}
    for f in _PROFILE_ADDITIONAL_DATA_FIELDS:
        # Path JSONB literal — `f` está hard-whitelisted no frozenset acima
        # (mesma defesa em profundidade do A1). Aspas duplas do path JSON
        # são seguras pois `f` casa com [a-z_]+ por construção.
        path = "{" + f + "}"
        select_q = (
            "SELECT id, additional_data->>'" + f + "' AS prev "
            "FROM company_profiles WHERE id::text = :company_id LIMIT 1"
        )
        # NOTE (Task #1012): usar `CAST(:value AS text)` em vez de
        # `:value::text`. SQLAlchemy text() detecta bind params com a
        # regex `(?<![:\w]):(\w+)(?!:)` — o lookahead `(?!:)` REJEITA o
        # match quando o próximo caractere é `:`, então `:value::text`
        # NUNCA era reconhecido como bind. Com asyncpg (driver de prod),
        # a query chegava ao Postgres com o literal `:value::text` e
        # estourava `syntax error at or near ":"`. Com psycopg2 o bug
        # passava despercebido porque o driver não interpreta `:name`.
        # `CAST(... AS text)` é equivalente semântico e binda corretamente.
        # NOTE (Task #1012, parte 2): cast explícito `additional_data::jsonb`
        # dentro do COALESCE. A coluna `company_profiles.additional_data`
        # é declarada como `json` (não `jsonb`) e Postgres não unifica
        # `json` com `'{}'::jsonb` no COALESCE — falha com
        # `CannotCoerceError: COALESCE could not convert type jsonb to json`.
        # Escrita continua portátil pra envs onde a coluna já foi
        # migrada pra jsonb.
        update_q = (
            "UPDATE company_profiles "
            "SET additional_data = jsonb_set("
            "COALESCE(additional_data::jsonb, '{}'::jsonb), "
            f"'{path}', "
            "to_jsonb(CAST(:value AS text)), true), "
            "updated_at = NOW() "
            "WHERE id::text = :company_id"
        )
        insert_q = (
            "INSERT INTO company_profiles "
            "(id, additional_data, created_at, updated_at) "
            "VALUES (CAST(:company_id AS uuid), "
            "jsonb_build_object('" + f + "', to_jsonb(CAST(:value AS text))), "
            "NOW(), NOW())"
        )
        out[f] = (select_q, update_q, insert_q)
    return out


_PROFILE_FIELD_QUERIES: dict[str, tuple[str, str, str]] = _build_profile_queries()
_CULTURE_FIELD_QUERIES: dict[str, tuple[str, str, str]] = _build_culture_queries()
_PROFILE_ADDITIONAL_DATA_QUERIES: dict[str, tuple[str, str, str]] = (
    _build_profile_additional_data_queries()
)


# ────────────────────────────────────────────────────────────────────────────
# A6 (PR5 / Task #1005) — gate de ConfidencePolicy. Bloqueia auto-save
# quando o caller declara `autonomous_intent=True` mas não atinge o
# threshold APPLY_NOTIFY (>=0.70). Default fail-CLOSED para auto-save
# sem score. Chamadas HITL (sem `autonomous_intent`) passam direto.
# ────────────────────────────────────────────────────────────────────────────

def _check_confidence_gate(kwargs: dict[str, Any]) -> dict[str, Any] | None:
    """Retorna payload de bloqueio se o gate falhar, ou None se passar.

    Contrato:
      - Sem `autonomous_intent`: HITL convencional, gate desliga (None).
      - Com `autonomous_intent=True` e sem `confidence`: FAIL-CLOSED.
      - Com `autonomous_intent=True` e `confidence` numérico:
        consulta `ConfidencePolicyService.get_action_for_confidence()`.
        Libera para APPLY_SILENT/APPLY_NOTIFY; bloqueia para
        ASK_USER/ALERT_CONFLICT.
    """
    # Estrito: só ativa para `autonomous_intent is True` (boolean real).
    # Strings ("false", "0") seriam truthy e ativariam o gate por engano.
    if kwargs.get("autonomous_intent") is not True:
        return None

    confidence = kwargs.get("confidence")
    if confidence is None:
        return {
            "success": False,
            "requires_human_approval": True,
            "reason": "confidence_missing",
            "message": (
                "Save autônomo requer score de confidence. Peça confirmação "
                "ao recrutador antes de persistir."
            ),
        }
    try:
        conf_value = float(confidence)
    except (TypeError, ValueError):
        return {
            "success": False,
            "requires_human_approval": True,
            "reason": "confidence_invalid",
            "message": (
                f"Confidence inválido ({confidence!r}). Peça confirmação ao "
                "recrutador antes de persistir."
            ),
        }

    action = confidence_policy_service.get_action_for_confidence(conf_value)
    if action in (ConfidenceAction.APPLY_SILENT, ConfidenceAction.APPLY_NOTIFY):
        return None

    return {
        "success": False,
        "requires_human_approval": True,
        "reason": "low_confidence",
        "confidence": conf_value,
        "action": action.value,
        "message": (
            f"Confidence {conf_value:.2f} abaixo do threshold para auto-save "
            "(0.70). Peça confirmação humana antes de persistir."
        ),
    }


def _fairness_violation_response(
    result: RecursiveFairnessResult,
    *,
    fallback_field: str | None = None,
) -> dict[str, Any]:
    """PR3 (Task #1003) — formato canônico de resposta quando o
    FairnessGuard recursivo veta um payload. Mantém o contrato consumido
    pelo prompt YAML (rule #4 de structured_action_tags): a LIA verbaliza
    `educational_message` + oferece reformulação inclusiva."""
    field_label = result.offending_field or fallback_field or "<root>"
    signal = result.offending_signal or ""
    base_msg = (
        result.educational_message
        or "Trecho com sinal de viés detectado pelo FairnessGuard."
    )
    return {
        "success": False,
        "reason": "fairness_violation",
        "offending_field": field_label,
        "offending_signal": signal,
        "category": result.category,
        "blocked_terms": result.blocked_terms or [],
        "message": (
            f"Bloqueio de compliance em '{field_label}': {base_msg} "
            f"Trecho sinalizado: «{signal}». Quer reescrever de forma inclusiva?"
        ),
    }


@tool_handler("company_settings")
async def _wrap_get_company_profile(**kwargs: Any) -> dict[str, Any]:
    company_id = kwargs.get("company_id", "")
    async with AsyncSessionLocal() as session:
        repo = CompanyProfileRepository(db=session)
        full_profile = await repo.get_full_profile(company_id)

        benefits_result = await session.execute(
            # ADR-001-EXEMPT: company_benefits cross-table read with ORDER BY — BenefitsRepository pending W1-004-E
            # (ADR-001 Wave C-2 Agent D)
            text("""
                SELECT id, name, category, description, is_active
                FROM company_benefits
                WHERE company_id = :company_id AND is_active = true
                ORDER BY category, name
            """),
            {"company_id": company_id},
        )
        benefits_rows = benefits_result.mappings().all()

    if full_profile is None:
        profile_row = None
        culture_row = None
    else:
        # Split the combined row back into profile vs culture fields
        _profile_keys = {
            "id", "name", "trading_name", "cnpj", "website", "hr_email", "hr_phone",
            "address", "industry", "company_size", "employee_count", "founded_year",
            "linkedin_url", "logo_url", "additional_data",
        }
        _culture_keys = {
            "mission", "vision", "values", "core_competencies", "evp_bullets",
            "work_model", "hybrid_days_onsite", "employment_types", "growth_opportunities",
            "team_dynamics", "leadership_style", "dei_initiatives", "sustainability",
            "social_impact", "tech_stack", "engineering_culture", "default_languages",
            "seniority_levels", "default_behavioral_competencies", "default_salary_ranges",
            "locations", "headquarters", "lia_field_toggles", "lia_instructions", "ai_persona",
        }
        profile_row = {k: v for k, v in full_profile.items() if k in _profile_keys}
        _culture_raw = {k: v for k, v in full_profile.items() if k in _culture_keys}
        culture_row = _culture_raw if any(v is not None for v in _culture_raw.values()) else None
    if not profile_row:
        # M5 (PR8 / Task #1008 — code review #2): também substitui o
        # literal `20` mágico no branch "perfil inexistente" pelo
        # cardinal real da união de whitelists `_PROFILE_FIELDS ∪
        # _CULTURE_FIELDS`. Mantém o denominador consistente com o
        # branch principal abaixo (filled = profile_data + culture_data).
        _empty_total = len(_PROFILE_FIELDS) + len(_CULTURE_FIELDS)
        return {
            "success": True,
            "data": {
                "exists": False,
                "profile": {},
                "culture": {},
                "benefits": [],
                "completion": {
                    "filled": 0,
                    "total": _empty_total,
                    "percentage": 0,
                },
            },
            "message": "Nenhum perfil encontrado. Vamos comecar do zero!",
        }

    profile_data = dict(profile_row)
    culture_data = dict(culture_row) if culture_row else {}
    benefits_data = [dict(b) for b in benefits_rows]

    filled = sum(1 for v in profile_data.values() if v not in (None, "", [], {}))
    filled += sum(1 for v in culture_data.values() if v not in (None, "", [], {}))
    # M5 (PR8 / Task #1008) — substitui o `+ 20` mágico (audit M5) pelo
    # cardinal real da whitelist `_CULTURE_FIELDS`. Quando `culture_row`
    # é vazio, o denominador da % de completude reflete os campos
    # canônicos esperados (mesma lista que dirige _build_culture_queries
    # e o whitelist do save_company_field), não um chute fixo de 20.
    _expected_culture_count = len(_CULTURE_FIELDS)
    total = (
        len(profile_data) + len(culture_data)
        if culture_data
        else len(profile_data) + _expected_culture_count
    )

    return {
        "success": True,
        "data": {
            "exists": True,
            "profile": profile_data,
            "culture": culture_data,
            "benefits": benefits_data,
            "completion": {
                "filled": filled,
                "total": total,
                "percentage": int(filled / total * 100) if total > 0 else 0,
            },
        },
        "message": f"Perfil carregado: {filled}/{total} campos preenchidos ({int(filled/total*100) if total > 0 else 0}%).",
    }


@tool_handler("company_settings")
async def _wrap_save_company_field(**kwargs: Any) -> dict[str, Any]:
    company_id = kwargs.get("company_id", "")
    section = kwargs.get("section", "profile")
    field = kwargs.get("field", "")
    value = kwargs.get("value")
    user_id = kwargs.get("user_id")

    # A6 (PR5 / Task #1005) — gate de ConfidencePolicy. Curto-circuita
    # ANTES da audit ctx para evitar emitir intent de mutação que nunca
    # acontecerá (mantém audit trail honesto).
    gate = _check_confidence_gate(kwargs)
    if gate is not None:
        return gate

    # Task #1010 — pre-check de tamanho de payload. Rejeita payloads
    # patológicos com 4xx claro ANTES de abrir audit ctx ou tocar DB,
    # e emite warning estruturado (tool_name + tenant_id) para SRE.
    too_large = check_payload_limits(
        value, tool_name="save_company_field", tenant_id=company_id,
    )
    if too_large is not None:
        return too_large

    # PR4 (Task #1004) — audit log SOX/ISO canônico fail-CLOSED com
    # transação atômica: business writes + outcome row commitados juntos.
    async with audit_company_change(
        action="save_company_field",
        company_id=company_id,
        actor=user_id,
        target_table=(
            "company_culture_profiles" if section == "culture" else "company_profiles"
        ),
        target_id=f"{company_id}::{section}.{field}",
        metadata={"section": section, "field": field},
    ) as _audit:
        result = await _save_company_field_impl(
            session=_audit.session,
            company_id=company_id, section=section, field=field, value=value,
        )
        # Canonical SOX payload: before/after capturados pelo impl.
        _audit.set_before(result.pop("_before", None))
        _audit.set_after(result.pop("_after", None))
        _audit.set_result(result)
        return result


async def _save_company_field_impl(
    *,
    session,
    company_id: str,
    section: str,
    field: str,
    value: Any,
    skip_fairness: bool = False,
) -> dict[str, Any]:
    """PR4 (Task #1004) — usa ``session`` injetada (compartilhada com
    o wrapper de audit) e NÃO commita: o ``audit_company_change``
    commita business writes + outcome row em transação atômica.

    A1 (PR5 / Task #1005) — queries pré-compostas em
    ``_PROFILE_FIELD_QUERIES`` / ``_CULTURE_FIELD_QUERIES`` (no topo do
    módulo). Lookup por whitelist; ZERO f-string em runtime.

    ADR-001-EXEMPT: pre-composed queries at import time via _build_profile_queries()
    — field names never interpolated at runtime; equivalent security to typed repo
    method per _PROFILE_FIELDS frozenset whitelist (ADR-001 Wave C-2 Agent D)."""
    if section == "profile":
        queries = _PROFILE_FIELD_QUERIES.get(field)
        if queries is None:
            # A5 (PR7 / Task #1007) — fallback JSONB para campos do bloco
            # "Remuneração & Onboarding" (additional_notes,
            # responsible_name, responsible_position) que vivem em
            # `company_profiles.additional_data`. Antes do PR7 caíam no
            # `else` e o save morria silenciosamente — gap A5 do audit.
            queries = _PROFILE_ADDITIONAL_DATA_QUERIES.get(field)
        if queries is None:
            return {"success": False, "data": {}, "message": f"Campo '{field}' nao e valido para perfil."}
    elif section == "culture":
        queries = _CULTURE_FIELD_QUERIES.get(field)
        if queries is None:
            return {"success": False, "data": {}, "message": f"Campo '{field}' nao e valido para cultura."}
    else:
        return {"success": False, "data": {}, "message": f"Secao '{section}' nao e valida."}

    select_q, update_q, insert_q = queries

    # PR3 (Task #1003) — FairnessGuard recursivo. Cobre str/list/dict/strings
    # curtas; sem mais filtro `len > 10` (era bypass C3 do audit T1-T6).
    # Task #1010 — propaga tool_name + tenant_id para o warning estruturado
    # caso o pre-check tenha sido pulado e os limites estourem aqui.
    # Task #1011: quando chamado a partir de ``_wrap_save_company_section``,
    # a varredura recursiva já foi feita uma vez sobre o payload inteiro —
    # ``skip_fairness=True`` evita revalidar campo a campo (duplica trabalho
    # de FairnessGuard em seções grandes). Callers diretos (single-field
    # save) seguem com a varredura habilitada.
    if not skip_fairness:
        fairness = validate_fairness_recursive(
            value, guard=_fairness_guard, root_label=field or "value",
            tool_name="save_company_field", tenant_id=company_id,
        )
        if fairness.is_blocked:
            return _fairness_violation_response(fairness, fallback_field=field)

    # PR4: usa session injetada (compartilhada com audit wrapper) e
    # captura `before` (estado anterior) para o payload canônico SOX.
    serialized_value: Any = (
        json.dumps(value, ensure_ascii=False) if isinstance(value, (list, dict)) else value
    )
    before_value: Any = None
    existing = await session.execute(
        text(select_q), {"company_id": company_id},
    )
    prev_row = existing.mappings().first()
    if prev_row:
        before_value = prev_row.get("prev")
        await session.execute(
            text(update_q),
            {"value": serialized_value, "company_id": company_id},
        )
    else:
        await session.execute(
            text(insert_q),
            {"company_id": company_id, "value": serialized_value},
        )

    return {
        "success": True,
        "data": {"section": section, "field": field, "value": value, "saved": True},
        "message": f"Dado salvo: {section}.{field}",
        "_before": {"value": before_value},
        "_after": {"value": value},
    }


@tool_handler("company_settings")
async def _wrap_save_company_section(**kwargs: Any) -> dict[str, Any]:
    company_id = kwargs.get("company_id", "")
    section = kwargs.get("section", "profile")
    data = kwargs.get("data", {})
    user_id = kwargs.get("user_id")

    # A6 (PR5 / Task #1005) — gate de ConfidencePolicy.
    gate = _check_confidence_gate(kwargs)
    if gate is not None:
        return gate

    # Task #1010 — pre-check de tamanho do dict completo da seção.
    too_large = check_payload_limits(
        data, tool_name="save_company_section", tenant_id=company_id,
    )
    if too_large is not None:
        return too_large

    # PR4 (Task #1004) — audit log SOX/ISO canônico fail-CLOSED. Granularidade
    # de lote (cada save_company_field interno emite seu próprio par
    # intent+outcome). Esta row registra a chamada agregada com lista de
    # campos como `after` (canonical SOX payload).
    async with audit_company_change(
        action="save_company_section",
        company_id=company_id,
        actor=user_id,
        target_table=(
            "company_culture_profiles" if section == "culture" else "company_profiles"
        ),
        target_id=f"{company_id}::{section}",
        metadata={
            "section": section,
            "field_count": len(data) if isinstance(data, dict) else 0,
        },
    ) as _audit:
        _audit.set_before({"section": section, "fields": sorted(list(data.keys())) if isinstance(data, dict) else []})

        if not data or not isinstance(data, dict):
            result = {"success": False, "data": {}, "message": "Dados vazios ou invalidos."}
            _audit.set_after({"fields_saved": []})
            _audit.set_result(result)
            return result

        # PR3 (Task #1003) — varre o dict inteiro recursivamente (cobre listas e
        # nested dicts em campos como dei_initiatives, default_salary_ranges,
        # seniority_levels). Substitui o filtro `len > 10` (bypass C3).
        # Task #1010 — propaga tool_name + tenant_id (defesa em profundidade).
        fairness = validate_fairness_recursive(
            data, guard=_fairness_guard, root_label=section or "data",
            tool_name="save_company_section", tenant_id=company_id,
        )
        if fairness.is_blocked:
            result = _fairness_violation_response(fairness)
            _audit.set_after({"fields_saved": [], "fairness_blocked": True})
            _audit.set_result(result)
            return result

        # PR4 (rev #3): chama o IMPL diretamente com a session compartilhada
        # do audit (NÃO o wrapper) — garante que toda a seção + outcome row
        # commitam atômicamente. Antes (chamando `_wrap_save_company_field`),
        # cada inner field abria sua própria session/audit ctx e commitava
        # independentemente, quebrando o fail-CLOSED transacional do outer.
        # M2 (PR8 / Task #1008) — fail-LOUD em falhas parciais: campos que
        # voltam `success=false` (whitelist miss, fairness block, DB error)
        # NÃO são mais descartados silenciosamente; o agente recebe a lista
        # `failed_fields` e a verbaliza ao recrutador (anti-pattern
        # canonical-fix #3 — fallback silencioso eliminado).
        saved_fields: list[str] = []
        failed_fields: list[dict[str, Any]] = []
        for field, value in data.items():
            inner = await _save_company_field_impl(
                session=_audit.session,
                company_id=company_id,
                section=section,
                field=field,
                value=value,
                # Task #1011: a varredura recursiva de FairnessGuard já
                # foi feita acima sobre o `data` inteiro (cobre str/list/
                # dict aninhados). Revalidar campo a campo aqui duplica
                # trabalho sem ganho — qualquer flag teria abortado o
                # bloco antes de chegar neste loop.
                skip_fairness=True,
            )
            inner.pop("_before", None)
            inner.pop("_after", None)
            if inner.get("success"):
                saved_fields.append(field)
            else:
                failed_fields.append({
                    "field": field,
                    "reason": inner.get("reason") or "save_failed",
                    "message": inner.get("message", ""),
                })

        all_ok = not failed_fields
        if all_ok:
            msg = f"Secao '{section}' salva com {len(saved_fields)} campos."
        else:
            msg = (
                f"Secao '{section}' salva parcialmente: "
                f"{len(saved_fields)} ok, {len(failed_fields)} falharam — "
                f"verifique `failed_fields` antes de confirmar ao recrutador."
            )
        result = {
            "success": all_ok,
            "data": {
                "section": section,
                "fields_saved": saved_fields,
                "failed_fields": failed_fields,
                "count": len(saved_fields),
            },
            "message": msg,
        }
        _audit.set_after({
            "fields_saved": saved_fields,
            "failed_fields": [f["field"] for f in failed_fields],
            "count": len(saved_fields),
        })
        _audit.set_result(result)
        return result


@tool_handler("company_settings")
async def _wrap_analyze_company_website(**kwargs: Any) -> dict[str, Any]:
    company_id = kwargs.get("company_id", "")
    website_url = kwargs.get("website_url", "")
    linkedin_url = kwargs.get("linkedin_url", "")

    if not website_url:
        return {"success": False, "data": {}, "message": "URL do website e obrigatoria."}

    try:
        import httpx
        # M1 (PR8 / Task #1008) — fix hardcoded loopback. Resolve from env
        # (LIA_INTERNAL_BACKEND_URL) → settings.APP_BASE_URL → loopback default
        # (preserva comportamento dev). Permite deploy em containers separados
        # sem patch de código.
        import os
        from libs.config.lia_config.config import settings as _app_settings
        backend_url = (
            os.getenv("LIA_INTERNAL_BACKEND_URL")
            or (_app_settings.APP_BASE_URL or "").rstrip("/")
            or f"http://127.0.0.1:{_app_settings.API_PORT or 8001}"
        )
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{backend_url}/api/v1/company/culture-profile/analyze-direct",
                json={
                    "website_url": website_url,
                    "linkedin_url": linkedin_url or None,
                    "company_id": company_id,
                },
            )
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "data": {
                        "extracted": result,
                        "source": "website_analysis",
                        "website_url": website_url,
                    },
                    "message": "Website analisado com sucesso! Dados extraidos para revisao.",
                }
            else:
                return {
                    "success": False,
                    "data": {},
                    "message": f"Erro ao analisar website: HTTP {response.status_code}",
                }
    except Exception as e:
        logger.error(f"[company_settings] Website analysis failed: {e}")
        return {
            "success": False,
            "data": {},
            "message": f"Erro ao analisar website: {str(e)}",
        }


@tool_handler("company_settings")
async def _wrap_process_uploaded_document(**kwargs: Any) -> dict[str, Any]:
    company_id = kwargs.get("company_id", "")
    document_text = kwargs.get("document_text", "")
    document_type = kwargs.get("document_type", "general")

    if not document_text:
        return {"success": False, "data": {}, "message": "Texto do documento esta vazio."}

    check = _fairness_guard.check(document_text)
    anonymized_text = document_text
    anonymization_applied = []

    if check.soft_warnings:
        anonymization_applied = check.soft_warnings

    extraction_hints = {
        # P1-4 fix: handbook is a "Políticas de Recrutamento" document — extract hiring policy
        # fields, NOT company culture fields (mission/vision/values).
        "handbook": [
            "min_interviews_before_offer",
            "manager_approval_for_offer",
            "max_days_in_stage",
            "allowed_days",
            "allowed_hours",
            "default_duration_minutes",
            "self_scheduling_enabled",
            "auto_rejection_feedback",
            "rejection_feedback_deadline_hours",
            "preferred_channel",
            "lia_tone",
            "salary_expectation_filter",
            "salary_tolerance_percent",
            "experience_policy",
            "auto_screening",
            "auto_stage_advance",
            "autonomy_level",
        ],
        "org_chart": ["departments", "hierarchy", "headcount"],
        "compensation": ["seniority_levels", "salary_ranges", "benefits"],  # P0-W2-10 (2026-05-24): removed variable_compensation -- field not in DB
        "tech_doc": ["tech_stack", "engineering_culture", "tools"],
        "general": ["mission", "vision", "values", "tech_stack", "benefits"],
    }
    expected_fields = extraction_hints.get(document_type, extraction_hints["general"])

    return {
        "success": True,
        "data": {
            "document_type": document_type,
            "text_length": len(document_text),
            "anonymization_warnings": anonymization_applied,
            "expected_fields": expected_fields,
            "compliance_check": {
                "is_blocked": check.is_blocked,
                "category": check.category if check.is_blocked else None,
                "warnings": check.soft_warnings,
            },
        },
        "message": f"Documento processado ({len(document_text)} caracteres). Campos esperados: {', '.join(expected_fields)}.",
    }


@tool_handler("company_settings")
async def _wrap_import_workforce_plan(**kwargs: Any) -> dict[str, Any]:
    company_id = kwargs.get("company_id", "")
    plan_data = kwargs.get("plan_data", [])
    user_id = kwargs.get("user_id")

    # Task #1010 — pre-check de tamanho do plano antes de abrir audit ctx.
    too_large = check_payload_limits(
        plan_data, tool_name="import_workforce_plan", tenant_id=company_id,
    )
    if too_large is not None:
        return too_large

    async with audit_company_change(
        action="import_workforce_plan",
        company_id=company_id,
        actor=user_id,
        target_table="company_culture_profiles",
        target_id=f"{company_id}::workforce_plan",
        metadata={
            "items_count": len(plan_data) if isinstance(plan_data, list) else 0,
        },
    ) as _audit:
        result = await _import_workforce_plan_impl(
            session=_audit.session, company_id=company_id, plan_data=plan_data,
        )
        _audit.set_before(result.pop("_before", None))
        _audit.set_after(result.pop("_after", None))
        _audit.set_result(result)
        return result


async def _import_workforce_plan_impl(
    *, session, company_id: str, plan_data: Any
) -> dict[str, Any]:
    """PR4 (Task #1004) — usa ``session`` injetada e NÃO commita
    (transação atômica gerenciada pelo ``audit_company_change``)."""
    if not plan_data or not isinstance(plan_data, list):
        return {
            "success": False,
            "data": {},
            "message": "Dados do plano de contratacoes vazios. Envie uma lista com departamento, cargo, quantidade e prazo.",
        }

    # PR3 (Task #1003) — bug C3 do audit T1-T6: import_workforce_plan NUNCA
    # passava pelo FairnessGuard. Agora cada item (department/role/seniority/
    # observações) é varrido recursivamente. Cobre casos como
    # `[{"role": "estagiário branco"}]` ou `[{"seniority": "homem júnior"}]`.
    fairness = validate_fairness_recursive(
        plan_data, guard=_fairness_guard, root_label="plan_data",
        tool_name="import_workforce_plan", tenant_id=company_id,
    )
    if fairness.is_blocked:
        return _fairness_violation_response(fairness)

    total_hires = sum(item.get("quantity", 0) for item in plan_data if isinstance(item, dict))
    departments = list(set(item.get("department", "N/A") for item in plan_data if isinstance(item, dict)))

    # PR4: usa session injetada; captura `before` (plano anterior) para
    # payload canônico SOX. Migrado para repo (ADR-001 Wave C-2 Agent D).
    repo = CompanyProfileRepository(db=session)
    _wf = await repo.get_workforce_plan(company_id)
    before_plan: Any = _wf["workforce_plan"] if _wf else None

    plan_json = json.dumps(plan_data, ensure_ascii=False)
    await repo.upsert_workforce_plan(company_id, plan_json, session=session)

    # Sistema B (canonical): grava PlannedHeadcount via produtor unico
    # (headcount_import_service), que resolve department NAME -> FK. Antes este
    # loop gravava department_id=None (fragmentacao Track B / Fase 2). Sistema C
    # (JSON acima) permanece como before-state de auditoria SOX.
    wf_summary: dict[str, Any] = {}
    try:
        wf_summary = await import_planned_headcounts(
            session=session,
            company_id=company_id,
            items=plan_data,
            source="chat",
        )
    except Exception as _wf_err:
        # REGRA 4: falha alto e explicita; nao finge sucesso silenciosamente.
        logger.error(
            "[workforce] canonical headcount import failed for company %s: %s",
            company_id, _wf_err, exc_info=True,
        )
        return {
            "success": False,
            "data": {"departments": departments},
            "message": (
                "Falha ao gravar o planejamento de headcount. Os dados nao "
                "foram salvos corretamente; tente novamente."
            ),
            "_before": {"workforce_plan": before_plan},
            "_after": None,
        }

    unresolved = wf_summary.get("unresolved_departments") or []
    msg = (
        f"Plano importado: {total_hires} contratacoes planejadas em "
        f"{len(departments)} departamentos."
    )
    if unresolved:
        msg += (
            " Departamentos sem vinculo (nao cadastrados): "
            + ", ".join(unresolved)
            + ". Cadastre em Configuracoes > Departamentos para vincular."
        )
    return {
        "success": True,
        "data": {
            "total_hires": total_hires,
            "departments": departments,
            "items_count": len(plan_data),
            "headcounts_created": wf_summary.get("created", 0),
            "unresolved_departments": unresolved,
        },
        "message": msg,
        "_before": {"workforce_plan": before_plan},
        "_after": {"workforce_plan": plan_data, "total_hires": total_hires},
    }


@tool_handler("company_settings")
async def _wrap_save_hiring_policy(**kwargs: Any) -> dict[str, Any]:
    """PR2 (Task #1002) — local toolset wrapper for `save_hiring_policy`.

    The `CompanySettingsReActAgent` binds tools via `get_company_settings_tools()`
    (this file), not the global tool_registry. Without this wrapper the YAML
    mapping `policy → save_hiring_policy` would resolve to `tool_not_found`
    in the company_settings chat flow — re-creating bug C1 (audit T1-T6) at
    the agent layer instead of the tool layer.

    Delegates to the canonical `save_hiring_policy` handler in
    `app/domains/company_settings/tools/import_tools.py`, reconstructing the
    `_context` from the `company_id`/`user_id` already extracted by the local
    toolset convention.
    """
    company_id = kwargs.get("company_id", "")
    user_id = kwargs.get("user_id", "")
    rules = kwargs.get("rules", {})

    # A6 (PR5 / Task #1005) — gate de ConfidencePolicy. Curto-circuita
    # antes de delegar ao handler canônico (que abre audit ctx).
    gate = _check_confidence_gate(kwargs)
    if gate is not None:
        return gate

    ctx = SimpleNamespace(company_id=company_id, user_id=user_id)
    return await _save_hiring_policy_handler(rules=rules, _context=ctx)


@tool_handler("company_settings")
async def _wrap_get_company_completion(**kwargs: Any) -> dict[str, Any]:
    company_id = kwargs.get("company_id", "")
    result = await _wrap_get_company_profile(company_id=company_id)
    if not result["success"]:
        return result

    data = result["data"]
    completion = data.get("completion", {})

    sections_status = {
        "institutional": {"label": "Dados Institucionais", "filled": 0, "total": 8},
        "culture": {"label": "Cultura & EVP", "filled": 0, "total": 13},
        "tech_stack": {"label": "Tech Stack", "filled": 0, "total": 3},
        "benefits": {"label": "Beneficios", "filled": 0, "total": 1},
        "seniority": {"label": "Niveis & Remuneracao", "filled": 0, "total": 3},
        "workforce": {"label": "Planejamento", "filled": 0, "total": 1},
    }

    profile = data.get("profile", {})
    inst_fields = ["name", "cnpj", "website", "hr_email", "hr_phone", "industry", "company_size", "employee_count"]
    sections_status["institutional"]["filled"] = sum(1 for f in inst_fields if profile.get(f))

    culture = data.get("culture", {})
    # P1-10 (auditoria Configuracoes): incluir os 3 campos preenchiveis na UI de
    # Cultura que nao eram contados (usuario preenchia e o % de completude nao subia).
    culture_fields = ["mission", "vision", "values", "core_competencies", "evp_bullets",
                      "work_model", "employment_types", "team_dynamics", "leadership_style", "dei_initiatives",
                      "sustainability", "social_impact", "growth_opportunities"]
    sections_status["culture"]["filled"] = sum(1 for f in culture_fields if culture.get(f))

    tech_fields = ["tech_stack", "engineering_culture", "default_languages"]
    sections_status["tech_stack"]["filled"] = sum(1 for f in tech_fields if culture.get(f))

    benefits = data.get("benefits", [])
    sections_status["benefits"]["filled"] = 1 if benefits else 0

    sen_fields = ["seniority_levels", "default_behavioral_competencies", "default_salary_ranges"]
    sections_status["seniority"]["filled"] = sum(1 for f in sen_fields if culture.get(f))

    pending = [s["label"] for s in sections_status.values() if s["filled"] < s["total"]]

    return {
        "success": True,
        "data": {
            "overall": completion,
            "sections": sections_status,
            "pending_sections": pending,
        },
        "message": f"Completude: {completion.get('percentage', 0)}%. Pendentes: {', '.join(pending) if pending else 'nenhum'}.",
    }


def get_company_settings_tools() -> list[ToolDefinition]:
    return [
        ToolDefinition(
            name="get_company_profile",
            description="Carrega todos os dados atuais da empresa: perfil, cultura, tech stack, beneficios.",
            parameters={
                "type": "object",
                "properties": {
                },
                "required": [],
            },
            output_schema=ToolOutput,
            function=_wrap_get_company_profile,
        ),
        ToolDefinition(
            name="save_company_field",
            description="Salva um campo especifico do perfil ou cultura da empresa.",
            parameters={
                "type": "object",
                "properties": {
                    "section": {"type": "string", "description": "Secao (profile ou culture)"},
                    "field": {"type": "string", "description": "Nome do campo"},
                    "value": {"description": "Valor a salvar"},
                },
                "required": ["section", "field", "value"],
            },
            output_schema=ToolOutput,
            function=_wrap_save_company_field,
        ),
        ToolDefinition(
            name="save_company_section",
            description="Salva multiplos campos de uma secao de uma vez.",
            parameters={
                "type": "object",
                "properties": {
                    "section": {"type": "string", "description": "Secao (profile ou culture)"},
                    "data": {"type": "object", "description": "Dicionario com campos e valores"},
                },
                "required": ["section", "data"],
            },
            output_schema=ToolOutput,
            function=_wrap_save_company_section,
        ),
        ToolDefinition(
            name="analyze_company_website",
            description="Analisa o website da empresa via Apify para extrair dados automaticamente (missao, cultura, tech stack, beneficios).",
            parameters={
                "type": "object",
                "properties": {
                    "website_url": {"type": "string", "description": "URL do website"},
                    "linkedin_url": {"type": "string", "description": "URL do LinkedIn (opcional)"},
                },
                "required": ["website_url"],
            },
            output_schema=ToolOutput,
            function=_wrap_analyze_company_website,
        ),
        ToolDefinition(
            name="process_uploaded_document",
            description="Processa documento enviado pelo recrutador (handbook, organograma, plano de cargos) com anonimizacao via FairnessGuard.",
            parameters={
                "type": "object",
                "properties": {
                    "document_text": {"type": "string", "description": "Texto extraido do documento"},
                    "document_type": {"type": "string", "description": "Tipo do documento (handbook, org_chart, compensation, tech_doc, general)"},
                },
                "required": ["document_text"],
            },
            output_schema=ToolOutput,
            function=_wrap_process_uploaded_document,
        ),
        ToolDefinition(
            name="import_workforce_plan",
            description="Importa planejamento de contratacoes (de planilha ou conversa). Cada item deve ter departamento, cargo, quantidade e prazo.",
            parameters={
                "type": "object",
                "properties": {
                    "plan_data": {
                        "type": "array",
                        "description": "Lista de contratacoes planejadas",
                        "items": {
                            "type": "object",
                            "properties": {
                                "department": {"type": "string"},
                                "role": {"type": "string"},
                                "quantity": {"type": "integer"},
                                "deadline": {"type": "string"},
                                "seniority": {"type": "string"},
                            },
                        },
                    },
                },
                "required": ["plan_data"],
            },
            output_schema=ToolOutput,
            function=_wrap_import_workforce_plan,
        ),
        ToolDefinition(
            name="save_hiring_policy",
            description=(
                "PR2/Task #1002 — Persiste (upsert) a política de recrutamento "
                "em company_hiring_policies. Aceita dict com blocos canônicos "
                "(pipeline_rules, scheduling_rules, communication_rules, "
                "screening_rules, automation_rules) e/ou campos atômicos "
                "(min_interviews_before_offer, manager_approval_for_offer, "
                "allowed_days, allowed_hours, auto_rejection_feedback, lia_tone, "
                "auto_screening, autonomy_level). Aplica FairnessGuard nos "
                "campos textuais. Use APÓS confirmação humana (HITL) da "
                "política sugerida por suggest_recruiting_policy — NUNCA use "
                "save_company_section/save_company_field para policy."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "rules": {
                        "type": "object",
                        "description": (
                            "Dict com blocos canônicos e/ou campos atômicos."
                        ),
                    },
                },
                "required": ["rules"],
            },
            output_schema=ToolOutput,
            function=_wrap_save_hiring_policy,
        ),
        ToolDefinition(
            name="get_company_completion",
            description="Retorna o progresso de preenchimento do perfil da empresa por secao.",
            parameters={
                "type": "object",
                "properties": {
                },
                "required": [],
            },
            output_schema=ToolOutput,
            function=_wrap_get_company_completion,
        ),
        # ─── WT-2022 Fase 4: tools dedicadas (learning loops, lia_field, DSR) ───
        ToolDefinition(
            name="toggle_learning_loop",
            description=(
                "WT-2022 Fase 4 — Liga/desliga um learning loop especifico "
                "(Big5 cultura, Big5 departamento, WSI question effectiveness, "
                "JD similar suggestion, enabled global). Use quando recrutador "
                "pedir explicitamente para ativar/desativar aprendizado automatico."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "loop_name": {
                        "type": "string",
                        "enum": sorted(VALID_LEARNING_LOOPS),
                        "description": "Nome do loop",
                    },
                    "value": {"type": "boolean", "description": "True liga, False desliga"},
                },
                "required": ["loop_name", "value"],
            },
            output_schema=ToolOutput,
            function=_wrap_toggle_learning_loop,
        ),
        ToolDefinition(
            name="toggle_lia_field",
            description=(
                "WT-2022 Fase 4 — Liga/desliga toggle de campo LIA + opcional "
                "adiciona instrucao customizada. Use quando recrutador pedir "
                "para LIA respeitar/ignorar campo (mission, vision, tech_stack, "
                "departments, beneficios, etc) ou customizar instrucao."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "field_name": {
                        "type": "string",
                        "description": "Nome do campo (mission, vision, tech_stack, departments, etc)",
                    },
                    "value": {"type": "boolean", "description": "True liga campo, False desliga"},
                    "instruction": {
                        "type": "string",
                        "description": "Opcional: instrucao customizada que LIA aplica quando consumir o campo",
                    },
                },
                "required": ["field_name", "value"],
            },
            output_schema=ToolOutput,
            function=_wrap_toggle_lia_field,
        ),
        ToolDefinition(
            name="record_dsr_action",
            description=(
                "WT-2022 Fase 4 — Workflow DSR (data subject request / LGPD) "
                "via chat: assign, verify-identity, process, complete ou reject. "
                "Use quando recrutador pedir para marcar DSR como concluido/rejeitado "
                "ou iniciar processamento."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "request_id": {"type": "string", "description": "UUID do DSR"},
                    "action": {
                        "type": "string",
                        "enum": ["assign", "verify-identity", "process", "complete", "reject"],
                    },
                    "response": {"type": "string", "description": "Required se action=complete"},
                    "rejection_reason": {"type": "string", "description": "Required se action=reject"},
                    "assignee_email": {"type": "string", "description": "Required se action=assign"},
                },
                "required": ["request_id", "action"],
            },
            output_schema=ToolOutput,
            function=_wrap_record_dsr_action,
        ),
        # ─── WT-2022 Fase 4 Extended (5 tools high-impact) ───────────────────
        ToolDefinition(
            name="toggle_communication_alert",
            description=(
                "WT-2022 Fase 4 — Liga/desliga (ou troca canal de) um alerta de "
                "comunicacao: sla_warning, interview_reminder, feedback_pending, "
                "candidate_waiting, anomaly_detected, monthly_goal_at_risk. "
                "Use quando recrutador pedir para silenciar/ativar alerta ou "
                "redirecionar canal (email/teams/whatsapp/in_app)."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "alert_id": {
                        "type": "string",
                        "enum": sorted(VALID_ALERT_IDS),
                        "description": "Identificador canonical do alerta",
                    },
                    "enabled": {
                        "type": "boolean",
                        "description": "True liga, False desliga (opcional — se omitido mantem estado)",
                    },
                    "channel": {
                        "type": "string",
                        "enum": sorted(VALID_ALERT_CHANNELS),
                        "description": "Canal de entrega (email, in_app, teams, whatsapp, both, none)",
                    },
                },
                "required": ["alert_id"],
            },
            output_schema=ToolOutput,
            function=_wrap_toggle_communication_alert,
        ),
        ToolDefinition(
            name="update_email_signature",
            description=(
                "WT-2022 Fase 4 — Atualiza assinatura de email (texto e/ou HTML) "
                "usada nas comunicacoes outbound da empresa. Use quando recrutador "
                "pedir para mudar/criar assinatura padrao."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Assinatura em texto puro (max 4000 chars)",
                    },
                    "html": {
                        "type": "string",
                        "description": "Assinatura em HTML (max 16000 chars)",
                    },
                },
                "required": [],
            },
            output_schema=ToolOutput,
            function=_wrap_update_email_signature,
        ),
        ToolDefinition(
            name="configure_pipeline_stage",
            description=(
                "WT-2022 Fase 4 — CRUD de pipeline stages (etapas do funil de "
                "recrutamento): create/update/delete/toggle_active. Use quando "
                "recrutador pedir para criar etapa nova, renomear, reordenar "
                "ou desativar etapa existente."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": sorted(VALID_PIPELINE_ACTIONS),
                        "description": "Tipo de operacao no stage",
                    },
                    "stage_data": {
                        "type": "object",
                        "description": (
                            "create: name (req), display_name (req), stage_order, color, "
                            "icon, description, stage_type, default_channel. "
                            "update/delete/toggle_active: id (UUID) obrigatorio. "
                            "toggle_active: is_active (bool) obrigatorio."
                        ),
                    },
                },
                "required": ["action", "stage_data"],
            },
            output_schema=ToolOutput,
            function=_wrap_configure_pipeline_stage,
        ),
        ToolDefinition(
            name="configure_screening_questions",
            description=(
                "WT-2022 Fase 4 — CRUD de perguntas de triagem eligibility "
                "(CompanyScreeningQuestion): add/update/remove. Use quando "
                "recrutador pedir para adicionar pergunta de triagem nova, "
                "editar texto/tipo/eliminatoria, ou remover pergunta."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": sorted(VALID_SCREENING_ACTIONS),
                    },
                    "question_data": {
                        "type": "object",
                        "description": (
                            "add: question_text (req), question_type "
                            "(text|single_choice|multiple_choice|yes_no|scale), "
                            "is_eliminatory, is_required, expected_answer, "
                            "category, options. update/remove: id (UUID) obrigatorio."
                        ),
                    },
                },
                "required": ["action", "question_data"],
            },
            output_schema=ToolOutput,
            function=_wrap_configure_screening_questions,
        ),
        ToolDefinition(
            name="set_communication_schedule",
            description=(
                "WT-2022 Fase 4 — Configura janela LGPD de envio outbound: "
                "sending_hours_start (6-12), sending_hours_end (18-22), "
                "respect_weekends, max_messages_per_day (1-50). Use quando "
                "recrutador pedir para mudar horario permitido de envio, "
                "ativar/desativar finais de semana, ou limitar mensagens/dia."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "sending_hours_start": {
                        "type": "integer",
                        "minimum": 6,
                        "maximum": 12,
                        "description": "Hora inicio envio (6-12)",
                    },
                    "sending_hours_end": {
                        "type": "integer",
                        "minimum": 18,
                        "maximum": 22,
                        "description": "Hora fim envio (18-22)",
                    },
                    "respect_weekends": {
                        "type": "boolean",
                        "description": "True nao envia em sabado/domingo",
                    },
                    "max_messages_per_day": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 50,
                        "description": "Limite diario por candidato (1-50)",
                    },
                },
                "required": [],
            },
            output_schema=ToolOutput,
            function=_wrap_set_communication_schedule,
        ),
    ]


# ─── STAGE_TOOLS canonical allowlist ──────────────────────────────────────────
# Audit 2026-05-20 P1.6 / Tema C — canonical pattern CLAUDE.md (vacancy
# preview Phase E). Maps Settings UI subsection → tools relevantes pro agente
# naquele contexto. Stage names correspondem aos blocos MinhaEmpresaHub +
# extras (learning-loops, overview). Fallback canonical: stage não declarado
# retorna TODAS as tools (preserva backward compat de chamadas sem stage).

STAGE_TOOLS: dict[str, list[str]] = {
    "basic": [
        "get_company_profile",
        "save_company_field",
        "get_company_completion",
    ],
    "culture": [
        "get_company_profile",
        "save_company_field",
        "save_company_section",
        "analyze_company_website",
        "process_uploaded_document",
        "get_company_completion",
    ],
    "tech": [
        "get_company_profile",
        "save_company_field",
        "save_company_section",
        "process_uploaded_document",
        "get_company_completion",
    ],
    "benefits": [
        "get_company_profile",
        "save_company_field",
        "save_company_section",
        "process_uploaded_document",
        "get_company_completion",
    ],
    "policy": [
        "get_company_profile",
        "save_company_field",
        "save_company_section",
        "save_hiring_policy",
        "process_uploaded_document",
        "get_company_completion",
    ],
    "workforce": [
        "get_company_profile",
        "save_company_field",
        "save_company_section",
        "import_workforce_plan",
        "process_uploaded_document",
        "get_company_completion",
    ],
    "compensation": [
        "get_company_profile",
        "save_company_field",
        "save_company_section",
        "save_hiring_policy",
        "get_company_completion",
    ],
    "learning-loops": [
        "get_company_profile",
        "get_company_completion",
        "toggle_learning_loop",
    ],
    "instrucoes-lia": [
        "get_company_profile",
        "toggle_lia_field",
    ],
    "lgpd-candidatos": [
        "record_dsr_action",
    ],
    "overview": [
        "get_company_profile",
        "get_company_completion",
        "analyze_company_website",
    ],
    # ─── WT-2022 Fase 4 Extended subsections ──────────────────────────────
    "comunicacao-alertas": [
        "get_company_profile",
        "toggle_communication_alert",
        "set_communication_schedule",
    ],
    "templates-assinatura": [
        "get_company_profile",
        "update_email_signature",
    ],
    "pipeline": [
        "get_company_profile",
        "configure_pipeline_stage",
    ],
    "screening": [
        "get_company_profile",
        "configure_screening_questions",
    ],
    # P1-W4-04: stages read-only/observability sem tools de escrita
    "studio": [],            # Agent Studio Compliance
    "ai-transparency": [],   # AI Transparency - read-only
}


def get_company_settings_tools_for_stage(stage: str) -> list[ToolDefinition]:
    """
    Return tools filtered by Settings stage (subsection canonical).

    Stage names match MinhaEmpresaHub subsections + extras:
      basic, culture, tech, benefits, policy, workforce, compensation,
      learning-loops, overview

    Fallback canonical: stage not in STAGE_TOOLS returns ALL tools
    (preserva backward compat de chamadas conversacionais sem stage).
    """
    all_tools = get_company_settings_tools()
    tool_names = STAGE_TOOLS.get(stage)
    if tool_names is None:
        return all_tools
    tool_map = {t.name: t for t in all_tools}
    return [tool_map[name] for name in tool_names if name in tool_map]

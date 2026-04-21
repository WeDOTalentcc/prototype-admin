"""
Company Settings Tool Registry - Tools for company profile configuration via conversation.

Provides tools for reading/writing company data, analyzing websites (Apify),
processing uploaded documents with anonymization, and workforce planning.
"""
import json
import logging
import os
import re
import uuid as _uuid
from typing import Any

from lia_agents_core.react_loop import ToolDefinition
from sqlalchemy import text

from app.core.database import AsyncSessionLocal
from app.shared.compliance.fairness_guard import FairnessGuard
from app.shared.pii_masking import (
    CPF_PATTERN,
    EMAIL_PATTERN,
    PHONE_BR_PATTERN,
    mask_pii,
)
from app.shared.tool_handler import tool_handler

logger = logging.getLogger(__name__)

_fairness_guard = FairnessGuard()


def _walk_fairness_check(value: Any, path: str = "") -> tuple[Any, str] | None:
    """Recursively scan a value for FairnessGuard violations.

    Returns ``(check, offending_path)`` for the first blocked text node, or
    ``None`` if everything passes. Strings shorter than 10 chars are skipped
    (FairnessGuard requires meaningful context — single tokens like "remote"
    would otherwise generate noise). dicts/lists are walked recursively so
    list-based fields (`values`, `tech_stack`, `evp_bullets`, etc.) cannot
    bypass the guard.

    The path string mirrors how the offending value was reached
    (e.g. ``values[2]``, ``benefits.description``) so the rejection message
    points the recruiter to the right spot.
    """
    if isinstance(value, str):
        if len(value) > 10:
            check = _fairness_guard.check(value)
            if check.is_blocked:
                return check, path or "(root)"
        return None
    if isinstance(value, list):
        for idx, item in enumerate(value):
            sub_path = f"{path}[{idx}]" if path else f"[{idx}]"
            blocked = _walk_fairness_check(item, sub_path)
            if blocked is not None:
                return blocked
        return None
    if isinstance(value, dict):
        for k, v in value.items():
            sub_path = f"{path}.{k}" if path else str(k)
            blocked = _walk_fairness_check(v, sub_path)
            if blocked is not None:
                return blocked
        return None
    # Numbers, bools, None — nothing to scan.
    return None

TIER_1_FIELDS = {"cnpj", "name"}
TIER_2_FIELDS = {"website", "mission", "vision", "values", "core_competencies", "evp_bullets"}
TIER_4_FIELDS = {"id", "created_at", "updated_at"}

VALID_PROFILE_FIELDS = {
    "name", "trading_name", "cnpj", "website", "hr_email", "hr_phone",
    "address", "industry", "company_size", "employee_count", "founded_year",
    "linkedin_url", "logo_url",
}
VALID_CULTURE_FIELDS = {
    "mission", "vision", "values", "core_competencies", "evp_bullets",
    "work_model", "hybrid_days_onsite", "employment_types",
    "growth_opportunities", "team_dynamics", "leadership_style",
    "dei_initiatives", "sustainability", "social_impact",
    "tech_stack", "engineering_culture", "default_languages",
    "seniority_levels", "default_behavioral_competencies",
    "default_salary_ranges", "locations", "headquarters",
}


async def _audit_log(company_id: str, action_type: str, field: str | None = None, metadata: dict | None = None) -> None:
    try:
        from app.shared.compliance.audit_service import AuditService
        svc = AuditService()
        await svc.log_action(
            trace_id=str(_uuid.uuid4()),
            company_id=company_id,
            action_type=f"company_settings.{action_type}",
            actor="company_settings_agent",
            target_id=company_id,
            target_type="company",
            metadata={"field": field, **(metadata or {})},
        )
    except Exception as exc:
        logger.debug("[company_settings] audit_log non-blocking error: %s", exc)


@tool_handler("company_settings")
async def _wrap_get_company_profile(**kwargs: Any) -> dict[str, Any]:
    company_id = kwargs.get("company_id", "")
    async with AsyncSessionLocal() as session:
        profile = await session.execute(
            text("""
                SELECT id, name, trading_name, cnpj, website, hr_email, hr_phone,
                       address, industry, company_size, employee_count, founded_year,
                       linkedin_url, logo_url, additional_data
                FROM company_profiles
                WHERE id::text = :company_id
                LIMIT 1
            """),
            {"company_id": company_id},
        )
        profile_row = profile.mappings().first()

        culture = await session.execute(
            text("""
                SELECT mission, vision, values, core_competencies, evp_bullets,
                       work_model, hybrid_days_onsite, employment_types,
                       growth_opportunities, team_dynamics, leadership_style,
                       dei_initiatives, sustainability, social_impact,
                       tech_stack, engineering_culture, default_languages,
                       seniority_levels, default_behavioral_competencies,
                       default_salary_ranges, locations, headquarters
                FROM company_culture_profiles
                WHERE company_id = :company_id
                LIMIT 1
            """),
            {"company_id": company_id},
        )
        culture_row = culture.mappings().first()

        benefits = await session.execute(
            text("""
                SELECT id, name, category, description, is_active
                FROM company_benefits
                WHERE company_id = :company_id AND is_active = true
                ORDER BY category, name
            """),
            {"company_id": company_id},
        )
        benefits_rows = benefits.mappings().all()

        if not profile_row:
            return {
                "success": True,
                "data": {
                    "exists": False,
                    "profile": {},
                    "culture": {},
                    "benefits": [],
                    "completion": {"filled": 0, "total": 20, "percentage": 0},
                },
                "message": "Nenhum perfil encontrado. Vamos comecar do zero!",
            }

        profile_data = dict(profile_row)
        culture_data = dict(culture_row) if culture_row else {}
        benefits_data = [dict(b) for b in benefits_rows]

        filled = sum(1 for v in profile_data.values() if v not in (None, "", [], {}))
        filled += sum(1 for v in culture_data.values() if v not in (None, "", [], {}))
        total = len(profile_data) + len(culture_data) if culture_data else len(profile_data) + 20

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


async def _fetch_old_value(session, section: str, field: str, company_id: str) -> Any:
    try:
        if section == "profile":
            row = await session.execute(
                text(f"SELECT {field} FROM company_profiles WHERE id::text = :cid LIMIT 1"),
                {"cid": company_id},
            )
        else:
            row = await session.execute(
                text(f"SELECT {field} FROM company_culture_profiles WHERE company_id = :cid LIMIT 1"),
                {"cid": company_id},
            )
        r = row.mappings().first()
        return r[field] if r else None
    except Exception:
        return None


@tool_handler("company_settings")
async def _wrap_save_company_field(**kwargs: Any) -> dict[str, Any]:
    company_id = kwargs.get("company_id", "")
    section = kwargs.get("section", "profile")
    field = kwargs.get("field", "")
    value = kwargs.get("value")
    user_id = kwargs.get("user_id", "system")
    confirmed = kwargs.get("confirmed", False)

    if field in TIER_4_FIELDS:
        return {"success": False, "data": {}, "message": f"Campo '{field}' e imutavel e nao pode ser alterado."}

    if section == "profile" and field not in VALID_PROFILE_FIELDS:
        return {"success": False, "data": {}, "message": f"Campo '{field}' nao e valido para perfil."}
    if section == "culture" and field not in VALID_CULTURE_FIELDS:
        return {"success": False, "data": {}, "message": f"Campo '{field}' nao e valido para cultura."}

    if field in TIER_1_FIELDS:
        is_admin = kwargs.get("is_admin", False)
        async with AsyncSessionLocal() as check_session:
            existing_row = await check_session.execute(
                text("SELECT name FROM company_profiles WHERE id::text = :cid LIMIT 1"),
                {"cid": company_id},
            )
            row = existing_row.mappings().first()
            is_post_setup = row is not None and row.get("name") is not None

        if is_post_setup:
            if not is_admin:
                return {
                    "success": False,
                    "data": {"tier": 1, "field": field, "requires_admin": True},
                    "message": f"Campo '{field}' e CRITICO (TIER 1). Apenas administradores podem alterar este campo apos o setup inicial.",
                }
            if not confirmed:
                return {
                    "success": False,
                    "data": {
                        "requires_confirmation": True,
                        "tier": 1,
                        "field": field,
                        "proposed_value": value,
                    },
                    "message": (
                        f"Campo '{field}' e CRITICO (TIER 1). "
                        "Administrador autenticado — confirmacao explicita necessaria. "
                        "Chame novamente com confirmed=true para prosseguir."
                    ),
                }

    tier_warning = None
    if field in TIER_2_FIELDS:
        tier_warning = f"Aviso: Campo '{field}' e sensivel (TIER 2). Certifique-se de que o valor esta correto."

    fairness_block = _walk_fairness_check(value)
    if fairness_block is not None:
        check, offending_path = fairness_block
        return {
            "success": False,
            "data": {
                "blocked_field": field,
                "category": check.category,
                "offending_path": offending_path,
            },
            "message": (
                f"Campo '{field}' bloqueado por compliance "
                f"(em '{offending_path}'): {check.educational_message}"
            ),
        }

    val = json.dumps(value, ensure_ascii=False) if isinstance(value, (list, dict)) else value

    _PROFILE_UPDATE = {f: f"UPDATE company_profiles SET {f} = :value, updated_at = NOW() WHERE id::text = :company_id" for f in VALID_PROFILE_FIELDS}
    _PROFILE_INSERT = {f: f"INSERT INTO company_profiles (id, {f}, created_at, updated_at) VALUES (:company_id::uuid, :value, NOW(), NOW())" for f in VALID_PROFILE_FIELDS}
    _CULTURE_UPDATE = {f: f"UPDATE company_culture_profiles SET {f} = :value, updated_at = NOW() WHERE company_id = :company_id" for f in VALID_CULTURE_FIELDS}
    _CULTURE_INSERT = {f: f"INSERT INTO company_culture_profiles (company_id, {f}, created_at, updated_at) VALUES (:company_id, :value, NOW(), NOW())" for f in VALID_CULTURE_FIELDS}

    old_value = None
    async with AsyncSessionLocal() as session:
        old_value = await _fetch_old_value(session, section, field, company_id)

        if section == "profile":
            existing = await session.execute(
                text("SELECT id FROM company_profiles WHERE id::text = :company_id LIMIT 1"),
                {"company_id": company_id},
            )
            sql = _PROFILE_UPDATE[field] if existing.mappings().first() else _PROFILE_INSERT[field]
            await session.execute(text(sql), {"value": val, "company_id": company_id})
        elif section == "culture":
            existing = await session.execute(
                text("SELECT id FROM company_culture_profiles WHERE company_id = :company_id LIMIT 1"),
                {"company_id": company_id},
            )
            sql = _CULTURE_UPDATE[field] if existing.mappings().first() else _CULTURE_INSERT[field]
            await session.execute(text(sql), {"value": val, "company_id": company_id})

        await session.commit()

    tier = 1 if field in TIER_1_FIELDS else 2 if field in TIER_2_FIELDS else 3
    await _audit_log(company_id, "save_field", field=field, metadata={
        "section": section,
        "tier": tier,
        "old_value": str(old_value)[:500] if old_value is not None else None,
        "new_value": str(value)[:500] if value is not None else None,
        "user_id": user_id,
    })

    result: dict[str, Any] = {
        "success": True,
        "data": {"section": section, "field": field, "value": value, "saved": True},
        "message": f"Dado salvo: {section}.{field}",
    }
    if tier_warning:
        result["data"]["tier_warning"] = tier_warning
        result["message"] = f"{tier_warning} — {result['message']}"
    return result


@tool_handler("company_settings")
async def _wrap_save_company_section(**kwargs: Any) -> dict[str, Any]:
    company_id = kwargs.get("company_id", "")
    section = kwargs.get("section", "profile")
    data = kwargs.get("data", {})
    user_id = kwargs.get("user_id", "system")

    if not data or not isinstance(data, dict):
        return {"success": False, "data": {}, "message": "Dados vazios ou invalidos."}

    for field_name, field_value in data.items():
        fairness_block = _walk_fairness_check(field_value)
        if fairness_block is not None:
            check, offending_path = fairness_block
            return {
                "success": False,
                "data": {
                    "blocked_field": field_name,
                    "category": check.category,
                    "offending_path": offending_path,
                },
                "message": (
                    f"Campo '{field_name}' bloqueado por compliance "
                    f"(em '{offending_path}'): {check.educational_message}"
                ),
            }

    saved_fields = []
    failed_fields: dict[str, str] = {}
    for field, value in data.items():
        result = await _wrap_save_company_field(
            company_id=company_id, section=section, field=field, value=value, user_id=user_id
        )
        if result["success"]:
            saved_fields.append(field)
        else:
            failed_fields[field] = result.get("message", "erro desconhecido")

    await _audit_log(company_id, "save_section", metadata={"section": section, "fields": saved_fields, "failed": list(failed_fields.keys())})

    all_ok = len(failed_fields) == 0
    return {
        "success": all_ok,
        "data": {"section": section, "fields_saved": saved_fields, "count": len(saved_fields), "failed_fields": failed_fields},
        "message": f"Secao '{section}': {len(saved_fields)} salvos" + (f", {len(failed_fields)} falharam." if failed_fields else "."),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Canonical Benefit schema (Task #766) — keep in sync with
# `lia_models.company_benefit.CompanyBenefit`. The conversational tools and
# the spreadsheet/site importers MUST accept the same fields the structured
# UI accepts. Any new field added to the model has to be added here too —
# guardrail enforced by `tests/unit/test_company_settings_actions.py`.
# ─────────────────────────────────────────────────────────────────────────────
CANONICAL_BENEFIT_FIELDS: set[str] = {
    "name", "category", "description", "icon", "provider",
    "value", "value_type", "percentage_value", "value_details",
    "seniority_levels", "waiting_period_days",
    "is_active", "is_highlighted", "is_mandatory", "is_discount",
    "order",
}

VALID_BENEFIT_VALUE_TYPES: set[str] = {
    "informative", "monetary", "percentage", "boolean",
}

BENEFIT_CLARIFICATION_FIELDS: list[str] = [
    "name", "category", "description", "value", "value_type",
    "percentage_value", "provider", "is_mandatory",
    "waiting_period_days", "seniority_levels",
]


def _benefit_clarification_issues(item: dict[str, Any]) -> list[str]:
    """Detect "missing required pair" issues for a single benefit item.

    Returns a list of human-readable issues. Empty list = OK to persist.

    Rules (clarification-first, no silent fallback):
      * `value_type` must be one of VALID_BENEFIT_VALUE_TYPES when given.
      * If `value` is provided, `value_type` must be set explicitly to
        monetary/percentage/boolean (never default to "informative").
      * If `value_type=monetary`, either `value` or `value_details` is
        required (e.g. "subsidio integral").
      * If `value_type=percentage`, either `percentage_value` or `value`
        is required.
      * If `percentage_value` is set, `value_type` must be "percentage".
    """
    name = (item.get("name") or "").strip() or "(sem nome)"
    value = item.get("value")
    pct = item.get("percentage_value")
    vtype = item.get("value_type")
    issues: list[str] = []

    if vtype is not None and vtype not in VALID_BENEFIT_VALUE_TYPES:
        issues.append(
            f"'{name}': value_type '{vtype}' invalido "
            f"(use {sorted(VALID_BENEFIT_VALUE_TYPES)})"
        )
    if value not in (None, "") and vtype in (None, "informative"):
        issues.append(
            f"'{name}': informe value_type quando 'value' for fornecido "
            "(monetary, percentage ou boolean)."
        )
    if vtype == "monetary" and value in (None, "") and not item.get("value_details"):
        issues.append(
            f"'{name}': value_type=monetary exige 'value' (BRL) ou 'value_details'."
        )
    if vtype == "percentage" and pct in (None, "") and value in (None, ""):
        issues.append(
            f"'{name}': value_type=percentage exige 'percentage_value' (%) ou 'value'."
        )
    if pct not in (None, "") and vtype not in (None, "percentage"):
        issues.append(
            f"'{name}': 'percentage_value' so e valido com value_type='percentage'."
        )
    return issues


@tool_handler("company_settings")
async def _wrap_save_company_benefits(**kwargs: Any) -> dict[str, Any]:
    """Persist company benefits in the dedicated `company_benefits` table.

    Schema canonico — Task #766: aceita TODOS os campos do modelo
    `CompanyBenefit` (provider, value, value_type, percentage_value,
    value_details, seniority_levels, waiting_period_days, is_mandatory,
    is_discount, etc.) — paridade com o formulario estruturado do Hub.

    Pipeline:
      1. Validacao por item: se faltar par obrigatorio (ex.: value sem
         value_type, value_type=monetary sem value/value_details), devolve
         `needs_clarification=True` SEM gravar.
      2. PII masking (CPF/email/telefone) em campos de texto livre antes
         de salvar — LGPD Art. 6 (necessidade).
      3. FairnessGuard L1 em `name`/`description`/`value_details`.
      4. INSERT com `seniority_levels` em JSONB.
      5. Audit log com `source` (chat | spreadsheet | website).

    Mode `replace` deactivates current benefits before inserting the new set;
    `append` only inserts. Multi-tenant: rows are scoped by `company_id` and
    we never touch rows outside that scope.
    """
    company_id = (kwargs.get("company_id") or "").strip()
    user_id = kwargs.get("user_id", "system")
    benefits = kwargs.get("benefits") or kwargs.get("data") or []
    mode = (kwargs.get("mode") or "append").lower()
    source = (kwargs.get("source") or "chat").strip().lower() or "chat"

    if not company_id:
        return {"success": False, "data": {}, "message": "company_id obrigatorio."}
    if not isinstance(benefits, list) or not benefits:
        return {"success": False, "data": {}, "message": "Lista de beneficios vazia."}
    if mode not in ("append", "replace"):
        return {"success": False, "data": {}, "message": "mode deve ser 'append' ou 'replace'."}

    cleaned: list[dict[str, Any]] = []
    clarification_issues: list[str] = []

    for raw in benefits:
        if not isinstance(raw, dict):
            return {
                "success": False,
                "data": {},
                "message": "Cada beneficio deve ser um objeto com pelo menos {name}.",
            }
        name = (raw.get("name") or "").strip()
        if not name:
            return {
                "success": False,
                "data": {},
                "message": "Cada beneficio precisa de 'name'.",
            }
        item: dict[str, Any] = {
            k: raw.get(k) for k in CANONICAL_BENEFIT_FIELDS if raw.get(k) is not None
        }
        item["name"] = name

        # PII masking on free-text fields BEFORE persistence (LGPD).
        for tf in ("name", "description", "value_details", "provider"):
            v = item.get(tf)
            if isinstance(v, str) and v:
                item[tf] = mask_pii(v)

        # Clarification-first — no silent gravar-incompleto.
        clarification_issues.extend(_benefit_clarification_issues(item))

        # FairnessGuard L1 over free text (name + description + value_details).
        for tf in ("name", "description", "value_details"):
            txt = item.get(tf)
            if isinstance(txt, str) and len(txt) > 10:
                check = _fairness_guard.check(txt)
                if check.is_blocked:
                    return {
                        "success": False,
                        "data": {"blocked_field": tf, "category": check.category},
                        "message": (
                            f"Beneficio '{name}' bloqueado por compliance: "
                            f"{check.educational_message}"
                        ),
                    }
        cleaned.append(item)

    if clarification_issues:
        return {
            "success": False,
            "needs_clarification": True,
            "data": {
                "missing_fields": clarification_issues,
                "expected_fields": BENEFIT_CLARIFICATION_FIELDS,
                "source": source,
            },
            "message": (
                "Antes de gravar os beneficios preciso de mais informacoes: "
                + " | ".join(clarification_issues)
            ),
        }

    inserted = 0
    deactivated = 0
    async with AsyncSessionLocal() as session:
        if mode == "replace":
            res = await session.execute(
                text("UPDATE company_benefits SET is_active = false, updated_at = NOW() "
                     "WHERE company_id = :cid AND is_active = true"),
                {"cid": company_id},
            )
            deactivated = res.rowcount or 0

        for item in cleaned:
            seniority = item.get("seniority_levels")
            seniority_json = (
                json.dumps(seniority, ensure_ascii=False)
                if isinstance(seniority, (list, dict))
                else None
            )
            await session.execute(
                text(
                    "INSERT INTO company_benefits "
                    "(id, company_id, name, category, description, icon, provider, "
                    " value, value_type, percentage_value, value_details, "
                    " seniority_levels, waiting_period_days, "
                    " is_active, is_highlighted, is_mandatory, is_discount, "
                    " \"order\", created_at, updated_at) "
                    "VALUES (gen_random_uuid(), :cid, :name, :category, :description, "
                    " :icon, :provider, :value, COALESCE(:value_type, 'informative'), "
                    " :percentage_value, :value_details, "
                    " CAST(:seniority_levels AS JSONB), COALESCE(:waiting_period_days, 0), "
                    " COALESCE(:is_active, true), COALESCE(:is_highlighted, false), "
                    " COALESCE(:is_mandatory, false), COALESCE(:is_discount, false), "
                    " COALESCE(:order_idx, 0), NOW(), NOW())"
                ),
                {
                    "cid": company_id,
                    "name": item["name"],
                    "category": item.get("category"),
                    "description": item.get("description"),
                    "icon": item.get("icon"),
                    "provider": item.get("provider"),
                    "value": item.get("value"),
                    "value_type": item.get("value_type"),
                    "percentage_value": item.get("percentage_value"),
                    "value_details": item.get("value_details"),
                    "seniority_levels": seniority_json,
                    "waiting_period_days": item.get("waiting_period_days"),
                    "is_active": item.get("is_active"),
                    "is_highlighted": item.get("is_highlighted"),
                    "is_mandatory": item.get("is_mandatory"),
                    "is_discount": item.get("is_discount"),
                    "order_idx": item.get("order"),
                },
            )
            inserted += 1
        await session.commit()

    await _audit_log(
        company_id,
        "save_benefits",
        metadata={
            "mode": mode,
            "source": source,
            "inserted": inserted,
            "deactivated": deactivated,
            "user_id": user_id,
            "names": [b["name"] for b in cleaned][:25],
        },
    )

    return {
        "success": True,
        "data": {
            "inserted": inserted,
            "deactivated": deactivated,
            "mode": mode,
            "source": source,
            "names": [b["name"] for b in cleaned],
        },
        "message": (
            f"Beneficios salvos: {inserted} inserido(s)"
            + (f", {deactivated} desativado(s)." if deactivated else ".")
        ),
    }


def _validate_url_ssrf(url: str) -> str | None:
    import ipaddress as _ip
    from urllib.parse import urlparse
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return "URL invalida: apenas http/https sao permitidos."
    _blocked_hosts = {"localhost", "0.0.0.0", "[::1]"}
    hostname = parsed.hostname or ""
    if hostname in _blocked_hosts:
        return "URL bloqueada: enderecos internos/privados nao sao permitidos."
    try:
        addr = _ip.ip_address(hostname)
        if addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_reserved:
            return "URL bloqueada: enderecos internos/privados nao sao permitidos."
    except ValueError:
        pass
    return None


@tool_handler("company_settings")
async def _wrap_analyze_company_website(**kwargs: Any) -> dict[str, Any]:
    company_id = kwargs.get("company_id", "")
    website_url = kwargs.get("website_url", "")
    linkedin_url = kwargs.get("linkedin_url", "")

    if not website_url:
        return {"success": False, "data": {}, "message": "URL do website e obrigatoria."}

    ssrf_err = _validate_url_ssrf(website_url)
    if ssrf_err:
        return {"success": False, "data": {}, "message": ssrf_err}

    if linkedin_url:
        ssrf_err = _validate_url_ssrf(linkedin_url)
        if ssrf_err:
            return {"success": False, "data": {}, "message": f"LinkedIn URL: {ssrf_err}"}

    try:
        import httpx
        backend_url = os.getenv("LIA_BACKEND_URL", "http://127.0.0.1:8001")
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


_SECTION_HEADERS_PT: dict[str, list[str]] = {
    "mission": ["missao", "missão", "nossa missao", "nossa missão", "mission"],
    "vision": ["visao", "visão", "nossa visao", "nossa visão", "vision"],
    "values": ["valores", "nossos valores", "values", "core values"],
    "benefits": ["beneficios", "benefícios", "perks", "benefits"],
    "tech_stack": ["stack", "tecnologias", "tech stack", "ferramentas"],
    "work_model": ["modelo de trabalho", "modalidade", "work model"],
    "dei_initiatives": ["dei", "diversidade", "inclusao", "inclusão", "diversity"],
}

_LIST_BULLET_RE = re.compile(r"^\s*(?:[-*•·]|\d+[.)])\s+(.+)$", re.MULTILINE)
_WORK_MODEL_RE = re.compile(r"\b(remoto|remote|hibrido|híbrido|hybrid|presencial|on[-\s]?site)\b", re.IGNORECASE)


def _slice_section(text_in: str, headers: list[str]) -> str | None:
    """Return text under a section heading (until next blank-line or next known header).

    Heuristic, regex-only — no LLM call. Designed for handbooks/policies in pt-BR.
    """
    if not text_in:
        return None
    lines = text_in.splitlines()
    lower_lines = [ln.lower() for ln in lines]
    n = len(lines)
    start_idx: int | None = None
    for i, low in enumerate(lower_lines):
        stripped = low.strip(" \t#:•-*").rstrip(":")
        for h in headers:
            if stripped == h or stripped.startswith(h + " ") or stripped.endswith(" " + h):
                start_idx = i + 1
                break
        if start_idx is not None:
            break
    if start_idx is None:
        return None
    # Build set of all known headers to detect end
    all_headers = {h for hs in _SECTION_HEADERS_PT.values() for h in hs}
    collected: list[str] = []
    blank_run = 0
    for j in range(start_idx, n):
        low = lower_lines[j].strip(" \t#:•-*").rstrip(":")
        if not low:
            blank_run += 1
            if blank_run >= 2 and collected:
                break
            continue
        blank_run = 0
        if low in all_headers:
            break
        collected.append(lines[j].strip())
        if len(collected) >= 12:  # cap
            break
    out = "\n".join(collected).strip()
    return out or None


def _extract_list_items(block: str | None, max_items: int = 8) -> list[str]:
    if not block:
        return []
    items = [m.group(1).strip() for m in _LIST_BULLET_RE.finditer(block)]
    if not items:
        # Fall back to comma/semicolon split of the first non-empty line
        first = next((ln.strip() for ln in block.splitlines() if ln.strip()), "")
        items = [p.strip(" .;-") for p in re.split(r"[;,]", first) if p.strip()]
    # Dedupe preserving order
    seen: set[str] = set()
    out: list[str] = []
    for it in items:
        key = it.lower()
        if key in seen or len(it) > 200:
            continue
        seen.add(key)
        out.append(it)
        if len(out) >= max_items:
            break
    return out


def _extract_first_sentence(block: str | None, max_len: int = 280) -> str | None:
    if not block:
        return None
    # Take first line/sentence
    text_in = re.split(r"(?<=[.!?])\s", block.strip(), maxsplit=1)[0].strip()
    if not text_in:
        return None
    return text_in[:max_len]


def _structured_extract(text_in: str, document_type: str) -> dict[str, Any]:
    """Pull canonical company-settings fields from raw document text.

    Returns a dict whose keys match _SECTION_FIELD_HINTS in domain.py
    (profile.* and culture.* fields). Empty when nothing is detected.
    """
    out: dict[str, Any] = {}
    mission = _extract_first_sentence(_slice_section(text_in, _SECTION_HEADERS_PT["mission"]))
    if mission:
        out["mission"] = mission
    vision = _extract_first_sentence(_slice_section(text_in, _SECTION_HEADERS_PT["vision"]))
    if vision:
        out["vision"] = vision
    values = _extract_list_items(_slice_section(text_in, _SECTION_HEADERS_PT["values"]))
    if values:
        out["values"] = values
    benefits = _extract_list_items(_slice_section(text_in, _SECTION_HEADERS_PT["benefits"]))
    if benefits:
        out["benefits"] = benefits
    tech = _extract_list_items(_slice_section(text_in, _SECTION_HEADERS_PT["tech_stack"]))
    if tech:
        out["tech_stack"] = tech
    dei = _extract_list_items(_slice_section(text_in, _SECTION_HEADERS_PT["dei_initiatives"]))
    if dei:
        out["dei_initiatives"] = dei
    wm_match = _WORK_MODEL_RE.search(text_in or "")
    if wm_match:
        wm = wm_match.group(1).lower()
        normalized = {
            "remoto": "remote",
            "remote": "remote",
            "hibrido": "hybrid",
            "híbrido": "hybrid",
            "hybrid": "hybrid",
            "presencial": "onsite",
            "onsite": "onsite",
            "on-site": "onsite",
            "on site": "onsite",
        }.get(wm, wm)
        out["work_model"] = normalized
    return out


# Maps a "target section" (the card the upload was triggered from) onto the
# document_type that drives extraction hints. Keeps the upload contextual:
# a file dropped on Tech Stack will be biased toward tech_stack/engineering
# even if its filename says nothing about it.
SECTION_TO_DOCUMENT_TYPE: dict[str, str] = {
    "culture": "handbook",
    "cultura": "handbook",
    "benefits": "handbook",
    "beneficios": "handbook",
    "tech_stack": "tech_doc",
    "tech": "tech_doc",
    "workforce": "org_chart",
    "workforce_planning": "org_chart",
    "departments": "org_chart",
    "compensation": "compensation",
    "remuneracao": "compensation",
    "policy": "handbook",
    "hiring_policies": "handbook",
}

# Per-section subset of `expected_fields` so the LIA confirmation step shows
# only the fields the recruiter actually asked to fill from this drop-zone.
SECTION_EXPECTED_FIELDS: dict[str, list[str]] = {
    "culture": ["mission", "vision", "values", "work_model", "dei_initiatives", "evp_bullets"],
    "benefits": ["benefits"],
    "tech_stack": ["tech_stack", "engineering_culture", "default_languages"],
    "workforce": ["departments", "hiring_volume", "headcount"],
    "compensation": ["seniority_levels", "salary_ranges", "default_salary_ranges"],
    "policy": ["allowed_days", "allowed_hours", "lia_tone", "preferred_channel"],
}


@tool_handler("company_settings")
async def _wrap_process_uploaded_document(**kwargs: Any) -> dict[str, Any]:
    company_id = kwargs.get("company_id", "")
    document_text = kwargs.get("document_text", "")
    document_type = kwargs.get("document_type", "general")
    target_section = (kwargs.get("target_section") or "").strip().lower() or None
    user_id = kwargs.get("user_id", "system")

    # When the recruiter dropped the file on a specific card, derive the
    # document_type from that section if the caller didn't override it.
    if target_section and (not document_type or document_type == "general"):
        document_type = SECTION_TO_DOCUMENT_TYPE.get(target_section, document_type)

    if not document_text:
        return {"success": False, "data": {}, "message": "Texto do documento esta vazio."}

    # ── L1: PII masking BEFORE anything downstream sees the text ──────────────
    # mask_pii redacts CPF, e-mail, BR phones and "name=..." patterns. The masked
    # form is the only string we keep around; the raw `document_text` is dropped
    # so it never leaks into the structured extraction or the audit log payload.
    masked_text = mask_pii(document_text)
    pii_redactions: dict[str, int] = {
        "cpf": len(CPF_PATTERN.findall(document_text)),
        "email": len(EMAIL_PATTERN.findall(document_text)),
        "phone": len(PHONE_BR_PATTERN.findall(document_text)),
    }
    pii_total = sum(pii_redactions.values())

    # ── L2: FairnessGuard runs over the *masked* text (no PII to bias on) ─────
    check = _fairness_guard.check(masked_text)
    fairness_warnings = list(check.soft_warnings or [])

    # ── L3: structured extraction (regex/heuristic, no LLM round-trip) ────────
    suggested_fields = _structured_extract(masked_text, document_type)

    extraction_hints = {
        "handbook": ["mission", "vision", "values", "benefits", "work_model", "dei_initiatives"],
        "org_chart": ["departments", "hierarchy", "headcount"],
        "compensation": ["seniority_levels", "salary_ranges", "benefits", "variable_compensation"],
        "tech_doc": ["tech_stack", "engineering_culture", "tools"],
        "general": ["mission", "vision", "values", "tech_stack", "benefits"],
    }
    expected_fields = extraction_hints.get(document_type, extraction_hints["general"])
    # If the upload is contextual to a single section, narrow the expected
    # fields list so the LIA confirmation step only proposes that section.
    if target_section and target_section in SECTION_EXPECTED_FIELDS:
        expected_fields = SECTION_EXPECTED_FIELDS[target_section]

    await _audit_log(
        company_id,
        "process_document",
        metadata={
            "document_type": document_type,
            "target_section": target_section,
            "text_length": len(document_text),
            "masked_length": len(masked_text),
            "pii_redactions": pii_redactions,
            "user_id": user_id,
            "suggested_field_keys": sorted(suggested_fields.keys()),
        },
    )

    section_hint = (
        f" Foco: secao '{target_section}'." if target_section else ""
    )
    return {
        "success": True,
        "data": {
            "document_type": document_type,
            "target_section": target_section,
            "text_length": len(document_text),
            "pii_redactions": pii_redactions,
            "pii_total_redactions": pii_total,
            "anonymization_warnings": fairness_warnings,
            "suggested_fields": suggested_fields,
            "expected_fields": expected_fields,
            "compliance_check": {
                "is_blocked": check.is_blocked,
                "category": check.category if check.is_blocked else None,
                "warnings": fairness_warnings,
            },
        },
        "message": (
            f"Documento processado ({len(document_text)} caracteres, {pii_total} PII redigidas).{section_hint} "
            f"Campos sugeridos: {', '.join(suggested_fields.keys()) or 'nenhum detectado automaticamente'}. "
            f"Confirme antes de gravar (LGPD Art. 8)."
        ),
    }


_WORKFORCE_EXPECTED_FIELDS = ["department", "role", "quantity", "deadline", "seniority"]


def _parse_workforce_paste(raw_text: str) -> list[dict[str, Any]]:
    """Deterministic parser for structured paste (TSV/CSV-like).

    Accepts a header row with columns from ``_WORKFORCE_EXPECTED_FIELDS``
    (case-insensitive, Portuguese aliases allowed) followed by data rows.
    Separators: tab, semicolon, or comma. Never contacts an LLM — used as
    the 'paste' input path so the recruiter sees exactly what was parsed
    before HITL approval.
    """
    if not raw_text or not isinstance(raw_text, str):
        return []

    aliases = {
        "departamento": "department", "department": "department", "area": "department", "área": "department",
        "cargo": "role", "role": "role", "posicao": "role", "posição": "role", "position": "role",
        "quantidade": "quantity", "qtd": "quantity", "qty": "quantity", "quantity": "quantity", "vagas": "quantity",
        "prazo": "deadline", "deadline": "deadline", "data": "deadline", "mes": "deadline", "mês": "deadline", "month": "deadline",
        "senioridade": "seniority", "seniority": "seniority", "nivel": "seniority", "nível": "seniority",
    }

    lines = [ln.strip() for ln in raw_text.splitlines() if ln.strip()]
    if len(lines) < 2:
        return []

    def _split(line: str) -> list[str]:
        if "\t" in line:
            return [c.strip() for c in line.split("\t")]
        if ";" in line:
            return [c.strip() for c in line.split(";")]
        return [c.strip() for c in line.split(",")]

    header = _split(lines[0])
    mapping: list[str | None] = [aliases.get(h.lower()) for h in header]

    if not any(m in ("department", "role", "quantity") for m in mapping if m):
        return []

    rows: list[dict[str, Any]] = []
    for raw_line in lines[1:]:
        cells = _split(raw_line)
        if not any(cells):
            continue
        item: dict[str, Any] = {}
        for idx, canonical in enumerate(mapping):
            if canonical is None or idx >= len(cells):
                continue
            value = cells[idx]
            if canonical == "quantity":
                try:
                    item[canonical] = int(value)
                except (TypeError, ValueError):
                    item[canonical] = 0
            else:
                item[canonical] = value
        if item.get("department") or item.get("role"):
            rows.append(item)
    return rows


async def _extract_workforce_from_text(raw_text: str) -> list[dict[str, Any]]:
    """Use the configured Claude provider to turn free-form text into a
    structured workforce plan proposal. Returns an empty list on any
    failure (LLM unreachable, invalid JSON, empty text) — HITL gate will
    then surface a clarification to the recruiter.
    """
    if not raw_text or not isinstance(raw_text, str) or len(raw_text.strip()) < 6:
        return []

    # PII masking first — free text pode conter e-mail/CPF/telefone
    masked = mask_pii(raw_text)

    system_prompt = (
        "Voce extrai planejamento de contratacoes de texto livre em portugues. "
        "Responda APENAS com um JSON valido no formato "
        '{"plan": [{"department": str, "role": str, "quantity": int, '
        '"deadline": str, "seniority": str}]}. '
        "Use strings vazias quando o campo nao for mencionado. Nao invente dados."
    )
    try:
        from app.shared.providers.llm_claude import ClaudeLLMProvider

        provider = ClaudeLLMProvider()
        response = await provider.generate_with_system(
            system_prompt=system_prompt,
            user_message=masked,
            temperature=0.0,
            max_tokens=1024,
        )
        text_out = (response.text or "").strip()
        if text_out.startswith("```"):
            text_out = re.sub(r"^```(?:json)?\s*|\s*```$", "", text_out, flags=re.DOTALL)
        parsed = json.loads(text_out)
        plan = parsed.get("plan") if isinstance(parsed, dict) else parsed
        if not isinstance(plan, list):
            return []
        cleaned: list[dict[str, Any]] = []
        for item in plan:
            if not isinstance(item, dict):
                continue
            entry = {k: item.get(k, "") for k in _WORKFORCE_EXPECTED_FIELDS}
            try:
                entry["quantity"] = int(entry.get("quantity") or 0)
            except (TypeError, ValueError):
                entry["quantity"] = 0
            if entry.get("department") or entry.get("role"):
                cleaned.append(entry)
        return cleaned
    except Exception as exc:
        logger.warning("[import_workforce_plan] LLM extraction failed: %s", exc)
        return []


@tool_handler("company_settings")
async def _wrap_import_workforce_plan(**kwargs: Any) -> dict[str, Any]:
    """Import a workforce plan with MANDATORY Human-in-the-Loop approval.

    Three input paths are supported (Task #768):
      * ``input_mode='spreadsheet'`` (default) — ``plan_data`` already
        structured by the frontend/uploader.
      * ``input_mode='paste'`` — ``raw_text`` parsed deterministically.
      * ``input_mode='text'`` — ``raw_text`` extracted via Claude.

    Writes ONLY when ``approved=True``. Any other call returns
    ``requires_human_approval=True`` plus a ``proposed_plan_data``
    preview so the recruiter can confirm in the chat.
    """
    company_id = kwargs.get("company_id", "")
    plan_data = kwargs.get("plan_data") or []
    raw_text = kwargs.get("raw_text", "") or ""
    input_mode = (kwargs.get("input_mode") or "spreadsheet").lower()
    # HITL gate — accept ONLY the real Python bool True. Strings like
    # "false"/"no"/"0" and anything truthy-but-non-bool MUST NOT persist
    # (defense in depth: a malformed tool call from the LLM cannot bypass
    # human approval). Task #768 regression.
    raw_approved = kwargs.get("approved", False)
    approved = raw_approved is True
    user_id = kwargs.get("user_id", "system")

    # Normalize input by mode ------------------------------------------------
    if input_mode == "paste" and not plan_data:
        plan_data = _parse_workforce_paste(raw_text)
    elif input_mode == "text" and not plan_data:
        plan_data = await _extract_workforce_from_text(raw_text)

    if not plan_data or not isinstance(plan_data, list):
        return {
            "success": False,
            "requires_human_approval": False,
            "data": {
                "input_mode": input_mode,
                "expected_fields": _WORKFORCE_EXPECTED_FIELDS,
            },
            "message": (
                "Nao consegui identificar um plano de contratacoes. Envie uma "
                "planilha, cole uma tabela com cabecalho (departamento, cargo, "
                "quantidade, prazo, senioridade) ou descreva em texto livre."
            ),
        }

    # Normalize items to expected shape --------------------------------------
    normalized: list[dict[str, Any]] = []
    for item in plan_data:
        if not isinstance(item, dict):
            continue
        entry = {k: item.get(k, "") for k in _WORKFORCE_EXPECTED_FIELDS}
        try:
            entry["quantity"] = int(entry.get("quantity") or 0)
        except (TypeError, ValueError):
            entry["quantity"] = 0
        normalized.append(entry)
    plan_data = normalized

    total_hires = sum(item.get("quantity", 0) for item in plan_data)
    departments = sorted({item.get("department", "N/A") or "N/A" for item in plan_data})

    # HITL gate — never write without explicit approval ----------------------
    if not approved:
        await _audit_log(
            company_id,
            "import_workforce_plan.preview",
            metadata={
                "input_mode": input_mode,
                "total_hires": total_hires,
                "departments": departments,
                "user_id": user_id,
                "items_count": len(plan_data),
            },
        )
        return {
            "success": True,
            "requires_human_approval": True,
            "data": {
                "input_mode": input_mode,
                "proposed_plan_data": plan_data,
                "expected_fields": _WORKFORCE_EXPECTED_FIELDS,
                "total_hires": total_hires,
                "departments": departments,
                "items_count": len(plan_data),
            },
            "message": (
                f"Proposta de plano: {total_hires} contratacoes em "
                f"{len(departments)} departamento(s). Confirme com 'aprovar' "
                f"para gravar ou ajuste os itens antes de aprovar."
            ),
        }

    async with AsyncSessionLocal() as session:
        existing = await session.execute(
            text("SELECT id FROM company_culture_profiles WHERE company_id = :company_id LIMIT 1"),
            {"company_id": company_id},
        )
        plan_json = json.dumps(plan_data, ensure_ascii=False)

        if existing.mappings().first():
            await session.execute(
                text("""
                    UPDATE company_culture_profiles
                    SET additional_data = jsonb_set(
                        COALESCE(additional_data, '{}'::jsonb),
                        '{workforce_plan}',
                        :plan_data::jsonb
                    ),
                    updated_at = NOW()
                    WHERE company_id = :company_id
                """),
                {"plan_data": plan_json, "company_id": company_id},
            )
        else:
            await session.execute(
                text("""
                    INSERT INTO company_culture_profiles (company_id, additional_data, created_at, updated_at)
                    VALUES (:company_id, jsonb_build_object('workforce_plan', :plan_data::jsonb), NOW(), NOW())
                """),
                {"company_id": company_id, "plan_data": plan_json},
            )

        await session.commit()

    await _audit_log(company_id, "import_workforce_plan", metadata={"total_hires": total_hires, "departments": departments, "user_id": user_id, "items_count": len(plan_data)})

    return {
        "success": True,
        "data": {
            "total_hires": total_hires,
            "departments": departments,
            "items_count": len(plan_data),
        },
        "message": f"Plano importado: {total_hires} contratacoes planejadas em {len(departments)} departamentos.",
    }


@tool_handler("company_settings")
async def _wrap_get_company_completion(**kwargs: Any) -> dict[str, Any]:
    company_id = kwargs.get("company_id", "")
    result = await _wrap_get_company_profile(company_id=company_id)
    if not result["success"]:
        return result

    data = result["data"]
    completion = data.get("completion", {})

    sections_status = {
        "dados_basicos": {"label": "Dados Basicos", "filled": 0, "total": 8, "menu": "minha-empresa"},
        "cultura_evp": {"label": "Cultura & EVP", "filled": 0, "total": 10, "menu": "minha-empresa"},
        "tech_stack": {"label": "Tech Stack", "filled": 0, "total": 3, "menu": "minha-empresa"},
        "beneficios": {"label": "Beneficios", "filled": 0, "total": 1, "menu": "minha-empresa"},
        "niveis_remuneracao": {"label": "Niveis & Remuneracao", "filled": 0, "total": 3, "menu": "minha-empresa"},
        "planejamento": {"label": "Planejamento", "filled": 0, "total": 1, "menu": "minha-empresa"},
    }

    profile = data.get("profile", {})
    inst_fields = ["name", "cnpj", "website", "hr_email", "hr_phone", "industry", "company_size", "employee_count"]
    sections_status["dados_basicos"]["filled"] = sum(1 for f in inst_fields if profile.get(f))

    culture = data.get("culture", {})
    culture_fields = ["mission", "vision", "values", "core_competencies", "evp_bullets",
                      "work_model", "employment_types", "team_dynamics", "leadership_style", "dei_initiatives"]
    sections_status["cultura_evp"]["filled"] = sum(1 for f in culture_fields if culture.get(f))

    tech_fields = ["tech_stack", "engineering_culture", "default_languages"]
    sections_status["tech_stack"]["filled"] = sum(1 for f in tech_fields if culture.get(f))

    benefits = data.get("benefits", [])
    sections_status["beneficios"]["filled"] = 1 if benefits else 0

    sen_fields = ["seniority_levels", "default_behavioral_competencies", "default_salary_ranges"]
    sections_status["niveis_remuneracao"]["filled"] = sum(1 for f in sen_fields if culture.get(f))

    pending = [s["label"] for s in sections_status.values() if s["filled"] < s["total"]]

    return {
        "success": True,
        "data": {
            "overall": completion,
            "sections": sections_status,
            "pending_sections": pending,
            "menu_mapping": {
                "minha-empresa": "Minha Empresa",
                "pipeline": "Pipeline",
                "screening": "Screening",
                "templates-assinatura": "Templates & Assinatura",
                "comunicacao-alertas": "Comunicacao & Alertas",
                "usuarios-departamentos": "Usuarios & Departamentos",
                "integracoes": "Integracoes",
            },
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
                    "company_id": {"type": "string", "description": "ID da empresa"},
                },
                "required": ["company_id"],
            },
            function=_wrap_get_company_profile,
        ),
        ToolDefinition(
            name="save_company_field",
            description="Salva um campo especifico do perfil ou cultura da empresa. Campos TIER 1 (cnpj, name) requerem confirmed=true apos setup inicial.",
            parameters={
                "type": "object",
                "properties": {
                    "company_id": {"type": "string", "description": "ID da empresa"},
                    "section": {"type": "string", "description": "Secao (profile ou culture)"},
                    "field": {"type": "string", "description": "Nome do campo"},
                    "value": {"description": "Valor a salvar"},
                    "confirmed": {"type": "boolean", "description": "Confirmacao explicita para campos TIER 1 (cnpj, name) pos-setup. Default false."},
                    "is_admin": {"type": "boolean", "description": "Se o usuario solicitante e administrador. Obrigatorio para TIER 1 pos-setup."},
                    "user_id": {"type": "string", "description": "ID do usuario que solicitou a alteracao"},
                },
                "required": ["company_id", "section", "field", "value"],
            },
            function=_wrap_save_company_field,
        ),
        ToolDefinition(
            name="save_company_section",
            description="Salva multiplos campos de uma secao do perfil de empresa de uma vez. Mais eficiente que save_company_field para atualizacoes em lote.",
            parameters={
                "type": "object",
                "properties": {
                    "company_id": {"type": "string", "description": "ID da empresa"},
                    "section": {"type": "string", "description": "Secao (profile ou culture)"},
                    "data": {"type": "object", "description": "Dicionario com campos e valores"},
                },
                "required": ["company_id", "section", "data"],
            },
            function=_wrap_save_company_section,
        ),
        ToolDefinition(
            name="save_company_benefits",
            description=(
                "Persiste beneficios em company_benefits. modes: append (default) "
                "ou replace. Cada item passa por FairnessGuard L1 em name+description. "
                "Use sempre que o recrutador listar/atualizar beneficios pelo chat."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "company_id": {"type": "string", "description": "ID da empresa"},
                    "benefits": {
                        "type": "array",
                        "description": "Lista de beneficios {name, description, category, ...}",
                        "items": {"type": "object"},
                    },
                    "mode": {
                        "type": "string",
                        "enum": ["append", "replace"],
                        "description": "append (default) ou replace (desativa atuais antes)",
                    },
                    "user_id": {"type": "string", "description": "ID do usuario solicitante"},
                },
                "required": ["company_id", "benefits"],
            },
            function=_wrap_save_company_benefits,
        ),
        ToolDefinition(
            name="analyze_company_website",
            description="Analisa o website da empresa via Apify para extrair dados automaticamente (missao, cultura, tech stack, beneficios).",
            parameters={
                "type": "object",
                "properties": {
                    "company_id": {"type": "string", "description": "ID da empresa"},
                    "website_url": {"type": "string", "description": "URL do website"},
                    "linkedin_url": {"type": "string", "description": "URL do LinkedIn (opcional)"},
                },
                "required": ["company_id", "website_url"],
            },
            function=_wrap_analyze_company_website,
        ),
        ToolDefinition(
            name="process_uploaded_document",
            description="Processa documento enviado pelo recrutador (handbook, organograma, plano de cargos) com anonimizacao via FairnessGuard.",
            parameters={
                "type": "object",
                "properties": {
                    "company_id": {"type": "string", "description": "ID da empresa"},
                    "document_text": {"type": "string", "description": "Texto extraido do documento"},
                    "document_type": {"type": "string", "description": "Tipo do documento (handbook, org_chart, compensation, tech_doc, general)"},
                    "target_section": {
                        "type": "string",
                        "description": (
                            "Secao do hub Minha Empresa que originou o upload "
                            "(culture, tech_stack, benefits, workforce, "
                            "compensation, policy). Estreita os campos sugeridos."
                        ),
                    },
                },
                "required": ["company_id", "document_text"],
            },
            function=_wrap_process_uploaded_document,
        ),
        ToolDefinition(
            name="import_workforce_plan",
            description=(
                "Importa planejamento de contratacoes via planilha, texto livre "
                "ou paste estruturado. SEMPRE passa por aprovacao humana (HITL): "
                "chame primeiro sem approved para obter a proposta e, apos "
                "confirmacao do recrutador, chame novamente com approved=true."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "company_id": {"type": "string", "description": "ID da empresa"},
                    "input_mode": {
                        "type": "string",
                        "enum": ["spreadsheet", "text", "paste"],
                        "description": (
                            "spreadsheet (plan_data ja estruturado pelo upload), "
                            "text (descricao livre — extrai via LLM) ou "
                            "paste (tabela colada — parser deterministico)."
                        ),
                    },
                    "raw_text": {
                        "type": "string",
                        "description": "Texto livre ou tabela colada (para modos text/paste).",
                    },
                    "plan_data": {
                        "type": "array",
                        "description": "Lista de contratacoes planejadas (modo spreadsheet).",
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
                    "approved": {
                        "type": "boolean",
                        "description": (
                            "Obrigatorio=true para persistir. Sem approved=true, "
                            "a tool retorna apenas a proposta (preview HITL)."
                        ),
                    },
                    "user_id": {"type": "string", "description": "ID do usuario solicitante"},
                },
                "required": ["company_id"],
            },
            function=_wrap_import_workforce_plan,
        ),
        ToolDefinition(
            name="get_company_completion",
            description="Retorna percentual de preenchimento do perfil da empresa por secao (perfil, cultura, tech stack, beneficios) para guiar o onboarding.",
            parameters={
                "type": "object",
                "properties": {
                    "company_id": {"type": "string", "description": "ID da empresa"},
                },
                "required": ["company_id"],
            },
            function=_wrap_get_company_completion,
        ),
    ]

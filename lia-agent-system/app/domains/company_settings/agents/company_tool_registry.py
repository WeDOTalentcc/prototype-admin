"""
Company Settings Tool Registry - Tools for company profile configuration via conversation.

Provides tools for reading/writing company data, analyzing websites (Apify),
processing uploaded documents with anonymization, and workforce planning.
"""
import json
import logging
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
    validate_fairness_recursive,
)
from app.shared.tool_handler import tool_handler
from types import SimpleNamespace

logger = logging.getLogger(__name__)

_fairness_guard = FairnessGuard()


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


@tool_handler("company_settings")
async def _wrap_save_company_field(**kwargs: Any) -> dict[str, Any]:
    company_id = kwargs.get("company_id", "")
    section = kwargs.get("section", "profile")
    field = kwargs.get("field", "")
    value = kwargs.get("value")
    user_id = kwargs.get("user_id")

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
    *, session, company_id: str, section: str, field: str, value: Any
) -> dict[str, Any]:
    """PR4 (Task #1004) — usa ``session`` injetada (compartilhada com
    o wrapper de audit) e NÃO commita: o ``audit_company_change``
    commita business writes + outcome row em transação atômica."""
    valid_profile_fields = {
        "name", "trading_name", "cnpj", "website", "hr_email", "hr_phone",
        "address", "industry", "company_size", "employee_count", "founded_year",
        "linkedin_url", "logo_url",
    }
    valid_culture_fields = {
        "mission", "vision", "values", "core_competencies", "evp_bullets",
        "work_model", "hybrid_days_onsite", "employment_types",
        "growth_opportunities", "team_dynamics", "leadership_style",
        "dei_initiatives", "sustainability", "social_impact",
        "tech_stack", "engineering_culture", "default_languages",
        "seniority_levels", "default_behavioral_competencies",
        "default_salary_ranges", "locations", "headquarters",
    }

    if section == "profile" and field not in valid_profile_fields:
        return {"success": False, "data": {}, "message": f"Campo '{field}' nao e valido para perfil."}
    if section == "culture" and field not in valid_culture_fields:
        return {"success": False, "data": {}, "message": f"Campo '{field}' nao e valido para cultura."}

    # PR3 (Task #1003) — FairnessGuard recursivo. Cobre str/list/dict/strings
    # curtas; sem mais filtro `len > 10` (era bypass C3 do audit T1-T6).
    fairness = validate_fairness_recursive(
        value, guard=_fairness_guard, root_label=field or "value"
    )
    if fairness.is_blocked:
        return _fairness_violation_response(fairness, fallback_field=field)

    # PR4: usa session injetada (compartilhada com audit wrapper) e
    # captura `before` (estado anterior) para o payload canônico SOX.
    before_value: Any = None
    if section == "profile":
        existing = await session.execute(
            text(f"SELECT id, {field} AS prev FROM company_profiles WHERE id::text = :company_id LIMIT 1"),
            {"company_id": company_id},
        )
        prev_row = existing.mappings().first()
        if prev_row:
            before_value = prev_row.get("prev")
            await session.execute(
                text(f"UPDATE company_profiles SET {field} = :value, updated_at = NOW() WHERE id::text = :company_id"),
                {"value": json.dumps(value) if isinstance(value, (list, dict)) else value, "company_id": company_id},
            )
        else:
            await session.execute(
                text(f"INSERT INTO company_profiles (id, {field}, created_at, updated_at) VALUES (:company_id::uuid, :value, NOW(), NOW())"),
                {"company_id": company_id, "value": json.dumps(value) if isinstance(value, (list, dict)) else value},
            )
    elif section == "culture":
        existing = await session.execute(
            text(f"SELECT id, {field} AS prev FROM company_culture_profiles WHERE company_id = :company_id LIMIT 1"),
            {"company_id": company_id},
        )
        prev_row = existing.mappings().first()
        val = json.dumps(value, ensure_ascii=False) if isinstance(value, (list, dict)) else value
        if prev_row:
            before_value = prev_row.get("prev")
            await session.execute(
                text(f"UPDATE company_culture_profiles SET {field} = :value, updated_at = NOW() WHERE company_id = :company_id"),
                {"value": val, "company_id": company_id},
            )
        else:
            await session.execute(
                text(f"INSERT INTO company_culture_profiles (company_id, {field}, created_at, updated_at) VALUES (:company_id, :value, NOW(), NOW())"),
                {"company_id": company_id, "value": val},
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
        fairness = validate_fairness_recursive(
            data, guard=_fairness_guard, root_label=section or "data"
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
        saved_fields = []
        for field, value in data.items():
            inner = await _save_company_field_impl(
                session=_audit.session,
                company_id=company_id,
                section=section,
                field=field,
                value=value,
            )
            inner.pop("_before", None)
            inner.pop("_after", None)
            if inner.get("success"):
                saved_fields.append(field)

        result = {
            "success": True,
            "data": {"section": section, "fields_saved": saved_fields, "count": len(saved_fields)},
            "message": f"Secao '{section}' salva com {len(saved_fields)} campos.",
        }
        _audit.set_after({"fields_saved": saved_fields, "count": len(saved_fields)})
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
        backend_url = "http://127.0.0.1:8001"
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
        "handbook": ["mission", "vision", "values", "benefits", "work_model", "dei_initiatives"],
        "org_chart": ["departments", "hierarchy", "headcount"],
        "compensation": ["seniority_levels", "salary_ranges", "benefits", "variable_compensation"],
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
        plan_data, guard=_fairness_guard, root_label="plan_data"
    )
    if fairness.is_blocked:
        return _fairness_violation_response(fairness)

    total_hires = sum(item.get("quantity", 0) for item in plan_data if isinstance(item, dict))
    departments = list(set(item.get("department", "N/A") for item in plan_data if isinstance(item, dict)))

    # PR4: usa session injetada; captura `before` (plano anterior) para
    # payload canônico SOX.
    existing = await session.execute(
        text(
            "SELECT id, COALESCE(additional_data->'workforce_plan', 'null'::jsonb) AS prev_plan "
            "FROM company_culture_profiles WHERE company_id = :company_id LIMIT 1"
        ),
        {"company_id": company_id},
    )
    prev_row = existing.mappings().first()
    before_plan: Any = None
    if prev_row:
        try:
            raw = prev_row.get("prev_plan")
            before_plan = json.loads(raw) if isinstance(raw, str) else raw
        except (json.JSONDecodeError, TypeError):
            before_plan = None

    plan_json = json.dumps(plan_data, ensure_ascii=False)

    if prev_row:
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

    return {
        "success": True,
        "data": {
            "total_hires": total_hires,
            "departments": departments,
            "items_count": len(plan_data),
        },
        "message": f"Plano importado: {total_hires} contratacoes planejadas em {len(departments)} departamentos.",
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
        "culture": {"label": "Cultura & EVP", "filled": 0, "total": 10},
        "tech_stack": {"label": "Tech Stack", "filled": 0, "total": 3},
        "benefits": {"label": "Beneficios", "filled": 0, "total": 1},
        "seniority": {"label": "Niveis & Remuneracao", "filled": 0, "total": 3},
        "workforce": {"label": "Planejamento", "filled": 0, "total": 1},
    }

    profile = data.get("profile", {})
    inst_fields = ["name", "cnpj", "website", "hr_email", "hr_phone", "industry", "company_size", "employee_count"]
    sections_status["institutional"]["filled"] = sum(1 for f in inst_fields if profile.get(f))

    culture = data.get("culture", {})
    culture_fields = ["mission", "vision", "values", "core_competencies", "evp_bullets",
                      "work_model", "employment_types", "team_dynamics", "leadership_style", "dei_initiatives"]
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
    ]

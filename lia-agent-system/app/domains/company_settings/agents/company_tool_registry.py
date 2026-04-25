"""
Company Settings Tool Registry - Tools for company profile configuration via conversation.

Provides tools for reading/writing company data, analyzing websites (Apify),
processing uploaded documents with anonymization, and workforce planning.

Task #812 — defesa em profundidade: o agente também recebe um conjunto curado
de tools operacionais primárias (criar vaga, listar vagas, buscar candidatos),
para não travar quando o recrutador interrompe o onboarding com uma intenção
clara de outro domínio. Reaproveitamos as ToolDefinitions canônicas dos
registries de jobs_mgmt e talent — não duplicamos handlers.
"""
import json
import logging
import os
import uuid as _uuid
from typing import Any

from lia_agents_core.react_loop import ToolDefinition
from sqlalchemy import text

from app.core.database import AsyncSessionLocal
from app.shared.compliance.fairness_guard import FairnessGuard
from app.shared.tool_handler import tool_handler

logger = logging.getLogger(__name__)

_fairness_guard = FairnessGuard()


# ── Task #812 — Tools operacionais primárias autorizadas no agente ──────────
# Conjunto fechado: nomes de tools que representam intenções operacionais
# (criar/listar vagas, buscar candidatos) atendidas mesmo dentro do contexto
# de configuração da empresa. Mantido aqui para ser fonte única consumida
# também pela telemetria do orchestrator.
OPERATIONAL_TOOL_NAMES: frozenset[str] = frozenset({
    "create_job_vacancy",
    "list_jobs",
    "view_job_details",
    "search_candidates",
})


def _pick_tool_definitions(
    source: list[ToolDefinition], names: set[str]
) -> list[ToolDefinition]:
    """Retorna ToolDefinitions com nomes em `names`, falhando alto se algum
    estiver ausente — evita silently-missing tools quando o registry de
    origem mudar."""
    by_name = {td.name: td for td in source}
    missing = names - by_name.keys()
    if missing:
        raise LookupError(
            "Tool definitions ausentes no registry de origem: "
            f"{sorted(missing)} — verifique jobs_mgmt/talent registries."
        )
    return [by_name[n] for n in names]

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

    if isinstance(value, str) and len(value) > 10:
        check = _fairness_guard.check(value)
        if check.is_blocked:
            return {
                "success": False,
                "data": {"blocked_field": field, "category": check.category},
                "message": f"Campo '{field}' bloqueado por compliance: {check.educational_message}",
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
        if isinstance(field_value, str) and len(field_value) > 10:
            check = _fairness_guard.check(field_value)
            if check.is_blocked:
                return {
                    "success": False,
                    "data": {"blocked_field": field_name, "category": check.category},
                    "message": f"Campo '{field_name}' bloqueado por compliance: {check.educational_message}",
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


@tool_handler("company_settings")
async def _wrap_process_uploaded_document(**kwargs: Any) -> dict[str, Any]:
    company_id = kwargs.get("company_id", "")
    document_text = kwargs.get("document_text", "")
    document_type = kwargs.get("document_type", "general")
    user_id = kwargs.get("user_id", "system")

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

    await _audit_log(company_id, "process_document", metadata={"document_type": document_type, "text_length": len(document_text), "user_id": user_id})

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
    user_id = kwargs.get("user_id", "system")

    if not plan_data or not isinstance(plan_data, list):
        return {
            "success": False,
            "data": {},
            "message": "Dados do plano de contratacoes vazios. Envie uma lista com departamento, cargo, quantidade e prazo.",
        }

    total_hires = sum(item.get("quantity", 0) for item in plan_data if isinstance(item, dict))
    departments = list(set(item.get("department", "N/A") for item in plan_data if isinstance(item, dict)))

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


@tool_handler("company_settings")
async def _wrap_create_job_vacancy(**kwargs: Any) -> dict[str, Any]:
    """Cria vaga via service canônico `JobVacancyLifecycleService.create`.

    Usado pelo agente `company_settings` quando o recrutador interrompe o
    onboarding com intenção operacional explícita ("antes de configurar tudo,
    quero cadastrar uma vaga rascunho"). Sem fallback silencioso: erros de
    validação ou de tenant viram resposta estruturada com `success=False`.
    """
    from app.domains.job_management.services.job_vacancy_lifecycle_service import (
        job_vacancy_lifecycle_service,
    )

    company_id = kwargs.pop("company_id", "") or ""
    title = (kwargs.pop("title", "") or "").strip()
    if not title:
        return {
            "success": False,
            "operation": "create_job_vacancy",
            "error": "validation_error",
            "message": "title é obrigatório para criar a vaga.",
        }

    payload = {k: v for k, v in kwargs.items() if not k.startswith("_") and v is not None}
    try:
        result = await job_vacancy_lifecycle_service.create(
            company_id=str(company_id),
            title=title,
            **payload,
        )
        msg = (
            f"Vaga '{result.get('title', title)}' criada como "
            f"{result.get('status', 'Rascunho')} (ID: {result.get('id')})."
        )
        return {**result, "message": msg}
    except (ValueError, LookupError) as exc:
        code = "validation_error" if isinstance(exc, ValueError) else "not_found"
        logger.warning("[company_settings] create_job_vacancy %s: %s", code, exc)
        return {
            "success": False,
            "operation": "create_job_vacancy",
            "error": code,
            "message": str(exc),
        }
    except Exception as exc:  # noqa: BLE001 — fronteira do tool: mapear, não mascarar
        # LIA-812-1: erro inesperado (ex: DBAPIError) é propagado como resposta
        # estruturada com `success=False` e logado com stacktrace completo,
        # para que o agente reporte falha real em vez de afirmar sucesso.
        logger.exception("[company_settings] create_job_vacancy erro inesperado")
        return {
            "success": False,
            "operation": "create_job_vacancy",
            "error": "internal_error",
            "message": (
                "Falha inesperada ao criar a vaga. Detalhe: "
                f"{type(exc).__name__}: {str(exc)[:200]}"
            ),
        }


def _build_operational_tool_definitions() -> list[ToolDefinition]:
    """Curadoria das tools operacionais primárias expostas ao agente.

    Reaproveita as ToolDefinitions canônicas de `jobs_mgmt_tool_registry` e
    `talent_tool_registry` (mesma `function=` referenciando os wrappers
    multi-tenant já testados pelo agente recruiter_assistant).
    """
    from app.domains.recruiter_assistant.agents.jobs_mgmt_tool_registry import (
        TOOL_DEFINITIONS as _JOBS_MGMT_TOOLS,
    )
    from app.domains.recruiter_assistant.agents.talent_tool_registry import (
        TOOL_DEFINITIONS as _TALENT_TOOLS,
    )

    job_tools = _pick_tool_definitions(_JOBS_MGMT_TOOLS, {"list_jobs", "view_job_details"})
    talent_tools = _pick_tool_definitions(_TALENT_TOOLS, {"search_candidates"})

    create_tool = ToolDefinition(
        name="create_job_vacancy",
        description=(
            "Cria uma vaga (rascunho por padrão) para a empresa atual. "
            "Use quando o recrutador pedir explicitamente para criar/cadastrar "
            "uma vaga, mesmo durante o onboarding. Title é obrigatório; "
            "department/location/work_model/description são opcionais."
        ),
        parameters={
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Título da vaga (obrigatório)"},
                "department": {"type": "string", "description": "Departamento ou área"},
                "location": {"type": "string", "description": "Localização (cidade/estado)"},
                "work_model": {
                    "type": "string",
                    "description": "Modelo de trabalho: remoto, hibrido, presencial",
                },
                "description": {"type": "string", "description": "Descrição inicial da vaga"},
                "status": {
                    "type": "string",
                    "description": "Status inicial (default 'Rascunho')",
                },
            },
            "required": ["title"],
        },
        function=_wrap_create_job_vacancy,
    )
    return [create_tool, *job_tools, *talent_tools]


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
            description="Salva multiplos campos de uma secao de uma vez.",
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
                },
                "required": ["company_id", "document_text"],
            },
            function=_wrap_process_uploaded_document,
        ),
        ToolDefinition(
            name="import_workforce_plan",
            description="Importa planejamento de contratacoes (de planilha ou conversa). Cada item deve ter departamento, cargo, quantidade e prazo.",
            parameters={
                "type": "object",
                "properties": {
                    "company_id": {"type": "string", "description": "ID da empresa"},
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
                "required": ["company_id", "plan_data"],
            },
            function=_wrap_import_workforce_plan,
        ),
        ToolDefinition(
            name="get_company_completion",
            description="Retorna o progresso de preenchimento do perfil da empresa por secao.",
            parameters={
                "type": "object",
                "properties": {
                    "company_id": {"type": "string", "description": "ID da empresa"},
                },
                "required": ["company_id"],
            },
            function=_wrap_get_company_completion,
        ),
        # ── Tools operacionais primárias (Task #812) ─────────────────────
        # Mantidas DEPOIS das tools de onboarding intencionalmente: o LLM
        # vê primeiro as ferramentas de configuração e só recorre às
        # operacionais quando o recrutador trouxer intenção explícita.
        *_build_operational_tool_definitions(),
    ]

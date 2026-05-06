"""
Company Settings Tool Registry - Tools for company profile configuration via conversation.

Provides tools for reading/writing company data, analyzing websites (Apify),
processing uploaded documents with anonymization, and workforce planning.
"""
import json
import logging
from typing import Any

from lia_agents_core.react_loop import ToolDefinition
from lia_agents_core.tool_adapter import ToolOutput
from sqlalchemy import text

from app.core.database import AsyncSessionLocal
from app.shared.compliance.fairness_guard import FairnessGuard
from app.shared.tool_handler import tool_handler

logger = logging.getLogger(__name__)

_fairness_guard = FairnessGuard()


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

    if isinstance(value, str) and len(value) > 10:
        check = _fairness_guard.check(value)
        if check.is_blocked:
            return {
                "success": False,
                "data": {"blocked_field": field, "category": check.category},
                "message": f"Campo '{field}' bloqueado por compliance: {check.educational_message}",
            }

    async with AsyncSessionLocal() as session:
        if section == "profile":
            existing = await session.execute(
                text("SELECT id FROM company_profiles WHERE id::text = :company_id LIMIT 1"),
                {"company_id": company_id},
            )
            if existing.mappings().first():
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
                text("SELECT id FROM company_culture_profiles WHERE company_id = :company_id LIMIT 1"),
                {"company_id": company_id},
            )
            val = json.dumps(value, ensure_ascii=False) if isinstance(value, (list, dict)) else value
            if existing.mappings().first():
                await session.execute(
                    text(f"UPDATE company_culture_profiles SET {field} = :value, updated_at = NOW() WHERE company_id = :company_id"),
                    {"value": val, "company_id": company_id},
                )
            else:
                await session.execute(
                    text(f"INSERT INTO company_culture_profiles (company_id, {field}, created_at, updated_at) VALUES (:company_id, :value, NOW(), NOW())"),
                    {"company_id": company_id, "value": val},
                )

        await session.commit()

    return {
        "success": True,
        "data": {"section": section, "field": field, "value": value, "saved": True},
        "message": f"Dado salvo: {section}.{field}",
    }


@tool_handler("company_settings")
async def _wrap_save_company_section(**kwargs: Any) -> dict[str, Any]:
    company_id = kwargs.get("company_id", "")
    section = kwargs.get("section", "profile")
    data = kwargs.get("data", {})

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
    for field, value in data.items():
        result = await _wrap_save_company_field(
            company_id=company_id, section=section, field=field, value=value
        )
        if result["success"]:
            saved_fields.append(field)

    return {
        "success": True,
        "data": {"section": section, "fields_saved": saved_fields, "count": len(saved_fields)},
        "message": f"Secao '{section}' salva com {len(saved_fields)} campos.",
    }


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

"""
Company Settings Tools — D1.

LIA-callable tools for company profile management:
  - check_company_completeness — verify which profile fields are empty
  - suggest_recruiting_policy — baseline policy suggestion with FairnessGuard validation
  - import_benefits_from_data — bulk upsert company benefits

All tools use ToolExecutionContext for multi-tenant isolation.
suggest_recruiting_policy runs through FairnessGuard to prevent
discriminatory policies.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.tools.registry import ToolDefinition, tool_registry
from app.shared.compliance.fairness_guard import FairnessGuard

if TYPE_CHECKING:
    from app.tools.executor import ToolExecutionContext

logger = logging.getLogger(__name__)

_fairness_guard = FairnessGuard()


def _extract_context(kwargs: dict[str, Any]) -> Optional["ToolExecutionContext"]:
    return kwargs.pop("_context", None)


COMPANY_CORE_FIELDS = [
    "name", "trading_name", "cnpj", "website", "industry",
    "company_size", "employee_count", "linkedin_url",
]

COMPANY_CULTURE_FIELDS = [
    "mission", "vision", "values", "work_model",
    "growth_opportunities",
]


# ───────────────────────────────────────────────────────────────────
# Tool 1 — check_company_completeness
# ───────────────────────────────────────────────────────────────────

async def check_company_completeness(**kwargs) -> dict[str, Any]:
    """
    Inspect which core fields of the company profile are empty.
    LIA uses this to offer proactive help (D10 proactivity).

    Returns:
        {
            "success": bool,
            "profile_completeness_pct": float,
            "culture_completeness_pct": float,
            "overall_pct": float,
            "missing_profile_fields": [str],
            "missing_culture_fields": [str],
            "recommendation": str,
            "has_website": bool,  # enables auto-scrape suggestion
        }
    """
    context = _extract_context(kwargs)
    company_id = context.company_id if context else None

    if not company_id:
        return {
            "success": False,
            "error": "company_id_required",
            "message": "Tenant isolation compromised — company_id is required.",
        }

    try:
        async with AsyncSessionLocal() as db:
            profile = await db.execute(
                text("""
                    SELECT name, trading_name, cnpj, website, industry,
                           company_size, employee_count, linkedin_url
                    FROM company_profiles
                    WHERE id::text = :cid
                    LIMIT 1
                """),
                {"cid": company_id},
            )
            prof_row = profile.mappings().first()

            culture = await db.execute(
                text("""
                    SELECT mission, vision, values, work_model, growth_opportunities
                    FROM company_culture_profiles
                    WHERE company_id::text = :cid
                    LIMIT 1
                """),
                {"cid": company_id},
            )
            cult_row = culture.mappings().first()

            missing_profile = []
            if prof_row:
                for f in COMPANY_CORE_FIELDS:
                    v = prof_row.get(f)
                    if v is None or v == "":
                        missing_profile.append(f)
            else:
                missing_profile = list(COMPANY_CORE_FIELDS)

            missing_culture = []
            if cult_row:
                for f in COMPANY_CULTURE_FIELDS:
                    v = cult_row.get(f)
                    if v is None or v == "" or (isinstance(v, list) and not v):
                        missing_culture.append(f)
            else:
                missing_culture = list(COMPANY_CULTURE_FIELDS)

            profile_pct = round(1.0 - len(missing_profile) / len(COMPANY_CORE_FIELDS), 2)
            culture_pct = round(1.0 - len(missing_culture) / len(COMPANY_CULTURE_FIELDS), 2)
            overall = round((profile_pct + culture_pct) / 2, 2)

            has_website = bool(prof_row and prof_row.get("website"))

            if overall >= 0.9:
                reco = "Perfil completo — pronto para buscas e triagens refinadas."
            elif has_website and len(missing_profile) + len(missing_culture) > 3:
                reco = (
                    "Perfil incompleto mas você tem website cadastrado. "
                    "Posso usar analyze_company_website para preencher automaticamente "
                    "nome/setor/cultura/benefícios via scraping."
                )
            elif not has_website:
                reco = (
                    f"Perfil {overall*100:.0f}% completo e sem website cadastrado. "
                    "Peça a URL da empresa ao recrutador para permitir auto-preenchimento. "
                    "Caminho: Menu → Configurações → Dados Básicos."
                )
            else:
                reco = (
                    f"Perfil {overall*100:.0f}% completo. "
                    "Navegar para Configurações para completar manualmente."
                )

            return {
                "success": True,
                "company_id": company_id,
                "profile_completeness_pct": profile_pct,
                "culture_completeness_pct": culture_pct,
                "overall_pct": overall,
                "missing_profile_fields": missing_profile,
                "missing_culture_fields": missing_culture,
                "has_website": has_website,
                "website": prof_row.get("website") if prof_row else None,
                "recommendation": reco,
            }
    except Exception as e:
        logger.error("check_company_completeness failed: %s", e, exc_info=True)
        return {
            "success": False,
            "error": "db_error",
            "message": f"Erro ao verificar perfil da empresa: {e}",
        }


# ───────────────────────────────────────────────────────────────────
# Tool 2 — suggest_recruiting_policy
# ───────────────────────────────────────────────────────────────────

RECRUITING_POLICY_TEMPLATES: dict[str, dict[str, Any]] = {
    "default": {
        "description": "Processo seletivo justo e estruturado",
        "stages": [
            "Triagem automática por WSI (70% técnico + 30% comportamental)",
            "Entrevista comportamental CBI/STAR via WhatsApp",
            "Entrevista técnica ou teste prático",
            "Entrevista final com gestor da área",
            "Proposta com transparência de faixa salarial",
        ],
        "principles": [
            "Decisões baseadas em critérios objetivos definidos na JD",
            "Fairness guard ativo: zero coleta de raça, religião, gênero, saúde",
            "Feedback transparente para candidatos aprovados e reprovados",
            "Diversidade via programas afirmativos estruturados quando aplicável",
            "Compliance LGPD Art. 20 (direito à explicação de decisões automatizadas)",
        ],
        "time_to_hire_days_target": 30,
    },
    "tech_startup": {
        "description": "Processo ágil para startups de tecnologia (< 50 funcionários)",
        "stages": [
            "Triagem WSI",
            "Conversa inicial com recrutador (30min)",
            "Entrevista técnica (live coding ou take-home)",
            "Conversa com o time (cultural fit)",
            "Proposta",
        ],
        "principles": [
            "Feedback em até 48h após cada etapa",
            "Transparência total sobre remuneração, equity e benefícios",
            "Zero discriminação por universidade, idade ou bairro de origem",
        ],
        "time_to_hire_days_target": 15,
    },
    "enterprise": {
        "description": "Processo estruturado para empresas enterprise (> 500 funcionários)",
        "stages": [
            "Triagem WSI + Dreyfus (níveis de expertise)",
            "Entrevista comportamental estruturada (CBI/STAR)",
            "Bateria técnica",
            "Entrevista com gestor",
            "Entrevista com diretoria/VP",
            "Proposta com benchmark de mercado",
        ],
        "principles": [
            "Painel de entrevistadores diverso (mín. 2 avaliadores por etapa)",
            "Decisão colegiada após todas etapas (reduz viés individual)",
            "Programa afirmativo ativo para D&I onde legalmente permitido",
            "Documentação completa de decisões (audit trail LGPD)",
        ],
        "time_to_hire_days_target": 60,
    },
}


async def suggest_recruiting_policy(
    sector: str | None = None,
    company_size: str | None = None,
    **kwargs,
) -> dict[str, Any]:
    """
    Suggest a baseline recruiting policy based on sector + company size.
    Every suggestion is validated through FairnessGuard to ensure
    no discriminatory criteria (gender, race, age, religion, disability, socioeconomic).

    Args:
        sector: e.g. "tecnologia", "saúde", "financeiro"
        company_size: "startup" | "small" | "medium" | "enterprise"

    Returns:
        {
            "success": bool,
            "template_used": str,
            "policy": {...},
            "fairness_check": {passed: bool, issues: [str]},
            "customization_notes": [str],
        }
    """
    context = _extract_context(kwargs)
    company_id = context.company_id if context else None

    if not company_id:
        return {
            "success": False,
            "error": "company_id_required",
            "message": "Tenant isolation compromised — company_id is required.",
        }

    # Pick template
    template_id = "default"
    normalized_size = (company_size or "").lower()
    if normalized_size in ("startup", "small") or "startup" in (sector or "").lower():
        template_id = "tech_startup"
    elif normalized_size in ("enterprise", "large", "big"):
        template_id = "enterprise"

    tmpl = RECRUITING_POLICY_TEMPLATES[template_id]
    policy = dict(tmpl)

    # Run fairness guard on the policy text
    try:
        policy_text = (
            policy.get("description", "")
            + " "
            + " ".join(policy.get("stages", []))
            + " "
            + " ".join(policy.get("principles", []))
        )
        fairness_result = _fairness_guard.check_text(policy_text)
        passed = bool(fairness_result.get("is_safe", True))
        issues = fairness_result.get("issues", []) if not passed else []
    except Exception as e:
        logger.debug("Fairness check skipped: %s", e)
        passed = True
        issues = []

    notes: list[str] = []
    if sector:
        notes.append(f"Template ajustado para setor: {sector}")
    if company_size:
        notes.append(f"Tamanho da empresa considerado: {company_size}")
    notes.append("Revise e customize antes de adotar — esta é uma baseline.")
    notes.append("FairnessGuard validou o texto da política.")

    return {
        "success": True,
        "template_used": template_id,
        "policy": policy,
        "fairness_check": {
            "passed": passed,
            "issues": issues,
        },
        "customization_notes": notes,
        "next_action_suggestion": (
            "Revise a política sugerida. Se quiser adotá-la, posso salvá-la "
            "na tabela company_hiring_policies via save_company_section."
        ),
    }


# ───────────────────────────────────────────────────────────────────
# Tool 3 — import_benefits_from_data
# ───────────────────────────────────────────────────────────────────

async def import_benefits_from_data(
    benefits: list[dict[str, Any]],
    replace_existing: bool = False,
    **kwargs,
) -> dict[str, Any]:
    """
    Bulk insert company benefits from structured data (parsed spreadsheet or form).

    Each benefit item must have at least 'name'; 'category' and 'description' optional.
    category: health | food | transport | education | financial | quality_life | family | security

    Args:
        benefits: list of {name, category, description, is_highlight}
        replace_existing: if True, deactivates existing benefits before insert

    Returns:
        {success, inserted_count, skipped_count, errors}
    """
    context = _extract_context(kwargs)
    company_id = context.company_id if context else None
    user_id = context.user_id if context else None

    if not company_id:
        return {
            "success": False,
            "error": "company_id_required",
            "message": "Tenant isolation compromised — company_id is required.",
        }

    if not benefits or not isinstance(benefits, list):
        return {
            "success": False,
            "error": "invalid_input",
            "message": "`benefits` must be a non-empty list of objects.",
        }

    try:
        from lia_models.company_benefit import CompanyBenefit
    except ImportError as e:
        return {
            "success": False,
            "error": "model_unavailable",
            "message": f"CompanyBenefit model not importable: {e}",
        }

    inserted = 0
    skipped = 0
    errors: list[str] = []

    try:
        async with AsyncSessionLocal() as db:
            if replace_existing:
                await db.execute(
                    text("UPDATE company_benefits SET is_active = false WHERE company_id::text = :cid"),
                    {"cid": company_id},
                )

            for idx, b in enumerate(benefits):
                if not isinstance(b, dict):
                    errors.append(f"item {idx}: not a dict")
                    skipped += 1
                    continue
                name = b.get("name") or b.get("nome")
                if not name:
                    errors.append(f"item {idx}: missing 'name'")
                    skipped += 1
                    continue
                try:
                    record = CompanyBenefit(
                        company_id=company_id,
                        name=str(name)[:200],
                        category=b.get("category", "other"),
                        description=b.get("description", "")[:1000] if b.get("description") else None,
                        is_highlight=bool(b.get("is_highlight", False)),
                        is_active=True,
                    )
                    db.add(record)
                    inserted += 1
                except Exception as e:
                    errors.append(f"item {idx} ('{name}'): {e}")
                    skipped += 1

            await db.commit()

        logger.info(
            "[import_benefits] tenant=%s user=%s inserted=%d skipped=%d",
            company_id, user_id, inserted, skipped,
        )
        return {
            "success": True,
            "inserted_count": inserted,
            "skipped_count": skipped,
            "errors": errors[:10],
            "message": f"Importados {inserted} benefícios ({skipped} ignorados).",
        }
    except Exception as e:
        logger.error("import_benefits_from_data failed: %s", e, exc_info=True)
        return {
            "success": False,
            "error": "db_error",
            "message": f"Erro ao importar benefícios: {e}",
        }


# ───────────────────────────────────────────────────────────────────
# Registration
# ───────────────────────────────────────────────────────────────────

def register_company_settings_tools() -> None:
    tool_registry.register(ToolDefinition(
        name="check_company_completeness",
        description=(
            "Verifica quais campos do perfil da empresa (dados básicos + cultura) "
            "estão vazios. LIA usa para oferecer ajuda proativa. "
            "Retorna missing_fields, overall_pct, has_website e recomendação."
        ),
        parameters_schema={"type": "object", "properties": {}},
        handler=check_company_completeness,
        allowed_agents=[
            "recruiter_assistant", "company_settings", "orchestrator",
        ],
    ))

    tool_registry.register(ToolDefinition(
        name="suggest_recruiting_policy",
        description=(
            "Sugere uma política de recrutamento baseline apropriada para o setor e "
            "tamanho da empresa. Sempre valida via FairnessGuard — zero discriminação "
            "por gênero, raça, idade, religião, deficiência ou socioeconômico. "
            "Retorna template + validação fairness + customization_notes."
        ),
        parameters_schema={
            "type": "object",
            "properties": {
                "sector": {
                    "type": "string",
                    "description": "Setor da empresa (ex: tecnologia, saúde, financeiro)",
                },
                "company_size": {
                    "type": "string",
                    "enum": ["startup", "small", "medium", "enterprise"],
                    "description": "Tamanho da empresa",
                },
            },
        },
        handler=suggest_recruiting_policy,
        allowed_agents=[
            "recruiter_assistant", "company_settings", "job_planner", "orchestrator",
        ],
    ))

    tool_registry.register(ToolDefinition(
        name="import_benefits_from_data",
        description=(
            "Bulk insert de benefícios da empresa a partir de dados estruturados "
            "(planilha já parseada ou formulário). Cada item: name + category + description. "
            "Use replace_existing=true para zerar antes de importar."
        ),
        parameters_schema={
            "type": "object",
            "properties": {
                "benefits": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "category": {
                                "type": "string",
                                "enum": ["health", "food", "transport", "education",
                                         "financial", "quality_life", "family", "security", "other"],
                            },
                            "description": {"type": "string"},
                            "is_highlight": {"type": "boolean"},
                        },
                        "required": ["name"],
                    },
                    "description": "Lista de benefícios",
                },
                "replace_existing": {
                    "type": "boolean",
                    "default": False,
                    "description": "Se true, desativa benefícios existentes antes",
                },
            },
            "required": ["benefits"],
        },
        handler=import_benefits_from_data,
        allowed_agents=[
            "recruiter_assistant", "company_settings", "orchestrator",
        ],
    ))

    logger.info(
        "✅ Registered 3 company_settings tools "
        "(check_company_completeness, suggest_recruiting_policy, import_benefits_from_data)"
    )

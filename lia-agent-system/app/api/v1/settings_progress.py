"""
Settings Progress API endpoint.
Calculates real completion percentages for the 7-item settings menu.

Section IDs:
  minha-empresa, pipeline, screening, templates-assinatura,
  comunicacao-alertas, usuarios-departamentos, integracoes
"""
import logging
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.company.repositories.settings_progress_repository import SettingsProgressRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/settings", tags=["settings"])


async def _calc_minha_empresa(repo: SettingsProgressRepository, company, company_uuid) -> tuple[int, dict]:
    if not company:
        return 0, {"company_data": False, "culture": False, "tech_stack": False, "benefits": False, "policies": False, "workforce": False}

    required_fields = [company.name, company.website, company.sector or company.industry]
    optional_fields = [company.description, company.headquarters_city, company.employee_count or company.company_size, company.logo_url]
    req_filled = sum(1 for f in required_fields if f)
    opt_filled = sum(1 for f in optional_fields if f)
    company_data_pct = int((req_filled / len(required_fields)) * 70 + (opt_filled / len(optional_fields)) * 30)
    company_data_ok = req_filled == len(required_fields)

    culture_profile = await repo.get_culture_profile(company_uuid) if company_uuid else None
    culture_fields = ["mission", "vision", "values", "core_competencies", "evp_bullets"]
    culture_filled = sum(1 for f in culture_fields if culture_profile and culture_profile.get(f)) if culture_profile else 0
    culture_pct = int((culture_filled / len(culture_fields)) * 100)
    culture_ok = culture_filled >= 3

    tech_fields = ["tech_stack", "engineering_culture", "default_languages"]
    tech_filled = sum(1 for f in tech_fields if culture_profile and culture_profile.get(f)) if culture_profile else 0
    tech_pct = int((tech_filled / len(tech_fields)) * 100)
    tech_ok = tech_filled >= 1

    benefit_count = await repo.count_active_benefits(company_uuid) if company_uuid else 0
    benefits_pct = 100 if benefit_count >= 1 else 0
    benefits_ok = benefit_count >= 1

    has_workforce = bool(
        culture_profile
        and isinstance(culture_profile.get("additional_data"), dict)
        and culture_profile["additional_data"].get("workforce_plan")
    ) if culture_profile else False
    workforce_pct = 100 if has_workforce else 0

    policy_count = await repo.count_active_policies(company_uuid) if company_uuid else 0
    policies_ok = policy_count >= 1
    policies_pct = min(100, int((policy_count / 3) * 100))

    total = int(
        company_data_pct * 0.25 +
        culture_pct * 0.25 +
        tech_pct * 0.15 +
        benefits_pct * 0.15 +
        workforce_pct * 0.10 +
        policies_pct * 0.10
    )

    subs = {
        "company_data": company_data_ok,
        "culture": culture_ok,
        "tech_stack": tech_ok,
        "benefits": benefits_ok,
        "policies": policies_ok,
        "workforce": has_workforce,
    }

    return total, subs


async def _calc_pipeline(repo: SettingsProgressRepository, company_uuid) -> tuple[int, dict]:
    if not company_uuid:
        return 0, {"stages": False, "slas": False}

    stage_count = await repo.count_active_stages(company_uuid)
    sla_count = await repo.count_active_slas(company_uuid)

    stages_ok = stage_count >= 3
    slas_ok = sla_count >= 1

    stages_pct = min(100, int((stage_count / 5) * 100))
    slas_pct = 100 if slas_ok else 0

    total = int(stages_pct * 0.60 + slas_pct * 0.40)
    return total, {"stages": stages_ok, "slas": slas_ok}


async def _calc_screening(repo: SettingsProgressRepository, company_uuid) -> tuple[int, dict]:
    if not company_uuid:
        return 0, {"questions": False}

    q_count = await repo.count_active_screening_questions(company_uuid)
    q_ok = q_count >= 1
    q_pct = min(100, int((q_count / 5) * 100))

    return q_pct, {"questions": q_ok}


async def _calc_templates_assinatura(repo: SettingsProgressRepository, company_uuid) -> tuple[int, dict]:
    if not company_uuid:
        return 0, {"templates": False, "signature": False}

    template_count = await repo.count_active_templates(company_uuid)
    has_sig = await repo.has_email_signature(company_uuid)

    templates_ok = template_count >= 1
    templates_pct = 100 if templates_ok else 0
    sig_pct = 100 if has_sig else 0

    total = int(templates_pct * 0.60 + sig_pct * 0.40)
    return total, {"templates": templates_ok, "signature": has_sig}


async def _calc_comunicacao_alertas(repo: SettingsProgressRepository, company_uuid) -> tuple[int, dict]:
    if not company_uuid:
        return 0, {"alerts": False, "lgpd_schedule": False}

    alert_count = await repo.count_active_alert_configs(company_uuid)
    has_lgpd = await repo.has_lgpd_schedule(company_uuid)

    alerts_ok = alert_count >= 1
    alerts_pct = 100 if alerts_ok else 0
    lgpd_pct = 100 if has_lgpd else 0

    total = int(alerts_pct * 0.50 + lgpd_pct * 0.50)
    return total, {"alerts": alerts_ok, "lgpd_schedule": has_lgpd}


async def _calc_usuarios_departamentos(repo: SettingsProgressRepository, company_uuid) -> tuple[int, dict]:
    if not company_uuid:
        return 0, {"users": False, "departments": False}

    user_count = await repo.count_active_users(company_uuid)
    dept_count = await repo.count_active_departments(company_uuid)

    users_ok = user_count >= 1
    depts_ok = dept_count >= 1

    users_pct = 100 if users_ok else 0
    depts_pct = 100 if depts_ok else 0

    total = int(users_pct * 0.50 + depts_pct * 0.50)
    return total, {"users": users_ok, "departments": depts_ok}


async def _calc_integracoes(repo: SettingsProgressRepository, company_uuid) -> tuple[int, dict]:
    if not company_uuid:
        return 0, {"integrations_active": False}

    int_count = await repo.count_active_integrations(company_uuid)
    int_ok = int_count >= 1
    int_pct = 100 if int_ok else 0

    return int_pct, {"integrations_active": int_ok}


@router.get("/progress", response_model=None)
async def get_settings_progress(
    company_id: str = Query(default=None, description="Company ID (uses default company if not provided)"),
    db: AsyncSession = Depends(get_db)
) -> dict[str, Any]:
    try:
        repo = SettingsProgressRepository(db)
        company = await repo.get_default_company()
        company_uuid = company.id if company else None

        async def _safe(coro, default):
            try:
                async with db.begin_nested():
                    return await coro
            except Exception as exc:
                logger.warning("settings_progress section failed: %s", exc)
                return default

        me_score, me_subs = await _safe(
            _calc_minha_empresa(repo, company, company_uuid),
            (0, {"company_data": False, "culture": False, "tech_stack": False, "benefits": False, "policies": False, "workforce": False}),
        )
        pipe_score, pipe_subs = await _safe(_calc_pipeline(repo, company_uuid), (0, {"stages": False, "slas": False}))
        scr_score, scr_subs = await _safe(_calc_screening(repo, company_uuid), (0, {"questions": False}))
        tmpl_score, tmpl_subs = await _safe(_calc_templates_assinatura(repo, company_uuid), (0, {"templates": False, "signature": False}))
        comm_score, comm_subs = await _safe(_calc_comunicacao_alertas(repo, company_uuid), (0, {"alerts": False, "lgpd_schedule": False}))
        usr_score, usr_subs = await _safe(_calc_usuarios_departamentos(repo, company_uuid), (0, {"users": False, "departments": False}))
        intg_score, intg_subs = await _safe(_calc_integracoes(repo, company_uuid), (0, {"integrations_active": False}))

        overall = int(
            me_score * 0.25 +
            pipe_score * 0.20 +
            scr_score * 0.15 +
            tmpl_score * 0.10 +
            comm_score * 0.10 +
            usr_score * 0.10 +
            intg_score * 0.10
        )

        all_subs = {}
        for sub_dict in [me_subs, pipe_subs, scr_subs, tmpl_subs, comm_subs, usr_subs, intg_subs]:
            all_subs.update(sub_dict)

        return {
            "overall": overall,
            "sections": {
                "minha-empresa": me_score,
                "pipeline": pipe_score,
                "screening": scr_score,
                "templates-assinatura": tmpl_score,
                "comunicacao-alertas": comm_score,
                "usuarios-departamentos": usr_score,
                "integracoes": intg_score,
            },
            "subsections": all_subs,
            "details": {
                "company_id": str(company_uuid) if company_uuid else None,
                "company_name": company.name if company else None,
                "scores": {
                    "minha_empresa": me_score,
                    "pipeline": pipe_score,
                    "screening": scr_score,
                    "templates_assinatura": tmpl_score,
                    "comunicacao_alertas": comm_score,
                    "usuarios_departamentos": usr_score,
                    "integracoes": intg_score,
                },
            },
        }

    except Exception as e:
        logger.error(f"Error calculating settings progress: {e}")
        return {
            "overall": 0,
            "sections": {
                "minha-empresa": 0,
                "pipeline": 0,
                "screening": 0,
                "templates-assinatura": 0,
                "comunicacao-alertas": 0,
                "usuarios-departamentos": 0,
                "integracoes": 0,
            },
            "subsections": {},
            "error": True,
            "error_message": str(e),
        }

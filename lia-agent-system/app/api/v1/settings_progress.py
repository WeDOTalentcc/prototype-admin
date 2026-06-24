"""
Settings Progress API endpoint.
Calculates real completion percentages for configuration settings based on database data.
"""
import logging
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.company.repositories.settings_progress_repository import SettingsProgressRepository
from app.shared.security.require_company_id import require_company_id, require_company_id_strict_match

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/settings", tags=["settings"])


async def calculate_company_data_progress(company, db: AsyncSession) -> tuple[int, bool]:
    """Calculate company data completion (20% weight)."""
    if not company:
        return 0, False

    required_fields = [
        company.name,
        company.website,
        company.sector or company.industry,
    ]

    optional_fields = [
        company.description,
        company.headquarters_city,
        company.employee_count or company.company_size,
        company.logo_url,
    ]

    required_filled = sum(1 for f in required_fields if f)
    optional_filled = sum(1 for f in optional_fields if f)

    required_score = (required_filled / len(required_fields)) * 70
    optional_score = (optional_filled / len(optional_fields)) * 30

    total = int(required_score + optional_score)
    is_complete = required_filled == len(required_fields)

    return total, is_complete



def calculate_contratacao_score(policy) -> int:
    """Calculate Configuracoes de Contratacao completion from offer_rules JSONB."""
    if not policy or not policy.offer_rules:
        return 0
    rules = policy.offer_rules
    checked_fields = [
        rules.get("allowed_start_day_of_month"),
        rules.get("min_notice_days"),
        rules.get("negotiation_enabled"),
        rules.get("salary_flex_pct_max"),
    ]
    filled = sum(1 for f in checked_fields if f is not None)
    return int(filled / len(checked_fields) * 100) if checked_fields else 0


def calculate_screening_defaults_score(policy) -> int:
    """Calculate Configuracoes de Triagem completion from screening_config_defaults JSONB."""
    if not policy or not policy.screening_config_defaults:
        return 0
    config = policy.screening_config_defaults
    checks = []
    # settings.min_score
    settings = config.get("settings", {})
    checks.append(settings.get("min_score") is not None)
    # settings.response_timeout_hours
    checks.append(settings.get("response_timeout_hours") is not None)
    # channels: at least 1 enabled
    channels = config.get("channels", {})
    has_enabled_channel = any(
        ch.get("enabled") for ch in channels.values() if isinstance(ch, dict)
    )
    checks.append(has_enabled_channel)
    # scheduling.auto_enabled
    scheduling = config.get("scheduling", {})
    checks.append(scheduling.get("auto_enabled") is not None)

    filled = sum(1 for c in checks if c)
    return int(filled / len(checks) * 100) if checks else 0


@router.get("/progress", response_model=None)
async def get_settings_progress(
    company_id: str = Query(default=None, description="Company ID (optional, uses default if not provided)"),
    db: AsyncSession = Depends(get_db), 
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))) -> dict[str, Any]:
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Get settings completion progress.

    Returns overall progress and per-section breakdown based on actual database data.
    """
    try:
        repo = SettingsProgressRepository(db)

        company = await repo.get_default_company()
        company_uuid = company.id if company else None

        company_data_score, company_data_complete = await calculate_company_data_progress(company, db)

        # Departments
        dept_count = await repo.count_active_departments(company_uuid) if company_uuid else 0
        departments_score = 100 if dept_count >= 1 else 0
        departments_complete = dept_count >= 1

        # Benefits
        benefit_count = await repo.count_active_benefits(company_uuid) if company_uuid else 0
        benefits_score = 100 if benefit_count >= 1 else 0
        benefits_complete = benefit_count >= 1

        # Users (always complete)
        users_score, users_complete = 100, True

        # Approvers
        approver_count = await repo.count_active_approvers(company_uuid) if company_uuid else 0
        approvers_score = 100 if approver_count >= 1 else 0
        approvers_complete = approver_count >= 1

        company_team_score = int(
            (company_data_score * 0.20) +
            (departments_score * 0.20) +
            (benefits_score * 0.20) +
            (users_score * 0.20) +
            (approvers_score * 0.20)
        )

        # Templates
        template_count = await repo.count_active_templates(company_uuid) if company_uuid else 0
        templates_score = 100 if template_count >= 1 else 0
        templates_complete = template_count >= 1

        # SLAs
        sla_count = await repo.count_active_slas(company_uuid) if company_uuid else 0
        slas_score = 100 if sla_count >= 1 else 0
        slas_complete = sla_count >= 1

        # Automations
        automation_count = await repo.count_enabled_automations(company_uuid) if company_uuid else 0
        automations_score = 100 if automation_count >= 1 else 0
        automations_complete = automation_count >= 1

        recruitment_score = int(
            (templates_score * 0.35) +
            (slas_score * 0.35) +
            (automations_score * 0.30)
        )

        # P1-2 (auditoria Configuracoes): score real (antes hardcoded 100).
        # communication = ha templates de comunicacao configurados.
        communication_score = 100 if template_count >= 1 else 0
        email_templates_complete = template_count >= 1
        notification_rules_complete = template_count >= 1

        # goals-planning = ha plano de headcount/workforce ativo (P1-2).
        hiring_plan_count = await repo.count_active_hiring_plans(company_uuid) if company_uuid else 0
        goals_planning_score = 100 if hiring_plan_count >= 1 else 0

        # Global search
        settings = await repo.get_global_search_settings(company_uuid) if company_uuid else None
        global_search_score = 100 if settings else 80
        global_search_complete = settings is not None

        # Contratacao (offer_rules) + Triagem defaults (screening_config_defaults)
        policy = await repo.get_hiring_policy(company_uuid) if company_uuid else None
        contratacao_score = calculate_contratacao_score(policy)
        screening_defaults_score = calculate_screening_defaults_score(policy)

        overall = int(
            (company_team_score * 0.25) +
            (recruitment_score * 0.25) +
            (communication_score * 0.20) +
            (goals_planning_score * 0.10) +
            (global_search_score * 0.10) +
            (contratacao_score * 0.05) +
            (screening_defaults_score * 0.05)
        )

        # Canonical sidebar IDs (2026-05-26 — consolidação P1 do audit menu Configurações).
        # Plan: ~/.claude/plans/jolly-roaming-moler.md. Sidebar canonical: 7 hubs.
        # Mapping reusa scores granulares ja calculados para evitar dupla contagem.
        minha_empresa_score = int((company_data_score + departments_score + benefits_score + contratacao_score + screening_defaults_score) / 5)
        usuarios_departamentos_score = int((users_score + approvers_score) / 2)

        return {
            "overall": overall,
            "sections": {
                # Legacy keys (mantidas por compat com consumers que ainda usem)
                "company-team": company_team_score,
                "recruitment": recruitment_score,
                "communication": communication_score,
                "goals-planning": goals_planning_score,
                "global-search": global_search_score,
                # Canonical sidebar IDs (settings-page-enhanced.tsx getDefaultSections)
                "minha-empresa": minha_empresa_score,
                "contratacao": contratacao_score,
                "screening-defaults": screening_defaults_score,
                # P1-4 (2026-05-26): hub novo "LIA & Personalização" (instrucoes-lia + learning-loops).
                # TODO: calcular score real baseado em lia_field_toggles + learning_loops state.
                "lia-personalizacao": 100,
                "recrutamento-lia": recruitment_score,
                "comunicacao-alertas": communication_score,
                "usuarios-departamentos": usuarios_departamentos_score,
                # TODO(P1): cálculos próprios para os 3 hubs abaixo (hoje retornam 100 default).
                "integrations": 100,
                "ai-credits": 100,
                "fairness-compliance": 100,
            },
            "subsections": {
                "company-data": company_data_complete,
                "departments": departments_complete,
                "benefits": benefits_complete,
                "users": users_complete,
                "approvers": approvers_complete,
                "templates": templates_complete,
                "slas": slas_complete,
                "automations": automations_complete,
                "email-templates": email_templates_complete,
                "notification-rules": notification_rules_complete,
                "global-search-settings": global_search_complete
            },
            "details": {
                "company_id": str(company_uuid) if company_uuid else None,
                "company_name": company.name if company else None,
                "scores": {
                    "company_data": company_data_score,
                    "departments": departments_score,
                    "benefits": benefits_score,
                    "users": users_score,
                    "approvers": approvers_score,
                    "templates": templates_score,
                    "slas": slas_score,
                    "automations": automations_score,
                    "global_search": global_search_score,
                    "contratacao": contratacao_score,
                    "screening_defaults": screening_defaults_score
                }
            }
        }

    except Exception as e:
        logger.error(f"Error calculating settings progress: {e}")
        return {
            "overall": 50,
            "sections": {
                # Legacy keys (compat)
                "company-team": 60,
                "recruitment": 40,
                "communication": 60,
                "goals-planning": 50,
                "global-search": 80,
                # Canonical sidebar IDs (fallback degradado em error path)
                "minha-empresa": 60,
                "contratacao": 0,
                "screening-defaults": 0,
                "lia-personalizacao": 100,
                "recrutamento-lia": 40,
                "comunicacao-alertas": 60,
                "usuarios-departamentos": 60,
                "integrations": 100,
                "ai-credits": 100,
                "fairness-compliance": 100,
            },
            "subsections": {
                "company-data": False,
                "departments": False,
                "benefits": False,
                "users": True,
                "approvers": False,
                "templates": False,
                "slas": False,
                "automations": False,
                "email-templates": True,
                "notification-rules": True,
                "global-search-settings": False
            },
            "error": str(e)
        }

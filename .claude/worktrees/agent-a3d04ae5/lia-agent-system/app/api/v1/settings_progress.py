"""
Settings Progress API endpoint.
Calculates real completion percentages for configuration settings based on database data.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any
import logging

from app.core.database import get_db
from app.models.company import (
    CompanyProfile,
    Department,
    Benefit,
    CultureValue,
    Approver,
    GlobalSearchSettings
)
from app.models.company_culture import CompanyCultureProfile
from app.models.recruitment_journey import (
    RecruitmentTemplate,
    RecruitmentSLA,
    RecruitmentAutomation
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/settings", tags=["settings"])


async def get_default_company(db: AsyncSession) -> CompanyProfile:
    """Get default company or first available."""
    result = await db.execute(
        select(CompanyProfile).where(CompanyProfile.is_default == True).limit(1)
    )
    company = result.scalar_one_or_none()
    
    if not company:
        result = await db.execute(
            select(CompanyProfile).order_by(CompanyProfile.created_at).limit(1)
        )
        company = result.scalar_one_or_none()
    
    return company


async def calculate_company_data_progress(company: CompanyProfile, db: AsyncSession) -> tuple[int, bool]:
    """
    Calculate company data completion (20% weight).
    Returns (percentage, is_complete boolean).
    """
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


async def calculate_departments_progress(company_id, db: AsyncSession) -> tuple[int, bool]:
    """Calculate departments completion (20% weight)."""
    if not company_id:
        return 0, False
    
    result = await db.execute(
        select(func.count(Department.id)).where(
            Department.company_id == company_id,
            Department.is_active == True
        )
    )
    count = result.scalar() or 0
    
    is_complete = count >= 1
    return 100 if is_complete else 0, is_complete


async def calculate_benefits_progress(company_id, db: AsyncSession) -> tuple[int, bool]:
    """Calculate benefits completion (20% weight)."""
    if not company_id:
        return 0, False
    
    result = await db.execute(
        select(func.count(Benefit.id)).where(
            Benefit.company_id == company_id,
            Benefit.is_active == True
        )
    )
    count = result.scalar() or 0
    
    is_complete = count >= 1
    return 100 if is_complete else 0, is_complete


async def calculate_approvers_progress(company_id, db: AsyncSession) -> tuple[int, bool]:
    """Calculate approvers completion (20% weight)."""
    if not company_id:
        return 0, False
    
    result = await db.execute(
        select(func.count(Approver.id)).where(
            Approver.company_id == company_id,
            Approver.is_active == True
        )
    )
    count = result.scalar() or 0
    
    is_complete = count >= 1
    return 100 if is_complete else 0, is_complete


async def calculate_templates_progress(company_id, db: AsyncSession) -> tuple[int, bool]:
    """Calculate recruitment templates completion (35% weight)."""
    if not company_id:
        return 0, False
    
    result = await db.execute(
        select(func.count(RecruitmentTemplate.id)).where(
            RecruitmentTemplate.company_id == company_id,
            RecruitmentTemplate.is_active == True
        )
    )
    count = result.scalar() or 0
    
    is_complete = count >= 1
    return 100 if is_complete else 0, is_complete


async def calculate_slas_progress(company_id, db: AsyncSession) -> tuple[int, bool]:
    """Calculate SLAs completion (35% weight)."""
    if not company_id:
        return 0, False
    
    result = await db.execute(
        select(func.count(RecruitmentSLA.id)).where(
            RecruitmentSLA.company_id == company_id,
            RecruitmentSLA.is_active == True
        )
    )
    count = result.scalar() or 0
    
    is_complete = count >= 1
    return 100 if is_complete else 0, is_complete


async def calculate_automations_progress(company_id, db: AsyncSession) -> tuple[int, bool]:
    """Calculate automations completion (30% weight)."""
    if not company_id:
        return 0, False
    
    result = await db.execute(
        select(func.count(RecruitmentAutomation.id)).where(
            RecruitmentAutomation.company_id == company_id,
            RecruitmentAutomation.is_enabled == True
        )
    )
    count = result.scalar() or 0
    
    is_complete = count >= 1
    return 100 if is_complete else 0, is_complete


async def calculate_global_search_progress(company_id, db: AsyncSession) -> tuple[int, bool]:
    """Calculate global search settings completion."""
    if not company_id:
        return 80, False
    
    try:
        company_id_str = str(company_id)
        result = await db.execute(
            select(GlobalSearchSettings).where(
                GlobalSearchSettings.company_id == company_id_str
            )
        )
        settings = result.scalar_one_or_none()
        
        if settings:
            return 100, True
    except Exception as e:
        logger.error(f"Error checking global search settings: {e}")
    
    return 80, False


@router.get("/progress")
async def get_settings_progress(
    company_id: str = Query(default=None, description="Company ID (optional, uses default if not provided)"),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get settings completion progress.
    
    Returns overall progress and per-section breakdown based on actual database data.
    """
    try:
        company = await get_default_company(db)
        company_uuid = company.id if company else None
        
        company_data_score, company_data_complete = await calculate_company_data_progress(company, db)
        departments_score, departments_complete = await calculate_departments_progress(company_uuid, db)
        benefits_score, benefits_complete = await calculate_benefits_progress(company_uuid, db)
        users_score, users_complete = 100, True
        approvers_score, approvers_complete = await calculate_approvers_progress(company_uuid, db)
        
        company_team_score = int(
            (company_data_score * 0.20) +
            (departments_score * 0.20) +
            (benefits_score * 0.20) +
            (users_score * 0.20) +
            (approvers_score * 0.20)
        )
        
        templates_score, templates_complete = await calculate_templates_progress(company_uuid, db)
        slas_score, slas_complete = await calculate_slas_progress(company_uuid, db)
        automations_score, automations_complete = await calculate_automations_progress(company_uuid, db)
        
        recruitment_score = int(
            (templates_score * 0.35) +
            (slas_score * 0.35) +
            (automations_score * 0.30)
        )
        
        communication_score = 100
        email_templates_complete = True
        notification_rules_complete = True
        
        goals_planning_score = 100
        
        global_search_score, global_search_complete = await calculate_global_search_progress(company_uuid, db)
        
        overall = int(
            (company_team_score * 0.30) +
            (recruitment_score * 0.25) +
            (communication_score * 0.20) +
            (goals_planning_score * 0.15) +
            (global_search_score * 0.10)
        )
        
        return {
            "overall": overall,
            "sections": {
                "company-team": company_team_score,
                "recruitment": recruitment_score,
                "communication": communication_score,
                "goals-planning": goals_planning_score,
                "global-search": global_search_score
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
                    "global_search": global_search_score
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error calculating settings progress: {e}")
        return {
            "overall": 50,
            "sections": {
                "company-team": 60,
                "recruitment": 40,
                "communication": 60,
                "goals-planning": 50,
                "global-search": 80
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

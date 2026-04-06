"""
Company Setup API endpoints for admin configuration.
Manages company profiles, departments, benefits, culture values, and ideal profiles.
"""
import csv
import io
import logging
import os
import uuid
from datetime import datetime
from typing import Any, Optional

import httpx
from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user_or_demo
from app.auth.models import User
from app.auth.schemas import UserManagementCreate, UserManagementResponse, UserManagementUpdate
from app.auth.security import generate_secure_token, get_password_hash
from app.core.database import get_db
from app.domains.communication.services.email_service import email_service
from app.domains.company.dependencies import (
    get_approver_repo,
    get_benefit_repo,
    get_big_five_repo,
    get_company_profile_repo,
    get_culture_value_repo,
    get_department_repo,
    get_global_settings_repo,
    get_ideal_profile_repo,
    get_technical_test_repo,
)
from app.domains.company.repositories.approver_repository import ApproverRepository
from app.domains.company.repositories.benefit_repository import BenefitRepository
from app.domains.company.repositories.big_five_repository import BigFiveRepository
from app.domains.company.repositories.company_profile_repository import CompanyProfileRepository
from app.domains.company.repositories.culture_value_repository import CultureValueRepository
from app.domains.company.repositories.department_repository import DepartmentRepository
from app.domains.company.repositories.global_settings_repository import GlobalSettingsRepository
from app.domains.company.repositories.ideal_profile_repository import IdealProfileRepository
from app.domains.company.repositories.technical_test_repository import TechnicalTestRepository
from app.domains.sourcing.services.apify_service import apify_service
from app.models.company import (
    Approver,
    Benefit,
    BigFiveQuestion,
    BigFiveRoleProfile,
    CompanyProfile,
    CultureValue,
    Department,
    DepartmentMember,
    GlobalSearchSettings,
    IdealProfile,
    TechnicalQuestion,
    TechnicalTestTemplate,
)
from app.models.company_culture import CompanyCultureProfile
from app.models.job_vacancy import JobVacancy
from app.schemas.company import (
    ApproverCreate,
    ApproverResponse,
    ApproverUpdate,
    BenefitCreate,
    BenefitResponse,
    BenefitUpdate,
    BigFiveQuestionCreate,
    BigFiveQuestionResponse,
    BigFiveQuestionUpdate,
    BigFiveRoleProfileCreate,
    BigFiveRoleProfileResponse,
    BigFiveRoleProfileUpdate,
    CompanyProfileCreate,
    CompanyProfileResponse,
    CompanyProfileUpdate,
    CompanyProfileWithRelations,
    CultureAnalysisRequest,
    CultureAnalysisResponse,
    CultureValueCreate,
    CultureValueResponse,
    CultureValueUpdate,
    DepartmentCreate,
    DepartmentMemberCreate,
    DepartmentMemberResponse,
    DepartmentMemberUpdate,
    DepartmentResponse,
    DepartmentUpdate,
    GlobalSearchSettingsResponse,
    GlobalSearchSettingsUpdate,
    IdealProfileCreate,
    IdealProfileResponse,
    IdealProfileUpdate,
    TechnicalQuestionCreate,
    TechnicalQuestionResponse,
    TechnicalQuestionUpdate,
    TechnicalTestTemplateCreate,
    TechnicalTestTemplateResponse,
    TechnicalTestTemplateUpdate,
)
from app.services.company_configuration_service import company_config_service
from app.services.llm import llm_service

FRONTEND_URL = os.getenv("FRONTEND_URL", "https://plataforma-lia.replit.app")
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/company", tags=["company"])


from app.auth.workos_models import CompanyWorkOSConfig
from app.models.client_account import ClientAccount


class TenantResolutionResponse(BaseModel):
    client_account_id: str | None = None
    company_profile_id: str | None = None
    company_name: str | None = None
    plan_id: str | None = None
    status: str | None = None


@router.get("/resolve-tenant", response_model=TenantResolutionResponse)
async def resolve_tenant(
    workos_organization_id: str | None = Query(None),
    client_account_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_or_demo)
):
    """Resolve tenant IDs from WorkOS organization ID or client account ID."""
    try:
        resolved_client_id = client_account_id

        if not resolved_client_id and current_user and hasattr(current_user, 'company_id') and current_user.company_id:
            resolved_client_id = str(current_user.company_id)

        if workos_organization_id and not resolved_client_id:
            config_result = await db.execute(
                select(CompanyWorkOSConfig).where(
                    CompanyWorkOSConfig.workos_organization_id == workos_organization_id
                )
            )
            config = config_result.scalars().first()
            if config:
                resolved_client_id = config.company_id

        if not resolved_client_id:
            raise HTTPException(status_code=404, detail="No tenant found for the given identifiers")

        if current_user and hasattr(current_user, 'company_id') and current_user.company_id:
            user_company = str(current_user.company_id)
            if client_account_id and client_account_id != user_company:
                logger.warning(f"Cross-tenant access attempt: user {current_user.email} (company={user_company}) tried to resolve tenant {client_account_id}")
                raise HTTPException(status_code=403, detail="Access denied: cross-tenant resolution not allowed")

        client_result = await db.execute(
            select(ClientAccount).where(ClientAccount.id == resolved_client_id)
        )
        client = client_result.scalars().first()

        profile_result = await db.execute(
            select(CompanyProfile).where(CompanyProfile.client_account_id == resolved_client_id)
        )
        profile = profile_result.scalars().first()

        return TenantResolutionResponse(
            client_account_id=str(resolved_client_id) if resolved_client_id else None,
            company_profile_id=str(profile.id) if profile else None,
            company_name=client.name if client else (profile.name if profile else None),
            plan_id=str(client.plan_id) if client and client.plan_id else None,
            status=client.status if client else None,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving tenant: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class CompanyEnrichRequest(BaseModel):
    linkedin_url: str | None = None
    glassdoor_company_name: str | None = None


class CompanyEnrichResponse(BaseModel):
    success: bool
    linkedin_data: dict[str, Any] = {}
    glassdoor_data: dict[str, Any] = {}
    enriched_culture: dict[str, Any] = {}
    errors: list[str] = []


class OnboardingCultureProfile(BaseModel):
    mission: str | None = None
    vision: str | None = None
    values: list[str] | None = None
    evp_bullets: list[str] | None = None
    openness_score: int | None = None
    conscientiousness_score: int | None = None
    extraversion_score: int | None = None
    agreeableness_score: int | None = None
    stability_score: int | None = None


class OnboardingData(BaseModel):
    company_id: str | None = None
    company_name: str
    trade_name: str | None = None
    cnpj: str | None = None
    address: str | None = None
    work_model: str | None = None
    logo_url: str | None = None
    sector: str | None = None
    employee_count: str | None = None
    website: str | None = None
    linkedin_url: str | None = None
    hiring_volume: int | None = None
    job_types: list[str] | None = None
    current_ats: str | None = None
    main_challenges: list[str] | None = None
    main_priority: str | None = None
    platform_expectations: str | None = None
    communication_channels: list[str] | None = None
    allow_lia_contact: bool = True
    additional_notes: str | None = None
    responsible_name: str | None = None
    responsible_email: str | None = None
    responsible_phone: str | None = None
    responsible_position: str | None = None
    preferred_contact_time: str | None = None
    culture_profile: OnboardingCultureProfile | None = None


@router.post("/onboarding", response_model=None)
async def submit_onboarding(
    data: OnboardingData,
    profile_repo: CompanyProfileRepository = Depends(get_company_profile_repo),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit onboarding data from the wizard.
    Creates or updates company profile with the provided information.
    """
    try:
        logger.info(f"Received onboarding data for company: {data.company_name}")

        profile = None

        if data.company_id:
            try:
                company_uuid = uuid.UUID(data.company_id)
                profile = await profile_repo.get_by_id(company_uuid)
                if profile:
                    logger.info(f"Found company profile by ID: {data.company_id}")
            except ValueError:
                logger.warning(f"Invalid company_id format: {data.company_id}")

        if not profile:
            profile = await profile_repo.get_default()
            if profile:
                logger.info(f"Found default company profile: {profile.name}")

        onboarding_metadata = {
            "hiring_volume": data.hiring_volume,
            "job_types": data.job_types,
            "current_ats": data.current_ats,
            "main_challenges": data.main_challenges,
            "main_priority": data.main_priority,
            "platform_expectations": data.platform_expectations,
            "communication_channels": data.communication_channels,
            "allow_lia_contact": data.allow_lia_contact,
            "additional_notes": data.additional_notes,
            "responsible_name": data.responsible_name,
            "responsible_email": data.responsible_email,
            "responsible_phone": data.responsible_phone,
            "responsible_position": data.responsible_position,
            "preferred_contact_time": data.preferred_contact_time,
            "work_model": data.work_model,
            "onboarding_completed_at": datetime.utcnow().isoformat()
        }

        if profile:
            update_data = {
                "name": data.company_name,
                "trading_name": data.trade_name,
                "cnpj": data.cnpj,
                "address": data.address,
                "industry": data.sector,
                "company_size": data.employee_count,
                "website": data.website,
                "linkedin_url": data.linkedin_url,
                "logo_url": data.logo_url,
                "hr_email": data.responsible_email,
                "hr_phone": data.responsible_phone,
                "updated_at": datetime.utcnow(),
                "additional_data": {**(profile.additional_data or {}), **onboarding_metadata},
            }
            profile = await profile_repo.update(profile.id, update_data)
            logger.info(f"Updated existing company profile: {data.company_name}")
        else:
            create_data = {
                "name": data.company_name,
                "trading_name": data.trade_name,
                "cnpj": data.cnpj,
                "address": data.address,
                "industry": data.sector,
                "company_size": data.employee_count,
                "website": data.website,
                "linkedin_url": data.linkedin_url,
                "logo_url": data.logo_url,
                "hr_email": data.responsible_email,
                "hr_phone": data.responsible_phone,
                "is_default": True,
                "additional_data": onboarding_metadata,
            }
            profile = await profile_repo.create(create_data, set_default=False)
            logger.info(f"Created new company profile: {data.company_name}")

        if data.culture_profile:
            cp = data.culture_profile
            existing_culture = await db.execute(
                select(CompanyCultureProfile).where(
                    CompanyCultureProfile.company_id == profile.id
                )
            )
            culture_profile = existing_culture.scalar_one_or_none()

            if culture_profile:
                culture_profile.mission = cp.mission
                culture_profile.vision = cp.vision
                culture_profile.values = cp.values or []
                culture_profile.evp_bullets = cp.evp_bullets or []
                culture_profile.openness_score = cp.openness_score or 50
                culture_profile.conscientiousness_score = cp.conscientiousness_score or 50
                culture_profile.extraversion_score = cp.extraversion_score or 50
                culture_profile.agreeableness_score = cp.agreeableness_score or 50
                culture_profile.stability_score = cp.stability_score or 50
                culture_profile.source = "onboarding"
                culture_profile.website_url = data.website
                culture_profile.updated_at = datetime.utcnow()
                logger.info(f"Updated culture profile for company: {data.company_name}")
            else:
                culture_profile = CompanyCultureProfile(
                    company_id=profile.id,
                    mission=cp.mission,
                    vision=cp.vision,
                    values=cp.values or [],
                    evp_bullets=cp.evp_bullets or [],
                    openness_score=cp.openness_score or 50,
                    conscientiousness_score=cp.conscientiousness_score or 50,
                    extraversion_score=cp.extraversion_score or 50,
                    agreeableness_score=cp.agreeableness_score or 50,
                    stability_score=cp.stability_score or 50,
                    source="onboarding",
                    website_url=data.website
                )
                db.add(culture_profile)
                logger.info(f"Created culture profile for company: {data.company_name}")

            await db.commit()

        return {
            "success": True,
            "message": "Onboarding data received successfully",
            "company_id": str(profile.id),
            "company_name": profile.name
        }
    except Exception as e:
        await db.rollback()
        logger.error(f"Error processing onboarding data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

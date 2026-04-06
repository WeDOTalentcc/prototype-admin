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


@router.post("/enrich", response_model=CompanyEnrichResponse)
async def enrich_company_profile(
    data: CompanyEnrichRequest,
):
    """Enrich company profile with LinkedIn and Glassdoor data via Apify actors."""
    errors = []
    linkedin_data = {}
    glassdoor_data = {}
    enriched_culture = {}

    if not data.linkedin_url and not data.glassdoor_company_name:
        raise HTTPException(status_code=400, detail="At least one of linkedin_url or glassdoor_company_name must be provided")

    try:
        if data.linkedin_url:
            logger.info(f"Enriching from LinkedIn: {data.linkedin_url}")
            linkedin_data = await apify_service.scrape_linkedin_company(data.linkedin_url)
            if not linkedin_data:
                errors.append("Failed to fetch LinkedIn data or no data found")

        if data.glassdoor_company_name:
            logger.info(f"Enriching from Glassdoor: {data.glassdoor_company_name}")
            glassdoor_data = await apify_service.scrape_glassdoor_company(data.glassdoor_company_name)
            if not glassdoor_data:
                errors.append("Failed to fetch Glassdoor data or no data found")

        if linkedin_data.get("description"):
            enriched_culture["company_description"] = linkedin_data["description"]
        if linkedin_data.get("tagline"):
            enriched_culture["tagline"] = linkedin_data["tagline"]
        if linkedin_data.get("specialties"):
            enriched_culture["specialties"] = linkedin_data["specialties"]
        if glassdoor_data.get("mission"):
            enriched_culture["mission"] = glassdoor_data["mission"]
        if glassdoor_data.get("overview"):
            enriched_culture["vision"] = glassdoor_data["overview"]
        if glassdoor_data.get("employee_pros"):
            enriched_culture["culture_highlights"] = glassdoor_data["employee_pros"]
        if glassdoor_data.get("culture_rating"):
            enriched_culture["culture_rating"] = glassdoor_data["culture_rating"]
        if glassdoor_data.get("overall_rating"):
            enriched_culture["overall_rating"] = glassdoor_data["overall_rating"]
        if glassdoor_data.get("work_life_balance"):
            enriched_culture["work_life_balance"] = glassdoor_data["work_life_balance"]

        return CompanyEnrichResponse(
            success=bool(linkedin_data or glassdoor_data),
            linkedin_data=linkedin_data,
            glassdoor_data=glassdoor_data,
            enriched_culture=enriched_culture,
            errors=errors,
        )
    except Exception as e:
        logger.error(f"Error enriching company profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class AutoEnrichResponse(BaseModel):
    success: bool
    fields_updated: list[str] = []
    apify_data: dict[str, Any] = {}
    inferred_data: dict[str, Any] = {}
    errors: list[str] = []


@router.post("/auto-enrich/{profile_id}", response_model=AutoEnrichResponse)
async def auto_enrich_company(
    profile_id: uuid.UUID,
    profile_repo: CompanyProfileRepository = Depends(get_company_profile_repo),
    db: AsyncSession = Depends(get_db),
):
    """Automatically enrich company profile after wizard submission."""
    errors = []
    fields_updated = []
    apify_data = {}
    inferred_data = {}

    try:
        profile = await profile_repo.get_by_id(profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Company profile not found")

        culture_result = await db.execute(
            select(CompanyCultureProfile).where(CompanyCultureProfile.company_id == profile_id)
        )
        culture_profile = culture_result.scalar_one_or_none()

        linkedin_data = {}
        glassdoor_data = {}

        if profile.linkedin_url or (profile.additional_data and profile.additional_data.get("linkedin_url")):
            linkedin_url = profile.linkedin_url or profile.additional_data.get("linkedin_url")
            try:
                logger.info(f"Auto-enriching from LinkedIn: {linkedin_url}")
                linkedin_data = await apify_service.scrape_linkedin_company(linkedin_url)
                apify_data["linkedin"] = linkedin_data
            except Exception as e:
                errors.append(f"LinkedIn enrichment failed: {str(e)}")

        if profile.name:
            try:
                logger.info(f"Auto-enriching from Glassdoor: {profile.name}")
                glassdoor_data = await apify_service.scrape_glassdoor_company(profile.name)
                apify_data["glassdoor"] = glassdoor_data
            except Exception as e:
                errors.append(f"Glassdoor enrichment failed: {str(e)}")

        profile_updates = {}

        if linkedin_data:
            if linkedin_data.get("headquarters") and not profile.headquarters_city:
                hq = linkedin_data["headquarters"]
                if isinstance(hq, dict):
                    profile_updates["headquarters_city"] = hq.get("city", "")
                    profile_updates["headquarters_state"] = hq.get("state", "")
                    profile_updates["headquarters_country"] = hq.get("country", "Brasil")
                elif isinstance(hq, str):
                    parts = hq.split(",")
                    if len(parts) >= 2:
                        profile_updates["headquarters_city"] = parts[0].strip()
                        profile_updates["headquarters_state"] = parts[1].strip()
                fields_updated.append("headquarters")

            if linkedin_data.get("founded") and not profile.founded_year:
                try:
                    profile_updates["founded_year"] = int(linkedin_data["founded"])
                    fields_updated.append("founded_year")
                except (ValueError, TypeError):
                    pass

            if linkedin_data.get("company_size") and not profile.employee_count:
                size_str = linkedin_data["company_size"]
                try:
                    if "-" in str(size_str):
                        nums = str(size_str).replace(",", "").replace("+", "").split("-")
                        profile_updates["employee_count"] = int(nums[1]) if len(nums) > 1 else int(nums[0])
                    else:
                        profile_updates["employee_count"] = int(str(size_str).replace(",", "").replace("+", ""))
                    fields_updated.append("employee_count")
                except (ValueError, TypeError):
                    pass

            if linkedin_data.get("description"):
                if not profile.description:
                    profile_updates["description"] = linkedin_data["description"]
                    fields_updated.append("description")
                if culture_profile and not culture_profile.culture_description:
                    culture_profile.culture_description = linkedin_data["description"]

        company_context = {
            "name": profile.name,
            "industry": profile.industry,
            "description": profile.description or linkedin_data.get("description", ""),
            "size": profile.company_size,
            "glassdoor_pros": glassdoor_data.get("employee_pros", []),
            "glassdoor_cons": glassdoor_data.get("employee_cons", []),
            "work_life_balance": glassdoor_data.get("work_life_balance", ""),
            "culture_rating": glassdoor_data.get("culture_rating", ""),
            "mission": culture_profile.mission if culture_profile else "",
            "vision": culture_profile.vision if culture_profile else "",
            "values": culture_profile.values if culture_profile else [],
        }

        if company_context.get("description") or company_context.get("mission"):
            inference_prompt = f"""Você é um especialista em cultura organizacional e employer branding.
Analise os dados da empresa abaixo e infira campos faltantes de forma consistente.

DADOS DISPONÍVEIS:
- Nome: {company_context['name']}
- Setor: {company_context['industry']}
- Descrição: {company_context['description'][:500] if company_context['description'] else 'N/A'}
- Porte: {company_context['size']}
- Missão: {company_context['mission']}
- Visão: {company_context['vision']}
- Valores: {', '.join(company_context['values']) if company_context['values'] else 'N/A'}
- Avaliação cultura (Glassdoor): {company_context['culture_rating']}
- Work-life balance: {company_context['work_life_balance']}
- Pontos positivos (funcionários): {', '.join(company_context['glassdoor_pros'][:3]) if company_context['glassdoor_pros'] else 'N/A'}
- Pontos negativos (funcionários): {', '.join(company_context['glassdoor_cons'][:2]) if company_context['glassdoor_cons'] else 'N/A'}

GERE UM JSON COM OS CAMPOS ABAIXO (baseado nos dados disponíveis, use inferências razoáveis):
{{
  "work_model": "remoto|híbrido|presencial",
  "growth_opportunities": "Descrição breve das oportunidades de crescimento",
  "team_dynamics": "Descrição da dinâmica de trabalho em equipe",
  "leadership_style": "Estilo de liderança predominante",
  "core_competencies": ["competência1", "competência2", "competência3"],
  "diversity_initiatives": "Iniciativas de diversidade e inclusão (se houver indicações)",
  "sustainability": "Práticas de sustentabilidade (se houver indicações)",
  "social_impact": "Impacto social da empresa (se houver indicações)",
  "engineering_culture": "Cultura de engenharia/tecnologia (se aplicável ao setor)"
}}

REGRAS:
1. Use APENAS informações que podem ser inferidas dos dados
2. Se não houver base para inferir, use "Não especificado"
3. Para core_competencies, liste 3-5 competências comportamentais típicas do setor
4. Responda APENAS com o JSON, sem texto adicional"""

            try:
                llm_response = await llm_service.generate(inference_prompt, provider="gemini")
                llm_response = llm_response.strip()
                if llm_response.startswith("```json"):
                    llm_response = llm_response[7:]
                if llm_response.startswith("```"):
                    llm_response = llm_response[3:]
                if llm_response.endswith("```"):
                    llm_response = llm_response[:-3]
                llm_response = llm_response.strip()

                inferred = json.loads(llm_response)
                inferred_data = inferred

                additional = dict(profile.additional_data or {})
                for field in ["work_model", "growth_opportunities", "team_dynamics", "leadership_style",
                              "diversity_initiatives", "sustainability", "social_impact", "engineering_culture"]:
                    if inferred.get(field) and inferred[field] != "Não especificado":
                        additional[field] = inferred[field]
                        fields_updated.append(field)

                profile_updates["additional_data"] = additional

                if culture_profile and inferred.get("core_competencies"):
                    if not culture_profile.core_competencies or len(culture_profile.core_competencies) == 0:
                        culture_profile.core_competencies = inferred["core_competencies"]
                        fields_updated.append("core_competencies")

            except json.JSONDecodeError as e:
                errors.append(f"Failed to parse LLM response: {str(e)}")
            except Exception as e:
                errors.append(f"LLM inference failed: {str(e)}")

        profile_updates["updated_at"] = datetime.utcnow()
        await profile_repo.update(profile_id, profile_updates)

        if culture_profile:
            culture_profile.updated_at = datetime.utcnow()
            await db.commit()

        logger.info(f"Auto-enriched company {profile.name}, updated fields: {fields_updated}")

        return AutoEnrichResponse(
            success=len(fields_updated) > 0,
            fields_updated=fields_updated,
            apify_data=apify_data,
            inferred_data=inferred_data,
            errors=errors,
        )

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in auto-enrich: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profile", response_model=CompanyProfileResponse)
async def get_company_profile(
    company_id: str | None = Query(None),
    profile_repo: CompanyProfileRepository = Depends(get_company_profile_repo),
    current_user = Depends(get_current_user_or_demo),
):
    """Get a company profile by ID, or resolve from authenticated user's tenant."""
    try:
        effective_company_id = company_id if (company_id and company_id not in ("default", "unknown")) else None

        if not effective_company_id and current_user and hasattr(current_user, 'company_id') and current_user.company_id:
            profile = await profile_repo.get_by_client_account(str(current_user.company_id))
            if profile:
                return profile
            logger.warning(f"get_company_profile: no profile linked to user's company_id={current_user.company_id}")
            raise HTTPException(status_code=404, detail="No company profile found for your tenant. Please complete company setup.")

        if not effective_company_id:
            logger.warning("get_company_profile called without company_id and no auth context — rejecting")
            raise HTTPException(status_code=400, detail="company_id is required. Use /api/v1/company/resolve-tenant to obtain your tenant ID.")

        try:
            company_uuid = uuid.UUID(effective_company_id)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid company_id format: {effective_company_id}")

        if current_user and hasattr(current_user, 'company_id') and current_user.company_id:
            user_company = str(current_user.company_id)
            profile = await profile_repo.get_by_id(company_uuid)
            if profile and profile.client_account_id and str(profile.client_account_id) != user_company:
                logger.warning(f"Cross-tenant access denied: user {current_user.email} (company={user_company}) tried to access profile {effective_company_id}")
                raise HTTPException(status_code=403, detail="Access denied: this profile belongs to a different tenant")
            if profile:
                return profile
            raise HTTPException(status_code=404, detail=f"Company profile not found for id: {effective_company_id}")

        profile = await profile_repo.get_by_id(company_uuid)
        if profile:
            return profile
        raise HTTPException(status_code=404, detail=f"Company profile not found for id: {effective_company_id}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching company profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/profile", response_model=CompanyProfileResponse)
async def create_company_profile(
    data: CompanyProfileCreate,
    client_account_id: str | None = Query(None),
    profile_repo: CompanyProfileRepository = Depends(get_company_profile_repo),
    current_user = Depends(get_current_user_or_demo),
):
    """Create a new company profile, optionally linking to a ClientAccount."""
    try:
        profile_data = data.model_dump()
        resolved_client_id = client_account_id
        if not resolved_client_id and current_user and hasattr(current_user, 'company_id') and current_user.company_id:
            resolved_client_id = str(current_user.company_id)
        if resolved_client_id:
            profile_data["client_account_id"] = resolved_client_id

        profile = await profile_repo.create(profile_data)
        logger.info(f"Created company profile: {profile.name} (client_account_id={resolved_client_id})")
        return profile
    except Exception as e:
        logger.error(f"Error creating company profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/profile/{profile_id}", response_model=CompanyProfileResponse)
async def update_company_profile(
    profile_id: uuid.UUID,
    data: CompanyProfileUpdate,
    profile_repo: CompanyProfileRepository = Depends(get_company_profile_repo),
    current_user = Depends(get_current_user_or_demo),
):
    """Update an existing company profile."""
    try:
        update_data = data.model_dump(exclude_unset=True)

        profile = await profile_repo.get_by_id(profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Company profile not found")

        if not profile.client_account_id and current_user and hasattr(current_user, 'company_id') and current_user.company_id:
            update_data["client_account_id"] = str(current_user.company_id)

        update_data["updated_at"] = datetime.utcnow()
        updated = await profile_repo.update(profile_id, update_data)
        logger.info(f"Updated company profile: {updated.name}")
        return updated
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating company profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profile/{profile_id}/full", response_model=CompanyProfileWithRelations)
async def get_company_profile_with_relations(
    profile_id: uuid.UUID,
    profile_repo: CompanyProfileRepository = Depends(get_company_profile_repo),
):
    """Get company profile with all related data (departments, benefits, culture)."""
    try:
        data = await profile_repo.get_with_relations(profile_id)
        if not data:
            raise HTTPException(status_code=404, detail="Company profile not found")

        profile = data["profile"]
        response = CompanyProfileWithRelations.model_validate(profile)
        response.departments = [DepartmentResponse.model_validate(d) for d in data["departments"]]
        response.benefits = [BenefitResponse.model_validate(b) for b in data["benefits"]]
        response.culture_values = [CultureValueResponse.model_validate(c) for c in data["culture_values"]]
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching company profile with relations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class EVPAnalysisResponse(BaseModel):
    success: bool
    evp_analysis: dict[str, Any] | None = None
    error: str | None = None


@router.post("/profile/{profile_id}/generate-evp", response_model=EVPAnalysisResponse)
async def generate_evp(
    profile_id: uuid.UUID,
    profile_repo: CompanyProfileRepository = Depends(get_company_profile_repo),
):
    """Generate EVP (Employee Value Proposition) analysis using LLM."""
    try:
        profile = await profile_repo.get_by_id(profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Company profile not found")

        additional_data = profile.additional_data or {}
        company_info = {
            "name": profile.name,
            "description": profile.description or additional_data.get("company_description", ""),
            "tagline": additional_data.get("tagline", ""),
            "mission": additional_data.get("mission", ""),
            "vision": additional_data.get("vision", ""),
            "values": additional_data.get("values", ""),
            "culture_highlights": additional_data.get("culture_highlights", []),
            "industry": profile.industry or "",
            "company_size": profile.company_size or "",
            "specialties": additional_data.get("specialties", []),
            "work_life_balance": additional_data.get("work_life_balance", ""),
            "culture_rating": additional_data.get("culture_rating", ""),
            "overall_rating": additional_data.get("overall_rating", ""),
        }

        sources = []
        if company_info.get("description") or company_info.get("tagline"):
            sources.append("linkedin")
        if company_info.get("mission") or company_info.get("culture_highlights"):
            sources.append("glassdoor")

        prompt = f"""Você é um especialista em Employer Branding e Employee Value Proposition (EVP).
Analise os dados da empresa abaixo e gere uma análise de EVP estruturada em português brasileiro.

DADOS DA EMPRESA:
- Nome: {company_info['name']}
- Descrição: {company_info['description']}
- Tagline: {company_info['tagline']}
- Missão: {company_info['mission']}
- Visão: {company_info['vision']}
- Valores: {company_info['values']}
- Setor: {company_info['industry']}
- Porte: {company_info['company_size']}
- Especialidades: {', '.join(company_info['specialties']) if isinstance(company_info['specialties'], list) else company_info['specialties']}
- Destaques culturais: {', '.join(company_info['culture_highlights']) if isinstance(company_info['culture_highlights'], list) else company_info['culture_highlights']}
- Rating de cultura: {company_info['culture_rating']}
- Rating geral: {company_info['overall_rating']}
- Work-life balance: {company_info['work_life_balance']}

GERE UMA ANÁLISE EVP NO FORMATO JSON EXATO ABAIXO:
{{
  "statement": "Uma frase de 1-2 sentenças que resume a proposta de valor única da empresa para seus colaboradores",
  "pillars": [
    {{"name": "Nome do Pilar 1", "description": "Descrição detalhada", "evidence": "Evidência concreta"}},
    {{"name": "Nome do Pilar 2", "description": "Descrição detalhada", "evidence": "Evidência concreta"}},
    {{"name": "Nome do Pilar 3", "description": "Descrição detalhada", "evidence": "Evidência concreta"}}
  ],
  "tone_guidance": ["adjetivo1", "adjetivo2", "adjetivo3", "adjetivo4", "adjetivo5"],
  "candidate_promise": "Uma frase clara sobre o que a empresa promete ao candidato"
}}

REGRAS:
1. Baseie-se APENAS nos dados fornecidos
2. Os pilares devem refletir os diferenciais reais da empresa
3. O tone_guidance deve ter 5 adjetivos que guiem a comunicação com candidatos
4. Use linguagem profissional mas acessível
5. Responda APENAS com o JSON, sem texto adicional"""

        logger.info(f"Generating EVP for company: {profile.name}")
        evp_response = await llm_service.generate(prompt, provider="gemini")

        try:
            evp_response = evp_response.strip()
            if evp_response.startswith("```json"):
                evp_response = evp_response[7:]
            if evp_response.startswith("```"):
                evp_response = evp_response[3:]
            if evp_response.endswith("```"):
                evp_response = evp_response[:-3]
            evp_data = json.loads(evp_response.strip())
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse EVP response: {e}")
            return EVPAnalysisResponse(success=False, error=f"Falha ao processar resposta da IA: {str(e)}")

        evp_analysis = {
            "statement": evp_data.get("statement", ""),
            "pillars": evp_data.get("pillars", []),
            "tone_guidance": evp_data.get("tone_guidance", []),
            "candidate_promise": evp_data.get("candidate_promise", ""),
            "generated_at": datetime.utcnow().isoformat(),
            "sources": sources,
        }

        updated_additional_data = {**(profile.additional_data or {}), "evp_analysis": evp_analysis}
        await profile_repo.update(profile_id, {"additional_data": updated_additional_data, "updated_at": datetime.utcnow()})
        logger.info(f"Generated EVP for company: {profile.name}")
        return EVPAnalysisResponse(success=True, evp_analysis=evp_analysis)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating EVP: {e}")
        raise HTTPException(status_code=500, detail=str(e))

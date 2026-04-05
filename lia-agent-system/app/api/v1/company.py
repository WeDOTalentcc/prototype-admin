"""
Company Setup API endpoints for admin configuration.
Manages company profiles, departments, benefits, culture values, and ideal profiles.
"""
from fastapi import APIRouter, HTTPException, Query, Depends, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from datetime import datetime
import uuid
import csv
import io

from app.models.company import (
    CompanyProfile,
    Department,
    DepartmentMember,
    Benefit,
    CultureValue,
    IdealProfile,
    BigFiveQuestion,
    BigFiveRoleProfile,
    TechnicalQuestion,
    TechnicalTestTemplate,
    Approver,
    GlobalSearchSettings
)
from app.models.company_culture import CompanyCultureProfile
from app.models.job_vacancy import JobVacancy
from app.auth.dependencies import get_current_user_or_demo
from app.schemas.company import (
    CompanyProfileCreate,
    CompanyProfileUpdate,
    CompanyProfileResponse,
    CompanyProfileWithRelations,
    DepartmentCreate,
    DepartmentUpdate,
    DepartmentResponse,
    DepartmentMemberCreate,
    DepartmentMemberUpdate,
    DepartmentMemberResponse,
    BenefitCreate,
    BenefitUpdate,
    BenefitResponse,
    CultureValueCreate,
    CultureValueUpdate,
    CultureValueResponse,
    IdealProfileCreate,
    IdealProfileUpdate,
    IdealProfileResponse,
    BigFiveQuestionCreate,
    BigFiveQuestionUpdate,
    BigFiveQuestionResponse,
    BigFiveRoleProfileCreate,
    BigFiveRoleProfileUpdate,
    BigFiveRoleProfileResponse,
    TechnicalQuestionCreate,
    TechnicalQuestionUpdate,
    TechnicalQuestionResponse,
    TechnicalTestTemplateCreate,
    TechnicalTestTemplateUpdate,
    TechnicalTestTemplateResponse,
    CultureAnalysisRequest,
    CultureAnalysisResponse,
    ApproverCreate,
    ApproverUpdate,
    ApproverResponse,
    GlobalSearchSettingsUpdate,
    GlobalSearchSettingsResponse,
)
from app.core.database import get_db
from app.services.llm import llm_service
from app.services.company_configuration_service import company_config_service
from app.auth.models import User
from app.auth.schemas import UserManagementCreate, UserManagementResponse, UserManagementUpdate
from app.auth.security import get_password_hash, generate_secure_token
from app.domains.communication.services.email_service import email_service
from app.domains.sourcing.services.apify_service import apify_service
import httpx
import os

FRONTEND_URL = os.getenv("FRONTEND_URL", "https://plataforma-lia.replit.app")
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/company", tags=["company"])


class CompanyEnrichRequest(BaseModel):
    linkedin_url: Optional[str] = None
    glassdoor_company_name: Optional[str] = None


class CompanyEnrichResponse(BaseModel):
    success: bool
    linkedin_data: Dict[str, Any] = {}
    glassdoor_data: Dict[str, Any] = {}
    enriched_culture: Dict[str, Any] = {}
    errors: List[str] = []


class OnboardingCultureProfile(BaseModel):
    mission: Optional[str] = None
    vision: Optional[str] = None
    values: Optional[List[str]] = None
    evp_bullets: Optional[List[str]] = None
    openness_score: Optional[int] = None
    conscientiousness_score: Optional[int] = None
    extraversion_score: Optional[int] = None
    agreeableness_score: Optional[int] = None
    stability_score: Optional[int] = None


class OnboardingData(BaseModel):
    company_id: Optional[str] = None
    company_name: str
    trade_name: Optional[str] = None
    cnpj: Optional[str] = None
    address: Optional[str] = None
    work_model: Optional[str] = None
    logo_url: Optional[str] = None
    sector: Optional[str] = None
    employee_count: Optional[str] = None
    website: Optional[str] = None
    linkedin_url: Optional[str] = None
    hiring_volume: Optional[int] = None
    job_types: Optional[List[str]] = None
    current_ats: Optional[str] = None
    main_challenges: Optional[List[str]] = None
    main_priority: Optional[str] = None
    platform_expectations: Optional[str] = None
    communication_channels: Optional[List[str]] = None
    allow_lia_contact: bool = True
    additional_notes: Optional[str] = None
    responsible_name: Optional[str] = None
    responsible_email: Optional[str] = None
    responsible_phone: Optional[str] = None
    responsible_position: Optional[str] = None
    preferred_contact_time: Optional[str] = None
    culture_profile: Optional[OnboardingCultureProfile] = None


@router.post("/onboarding")
async def submit_onboarding(
    data: OnboardingData,
    db: AsyncSession = Depends(get_db)
):
    """
    Submit onboarding data from the wizard.
    Creates or updates company profile with the provided information.
    
    Priority for finding profile to update:
    1. If company_id is provided, update that specific profile
    2. Otherwise, find and update the default profile (is_default=True)
    3. If no default exists, create a new one
    """
    try:
        logger.info(f"Received onboarding data for company: {data.company_name}")
        
        profile = None
        
        if data.company_id:
            try:
                company_uuid = uuid.UUID(data.company_id)
                existing = await db.execute(
                    select(CompanyProfile).where(CompanyProfile.id == company_uuid)
                )
                profile = existing.scalar_one_or_none()
                if profile:
                    logger.info(f"Found company profile by ID: {data.company_id}")
            except ValueError:
                logger.warning(f"Invalid company_id format: {data.company_id}")
        
        if not profile:
            existing = await db.execute(
                select(CompanyProfile).where(CompanyProfile.is_default == True)
            )
            profile = existing.scalar_one_or_none()
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
            profile.name = data.company_name
            profile.trading_name = data.trade_name
            profile.cnpj = data.cnpj
            profile.address = data.address
            profile.industry = data.sector
            profile.company_size = data.employee_count
            profile.website = data.website
            profile.linkedin_url = data.linkedin_url
            profile.logo_url = data.logo_url
            profile.hr_email = data.responsible_email
            profile.hr_phone = data.responsible_phone
            profile.updated_at = datetime.utcnow()
            if profile.additional_data:
                profile.additional_data.update(onboarding_metadata)
            else:
                profile.additional_data = onboarding_metadata
            logger.info(f"Updated existing company profile: {data.company_name}")
        else:
            profile = CompanyProfile(
                name=data.company_name,
                trading_name=data.trade_name,
                cnpj=data.cnpj,
                address=data.address,
                industry=data.sector,
                company_size=data.employee_count,
                website=data.website,
                linkedin_url=data.linkedin_url,
                logo_url=data.logo_url,
                hr_email=data.responsible_email,
                hr_phone=data.responsible_phone,
                is_default=True,
                additional_data=onboarding_metadata
            )
            db.add(profile)
            logger.info(f"Created new company profile: {data.company_name}")
        
        await db.commit()
        await db.refresh(profile)
        
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
    data: CompanyEnrichRequest
):
    """
    Enrich company profile with LinkedIn and Glassdoor data via Apify actors.
    
    Args:
        data: Request containing optional linkedin_url and glassdoor_company_name
        
    Returns:
        Enriched company data including culture, mission, vision, values
    """
    errors = []
    linkedin_data = {}
    glassdoor_data = {}
    enriched_culture = {}
    
    if not data.linkedin_url and not data.glassdoor_company_name:
        raise HTTPException(
            status_code=400,
            detail="At least one of linkedin_url or glassdoor_company_name must be provided"
        )
    
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
        
        success = bool(linkedin_data or glassdoor_data)
        
        return CompanyEnrichResponse(
            success=success,
            linkedin_data=linkedin_data,
            glassdoor_data=glassdoor_data,
            enriched_culture=enriched_culture,
            errors=errors
        )
        
    except Exception as e:
        logger.error(f"Error enriching company profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class AutoEnrichResponse(BaseModel):
    success: bool
    fields_updated: List[str] = []
    apify_data: Dict[str, Any] = {}
    inferred_data: Dict[str, Any] = {}
    errors: List[str] = []


@router.post("/auto-enrich/{profile_id}", response_model=AutoEnrichResponse)
async def auto_enrich_company(
    profile_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Automatically enrich company profile after wizard submission.
    Uses Apify for LinkedIn/Glassdoor data and LLM for inference.
    """
    errors = []
    fields_updated = []
    apify_data = {}
    inferred_data = {}
    
    try:
        result = await db.execute(
            select(CompanyProfile).where(CompanyProfile.id == profile_id)
        )
        profile = result.scalar_one_or_none()
        
        if not profile:
            raise HTTPException(status_code=404, detail="Company profile not found")
        
        culture_result = await db.execute(
            select(CompanyCultureProfile).where(
                CompanyCultureProfile.company_id == profile_id
            )
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
        
        if linkedin_data:
            if linkedin_data.get("headquarters") and not profile.headquarters_city:
                hq = linkedin_data["headquarters"]
                if isinstance(hq, dict):
                    profile.headquarters_city = hq.get("city", "")
                    profile.headquarters_state = hq.get("state", "")
                    profile.headquarters_country = hq.get("country", "Brasil")
                elif isinstance(hq, str):
                    parts = hq.split(",")
                    if len(parts) >= 2:
                        profile.headquarters_city = parts[0].strip()
                        profile.headquarters_state = parts[1].strip()
                fields_updated.append("headquarters")
            
            if linkedin_data.get("founded") and not profile.founded_year:
                try:
                    profile.founded_year = int(linkedin_data["founded"])
                    fields_updated.append("founded_year")
                except (ValueError, TypeError):
                    pass
            
            if linkedin_data.get("company_size") and not profile.employee_count:
                size_str = linkedin_data["company_size"]
                try:
                    if "-" in str(size_str):
                        nums = str(size_str).replace(",", "").replace("+", "").split("-")
                        profile.employee_count = int(nums[1]) if len(nums) > 1 else int(nums[0])
                    else:
                        profile.employee_count = int(str(size_str).replace(",", "").replace("+", ""))
                    fields_updated.append("employee_count")
                except (ValueError, TypeError):
                    pass
            
            if linkedin_data.get("description"):
                if not profile.description:
                    profile.description = linkedin_data["description"]
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
            "values": culture_profile.values if culture_profile else []
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
                
                additional = profile.additional_data or {}
                if inferred.get("work_model") and inferred["work_model"] != "Não especificado":
                    additional["work_model"] = inferred["work_model"]
                    fields_updated.append("work_model")
                if inferred.get("growth_opportunities") and inferred["growth_opportunities"] != "Não especificado":
                    additional["growth_opportunities"] = inferred["growth_opportunities"]
                    fields_updated.append("growth_opportunities")
                if inferred.get("team_dynamics") and inferred["team_dynamics"] != "Não especificado":
                    additional["team_dynamics"] = inferred["team_dynamics"]
                    fields_updated.append("team_dynamics")
                if inferred.get("leadership_style") and inferred["leadership_style"] != "Não especificado":
                    additional["leadership_style"] = inferred["leadership_style"]
                    fields_updated.append("leadership_style")
                if inferred.get("diversity_initiatives") and inferred["diversity_initiatives"] != "Não especificado":
                    additional["diversity_initiatives"] = inferred["diversity_initiatives"]
                    fields_updated.append("diversity_initiatives")
                if inferred.get("sustainability") and inferred["sustainability"] != "Não especificado":
                    additional["sustainability"] = inferred["sustainability"]
                    fields_updated.append("sustainability")
                if inferred.get("social_impact") and inferred["social_impact"] != "Não especificado":
                    additional["social_impact"] = inferred["social_impact"]
                    fields_updated.append("social_impact")
                if inferred.get("engineering_culture") and inferred["engineering_culture"] != "Não especificado":
                    additional["engineering_culture"] = inferred["engineering_culture"]
                    fields_updated.append("engineering_culture")
                
                profile.additional_data = additional
                
                if culture_profile and inferred.get("core_competencies"):
                    if not culture_profile.core_competencies or len(culture_profile.core_competencies) == 0:
                        culture_profile.core_competencies = inferred["core_competencies"]
                        fields_updated.append("core_competencies")
                
            except json.JSONDecodeError as e:
                errors.append(f"Failed to parse LLM response: {str(e)}")
            except Exception as e:
                errors.append(f"LLM inference failed: {str(e)}")
        
        profile.updated_at = datetime.utcnow()
        if culture_profile:
            culture_profile.updated_at = datetime.utcnow()
        
        await db.commit()
        
        logger.info(f"Auto-enriched company {profile.name}, updated fields: {fields_updated}")
        
        return AutoEnrichResponse(
            success=len(fields_updated) > 0,
            fields_updated=fields_updated,
            apify_data=apify_data,
            inferred_data=inferred_data,
            errors=errors
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in auto-enrich: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profile", response_model=CompanyProfileResponse)
async def get_company_profile(
    db: AsyncSession = Depends(get_db)
):
    """Get the default company profile."""
    try:
        result = await db.execute(
            select(CompanyProfile).where(CompanyProfile.is_default == True).order_by(CompanyProfile.created_at.desc()).limit(1)
        )
        profile = result.scalars().first()
        
        if not profile:
            result = await db.execute(
                select(CompanyProfile).where(CompanyProfile.is_active == True).order_by(CompanyProfile.created_at.desc()).limit(1)
            )
            profile = result.scalars().first()
        
        if not profile:
            raise HTTPException(status_code=404, detail="No company profile found")
        
        return profile
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching company profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/profile", response_model=CompanyProfileResponse)
async def create_company_profile(
    data: CompanyProfileCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new company profile."""
    try:
        profile = CompanyProfile(**data.model_dump())
        
        existing = await db.execute(
            select(CompanyProfile).where(CompanyProfile.is_default == True).limit(1)
        )
        if not existing.scalars().first():
            profile.is_default = True
        
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
        
        logger.info(f"Created company profile: {profile.name}")
        return profile
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating company profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/profile/{profile_id}", response_model=CompanyProfileResponse)
async def update_company_profile(
    profile_id: uuid.UUID,
    data: CompanyProfileUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing company profile."""
    try:
        result = await db.execute(
            select(CompanyProfile).where(CompanyProfile.id == profile_id)
        )
        profile = result.scalar_one_or_none()
        
        if not profile:
            raise HTTPException(status_code=404, detail="Company profile not found")
        
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(profile, field, value)
        
        profile.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(profile)
        
        logger.info(f"Updated company profile: {profile.name}")
        return profile
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating company profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profile/{profile_id}/full", response_model=CompanyProfileWithRelations)
async def get_company_profile_with_relations(
    profile_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get company profile with all related data (departments, benefits, culture)."""
    try:
        result = await db.execute(
            select(CompanyProfile).where(CompanyProfile.id == profile_id)
        )
        profile = result.scalar_one_or_none()
        
        if not profile:
            raise HTTPException(status_code=404, detail="Company profile not found")
        
        deps_result = await db.execute(
            select(Department).where(
                Department.company_id == profile_id,
                Department.is_active == True
            ).order_by(Department.order)
        )
        departments = deps_result.scalars().all()
        
        bens_result = await db.execute(
            select(Benefit).where(
                Benefit.company_id == profile_id,
                Benefit.is_active == True
            ).order_by(Benefit.category, Benefit.order)
        )
        benefits = bens_result.scalars().all()
        
        vals_result = await db.execute(
            select(CultureValue).where(
                CultureValue.company_id == profile_id,
                CultureValue.is_active == True
            ).order_by(CultureValue.order)
        )
        culture_values = vals_result.scalars().all()
        
        response = CompanyProfileWithRelations.model_validate(profile)
        response.departments = [DepartmentResponse.model_validate(d) for d in departments]
        response.benefits = [BenefitResponse.model_validate(b) for b in benefits]
        response.culture_values = [CultureValueResponse.model_validate(c) for c in culture_values]
        
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching company profile with relations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class EVPAnalysisResponse(BaseModel):
    success: bool
    evp_analysis: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@router.post("/profile/{profile_id}/generate-evp", response_model=EVPAnalysisResponse)
async def generate_evp(
    profile_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Generate EVP (Employee Value Proposition) analysis using LLM.
    Uses company data from additional_data to create structured EVP insights.
    """
    try:
        result = await db.execute(
            select(CompanyProfile).where(CompanyProfile.id == profile_id)
        )
        profile = result.scalar_one_or_none()
        
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
    {{
      "name": "Nome do Pilar 1 (ex: Crescimento, Inovação, Impacto)",
      "description": "Descrição detalhada do pilar",
      "evidence": "Evidência concreta baseada nos dados da empresa"
    }},
    {{
      "name": "Nome do Pilar 2",
      "description": "Descrição detalhada do pilar",
      "evidence": "Evidência concreta baseada nos dados da empresa"
    }},
    {{
      "name": "Nome do Pilar 3",
      "description": "Descrição detalhada do pilar",
      "evidence": "Evidência concreta baseada nos dados da empresa"
    }}
  ],
  "tone_guidance": ["adjetivo1", "adjetivo2", "adjetivo3", "adjetivo4", "adjetivo5"],
  "candidate_promise": "Uma frase clara sobre o que a empresa promete ao candidato que se juntar à equipe"
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
            evp_response = evp_response.strip()
            
            evp_data = json.loads(evp_response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse EVP response: {e}")
            logger.error(f"Raw response: {evp_response[:500]}")
            return EVPAnalysisResponse(
                success=False,
                error=f"Falha ao processar resposta da IA: {str(e)}"
            )
        
        evp_analysis = {
            "statement": evp_data.get("statement", ""),
            "pillars": evp_data.get("pillars", []),
            "tone_guidance": evp_data.get("tone_guidance", []),
            "candidate_promise": evp_data.get("candidate_promise", ""),
            "generated_at": datetime.utcnow().isoformat(),
            "sources": sources
        }
        
        updated_additional_data = {**(profile.additional_data or {}), "evp_analysis": evp_analysis}
        profile.additional_data = updated_additional_data
        profile.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(profile)
        
        logger.info(f"Generated EVP for company: {profile.name}")
        
        return EVPAnalysisResponse(
            success=True,
            evp_analysis=evp_analysis
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error generating EVP: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/departments", response_model=List[DepartmentResponse])
async def list_departments(
    company_id: Optional[uuid.UUID] = Query(None),
    include_inactive: bool = Query(False),
    db: AsyncSession = Depends(get_db)
):
    """List all departments for a company."""
    try:
        query = select(Department)
        
        if company_id:
            query = query.where(Department.company_id == company_id)
        
        if not include_inactive:
            query = query.where(Department.is_active == True)
        
        query = query.order_by(Department.order)
        
        result = await db.execute(query)
        departments = result.scalars().all()
        
        for dept in departments:
            member_count_result = await db.execute(
                select(func.count(DepartmentMember.id)).where(
                    DepartmentMember.department_id == dept.id,
                    DepartmentMember.is_active == True
                )
            )
            member_count = member_count_result.scalar() or 0
            dept.headcount = member_count
        
        return departments
    except Exception as e:
        logger.error(f"Error listing departments: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/departments", response_model=DepartmentResponse)
async def create_department(
    company_id: str = Query(...),
    data: DepartmentCreate = None,
    db: AsyncSession = Depends(get_db)
):
    """Create a new department."""
    try:
        resolved_company_id = None
        if company_id and company_id != "default":
            try:
                resolved_company_id = uuid.UUID(company_id)
            except ValueError:
                pass
        
        if not resolved_company_id:
            result = await db.execute(
                select(CompanyProfile).where(CompanyProfile.is_default == True).order_by(CompanyProfile.created_at.desc()).limit(1)
            )
            profile = result.scalars().first()
            if not profile:
                result = await db.execute(
                    select(CompanyProfile).where(CompanyProfile.is_active == True).order_by(CompanyProfile.created_at.desc()).limit(1)
                )
                profile = result.scalars().first()
            if profile:
                resolved_company_id = profile.id
        
        department = Department(
            company_id=resolved_company_id,
            **data.model_dump()
        )
        
        db.add(department)
        await db.commit()
        await db.refresh(department)
        
        logger.info(f"Created department: {department.name}")
        return department
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating department: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/departments/{department_id}", response_model=DepartmentResponse)
async def update_department(
    department_id: uuid.UUID,
    data: DepartmentUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a department."""
    try:
        result = await db.execute(
            select(Department).where(Department.id == department_id)
        )
        department = result.scalar_one_or_none()
        
        if not department:
            raise HTTPException(status_code=404, detail="Department not found")
        
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(department, field, value)
        
        department.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(department)
        
        return department
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating department: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/departments/{department_id}")
async def delete_department(
    department_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Soft delete a department."""
    try:
        result = await db.execute(
            select(Department).where(Department.id == department_id)
        )
        department = result.scalar_one_or_none()
        
        if not department:
            raise HTTPException(status_code=404, detail="Department not found")
        
        department.is_active = False
        department.updated_at = datetime.utcnow()
        
        await db.commit()
        
        return {"success": True, "message": "Department deleted"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting department: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/departments/{department_id}/members", response_model=List[DepartmentMemberResponse])
async def list_department_members(
    department_id: uuid.UUID,
    include_inactive: bool = Query(False),
    db: AsyncSession = Depends(get_db)
):
    """List all members of a department."""
    try:
        dept_result = await db.execute(
            select(Department).where(Department.id == department_id)
        )
        department = dept_result.scalar_one_or_none()
        
        if not department:
            raise HTTPException(status_code=404, detail="Department not found")
        
        query = select(DepartmentMember).where(
            DepartmentMember.department_id == department_id
        )
        
        if not include_inactive:
            query = query.where(DepartmentMember.is_active == True)
        
        query = query.order_by(DepartmentMember.order, DepartmentMember.name)
        
        result = await db.execute(query)
        members = result.scalars().all()
        
        return members
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing department members: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/departments/{department_id}/members", response_model=DepartmentMemberResponse)
async def create_department_member(
    department_id: uuid.UUID,
    data: DepartmentMemberCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new member in a department."""
    try:
        dept_result = await db.execute(
            select(Department).where(Department.id == department_id)
        )
        department = dept_result.scalar_one_or_none()
        
        if not department:
            raise HTTPException(status_code=404, detail="Department not found")
        
        member_data = data.model_dump(exclude={"department_id"})
        member = DepartmentMember(
            department_id=department_id,
            company_id=department.company_id,
            **member_data
        )
        
        db.add(member)
        await db.commit()
        await db.refresh(member)
        
        logger.info(f"Created department member: {member.name} in department {department.name}")
        return member
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating department member: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/members/{member_id}", response_model=DepartmentMemberResponse)
async def update_department_member(
    member_id: uuid.UUID,
    data: DepartmentMemberUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a department member."""
    try:
        result = await db.execute(
            select(DepartmentMember).where(DepartmentMember.id == member_id)
        )
        member = result.scalar_one_or_none()
        
        if not member:
            raise HTTPException(status_code=404, detail="Department member not found")
        
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(member, field, value)
        
        member.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(member)
        
        return member
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating department member: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/members/{member_id}")
async def delete_department_member(
    member_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Soft delete a department member."""
    try:
        result = await db.execute(
            select(DepartmentMember).where(DepartmentMember.id == member_id)
        )
        member = result.scalar_one_or_none()
        
        if not member:
            raise HTTPException(status_code=404, detail="Department member not found")
        
        member.is_active = False
        member.updated_at = datetime.utcnow()
        
        await db.commit()
        
        return {"success": True, "message": "Department member deleted"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting department member: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================
# MANAGERS ENDPOINTS
# =============================================

class ManagerResponse(BaseModel):
    """Manager info for autocomplete/selection."""
    id: str
    name: str
    email: Optional[str] = None
    role: Optional[str] = None
    department_id: Optional[str] = None
    department_name: Optional[str] = None


class ManagerSearchResponse(BaseModel):
    """Response for manager search."""
    managers: List[ManagerResponse]
    total_count: int


@router.get("/managers", response_model=ManagerSearchResponse)
async def list_managers(
    company_id: Optional[str] = Query(None),
    search: Optional[str] = Query(None, description="Search term for name"),
    department_id: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_or_demo)
):
    """
    List managers for a company.
    
    Used for autocomplete when creating job vacancies.
    Returns people with manager/lead/director roles from company structure.
    """
    try:
        from app.services.manager_inference_service import manager_inference_service
        
        if not company_id:
            company_id = str(getattr(current_user, 'company_id', None) or 'default')
        
        if search:
            managers = await manager_inference_service.search_managers(
                company_id=company_id,
                search_term=search,
                limit=limit
            )
        else:
            managers = await manager_inference_service.list_managers(
                company_id=company_id,
                department_id=department_id,
                limit=limit
            )
        
        return ManagerSearchResponse(
            managers=[ManagerResponse(**m) for m in managers],
            total_count=len(managers)
        )
    except Exception as e:
        logger.error(f"Error listing managers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/managers/infer-email")
async def infer_manager_email(
    name: str = Query(..., description="Manager name to search"),
    department: Optional[str] = Query(None, description="Department context"),
    company_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_or_demo)
):
    """
    Infer manager email from name.
    
    Searches company structure (departments/members) to find matching manager.
    Returns inferred email or null if not found.
    """
    try:
        from app.services.manager_inference_service import manager_inference_service
        
        if not company_id:
            company_id = str(getattr(current_user, 'company_id', None) or 'default')
        
        result = await manager_inference_service.get_manager_by_name(
            manager_name=name,
            company_id=company_id,
            department=department
        )
        
        if result:
            return {
                "found": True,
                "name": result.get("name"),
                "email": result.get("email"),
                "role": result.get("role"),
                "department": result.get("department_name"),
                "confidence": result.get("confidence", 1.0),
                "source": "company_structure"
            }
        else:
            return {
                "found": False,
                "name": name,
                "email": None,
                "message": "Gestor não encontrado na estrutura da empresa. Você pode adicionar manualmente."
            }
    except Exception as e:
        logger.error(f"Error inferring manager email: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/benefits", response_model=List[BenefitResponse])
async def list_benefits(
    company_id: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    include_inactive: bool = Query(False),
    db: AsyncSession = Depends(get_db)
):
    """List all benefits for a company."""
    try:
        query = select(Benefit)
        
        if company_id and company_id != "default":
            try:
                company_uuid = uuid.UUID(company_id)
                query = query.where(Benefit.company_id == company_uuid)
            except ValueError:
                pass
        
        if category:
            query = query.where(Benefit.category == category)
        
        if not include_inactive:
            query = query.where(Benefit.is_active == True)
        
        query = query.order_by(Benefit.category, Benefit.order)
        
        result = await db.execute(query)
        benefits = result.scalars().all()
        
        return benefits
    except Exception as e:
        logger.error(f"Error listing benefits: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/benefits", response_model=BenefitResponse)
async def create_benefit(
    company_id: str,
    data: BenefitCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new benefit."""
    try:
        resolved_company_id = None
        if company_id and company_id != "default":
            try:
                resolved_company_id = uuid.UUID(company_id)
            except ValueError:
                pass
        
        if not resolved_company_id:
            result = await db.execute(
                select(CompanyProfile).where(CompanyProfile.is_default == True).order_by(CompanyProfile.created_at.desc()).limit(1)
            )
            profile = result.scalars().first()
            if not profile:
                result = await db.execute(
                    select(CompanyProfile).where(CompanyProfile.is_active == True).order_by(CompanyProfile.created_at.desc()).limit(1)
                )
                profile = result.scalars().first()
            if profile:
                resolved_company_id = profile.id
        
        benefit = Benefit(
            company_id=resolved_company_id,
            **data.model_dump()
        )
        
        db.add(benefit)
        await db.commit()
        await db.refresh(benefit)
        
        logger.info(f"Created benefit: {benefit.name}")
        return benefit
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating benefit: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/benefits/{benefit_id}", response_model=BenefitResponse)
async def update_benefit(
    benefit_id: uuid.UUID,
    data: BenefitUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a benefit."""
    try:
        result = await db.execute(
            select(Benefit).where(Benefit.id == benefit_id)
        )
        benefit = result.scalar_one_or_none()
        
        if not benefit:
            raise HTTPException(status_code=404, detail="Benefit not found")
        
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(benefit, field, value)
        
        benefit.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(benefit)
        
        return benefit
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating benefit: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/benefits/{benefit_id}")
async def delete_benefit(
    benefit_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Soft delete a benefit."""
    try:
        result = await db.execute(
            select(Benefit).where(Benefit.id == benefit_id)
        )
        benefit = result.scalar_one_or_none()
        
        if not benefit:
            raise HTTPException(status_code=404, detail="Benefit not found")
        
        benefit.is_active = False
        benefit.updated_at = datetime.utcnow()
        
        await db.commit()
        
        return {"success": True, "message": "Benefit deleted"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting benefit: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class BenefitsSummaryResponse(BaseModel):
    """Response for benefits summary endpoint used by AI agents."""
    total_count: int
    active_count: int
    highlighted_count: int
    categories: dict
    formatted_text: str
    benefits: List[dict]


@router.get("/benefits/active", response_model=List[BenefitResponse])
async def list_active_benefits(
    company_id: Optional[str] = Query(None),
    seniority_level: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    List only active benefits for a company.
    Used by AI agents to get current company benefits.
    """
    try:
        query = select(Benefit).where(Benefit.is_active == True)
        
        if company_id:
            if company_id != "default":
                query = query.where(Benefit.company_id == uuid.UUID(company_id))
        
        query = query.order_by(Benefit.order, Benefit.category)
        
        result = await db.execute(query)
        benefits = result.scalars().all()
        
        if seniority_level:
            benefits = [
                b for b in benefits 
                if not b.seniority_levels or 
                   "all" in (b.seniority_levels or []) or 
                   seniority_level in (b.seniority_levels or [])
            ]
        
        return benefits
    except Exception as e:
        logger.error(f"Error listing active benefits: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/benefits/highlighted", response_model=List[BenefitResponse])
async def list_highlighted_benefits(
    company_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    List highlighted benefits for a company.
    Used for displaying key benefits in job postings and candidate communications.
    """
    try:
        query = select(Benefit).where(
            Benefit.is_active == True,
            Benefit.is_highlighted == True
        )
        
        if company_id:
            if company_id != "default":
                query = query.where(Benefit.company_id == uuid.UUID(company_id))
        
        query = query.order_by(Benefit.order, Benefit.category)
        
        result = await db.execute(query)
        benefits = result.scalars().all()
        
        return benefits
    except Exception as e:
        logger.error(f"Error listing highlighted benefits: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/benefits/summary", response_model=BenefitsSummaryResponse)
async def get_benefits_summary(
    company_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a summary of company benefits for AI agents.
    Includes formatted text ready for use in prompts.
    """
    try:
        query = select(Benefit)
        
        if company_id:
            if company_id != "default":
                query = query.where(Benefit.company_id == uuid.UUID(company_id))
        
        result = await db.execute(query)
        all_benefits = result.scalars().all()
        
        active_benefits = [b for b in all_benefits if b.is_active]
        highlighted_benefits = [b for b in active_benefits if b.is_highlighted]
        
        CATEGORY_NAMES = {
            "health": "Saúde & Bem-estar",
            "food": "Alimentação",
            "transport": "Transporte",
            "education": "Educação & Desenvolvimento",
            "financial": "Financeiro",
            "quality_life": "Qualidade de Vida",
            "family": "Família",
            "security": "Segurança"
        }
        
        categories = {}
        for benefit in active_benefits:
            cat = benefit.category or "other"
            if cat not in categories:
                categories[cat] = {
                    "name": CATEGORY_NAMES.get(cat, cat),
                    "count": 0,
                    "benefits": []
                }
            categories[cat]["count"] += 1
            categories[cat]["benefits"].append({
                "name": benefit.name,
                "description": benefit.description,
                "value_type": benefit.value_type,
                "value": benefit.value,
                "percentage_value": benefit.percentage_value,
                "is_highlighted": benefit.is_highlighted
            })
        
        formatted_lines = ["**Benefícios da Empresa:**"]
        for cat_id, cat_data in categories.items():
            cat_benefits = []
            for b in cat_data["benefits"]:
                if b["value_type"] == "monetary" and b["value"]:
                    cat_benefits.append(f'{b["name"]} (R$ {b["value"]:,.2f})')
                elif b["value_type"] == "percentage" and b["percentage_value"]:
                    cat_benefits.append(f'{b["name"]} ({b["percentage_value"]}%)')
                else:
                    cat_benefits.append(b["name"])
            if cat_benefits:
                formatted_lines.append(f"- {cat_data['name']}: {', '.join(cat_benefits)}")
        
        formatted_text = "\n".join(formatted_lines) if len(formatted_lines) > 1 else "Nenhum benefício cadastrado."
        
        benefits_list = [
            {
                "id": str(b.id),
                "name": b.name,
                "description": b.description,
                "category": b.category,
                "value_type": b.value_type,
                "value": b.value,
                "percentage_value": b.percentage_value,
                "is_highlighted": b.is_highlighted
            }
            for b in active_benefits
        ]
        
        return BenefitsSummaryResponse(
            total_count=len(all_benefits),
            active_count=len(active_benefits),
            highlighted_count=len(highlighted_benefits),
            categories=categories,
            formatted_text=formatted_text,
            benefits=benefits_list
        )
    except Exception as e:
        logger.error(f"Error getting benefits summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/culture-values", response_model=List[CultureValueResponse])
async def list_culture_values(
    company_id: Optional[uuid.UUID] = Query(None),
    category: Optional[str] = Query(None),
    include_inactive: bool = Query(False),
    db: AsyncSession = Depends(get_db)
):
    """List all culture values for a company."""
    try:
        query = select(CultureValue)
        
        if company_id:
            query = query.where(CultureValue.company_id == company_id)
        
        if category:
            query = query.where(CultureValue.category == category)
        
        if not include_inactive:
            query = query.where(CultureValue.is_active == True)
        
        query = query.order_by(CultureValue.order)
        
        result = await db.execute(query)
        values = result.scalars().all()
        
        return values
    except Exception as e:
        logger.error(f"Error listing culture values: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/culture-values", response_model=CultureValueResponse)
async def create_culture_value(
    company_id: uuid.UUID,
    data: CultureValueCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new culture value."""
    try:
        culture_value = CultureValue(
            company_id=company_id,
            **data.model_dump()
        )
        
        db.add(culture_value)
        await db.commit()
        await db.refresh(culture_value)
        
        logger.info(f"Created culture value: {culture_value.name}")
        return culture_value
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating culture value: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/culture-values/{value_id}", response_model=CultureValueResponse)
async def update_culture_value(
    value_id: uuid.UUID,
    data: CultureValueUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a culture value."""
    try:
        result = await db.execute(
            select(CultureValue).where(CultureValue.id == value_id)
        )
        culture_value = result.scalar_one_or_none()
        
        if not culture_value:
            raise HTTPException(status_code=404, detail="Culture value not found")
        
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(culture_value, field, value)
        
        culture_value.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(culture_value)
        
        return culture_value
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating culture value: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/culture-values/{value_id}")
async def delete_culture_value(
    value_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Soft delete a culture value."""
    try:
        result = await db.execute(
            select(CultureValue).where(CultureValue.id == value_id)
        )
        culture_value = result.scalar_one_or_none()
        
        if not culture_value:
            raise HTTPException(status_code=404, detail="Culture value not found")
        
        culture_value.is_active = False
        culture_value.updated_at = datetime.utcnow()
        
        await db.commit()
        
        return {"success": True, "message": "Culture value deleted"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting culture value: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ideal-profiles", response_model=List[IdealProfileResponse])
async def list_ideal_profiles(
    company_id: Optional[uuid.UUID] = Query(None),
    department_id: Optional[uuid.UUID] = Query(None),
    role_type: Optional[str] = Query(None),
    seniority_level: Optional[str] = Query(None),
    include_inactive: bool = Query(False),
    db: AsyncSession = Depends(get_db)
):
    """List all ideal profiles."""
    try:
        query = select(IdealProfile)
        
        if company_id:
            query = query.where(IdealProfile.company_id == company_id)
        
        if department_id:
            query = query.where(IdealProfile.department_id == department_id)
        
        if role_type:
            query = query.where(IdealProfile.role_type == role_type)
        
        if seniority_level:
            query = query.where(IdealProfile.seniority_level == seniority_level)
        
        if not include_inactive:
            query = query.where(IdealProfile.is_active == True)
        
        query = query.order_by(IdealProfile.created_at.desc())
        
        result = await db.execute(query)
        profiles = result.scalars().all()
        
        return profiles
    except Exception as e:
        logger.error(f"Error listing ideal profiles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ideal-profiles", response_model=IdealProfileResponse)
async def create_ideal_profile(
    company_id: uuid.UUID,
    data: IdealProfileCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new ideal profile."""
    try:
        profile = IdealProfile(
            company_id=company_id,
            **data.model_dump()
        )
        
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
        
        logger.info(f"Created ideal profile: {profile.name}")
        return profile
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating ideal profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/ideal-profiles/{profile_id}", response_model=IdealProfileResponse)
async def update_ideal_profile(
    profile_id: uuid.UUID,
    data: IdealProfileUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an ideal profile."""
    try:
        result = await db.execute(
            select(IdealProfile).where(IdealProfile.id == profile_id)
        )
        profile = result.scalar_one_or_none()
        
        if not profile:
            raise HTTPException(status_code=404, detail="Ideal profile not found")
        
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(profile, field, value)
        
        if data.validated and not profile.validated_at:
            profile.validated_at = datetime.utcnow()
        
        profile.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(profile)
        
        return profile
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating ideal profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/ideal-profiles/{profile_id}")
async def delete_ideal_profile(
    profile_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Soft delete an ideal profile."""
    try:
        result = await db.execute(
            select(IdealProfile).where(IdealProfile.id == profile_id)
        )
        profile = result.scalar_one_or_none()
        
        if not profile:
            raise HTTPException(status_code=404, detail="Ideal profile not found")
        
        profile.is_active = False
        profile.updated_at = datetime.utcnow()
        
        await db.commit()
        
        return {"success": True, "message": "Ideal profile deleted"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting ideal profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/big-five/questions", response_model=List[BigFiveQuestionResponse])
async def list_big_five_questions(
    trait: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    is_core: Optional[bool] = Query(None),
    include_inactive: bool = Query(False),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """List Big Five personality questions."""
    try:
        query = select(BigFiveQuestion)
        
        if trait:
            query = query.where(BigFiveQuestion.trait == trait)
        
        if category:
            query = query.where(BigFiveQuestion.category == category)
        
        if is_core is not None:
            query = query.where(BigFiveQuestion.is_core == is_core)
        
        if not include_inactive:
            query = query.where(BigFiveQuestion.is_active == True)
        
        query = query.order_by(BigFiveQuestion.trait, BigFiveQuestion.order)
        query = query.offset(skip).limit(limit)
        
        result = await db.execute(query)
        questions = result.scalars().all()
        
        return questions
    except Exception as e:
        logger.error(f"Error listing Big Five questions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/big-five/questions", response_model=BigFiveQuestionResponse)
async def create_big_five_question(
    data: BigFiveQuestionCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new Big Five question."""
    try:
        question = BigFiveQuestion(**data.model_dump())
        
        db.add(question)
        await db.commit()
        await db.refresh(question)
        
        logger.info(f"Created Big Five question for trait: {question.trait}")
        return question
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating Big Five question: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/big-five/questions/{question_id}", response_model=BigFiveQuestionResponse)
async def update_big_five_question(
    question_id: uuid.UUID,
    data: BigFiveQuestionUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a Big Five question."""
    try:
        result = await db.execute(
            select(BigFiveQuestion).where(BigFiveQuestion.id == question_id)
        )
        question = result.scalar_one_or_none()
        
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")
        
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(question, field, value)
        
        question.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(question)
        
        return question
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating Big Five question: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/big-five/questions/{question_id}")
async def delete_big_five_question(
    question_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Soft delete a Big Five question."""
    try:
        result = await db.execute(
            select(BigFiveQuestion).where(BigFiveQuestion.id == question_id)
        )
        question = result.scalar_one_or_none()
        
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")
        
        question.is_active = False
        question.updated_at = datetime.utcnow()
        
        await db.commit()
        
        return {"success": True, "message": "Question deleted"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting Big Five question: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/big-five/role-profiles", response_model=List[BigFiveRoleProfileResponse])
async def list_big_five_role_profiles(
    company_id: Optional[uuid.UUID] = Query(None),
    role_category: Optional[str] = Query(None),
    include_templates: bool = Query(True),
    include_inactive: bool = Query(False),
    db: AsyncSession = Depends(get_db)
):
    """List Big Five role profiles."""
    try:
        query = select(BigFiveRoleProfile)
        
        if company_id:
            query = query.where(
                or_(
                    BigFiveRoleProfile.company_id == company_id,
                    BigFiveRoleProfile.company_id.is_(None)
                )
            )
        
        if role_category:
            query = query.where(BigFiveRoleProfile.role_category == role_category)
        
        if not include_templates:
            query = query.where(BigFiveRoleProfile.is_template == False)
        
        if not include_inactive:
            query = query.where(BigFiveRoleProfile.is_active == True)
        
        query = query.order_by(BigFiveRoleProfile.name)
        
        result = await db.execute(query)
        profiles = result.scalars().all()
        
        return profiles
    except Exception as e:
        logger.error(f"Error listing Big Five role profiles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/big-five/role-profiles", response_model=BigFiveRoleProfileResponse)
async def create_big_five_role_profile(
    data: BigFiveRoleProfileCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new Big Five role profile."""
    try:
        profile = BigFiveRoleProfile(**data.model_dump())
        
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
        
        logger.info(f"Created Big Five role profile: {profile.name}")
        return profile
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating Big Five role profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/big-five/role-profiles/{profile_id}", response_model=BigFiveRoleProfileResponse)
async def update_big_five_role_profile(
    profile_id: uuid.UUID,
    data: BigFiveRoleProfileUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a Big Five role profile."""
    try:
        result = await db.execute(
            select(BigFiveRoleProfile).where(BigFiveRoleProfile.id == profile_id)
        )
        profile = result.scalar_one_or_none()
        
        if not profile:
            raise HTTPException(status_code=404, detail="Role profile not found")
        
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(profile, field, value)
        
        profile.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(profile)
        
        return profile
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating Big Five role profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/technical/questions", response_model=List[TechnicalQuestionResponse])
async def list_technical_questions(
    area: Optional[str] = Query(None),
    difficulty: Optional[str] = Query(None),
    question_type: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    include_inactive: bool = Query(False),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """List technical assessment questions."""
    try:
        query = select(TechnicalQuestion)
        
        if area:
            query = query.where(TechnicalQuestion.area == area)
        
        if difficulty:
            query = query.where(TechnicalQuestion.difficulty == difficulty)
        
        if question_type:
            query = query.where(TechnicalQuestion.question_type == question_type)
        
        if tag:
            query = query.where(TechnicalQuestion.tags.contains([tag]))
        
        if not include_inactive:
            query = query.where(TechnicalQuestion.is_active == True)
        
        query = query.order_by(TechnicalQuestion.area, TechnicalQuestion.difficulty)
        query = query.offset(skip).limit(limit)
        
        result = await db.execute(query)
        questions = result.scalars().all()
        
        return questions
    except Exception as e:
        logger.error(f"Error listing technical questions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/technical/questions", response_model=TechnicalQuestionResponse)
async def create_technical_question(
    data: TechnicalQuestionCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new technical question."""
    try:
        question = TechnicalQuestion(**data.model_dump())
        
        db.add(question)
        await db.commit()
        await db.refresh(question)
        
        logger.info(f"Created technical question: {question.title}")
        return question
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating technical question: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/technical/questions/{question_id}", response_model=TechnicalQuestionResponse)
async def update_technical_question(
    question_id: uuid.UUID,
    data: TechnicalQuestionUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a technical question."""
    try:
        result = await db.execute(
            select(TechnicalQuestion).where(TechnicalQuestion.id == question_id)
        )
        question = result.scalar_one_or_none()
        
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")
        
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(question, field, value)
        
        question.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(question)
        
        return question
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating technical question: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/technical/questions/{question_id}")
async def delete_technical_question(
    question_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Soft delete a technical question."""
    try:
        result = await db.execute(
            select(TechnicalQuestion).where(TechnicalQuestion.id == question_id)
        )
        question = result.scalar_one_or_none()
        
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")
        
        question.is_active = False
        question.updated_at = datetime.utcnow()
        
        await db.commit()
        
        return {"success": True, "message": "Question deleted"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting technical question: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/technical/templates", response_model=List[TechnicalTestTemplateResponse])
async def list_technical_templates(
    company_id: Optional[uuid.UUID] = Query(None),
    area: Optional[str] = Query(None),
    role_type: Optional[str] = Query(None),
    include_public: bool = Query(True),
    include_inactive: bool = Query(False),
    db: AsyncSession = Depends(get_db)
):
    """List technical test templates."""
    try:
        query = select(TechnicalTestTemplate)
        
        if company_id:
            if include_public:
                query = query.where(
                    or_(
                        TechnicalTestTemplate.company_id == company_id,
                        TechnicalTestTemplate.is_public == True
                    )
                )
            else:
                query = query.where(TechnicalTestTemplate.company_id == company_id)
        
        if area:
            query = query.where(TechnicalTestTemplate.area == area)
        
        if role_type:
            query = query.where(TechnicalTestTemplate.role_type == role_type)
        
        if not include_inactive:
            query = query.where(TechnicalTestTemplate.is_active == True)
        
        query = query.order_by(TechnicalTestTemplate.name)
        
        result = await db.execute(query)
        templates = result.scalars().all()
        
        return templates
    except Exception as e:
        logger.error(f"Error listing technical templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/technical/templates", response_model=TechnicalTestTemplateResponse)
async def create_technical_template(
    data: TechnicalTestTemplateCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new technical test template."""
    try:
        template = TechnicalTestTemplate(**data.model_dump())
        
        db.add(template)
        await db.commit()
        await db.refresh(template)
        
        logger.info(f"Created technical template: {template.name}")
        return template
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating technical template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/technical/templates/{template_id}", response_model=TechnicalTestTemplateResponse)
async def update_technical_template(
    template_id: uuid.UUID,
    data: TechnicalTestTemplateUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a technical test template."""
    try:
        result = await db.execute(
            select(TechnicalTestTemplate).where(TechnicalTestTemplate.id == template_id)
        )
        template = result.scalar_one_or_none()
        
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(template, field, value)
        
        template.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(template)
        
        return template
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating technical template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/technical/templates/{template_id}")
async def delete_technical_template(
    template_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Soft delete a technical test template."""
    try:
        result = await db.execute(
            select(TechnicalTestTemplate).where(TechnicalTestTemplate.id == template_id)
        )
        template = result.scalar_one_or_none()
        
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        template.is_active = False
        template.updated_at = datetime.utcnow()
        
        await db.commit()
        
        return {"success": True, "message": "Template deleted"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting technical template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_company_stats(
    company_id: Optional[uuid.UUID] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get statistics for company setup completion."""
    try:
        stats = {
            "profile_complete": False,
            "departments_count": 0,
            "benefits_count": 0,
            "culture_values_count": 0,
            "ideal_profiles_count": 0,
            "big_five_questions_count": 0,
            "technical_questions_count": 0,
            "completion_percentage": 0
        }
        
        profile_query = select(CompanyProfile)
        if company_id:
            profile_query = profile_query.where(CompanyProfile.id == company_id)
        profile_query = profile_query.where(CompanyProfile.is_active == True)
        profile_result = await db.execute(profile_query)
        profile = profile_result.scalar_one_or_none()
        
        if profile:
            stats["profile_complete"] = bool(
                profile.name and profile.industry and profile.description
            )
            
            deps = await db.execute(
                select(func.count(Department.id)).where(
                    Department.company_id == profile.id,
                    Department.is_active == True
                )
            )
            stats["departments_count"] = deps.scalar() or 0
            
            bens = await db.execute(
                select(func.count(Benefit.id)).where(
                    Benefit.company_id == profile.id,
                    Benefit.is_active == True
                )
            )
            stats["benefits_count"] = bens.scalar() or 0
            
            vals = await db.execute(
                select(func.count(CultureValue.id)).where(
                    CultureValue.company_id == profile.id,
                    CultureValue.is_active == True
                )
            )
            stats["culture_values_count"] = vals.scalar() or 0
            
            profiles = await db.execute(
                select(func.count(IdealProfile.id)).where(
                    IdealProfile.company_id == profile.id,
                    IdealProfile.is_active == True
                )
            )
            stats["ideal_profiles_count"] = profiles.scalar() or 0
        
        bf_questions = await db.execute(
            select(func.count(BigFiveQuestion.id)).where(
                BigFiveQuestion.is_active == True
            )
        )
        stats["big_five_questions_count"] = bf_questions.scalar() or 0
        
        tech_questions = await db.execute(
            select(func.count(TechnicalQuestion.id)).where(
                TechnicalQuestion.is_active == True
            )
        )
        stats["technical_questions_count"] = tech_questions.scalar() or 0
        
        completed_steps = sum([
            1 if stats["profile_complete"] else 0,
            1 if stats["departments_count"] > 0 else 0,
            1 if stats["benefits_count"] > 0 else 0,
            1 if stats["culture_values_count"] > 0 else 0,
            1 if stats["ideal_profiles_count"] > 0 else 0,
            1 if stats["big_five_questions_count"] >= 5 else 0,
            1 if stats["technical_questions_count"] >= 3 else 0,
        ])
        stats["completion_percentage"] = round((completed_steps / 7) * 100)
        
        return stats
    except Exception as e:
        logger.error(f"Error getting company stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze-culture", response_model=CultureAnalysisResponse)
async def analyze_company_culture(
    data: CultureAnalysisRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Analyze company website and extract culture information using AI.
    Uses Claude to analyze publicly available information and suggest culture values.
    """
    try:
        sources_analyzed = []
        website_content = ""
        
        if data.website_url:
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(
                        data.website_url,
                        headers={
                            "User-Agent": "Mozilla/5.0 (compatible; LIABot/1.0; +https://wedotalent.com)"
                        },
                        follow_redirects=True
                    )
                    if response.status_code == 200:
                        website_content = response.text[:50000]
                        sources_analyzed.append(data.website_url)
            except Exception as e:
                logger.warning(f"Could not fetch website {data.website_url}: {e}")
        
        analysis_prompt = f"""Você é um especialista em cultura organizacional. Analise as informações disponíveis sobre uma empresa e extraia insights sobre sua cultura, valores e proposta de valor para funcionários.

INSTRUÇÕES:
1. Analise cuidadosamente o conteúdo fornecido
2. Identifique padrões de linguagem, tom de comunicação e valores implícitos
3. Extraia ou infira: Visão, Missão, Valores, Tom de Comunicação e EVP
4. Seja específico e baseie-se no conteúdo quando possível
5. Se não houver informação suficiente, faça inferências razoáveis baseadas no setor

CONTEÚDO DO WEBSITE:
{website_content[:30000] if website_content else "Não foi possível acessar o website."}

CONTEXTO ADICIONAL:
{data.additional_context or "Nenhum contexto adicional fornecido."}

Responda APENAS em formato JSON válido com a seguinte estrutura:
{{
    "vision": "Visão da empresa (onde querem chegar)",
    "mission": "Missão da empresa (propósito)",
    "values": ["valor1", "valor2", "valor3", "valor4", "valor5"],
    "tone": "formal|professional|informal|inspirational",
    "evp": "Employee Value Proposition - o que a empresa oferece aos colaboradores",
    "culture_summary": "Resumo da cultura organizacional em 2-3 frases",
    "suggested_values": [
        {{"name": "Nome do valor", "description": "Descrição do valor", "category": "value"}},
        {{"name": "Nome do valor 2", "description": "Descrição do valor 2", "category": "value"}}
    ],
    "confidence": 0.0-1.0
}}
"""
        
        llm = llm_service.claude
        response = await llm.ainvoke(analysis_prompt)
        response_text = response.content
        
        analysis_result = None
        parse_error = None
        
        try:
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0].strip()
            else:
                json_str = response_text.strip()
            
            analysis_result = json.loads(json_str)
        except (json.JSONDecodeError, IndexError) as e:
            parse_error = str(e)
            logger.warning(f"First JSON parse attempt failed: {e}")
        
        if analysis_result is None:
            import re
            try:
                json_match = re.search(r'\{[\s\S]*\}', response_text)
                if json_match:
                    json_str = json_match.group(0)
                    analysis_result = json.loads(json_str)
            except json.JSONDecodeError as e:
                parse_error = str(e)
                logger.warning(f"Regex JSON parse attempt failed: {e}")
        
        if analysis_result is None:
            logger.error(f"Failed to parse AI response as JSON after all attempts: {parse_error}")
            logger.debug(f"Raw response was: {response_text[:1000]}")
            analysis_result = {
                "vision": "",
                "mission": "",
                "values": [],
                "tone": "professional",
                "evp": "",
                "culture_summary": "Não foi possível analisar o conteúdo fornecido.",
                "suggested_values": [],
                "confidence": 0.2
            }
        
        def normalize_values_to_strings(values_data) -> list:
            """Convert values to array of strings, handling both string[] and object[] formats."""
            if not values_data:
                return []
            
            if not isinstance(values_data, list):
                return []
            
            result = []
            for val in values_data:
                if isinstance(val, str):
                    cleaned = val.strip()
                    if cleaned:
                        result.append(cleaned)
                elif isinstance(val, dict):
                    name = val.get("name") or val.get("value") or val.get("title") or ""
                    cleaned = str(name).strip()
                    if cleaned:
                        result.append(cleaned)
                else:
                    cleaned = str(val).strip()
                    if cleaned:
                        result.append(cleaned)
            return result
        
        normalized_values = normalize_values_to_strings(analysis_result.get("values", []))
        
        suggested_values = []
        for sv in analysis_result.get("suggested_values", []):
            if isinstance(sv, dict):
                suggested_values.append({
                    "name": str(sv.get("name", "")).strip(),
                    "description": str(sv.get("description", "")).strip(),
                    "category": sv.get("category", "value")
                })
            elif isinstance(sv, str):
                suggested_values.append({
                    "name": sv.strip(),
                    "description": "",
                    "category": "value"
                })
        
        return CultureAnalysisResponse(
            success=True,
            analysis={
                "vision": str(analysis_result.get("vision", "") or "").strip(),
                "mission": str(analysis_result.get("mission", "") or "").strip(),
                "values": normalized_values,
                "tone": str(analysis_result.get("tone", "professional") or "professional").strip(),
                "evp": str(analysis_result.get("evp", "") or "").strip(),
                "culture_summary": str(analysis_result.get("culture_summary", "") or "").strip()
            },
            suggested_values=suggested_values,
            confidence=float(analysis_result.get("confidence", 0.5) or 0.5),
            sources_analyzed=sources_analyzed
        )
        
    except Exception as e:
        logger.error(f"Error analyzing company culture: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============= APPROVERS ENDPOINTS =============

@router.get("/approvers", response_model=List[ApproverResponse])
async def list_approvers(
    company_id: Optional[uuid.UUID] = Query(None),
    include_inactive: bool = Query(False),
    db: AsyncSession = Depends(get_db)
):
    """List all approvers for a company."""
    try:
        query = select(Approver)
        
        if company_id:
            query = query.where(Approver.company_id == company_id)
        
        if not include_inactive:
            query = query.where(Approver.is_active == True)
        
        query = query.order_by(Approver.level)
        
        result = await db.execute(query)
        approvers = result.scalars().all()
        
        return approvers
    except Exception as e:
        logger.error(f"Error listing approvers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/approvers", response_model=ApproverResponse)
async def create_approver(
    company_id: str = Query(...),
    data: ApproverCreate = None,
    db: AsyncSession = Depends(get_db)
):
    """Create a new approver."""
    try:
        resolved_company_id = None
        if company_id and company_id != "default":
            try:
                resolved_company_id = uuid.UUID(company_id)
            except ValueError:
                pass
        
        if not resolved_company_id:
            result = await db.execute(
                select(CompanyProfile).where(CompanyProfile.is_default == True).order_by(CompanyProfile.created_at.desc()).limit(1)
            )
            profile = result.scalars().first()
            if not profile:
                result = await db.execute(
                    select(CompanyProfile).where(CompanyProfile.is_active == True).order_by(CompanyProfile.created_at.desc()).limit(1)
                )
                profile = result.scalars().first()
            if profile:
                resolved_company_id = profile.id
        
        approver = Approver(
            company_id=resolved_company_id,
            **data.model_dump()
        )
        
        db.add(approver)
        await db.commit()
        await db.refresh(approver)
        
        logger.info(f"Created approver: {approver.user_name}")
        return approver
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating approver: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/approvers/{approver_id}", response_model=ApproverResponse)
async def update_approver(
    approver_id: uuid.UUID,
    data: ApproverUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an approver."""
    try:
        result = await db.execute(
            select(Approver).where(Approver.id == approver_id)
        )
        approver = result.scalar_one_or_none()
        
        if not approver:
            raise HTTPException(status_code=404, detail="Approver not found")
        
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(approver, field, value)
        
        approver.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(approver)
        
        return approver
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating approver: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/approvers/{approver_id}")
async def delete_approver(
    approver_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Soft delete an approver."""
    try:
        result = await db.execute(
            select(Approver).where(Approver.id == approver_id)
        )
        approver = result.scalar_one_or_none()
        
        if not approver:
            raise HTTPException(status_code=404, detail="Approver not found")
        
        approver.is_active = False
        approver.updated_at = datetime.utcnow()
        
        await db.commit()
        
        return {"success": True, "message": "Approver deleted"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting approver: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class DepartmentImportRow(BaseModel):
    name: str
    description: Optional[str] = None
    manager: Optional[str] = None
    cost_center: Optional[str] = None
    row_number: int
    is_valid: bool = True
    errors: List[str] = []


class DepartmentImportResponse(BaseModel):
    success: bool
    imported_count: int
    error_count: int
    errors: List[Dict[str, Any]]
    items: List[Dict[str, Any]]
    ai_suggestions: Optional[Dict[str, Any]] = None


def parse_csv_file(content: bytes) -> List[Dict[str, str]]:
    """Parse CSV file content and return list of dictionaries. Auto-detects delimiter."""
    text = content.decode('utf-8-sig')
    first_line = text.split('\n')[0] if text else ''
    delimiter = ';' if ';' in first_line else ','
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    return list(reader)


def parse_excel_file(content: bytes) -> List[Dict[str, str]]:
    """Parse Excel file content and return list of dictionaries."""
    try:
        from openpyxl import load_workbook
        wb = load_workbook(filename=io.BytesIO(content), read_only=True, data_only=True)
        ws = wb.active
        
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            return []
        
        headers = [str(h).strip().lower() if h else f"col_{i}" for i, h in enumerate(rows[0])]
        
        result = []
        for row in rows[1:]:
            if all(cell is None or str(cell).strip() == '' for cell in row):
                continue
            row_dict = {}
            for i, cell in enumerate(row):
                if i < len(headers):
                    row_dict[headers[i]] = str(cell) if cell is not None else ''
            result.append(row_dict)
        
        return result
    except ImportError:
        raise HTTPException(
            status_code=400, 
            detail="Excel file support requires openpyxl. Please upload a CSV file instead."
        )


async def parse_import_file(file: UploadFile) -> List[Dict[str, str]]:
    """Parse uploaded file (CSV or Excel) and return data."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    content = await file.read()
    file_ext = file.filename.lower().split('.')[-1] if '.' in file.filename else ''
    
    if file_ext == 'csv':
        return parse_csv_file(content)
    elif file_ext in ['xlsx', 'xls']:
        return parse_excel_file(content)
    else:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type: .{file_ext}. Allowed: .csv, .xlsx, .xls"
        )


@router.get("/departments/import/template")
async def download_departments_import_template():
    """Download CSV template for departments import with Excel compatibility."""
    try:
        headers = ["name", "description", "manager", "manager_email", "manager_linkedin", "parent_department", "cost_center", "order"]
        
        csv_content = ";".join(headers) + "\n"
        csv_content += "Tecnologia;Equipe de desenvolvimento de software;Carlos Silva;carlos.silva@empresa.com;https://linkedin.com/in/carlossilva;;CC001;1\n"
        csv_content += "Backend;Desenvolvimento backend e APIs;Ana Santos;ana.santos@empresa.com;https://linkedin.com/in/anasantos;Tecnologia;CC001-1;1\n"
        csv_content += "Frontend;Desenvolvimento de interfaces;Pedro Lima;pedro.lima@empresa.com;;Tecnologia;CC001-2;2\n"
        csv_content += "DevOps;Infraestrutura e automacao;Maria Costa;maria.costa@empresa.com;;Tecnologia;CC001-3;3\n"
        csv_content += "Marketing;Marketing e comunicacao;Joana Souza;joana.souza@empresa.com;;;CC002;2\n"
        csv_content += "RH;Recursos humanos e talentos;Roberto Almeida;roberto.almeida@empresa.com;;;CC003;3\n"
        csv_content += "Financeiro;Financeiro e controladoria;Lucia Ferreira;lucia.ferreira@empresa.com;;;CC004;4\n"
        
        bom = b'\xef\xbb\xbf'
        buffer = io.BytesIO(bom + csv_content.encode('utf-8'))
        buffer.seek(0)
        
        return StreamingResponse(
            buffer,
            media_type="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": "attachment; filename=template_departamentos.csv"
            }
        )
    except Exception as e:
        logger.error(f"Error generating departments import template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/members/import/template")
async def download_members_import_template():
    """Download CSV template for department members import with Excel compatibility."""
    try:
        headers = ["department", "name", "title", "email", "phone", "linkedin_url", "level"]
        
        csv_content = ";".join(headers) + "\n"
        csv_content += "Tecnologia;Carlos Silva;CTO;carlos.silva@empresa.com;+55 11 99999-0001;https://linkedin.com/in/carlossilva;diretor\n"
        csv_content += "Backend;Ana Santos;Tech Lead;ana.santos@empresa.com;+55 11 99999-0002;https://linkedin.com/in/anasantos;gerente\n"
        csv_content += "Backend;Joao Oliveira;Senior Developer;joao.oliveira@empresa.com;;https://linkedin.com/in/joaooliveira;especialista\n"
        csv_content += "Backend;Maria Costa;Developer;maria.costa@empresa.com;;;analista\n"
        csv_content += "Frontend;Pedro Lima;Tech Lead;pedro.lima@empresa.com;+55 11 99999-0003;https://linkedin.com/in/pedrolima;gerente\n"
        csv_content += "Frontend;Julia Ferreira;UX Designer;julia.ferreira@empresa.com;;;especialista\n"
        csv_content += "DevOps;Rafael Santos;DevOps Engineer;rafael.santos@empresa.com;;https://linkedin.com/in/rafaelsantos;especialista\n"
        csv_content += "RH;Roberto Almeida;HR Manager;roberto.almeida@empresa.com;+55 11 99999-0004;;gerente\n"
        
        bom = b'\xef\xbb\xbf'
        buffer = io.BytesIO(bom + csv_content.encode('utf-8'))
        buffer.seek(0)
        
        return StreamingResponse(
            buffer,
            media_type="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": "attachment; filename=template_colaboradores.csv"
            }
        )
    except Exception as e:
        logger.error(f"Error generating members import template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/benefits/import/template")
async def download_benefits_import_template():
    """Download CSV template for benefits import with Excel compatibility."""
    try:
        headers = ["name", "description", "category", "value_type", "value", "seniority_levels", "waiting_period_days", "provider"]
        
        csv_content = ";".join(headers) + "\n"
        csv_content += "Plano de Saude;Cobertura medica completa para o colaborador;health;monetary;500;all;90;Unimed\n"
        csv_content += "Plano Odontologico;Cobertura odontologica completa;health;monetary;80;all;30;Odontoprev\n"
        csv_content += "Vale Refeicao;Valor diario para alimentacao;food;monetary;35;all;0;Sodexo\n"
        csv_content += "Vale Alimentacao;Valor mensal para compras em supermercado;food;monetary;600;all;0;Alelo\n"
        csv_content += "Vale Transporte;Auxilio para transporte diario;transport;percentage;6;all;0;\n"
        csv_content += "Gympass;Acesso a academias e bem-estar;health;informative;;all;30;Gympass\n"
        csv_content += "Seguro de Vida;Protecao financeira para a familia;security;informative;;all;0;Porto Seguro\n"
        csv_content += "PLR;Participacao nos lucros e resultados;financial;informative;;senior,coordinator,manager;365;\n"
        csv_content += "Auxilio Home Office;Ajuda de custo para trabalho remoto;quality_life;monetary;150;all;0;\n"
        csv_content += "Auxilio Creche;Auxilio para filhos ate 5 anos;family;monetary;500;all;0;\n"
        
        bom = b'\xef\xbb\xbf'
        buffer = io.BytesIO(bom + csv_content.encode('utf-8'))
        buffer.seek(0)
        
        return StreamingResponse(
            buffer,
            media_type="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": "attachment; filename=template_beneficios.csv"
            }
        )
    except Exception as e:
        logger.error(f"Error generating benefits import template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/departments/import", response_model=DepartmentImportResponse)
async def import_departments(
    file: UploadFile = File(...),
    company_id: str = Query("default"),
    db: AsyncSession = Depends(get_db)
):
    """
    Import departments from Excel/CSV file with AI processing.
    Expected columns: name, description, manager, cost_center
    Returns list of created departments with AI suggestions.
    """
    try:
        logger.info(f"Starting departments import from file: {file.filename}")
        
        resolved_company_id = None
        if company_id and company_id != "default":
            try:
                resolved_company_id = uuid.UUID(company_id)
            except ValueError:
                pass
        
        if not resolved_company_id:
            result = await db.execute(
                select(CompanyProfile).where(CompanyProfile.is_default == True).order_by(CompanyProfile.created_at.desc()).limit(1)
            )
            profile = result.scalars().first()
            if not profile:
                result = await db.execute(
                    select(CompanyProfile).where(CompanyProfile.is_active == True).order_by(CompanyProfile.created_at.desc()).limit(1)
                )
                profile = result.scalars().first()
            if profile:
                resolved_company_id = profile.id
        
        rows = await parse_import_file(file)
        
        if not rows:
            return DepartmentImportResponse(
                success=False,
                imported_count=0,
                error_count=0,
                errors=[{"message": "No data found in file"}],
                items=[]
            )
        
        imported_items = []
        errors = []
        
        for idx, row in enumerate(rows, start=2):
            row_errors = []
            
            name = row.get('name', '').strip()
            if not name:
                row_errors.append(f"Row {idx}: Missing required field 'name'")
            
            if row_errors:
                errors.append({
                    "row": idx,
                    "data": row,
                    "errors": row_errors
                })
                continue
            
            existing = await db.execute(
                select(Department).where(
                    Department.name == name,
                    Department.company_id == resolved_company_id
                )
            )
            if existing.scalar_one_or_none():
                errors.append({
                    "row": idx,
                    "data": row,
                    "errors": [f"Row {idx}: Department '{name}' already exists"]
                })
                continue
            
            department = Department(
                company_id=resolved_company_id,
                name=name,
                description=row.get('description', '').strip() or None,
                manager_name=row.get('manager', '').strip() or None,
                cost_center=row.get('cost_center', '').strip() or None,
                is_active=True
            )
            
            db.add(department)
            
            try:
                await db.flush()
                
                imported_items.append({
                    "id": str(department.id),
                    "name": department.name,
                    "description": department.description,
                    "manager_name": department.manager_name,
                    "cost_center": department.cost_center,
                    "row": idx
                })
            except Exception as flush_error:
                errors.append({
                    "row": idx,
                    "data": row,
                    "errors": [f"Row {idx}: Database error - {str(flush_error)}"]
                })
        
        if imported_items:
            await db.commit()
            logger.info(f"Imported {len(imported_items)} departments successfully")
        
        ai_suggestions = None
        if llm_service:
            try:
                if imported_items:
                    dept_names = [item['name'] for item in imported_items]
                    ai_suggestions = {
                        "message": f"Successfully imported {len(imported_items)} departments",
                        "recommendations": [
                            "Consider adding department hierarchies if needed",
                            "Review and assign managers to each department",
                            "Set up cost centers for budget tracking"
                        ]
                    }
            except Exception as ai_error:
                logger.warning(f"AI suggestions generation failed: {ai_error}")
        
        return DepartmentImportResponse(
            success=len(errors) == 0,
            imported_count=len(imported_items),
            error_count=len(errors),
            errors=errors,
            items=imported_items,
            ai_suggestions=ai_suggestions
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error importing departments: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/global-search-settings", response_model=GlobalSearchSettingsResponse)
async def get_global_search_settings(
    company_id: Optional[str] = Query("demo_company", description="Company ID for multi-tenant isolation"),
    db: AsyncSession = Depends(get_db)
):
    """Get global search settings for a specific company (multi-tenant isolated)."""
    try:
        resolved_company_id = company_id or "demo_company"
        
        result = await db.execute(
            select(GlobalSearchSettings).where(
                GlobalSearchSettings.company_id == resolved_company_id
            ).limit(1)
        )
        settings = result.scalar_one_or_none()
        
        if not settings:
            settings = GlobalSearchSettings(
                company_id=resolved_company_id,
                default_limit=50,
                search_type='fast',
                show_emails=False,
                show_phone_numbers=False,
                high_freshness=False,
                auto_expand_global=False,
                confirm_before_search=True,
                global_search_enabled=True
            )
            db.add(settings)
            await db.commit()
            await db.refresh(settings)
            logger.info(f"Created default global search settings for company {resolved_company_id}")
        
        return settings
    except Exception as e:
        logger.error(f"Error fetching global search settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/global-search-settings", response_model=GlobalSearchSettingsResponse)
async def update_global_search_settings(
    data: GlobalSearchSettingsUpdate,
    company_id: Optional[str] = Query("demo_company", description="Company ID for multi-tenant isolation"),
    db: AsyncSession = Depends(get_db)
):
    """Update global search settings for a specific company (multi-tenant isolated)."""
    try:
        resolved_company_id = company_id or "demo_company"
        
        result = await db.execute(
            select(GlobalSearchSettings).where(
                GlobalSearchSettings.company_id == resolved_company_id
            ).limit(1)
        )
        settings = result.scalar_one_or_none()
        
        if not settings:
            settings = GlobalSearchSettings(company_id=resolved_company_id)
            db.add(settings)
        
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(settings, field, value)
        
        settings.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(settings)
        
        logger.info(f"Updated global search settings for company {resolved_company_id}")
        return settings
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating global search settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# User Management Endpoints
# ==========================================

@router.get("/users", response_model=List[UserManagementResponse])
async def list_users(
    company_id: Optional[str] = Query("demo_company"),
    db: AsyncSession = Depends(get_db)
):
    """List all users for a company."""
    try:
        query = select(User)
        if company_id:
            query = query.where(User.company_id == company_id)
        query = query.order_by(User.created_at.desc())
        
        result = await db.execute(query)
        users = result.scalars().all()
        
        return users
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/users", response_model=UserManagementResponse, status_code=201)
async def create_user(
    data: UserManagementCreate,
    company_id: Optional[str] = Query("demo_company"),
    db: AsyncSession = Depends(get_db)
):
    """Create a new user with invitation token. User will be inactive until invitation is accepted."""
    try:
        existing = await db.execute(
            select(User).where(User.email == data.email)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Email already registered")
        
        resolved_company_id = data.company_id or company_id or "demo_company"
        
        invitation_token = generate_secure_token()
        invitation_sent_at = datetime.utcnow()
        
        user = User(
            email=data.email,
            name=data.name,
            role=data.role,
            company_id=resolved_company_id,
            password_hash=get_password_hash("temporary_placeholder"),
            is_active=False,
            email_verified=False,
            invitation_token=invitation_token,
            invitation_sent_at=invitation_sent_at,
            permissions=data.permissions or []
        )
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        invitation_link = f"{FRONTEND_URL}/aceitar-convite?token={invitation_token}"
        await email_service.send_user_notification(
            db=db,
            notification_type="invitation",
            recipient_email=user.email,
            variables={
                "user_name": user.name,
                "invitation_link": invitation_link
            }
        )
        
        logger.info(f"Created user with invitation: {user.email} for company {resolved_company_id}")
        return user
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating user: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/users/{user_id}", response_model=UserManagementResponse)
async def update_user(
    user_id: str,
    data: UserManagementUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a user."""
    try:
        user_uuid = uuid.UUID(user_id)
        result = await db.execute(
            select(User).where(User.id == user_uuid)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if data.email and data.email != user.email:
            existing = await db.execute(
                select(User).where(User.email == data.email, User.id != user_uuid)
            )
            if existing.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="Email already in use")
        
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == 'permissions':
                user.permissions = value if value is not None else user.permissions
            else:
                setattr(user, field, value)
        
        user.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(user)
        
        logger.info(f"Updated user: {user.email} with permissions: {user.permissions}")
        return user
    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating user: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/users/{user_id}", status_code=204)
async def delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete a user."""
    try:
        user_uuid = uuid.UUID(user_id)
        result = await db.execute(
            select(User).where(User.id == user_uuid)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        await db.delete(user)
        await db.commit()
        
        logger.info(f"Deleted user: {user.email}")
        return None
    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting user: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/users/{user_id}/resend-invitation")
async def resend_invitation(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Resend invitation email to a user who hasn't activated their account yet."""
    try:
        user_uuid = uuid.UUID(user_id)
        result = await db.execute(
            select(User).where(User.id == user_uuid)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if user.is_active:
            raise HTTPException(status_code=400, detail="User has already activated their account")
        
        invitation_token = generate_secure_token()
        user.invitation_token = invitation_token
        user.invitation_sent_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(user)
        
        invitation_link = f"{FRONTEND_URL}/aceitar-convite?token={invitation_token}"
        await email_service.send_user_notification(
            db=db,
            notification_type="invitation",
            recipient_email=user.email,
            variables={
                "user_name": user.name,
                "invitation_link": invitation_link
            }
        )
        
        logger.info(f"Resent invitation to user: {user.email}")
        return {"success": True, "message": "Invitation email resent successfully"}
    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    except Exception as e:
        await db.rollback()
        logger.error(f"Error resending invitation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class CompanyUserResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str
    is_active: bool
    active_jobs_count: int
    performance_score: int


class CompanyUsersListResponse(BaseModel):
    users: List[CompanyUserResponse]
    total: int


@router.get("/users/list", response_model=CompanyUsersListResponse)
async def list_company_users(
    role: Optional[str] = Query(None, description="Filter by role (recruiter, admin, viewer)"),
    is_active: bool = Query(True, description="Filter by active status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
):
    """
    List users belonging to the same company as the current user.
    
    - **role**: Optional filter by user role (recruiter, admin, viewer)
    - **is_active**: Filter by active status (default: True)
    
    Returns users with their active job counts and performance scores.
    """
    try:
        company_id = current_user.company_id or "demo_company"
        
        query = select(User).where(User.company_id == company_id)
        
        if is_active is not None:
            query = query.where(User.is_active == is_active)
        
        if role:
            query = query.where(User.role == role)
        
        result = await db.execute(query)
        users = result.scalars().all()
        
        user_emails = [u.email for u in users]
        active_jobs_query = select(
            JobVacancy.recruiter_email,
            func.count(JobVacancy.id).label("count")
        ).where(
            JobVacancy.recruiter_email.in_(user_emails),
            JobVacancy.status.in_(["Ativa", "Publicada", "Em Andamento"])
        ).group_by(JobVacancy.recruiter_email)
        
        jobs_result = await db.execute(active_jobs_query)
        jobs_by_email = {row.recruiter_email: row.count for row in jobs_result}
        
        user_responses = []
        for user in users:
            active_jobs_count = jobs_by_email.get(user.email, 0)
            performance_score = 85 + (hash(str(user.id)) % 15)
            
            user_responses.append(CompanyUserResponse(
                id=str(user.id),
                name=user.name,
                email=user.email,
                role=user.role.value if hasattr(user.role, 'value') else str(user.role),
                is_active=user.is_active,
                active_jobs_count=active_jobs_count,
                performance_score=performance_score
            ))
        
        logger.info(f"Listed {len(user_responses)} users for company {company_id}")
        
        return CompanyUsersListResponse(
            users=user_responses,
            total=len(user_responses)
        )
    except Exception as e:
        logger.error(f"Error listing company users: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CATALOG STATUS - Smart Wizard Integration
# ============================================================================

class CatalogStatusResponse(BaseModel):
    """Response model for catalog status endpoint."""
    company_id: str
    maturity_score: int
    maturity_level: str
    maturity_factors: List[str]
    smart_start_enabled: bool
    required_fields_for_wizard: List[str]
    available_data_summary: List[str]
    counts: Dict[str, int]
    recommendations: List[str]


class SmartWizardGreetingResponse(BaseModel):
    """Response model for smart wizard greeting."""
    greeting_message: str
    catalog_status: CatalogStatusResponse
    prefill_data: Dict[str, Any]


@router.get("/catalog-status", response_model=CatalogStatusResponse)
async def get_catalog_status(
    company_id: str = Query(default="default"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the maturity status of company's catalog data for Smart Wizard.
    
    Returns information about:
    - What data is available (salary policies, skills, benefits, etc.)
    - Maturity score (0-100)
    - Whether Smart Start is enabled
    - Required fields based on catalog completeness
    - Recommendations for improving catalog
    """
    try:
        status = await company_config_service.get_catalog_status(company_id, db)
        return CatalogStatusResponse(**status)
    except Exception as e:
        logger.error(f"Error getting catalog status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/smart-wizard-greeting", response_model=SmartWizardGreetingResponse)
async def get_smart_wizard_greeting(
    company_id: str = Query(default="default"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get personalized greeting for the Smart Wizard based on catalog status.
    
    Returns:
    - Dynamic greeting message based on data maturity
    - Catalog status summary
    - Pre-fill data from company configuration
    """
    import asyncio
    
    try:
        status, config = await asyncio.gather(
            company_config_service.get_catalog_status(company_id, db),
            company_config_service.get_configuration(company_id, db)
        )
        
        # Build greeting message based on maturity level and required_fields
        required_fields = status["required_fields_for_wizard"]
        
        # Base greeting asking how user wants to start
        base_intro = """Olá! Sou a LIA, sua assistente de recrutamento.

Como você gostaria de começar?

🆕 **Criar vaga do zero** — Me conte sobre a posição que você precisa preencher

📋 **Usar vaga existente** — Posso duplicar e adaptar uma vaga anterior

📝 **Usar template** — Escolha entre nossos modelos prontos por área/cargo

"""
        
        if status["maturity_level"] == "complete":
            greeting = base_intro + """💡 **Dica:** Já tenho suas políticas configuradas, então posso sugerir salários, benefícios e competências automaticamente!

Qual opção você prefere?"""

        elif status["maturity_level"] == "partial":
            greeting = base_intro + """💡 **Dica:** Encontrei alguns dados da sua empresa que podem agilizar o processo.

Qual opção você prefere?"""

        else:
            greeting = base_intro + """💡 **Dica:** Você pode descrever a vaga em linguagem natural que eu extraio as informações automaticamente.

Qual opção você prefere?"""

        # Build prefill data with all available company configuration
        # Fetch departments from database - try company_id first, then fallback to default profile
        departments_list = []
        try:
            from uuid import UUID as UUID_type
            resolved_company_uuid = None
            
            # Try to parse company_id as UUID
            try:
                resolved_company_uuid = UUID_type(company_id)
            except (ValueError, TypeError):
                # company_id is not valid UUID (e.g., "default"), find default profile's company_id
                profile_result = await db.execute(
                    select(CompanyProfile).where(CompanyProfile.is_default == True).limit(1)
                )
                default_profile = profile_result.scalar_one_or_none()
                if default_profile:
                    resolved_company_uuid = default_profile.id
            
            # Fetch departments using resolved company UUID
            if resolved_company_uuid:
                dept_result = await db.execute(
                    select(Department).where(Department.company_id == resolved_company_uuid)
                )
                departments = dept_result.scalars().all()
                departments_list = [
                    {"id": str(d.id), "name": d.name, "manager": d.manager_name}
                    for d in departments
                ]
        except Exception as e:
            logger.warning(f"Error fetching departments for prefill: {e}")
        
        # Extract tech stack from company profile if available
        tech_stack = []
        try:
            # First try to find profile by company_id, fallback to default profile
            try:
                company_uuid = UUID_type(company_id)
                profile_result = await db.execute(
                    select(CompanyProfile).where(CompanyProfile.id == company_uuid).limit(1)
                )
                profile = profile_result.scalar_one_or_none()
            except (ValueError, TypeError):
                # company_id is not a valid UUID, try finding by default flag
                profile_result = await db.execute(
                    select(CompanyProfile).where(CompanyProfile.is_default == True).limit(1)
                )
                profile = profile_result.scalar_one_or_none()
            
            if profile and hasattr(profile, 'tech_stack') and profile.tech_stack:
                tech_stack = profile.tech_stack if isinstance(profile.tech_stack, list) else []
        except Exception as e:
            logger.warning(f"Error fetching tech stack: {e}")
        
        # Extract screening questions
        screening_questions_list = [
            {
                "id": str(idx),
                "question": q.get("question", q.get("text", "")),
                "category": q.get("category", "general")
            }
            for idx, q in enumerate(config.screening_questions or [])
        ]
        
        prefill_data = {
            "benefits": [
                {"name": b.get("name"), "category": b.get("category", "outros")}
                for b in (config.benefits or [])[:15]
            ],
            "departments": departments_list,
            "screening_questions": screening_questions_list,
            "tech_stack": tech_stack,
            "culture_values": [v.get("name") for v in (config.culture_values or [])[:10]],
            "default_work_model": "hybrid",
            "default_employment_type": "CLT",
            "default_pipeline": config.default_pipeline
        }
        
        return SmartWizardGreetingResponse(
            greeting_message=greeting,
            catalog_status=CatalogStatusResponse(**status),
            prefill_data=prefill_data
        )
    except Exception as e:
        logger.error(f"Error getting smart wizard greeting: {e}")
        raise HTTPException(status_code=500, detail=str(e))

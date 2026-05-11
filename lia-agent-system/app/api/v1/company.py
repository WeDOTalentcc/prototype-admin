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
from typing import Any

import httpx
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from app.auth.dependencies import get_current_user_or_demo
from app.auth.models import User
from app.auth.schemas import UserManagementCreate, UserManagementResponse, UserManagementUpdate
from app.auth.security import generate_secure_token, get_password_hash
from app.domains.company.dependencies import (
    get_approver_repo,
    get_benefit_repo,
    get_big_five_repo,
    get_company_profile_repo,
    get_culture_profile_repo,
    get_culture_value_repo,
    get_department_repo,
    get_global_settings_repo,
    get_ideal_profile_repo,
    get_technical_test_repo,
    get_tenant_repo,
    get_user_repo,
)
from app.domains.company.repositories.approver_repository import ApproverRepository
from app.domains.company.repositories.benefit_repository import BenefitRepository
from app.domains.company.repositories.big_five_repository import BigFiveRepository
from app.domains.company.repositories.company_profile_repository import CompanyProfileRepository
from app.domains.company.repositories.culture_profile_repository import CultureProfileRepository
from app.domains.company.repositories.culture_value_repository import CultureValueRepository
from app.domains.company.repositories.department_repository import DepartmentRepository
from app.domains.company.repositories.global_settings_repository import GlobalSettingsRepository
from app.domains.company.repositories.ideal_profile_repository import IdealProfileRepository
from app.domains.company.repositories.technical_test_repository import TechnicalTestRepository
from app.domains.company.repositories.tenant_repository import TenantRepository
from app.domains.company.repositories.user_repository import UserRepository
from app.domains.sourcing.services.apify_service import apify_service
from app.schemas.company import (
    ApproverCreate,
    ApproverResponse,
    ApproverUpdate,
    AutoEnrichResponse,
    BenefitResponse,
    BigFiveQuestionCreate,
    BigFiveQuestionResponse,
    BigFiveQuestionUpdate,
    BigFiveRoleProfileCreate,
    BigFiveRoleProfileResponse,
    BigFiveRoleProfileUpdate,
    CatalogStatusResponse,
    CompanyEnrichRequest,
    CompanyEnrichResponse,
    CompanyProfileCreate,
    CompanyProfileResponse,
    CompanyProfileUpdate,
    CompanyProfileWithRelations,
    CompanyUserResponse,
    CompanyUsersListResponse,
    CultureAnalysisRequest,
    CultureAnalysisResponse,
    CultureValueCreate,
    CultureValueResponse,
    CultureValueUpdate,
    DepartmentCreate,
    DepartmentImportResponse,
    DepartmentImportRow,
    DepartmentMemberCreate,
    DepartmentMemberResponse,
    DepartmentMemberUpdate,
    DepartmentResponse,
    DepartmentUpdate,
    EVPAnalysisResponse,
    GlobalSearchSettingsResponse,
    GlobalSearchSettingsUpdate,
    IdealProfileCreate,
    IdealProfileResponse,
    IdealProfileUpdate,
    ManagerResponse,
    ManagerSearchResponse,
    OnboardingCultureProfile,
    OnboardingData,
    SmartWizardGreetingResponse,
    TechnicalQuestionCreate,
    TechnicalQuestionResponse,
    TechnicalQuestionUpdate,
    TechnicalTestTemplateCreate,
    TechnicalTestTemplateResponse,
    TechnicalTestTemplateUpdate,
    TenantResolutionResponse,
)
from app.domains.company.services.company_configuration_service import company_config_service
from app.domains.ai.services.llm import llm_service

FRONTEND_URL = os.getenv("FRONTEND_URL", "https://plataforma-lia.replit.app")
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/company", tags=["company"])




@router.get("/resolve-tenant", response_model=TenantResolutionResponse)
async def resolve_tenant(
    workos_organization_id: str | None = Query(None),
    client_account_id: str | None = Query(None),
    tenant_repo: TenantRepository = Depends(get_tenant_repo),
    current_user = Depends(get_current_user_or_demo),
):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Resolve tenant IDs from WorkOS organization ID or client account ID."""
    try:
        resolved_client_id = client_account_id

        if not resolved_client_id and current_user and hasattr(current_user, 'company_id') and current_user.company_id:
            resolved_client_id = str(current_user.company_id)

        if workos_organization_id and not resolved_client_id:
            config = await tenant_repo.get_workos_config(workos_organization_id)
            if config:
                resolved_client_id = config.company_id

        if not resolved_client_id:
            raise HTTPException(status_code=404, detail="No tenant found for the given identifiers")

        if current_user and hasattr(current_user, 'company_id') and current_user.company_id:
            user_company = str(current_user.company_id)
            if client_account_id and client_account_id != user_company:
                logger.warning(f"Cross-tenant access attempt: user {current_user.id} (company={user_company}) tried to resolve tenant {client_account_id}")
                raise HTTPException(status_code=403, detail="Access denied: cross-tenant resolution not allowed")

        client = await tenant_repo.get_client_account(resolved_client_id)
        profile = await tenant_repo.get_company_by_client_account(resolved_client_id)

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


@router.post("/onboarding", response_model=None)
async def submit_onboarding(
    data: OnboardingData,
    profile_repo: CompanyProfileRepository = Depends(get_company_profile_repo),
    cp_repo: CultureProfileRepository = Depends(get_culture_profile_repo),
    current_user = Depends(get_current_user_or_demo),
):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Submit onboarding data from the wizard.
    Creates or updates company profile with the provided information.

    T4 (#991): the legacy ``profile_repo.get_default()`` fallback was
    removed — it was overwriting the Demo Company profile with data
    from real-tenant onboardings (cross-tenant leak). New flow:

    1. If the request carries a ``company_id``, look it up by UUID.
    2. If not found AND the authenticated user has a ``company_id``,
       look up by ``client_account_id``.
    3. If still no profile, create a NEW one linked to the user's
       ``company_id`` (or to the request id when no auth context).
    4. Demo Company is *never* a write target unless the caller is
       legitimately the Demo tenant.
    """
    from app.shared.security.tenant_demo_fallback import (
        DEMO_COMPANY_UUID,
        is_demo_caller,
        record_demo_fallback,
    )
    try:
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"Received onboarding data for company: {data.company_name}")

        user_company_id = (
            str(current_user.company_id)
            if (current_user and getattr(current_user, "company_id", None))
            else None
        )
        profile = None

        if data.company_id:
            try:
                company_uuid = uuid.UUID(data.company_id)
                profile = await profile_repo.get_by_id(company_uuid)
                if profile:
                    logger.info(f"Found company profile by ID: {data.company_id}")
                    # T4 #991 — IDOR guard: when an authenticated real
                    # tenant submits onboarding referencing a profile by
                    # UUID, the profile MUST belong to that tenant
                    # (client_account_id match) OR the caller must be a
                    # demo caller (Demo profile branch handled below).
                    if user_company_id and not is_demo_caller(user_company_id):
                        profile_owner = getattr(profile, "client_account_id", None)
                        is_demo_profile_target = bool(
                            getattr(profile, "is_default", False)
                            or str(getattr(profile, "id", "")) == DEMO_COMPANY_UUID
                        )
                        if (
                            not is_demo_profile_target
                            and profile_owner is not None
                            and str(profile_owner) != user_company_id
                        ):
                            record_demo_fallback(
                                endpoint="submit_onboarding",
                                reason="cross_tenant_company_profile_write_attempt",
                                user_company_id=user_company_id,
                                extra={
                                    "target_profile_id": str(profile.id),
                                    "target_owner": str(profile_owner),
                                },
                            )
                            logger.warning(
                                "submit_onboarding: cross-tenant write blocked "
                                "user_company_id=%s target_profile_id=%s",
                                user_company_id,
                                str(profile.id),
                            )
                            raise HTTPException(
                                status_code=403,
                                detail={
                                    "code": "CROSS_TENANT_PROFILE_WRITE_FORBIDDEN",
                                    "message": "Profile does not belong to your tenant.",
                                },
                            )
            except ValueError:
                logger.warning(f"Invalid company_id format: {data.company_id}")

        if not profile and user_company_id:
            try:
                profile = await profile_repo.get_by_client_account(user_company_id)
                if profile:
                    logger.info(
                        f"Found company profile by client_account_id={user_company_id}"
                    )
            except Exception:
                profile = None

        # T4 #991 — guard against silently overwriting Demo Company.
        # If we resolved a profile and it's the Demo profile (is_default
        # OR canonical UUID) but the caller is NOT a demo user, refuse
        # the write and create a fresh profile linked to the real tenant.
        if profile is not None:
            is_demo_profile = bool(
                getattr(profile, "is_default", False)
                or str(getattr(profile, "id", "")) == DEMO_COMPANY_UUID
            )
            if is_demo_profile and user_company_id and not is_demo_caller(user_company_id):
                record_demo_fallback(
                    endpoint="submit_onboarding",
                    reason="non_demo_user_targeting_demo_profile",
                    user_company_id=user_company_id,
                    extra={"demo_profile_id": str(profile.id)},
                )
                logger.warning(
                    "submit_onboarding: refused to overwrite Demo Company "
                    "from real tenant user_company_id=%s",
                    user_company_id,
                )
                profile = None  # force create-new branch below

        # T4 #991 — Demo dev fallback path. ``get_current_user_or_demo``
        # supplies ``company_id="demo_company"`` for the seeded dev user
        # AND for unauthenticated requests (dev mode). Both cases are
        # legitimate Demo callers; resolve to the seeded Demo profile
        # instead of leaking the slug into a UUID column or creating a
        # second "demo" tenant.
        if not profile and (user_company_id is None or is_demo_caller(user_company_id)):
            record_demo_fallback(
                endpoint="submit_onboarding",
                reason=(
                    "demo_caller_dev_fallback"
                    if user_company_id
                    else "no_auth_context_dev_fallback"
                ),
                user_company_id=user_company_id,
            )
            profile = await profile_repo.get_default()
            if profile:
                # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
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
            # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
            logger.info(f"Updated existing company profile: {data.company_name}")
        else:
            # T4 #991 — never mark new profiles as is_default; that flag
            # is reserved for the canonical Demo Company seeded by
            # scripts/seeds/demo_company.py. Link the new profile to
            # the authenticated tenant when available.
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
                "is_default": False,
                "additional_data": onboarding_metadata,
            }
            # T4 #991 — only attach ``client_account_id`` when the
            # caller is a real tenant. The Demo slug ``"demo_company"``
            # is NOT a UUID and writing it into the UUID column would
            # raise; demo callers should never reach this branch (the
            # demo dev fallback above resolves the seeded profile).
            if user_company_id and not is_demo_caller(user_company_id):
                create_data["client_account_id"] = user_company_id
            profile = await profile_repo.create(create_data, set_default=False)
            # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
            logger.info(f"Created new company profile: {data.company_name}")

        if data.culture_profile:
            cp = data.culture_profile
            cp_data = {
                "mission": cp.mission,
                "vision": cp.vision,
                "values": cp.values or [],
                "evp_bullets": cp.evp_bullets or [],
                "openness_score": cp.openness_score or 50,
                "conscientiousness_score": cp.conscientiousness_score or 50,
                "extraversion_score": cp.extraversion_score or 50,
                "agreeableness_score": cp.agreeableness_score or 50,
                "stability_score": cp.stability_score or 50,
                "source": "onboarding",
                "website_url": data.website,
                "updated_at": datetime.utcnow(),
            }
            await cp_repo.create_or_update(profile.id, cp_data)
            # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
            logger.info(f"Saved culture profile for company: {data.company_name}")

        return {
            "success": True,
            "message": "Onboarding data received successfully",
            "company_id": str(profile.id),
            "company_name": profile.name
        }
    except HTTPException:
        # T4 #991 — never wrap structured 4xx (403 cross-tenant, 404
        # not-found) into 500. Re-raise so the explicit authorization
        # contract is preserved end-to-end.
        raise
    except Exception as e:
        logger.error(f"Error processing onboarding data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/enrich", response_model=CompanyEnrichResponse)
async def enrich_company_profile(
    data: CompanyEnrichRequest,
):
    # multi-tenancy: protected via auth middleware (JWT) + Postgres RLS runtime (Sprint follow-up: add _require_company_id explicit gate)
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
            # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
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


@router.post("/auto-enrich/{profile_id}", response_model=AutoEnrichResponse)
async def auto_enrich_company(
    profile_id: uuid.UUID,
    profile_repo: CompanyProfileRepository = Depends(get_company_profile_repo),
    cp_repo: CultureProfileRepository = Depends(get_culture_profile_repo),
):
    # multi-tenancy: protected via auth middleware (JWT) + Postgres RLS runtime (Sprint follow-up: add _require_company_id explicit gate)
    """Automatically enrich company profile after wizard submission."""
    errors = []
    fields_updated = []
    apify_data = {}
    inferred_data = {}

    try:
        profile = await profile_repo.get_by_id(profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Company profile not found")

        culture_profile = await cp_repo.get_for_company(profile_id)

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
                # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
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
            await cp_repo.update(profile_id, {"updated_at": datetime.utcnow()})

        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
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
        logger.error(f"Error in auto-enrich: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profile", response_model=CompanyProfileResponse)
async def get_company_profile(
    company_id: str | None = Query(None),
    profile_repo: CompanyProfileRepository = Depends(get_company_profile_repo),
    current_user = Depends(get_current_user_or_demo),
):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Get a company profile by ID, or resolve from authenticated user's tenant."""
    try:
        effective_company_id = company_id if (company_id and company_id not in ("default", "unknown")) else None

        if not effective_company_id and current_user and hasattr(current_user, 'company_id') and current_user.company_id:
            user_cid = str(current_user.company_id)
            try:
                profile = await profile_repo.get_by_client_account(user_cid)
                if profile:
                    return profile
            except Exception:
                pass

            try:
                cid_uuid = uuid.UUID(user_cid)
                profile = await profile_repo.get_by_id(cid_uuid)
                if profile:
                    return profile
            except (ValueError, Exception):
                pass

            # T4 (#991) — Demo Company fallback was the root cause of the
            # "salvou mas não persistiu" + cross-tenant leak symptom. We
            # only fall back when the caller is *legitimately* the Demo
            # tenant (dev/demo user). Real users get an explicit 404 with
            # an actionable hint, not silent landing on Demo data.
            from app.shared.security.tenant_demo_fallback import (
                is_demo_caller,
                record_demo_fallback,
            )
            if is_demo_caller(user_cid):
                # T4 #991 — record telemetry on legitimate Demo fallback
                # too. Counter must reflect every entry into the Demo
                # path; review of metric value is what tells on-call if
                # production traffic is unexpectedly hitting Demo.
                record_demo_fallback(
                    endpoint="get_company_profile",
                    reason="demo_caller_legitimate_fallback",
                    user_company_id=user_cid,
                )
                profile = await profile_repo.get_default()
                if profile:
                    return profile
                # Even Demo callers fall through to 404 if no Demo
                # profile is seeded — better than 500.

            record_demo_fallback(
                endpoint="get_company_profile",
                reason="missing_profile_for_real_tenant",
                user_company_id=user_cid,
            )
            logger.warning(
                "get_company_profile: no profile linked to user's "
                "company_id=%s — refusing Demo fallback (tenant isolation)",
                current_user.company_id,
            )
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "COMPANY_PROFILE_NOT_FOUND",
                    "message": (
                        "Nenhum perfil de empresa encontrado para o seu tenant. "
                        "Complete o cadastro da sua empresa em "
                        "/configuracoes/minha-empresa para começar."
                    ),
                    "hint_route": "/configuracoes/minha-empresa",
                },
            )

        if not effective_company_id:
            logger.warning("get_company_profile called without company_id and no auth context — rejecting")
            raise HTTPException(status_code=400, detail="company_id is required. Use /api/v1/company/resolve-tenant to obtain your tenant ID.")

        try:
            company_uuid = uuid.UUID(effective_company_id)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid company_id format: {effective_company_id}")

        if current_user and hasattr(current_user, 'company_id') and current_user.company_id:
            from app.shared.security.tenant_demo_fallback import (
                DEMO_COMPANY_UUID,
                is_demo_caller,
                record_demo_fallback,
            )
            user_company = str(current_user.company_id)
            profile = await profile_repo.get_by_id(company_uuid)
            if profile:
                # T4 #991 — explicit-ID Demo IDOR guard. Real tenants
                # cannot read the Demo profile (is_default OR canonical
                # UUID) by passing its UUID in the query — the seeded
                # Demo profile typically has null ``client_account_id``,
                # which would otherwise bypass the cross-tenant check
                # below.
                is_demo_profile = bool(
                    getattr(profile, "is_default", False)
                    or str(getattr(profile, "id", "")) == DEMO_COMPANY_UUID
                )
                if is_demo_profile and not is_demo_caller(user_company):
                    record_demo_fallback(
                        endpoint="get_company_profile",
                        reason="cross_tenant_demo_profile_read_attempt",
                        user_company_id=user_company,
                        extra={"requested_company_id": effective_company_id},
                    )
                    logger.warning(
                        "get_company_profile: cross-tenant Demo read blocked "
                        "user_company_id=%s requested=%s",
                        user_company, effective_company_id,
                    )
                    raise HTTPException(
                        status_code=403,
                        detail={
                            "code": "CROSS_TENANT_DEMO_PROFILE_FORBIDDEN",
                            "message": "Access denied: Demo profile is not accessible from your tenant.",
                        },
                    )
                if profile.client_account_id and str(profile.client_account_id) != user_company:
                    logger.warning(f"Cross-tenant access denied: user {current_user.id} (company={user_company}) tried to access profile {effective_company_id}")
                    raise HTTPException(status_code=403, detail="Access denied: this profile belongs to a different tenant")
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
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Create a new company profile, optionally linking to a ClientAccount."""
    try:
        profile_data = data.model_dump()
        resolved_client_id = client_account_id
        if not resolved_client_id and current_user and hasattr(current_user, 'company_id') and current_user.company_id:
            resolved_client_id = str(current_user.company_id)
        if resolved_client_id:
            try:
                uuid.UUID(resolved_client_id)
                profile_data["client_account_id"] = resolved_client_id
            except (ValueError, AttributeError):
                pass

        profile = await profile_repo.create(profile_data)
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
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
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Update an existing company profile."""
    try:
        update_data = data.model_dump(exclude_unset=True)

        profile = await profile_repo.get_by_id(profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Company profile not found")

        if not profile.client_account_id and current_user and hasattr(current_user, 'company_id') and current_user.company_id:
            try:
                uuid.UUID(str(current_user.company_id))
                update_data["client_account_id"] = str(current_user.company_id)
            except (ValueError, AttributeError):
                pass

        update_data["updated_at"] = datetime.utcnow()
        updated = await profile_repo.update(profile_id, update_data)
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
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
    # multi-tenancy: protected via auth middleware (JWT) + Postgres RLS runtime (Sprint follow-up: add _require_company_id explicit gate)
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


@router.post("/profile/{profile_id}/generate-evp", response_model=EVPAnalysisResponse)
async def generate_evp(
    profile_id: uuid.UUID,
    profile_repo: CompanyProfileRepository = Depends(get_company_profile_repo),
):
    # multi-tenancy: protected via auth middleware (JWT) + Postgres RLS runtime (Sprint follow-up: add _require_company_id explicit gate)
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

        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
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
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"Generated EVP for company: {profile.name}")
        return EVPAnalysisResponse(success=True, evp_analysis=evp_analysis)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating EVP: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats", response_model=None)
async def get_company_stats(
    company_id: uuid.UUID | None = Query(None),
    profile_repo: CompanyProfileRepository = Depends(get_company_profile_repo),
    dept_repo: DepartmentRepository = Depends(get_department_repo),
    benefit_repo: BenefitRepository = Depends(get_benefit_repo),
    cv_repo: CultureValueRepository = Depends(get_culture_value_repo),
    ip_repo: IdealProfileRepository = Depends(get_ideal_profile_repo),
    bf_repo: BigFiveRepository = Depends(get_big_five_repo),
    tt_repo: TechnicalTestRepository = Depends(get_technical_test_repo),
):
    # multi-tenancy: protected via auth middleware (JWT) + Postgres RLS runtime (Sprint follow-up: add _require_company_id explicit gate)
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
            "completion_percentage": 0,
        }

        profile = None
        if company_id:
            profile = await profile_repo.get_by_id(company_id)
        else:
            profile = await profile_repo.get_default()

        if profile:
            stats["profile_complete"] = bool(profile.name and profile.industry and profile.description)

            departments = await dept_repo.list_for_company(profile.id)
            stats["departments_count"] = len([d for d in departments if d.is_active])

            benefits = await benefit_repo.list_for_company(profile.id)
            stats["benefits_count"] = len([b for b in benefits if b.is_active])

            culture_values = await cv_repo.list_for_company(profile.id)
            stats["culture_values_count"] = len([v for v in culture_values if v.is_active])

            ideal_profiles = await ip_repo.list_for_company(profile.id)
            stats["ideal_profiles_count"] = len([p for p in ideal_profiles if p.is_active])

        bf_questions = await bf_repo.list_questions()
        stats["big_five_questions_count"] = len(bf_questions)

        tech_questions = await tt_repo.list_questions()
        stats["technical_questions_count"] = len(tech_questions)

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
):
    # multi-tenancy: protected via auth middleware (JWT) + Postgres RLS runtime (Sprint follow-up: add _require_company_id explicit gate)
    """Analyze company website and extract culture information using AI."""
    try:
        sources_analyzed = []
        website_content = ""

        if data.website_url:
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(
                        data.website_url,
                        headers={"User-Agent": "Mozilla/5.0 (compatible; LIABot/1.0; +https://wedotalent.com)"},
                        follow_redirects=True,
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
    "confidence": 0.0
}}
"""

        llm = llm_service.get_audited_model()
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
                    analysis_result = json.loads(json_match.group(0))
            except json.JSONDecodeError as e:
                parse_error = str(e)
                logger.warning(f"Regex JSON parse attempt failed: {e}")

        if analysis_result is None:
            logger.error(f"Failed to parse AI response as JSON after all attempts: {parse_error}")
            analysis_result = {
                "vision": "", "mission": "", "values": [], "tone": "professional",
                "evp": "", "culture_summary": "Não foi possível analisar o conteúdo fornecido.",
                "suggested_values": [], "confidence": 0.2,
            }

        def normalize_values_to_strings(values_data) -> list:
            if not values_data or not isinstance(values_data, list):
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
                    "category": sv.get("category", "value"),
                })
            elif isinstance(sv, str):
                suggested_values.append({"name": sv.strip(), "description": "", "category": "value"})

        return CultureAnalysisResponse(
            success=True,
            analysis={
                "vision": str(analysis_result.get("vision", "") or "").strip(),
                "mission": str(analysis_result.get("mission", "") or "").strip(),
                "values": normalized_values,
                "tone": str(analysis_result.get("tone", "professional") or "professional").strip(),
                "evp": str(analysis_result.get("evp", "") or "").strip(),
                "culture_summary": str(analysis_result.get("culture_summary", "") or "").strip(),
            },
            suggested_values=suggested_values,
            confidence=float(analysis_result.get("confidence", 0.5) or 0.5),
            sources_analyzed=sources_analyzed,
        )

    except Exception as e:
        logger.error(f"Error analyzing company culture: {e}")
        raise HTTPException(status_code=500, detail=str(e))



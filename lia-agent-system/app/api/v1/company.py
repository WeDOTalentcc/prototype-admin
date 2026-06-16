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
from app.schemas.company import (
    ApproverCreate,
    ApproverResponse,
    ApproverUpdate,
    BenefitResponse,
    BigFiveQuestionCreate,
    BigFiveQuestionResponse,
    BigFiveQuestionUpdate,
    BigFiveRoleProfileCreate,
    BigFiveRoleProfileResponse,
    BigFiveRoleProfileUpdate,
    CatalogStatusResponse,
    CompanyProfileCreate,
    CompanyProfileResponse,
    CompanyProfileUpdate,
    CompanyProfileWithRelations,
    CompanyUserResponse,
    CompanyUsersListResponse,
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
from app.shared.security.require_company_id import require_company_id, require_company_id_strict_match

FRONTEND_URL = os.getenv("FRONTEND_URL", "https://plataforma-lia.replit.app")

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/company", tags=["company"])




@router.get("/resolve-tenant", response_model=TenantResolutionResponse)
async def resolve_tenant(
    workos_organization_id: str | None = Query(None),
    client_account_id: str | None = Query(None),
    tenant_repo: TenantRepository = Depends(get_tenant_repo),
    current_user = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)):
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
        raise LIAError(message="Erro interno do servidor")


@router.post("/onboarding", response_model=None)
async def submit_onboarding(
    data: OnboardingData,
    profile_repo: CompanyProfileRepository = Depends(get_company_profile_repo),
    cp_repo: CultureProfileRepository = Depends(get_culture_profile_repo),
    current_user = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)):
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

        # T-06 R2 downstream fix canonical: company_id now from JWT (always set).
        if company_id:
            try:
                company_uuid = uuid.UUID(company_id)
                profile = await profile_repo.get_by_id(company_uuid)
                if profile:
                    logger.info(f"Found company profile by ID: {company_id}")
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
                        # T4 #991 — explicit-target Demo write IDOR.
                        # Non-Demo caller passing the Demo UUID in
                        # JWT company_id must get an explicit 403
                        # — never silently degrade into create-new.
                        if is_demo_profile_target:
                            record_demo_fallback(
                                endpoint="submit_onboarding",
                                reason="cross_tenant_demo_profile_write_attempt",
                                user_company_id=user_company_id,
                                extra={"target_profile_id": str(profile.id)},
                            )
                            logger.warning(
                                "submit_onboarding: explicit Demo write "
                                "blocked user_company_id=%s target=%s",
                                user_company_id, str(profile.id),
                            )
                            raise HTTPException(
                                status_code=403,
                                detail={
                                    "code": "CROSS_TENANT_DEMO_PROFILE_FORBIDDEN",
                                    "message": "Demo profile is not editable from your tenant.",
                                },
                            )
                        if (
                            profile_owner is not None
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
                logger.warning(f"Invalid company_id format: {company_id}")

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
        raise LIAError(message="Erro interno do servidor")


@router.get("/profile", response_model=CompanyProfileResponse)
async def get_company_profile(
    company_id: str | None = Query(None),
    profile_repo: CompanyProfileRepository = Depends(get_company_profile_repo),
    current_user = Depends(get_current_user_or_demo),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
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
            except Exception as e:
                # PR-D (Task #1016) — bare except antes mascarava bugs
                # de DB (foi o que escondeu o is_default NULL por dias);
                # logar diagnostico e continuar pro fallback.
                logger.warning(
                    "[get_company_profile] get_by_client_account(%s) falhou: %s",
                    user_cid, e,
                )

            try:
                cid_uuid = uuid.UUID(user_cid)
                profile = await profile_repo.get_by_id(cid_uuid)
                if profile:
                    return profile
            except ValueError:
                # user_cid não é UUID válido — pula get_by_id silenciosamente
                # (esperado quando tenant é slug).
                pass
            except Exception as e:
                # PR-D (Task #1016) — log diagnostico, não engole.
                logger.warning(
                    "[get_company_profile] get_by_id(%s) falhou: %s",
                    user_cid, e,
                )

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
from app.shared.errors import LIAError
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
        raise LIAError(message="Erro interno do servidor")


@router.post("/profile", response_model=CompanyProfileResponse)
async def create_company_profile(
    data: CompanyProfileCreate,
    client_account_id: str | None = Query(None),
    profile_repo: CompanyProfileRepository = Depends(get_company_profile_repo),
    current_user = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)):
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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating company profile: {e}")
        raise LIAError(message="Erro interno do servidor")


@router.put("/profile/{profile_id}", response_model=CompanyProfileResponse)
async def update_company_profile(
    profile_id: uuid.UUID,
    data: CompanyProfileUpdate,
    profile_repo: CompanyProfileRepository = Depends(get_company_profile_repo),
    current_user = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Update an existing company profile."""
    try:
        update_data = data.model_dump(exclude_unset=True)

        profile = await profile_repo.get_by_id(profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Company profile not found")

        # P1-7 IDOR guard — verify profile belongs to authenticated tenant.
        # CompanyProfile uses client_account_id (FK -> client_accounts), not company_id.
        # Same canonical pattern as upload_company_logo and GET /profile cross-tenant check.
        if profile.client_account_id and str(profile.client_account_id) != str(company_id):
            raise HTTPException(
                status_code=403,
                detail="Tenant mismatch: profile does not belong to authenticated tenant.",
            )

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
        raise LIAError(message="Erro interno do servidor")


@router.post("/profile/{profile_id}/logo", response_model=CompanyProfileResponse)
async def upload_company_logo(
    profile_id: uuid.UUID,
    file: UploadFile = File(...),
    profile_repo: CompanyProfileRepository = Depends(get_company_profile_repo),
    current_user=Depends(get_current_user_or_demo),
    company_id: str = Depends(require_company_id),
):
    """Upload de arquivo logo da empresa.

    Audit 2026-05-20 Sessão I Step 4 (P1.13 extended):
    - Recebe multipart/form-data com arquivo de imagem
    - Valida content-type (PNG/JPG/SVG/WEBP) e tamanho (<500KB)
    - Encoda em base64 data URL e armazena em company_profiles.logo_url (TEXT)
    - Migration 152_logo_url_to_text ALTER coluna de String(500) → TEXT

    Multi-tenancy: company_id obrigatório via JWT canonical.
    """
    import base64

    # Validate content-type (declared header)
    allowed_types = {"image/png", "image/jpeg", "image/jpg", "image/webp"}
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Formato '{file.content_type}' não suportado. "
                "Use PNG, JPG ou WEBP (SVG bloqueado por segurança WT-2022 P0.LOGO)."
            ),
        )

    # WT-2022 P0.LOGO fix: magic bytes check (não confiar só em content-type declarado)
    header = await file.read(12)
    await file.seek(0)

    PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
    JPEG_MAGIC = b"\xff\xd8\xff"
    SVG_PREFIX_XML = b"<?xml"
    SVG_PREFIX_TAG = b"<svg"
    RIFF_MAGIC = b"RIFF"
    WEBP_MARKER = b"WEBP"

    is_png = header.startswith(PNG_MAGIC)
    is_jpeg = header.startswith(JPEG_MAGIC)
    is_svg = header.startswith(SVG_PREFIX_XML) or header.startswith(SVG_PREFIX_TAG)
    is_webp = header.startswith(RIFF_MAGIC) and header[8:12] == WEBP_MARKER

    # WT-2022 P0.LOGO fix: SVG bloqueado por XSS (script tags, foreignObject, etc.)
    if is_svg:
        raise HTTPException(
            status_code=400,
            detail="SVG não suportado por segurança (WT-2022 P0.LOGO). Use PNG, JPEG ou WEBP.",
        )

    if not (is_png or is_jpeg or is_webp):
        raise HTTPException(
            status_code=400,
            detail=(
                "Arquivo não corresponde aos tipos aceitos (PNG/JPEG/WEBP). "
                "Magic bytes não conferem com a extensão declarada."
            ),
        )

    # Validate size (500KB max)
    contents = await file.read()
    max_size = 500 * 1024  # 500KB
    if len(contents) > max_size:
        raise HTTPException(
            status_code=413,
            detail=(
                f"Arquivo muito grande ({len(contents) // 1024}KB). "
                f"Limite: {max_size // 1024}KB."
            ),
        )

    # Validate profile exists + tenancy
    profile = await profile_repo.get_by_id(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Company profile not found")

    # WT-2022 P0.LOGO fix: verify ownership (era cross-tenant write — qualquer recruiter
    # podia sobrescrever logo de OUTRA company só passando profile_id alheio).
    # CompanyProfile usa client_account_id (FK -> client_accounts), não company_id
    # (que é coluna apenas em models filhos como Department/Benefit). Mesmo pattern
    # canonical da linha 556 (GET /profile cross-tenant check).
    if profile.client_account_id and str(profile.client_account_id) != str(company_id):
        raise HTTPException(
            status_code=403,
            detail="Profile não pertence ao tenant autenticado",
        )

    # Build data URL canonical
    b64 = base64.b64encode(contents).decode("ascii")
    data_url = f"data:{file.content_type};base64,{b64}"

    # Persist via repository
    update_data = {
        "logo_url": data_url,
        "updated_at": datetime.utcnow(),
    }
    updated = await profile_repo.update(profile_id, update_data)
    # pii-logs ok: nome de entidade/config
    logger.info(
        "Logo uploaded for profile %s (size=%dKB, type=%s)",
        profile.name,
        len(contents) // 1024,
        file.content_type,
    )
    return updated


@router.get("/profile/{profile_id}/full", response_model=CompanyProfileWithRelations)
async def get_company_profile_with_relations(
    profile_id: uuid.UUID,
    profile_repo: CompanyProfileRepository = Depends(get_company_profile_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
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
        raise LIAError(message="Erro interno do servidor")


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
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting company stats: {e}")
        raise LIAError(message="Erro interno do servidor")



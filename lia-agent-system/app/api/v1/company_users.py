"""
Company Users API endpoints — user management, global search settings,
catalog status, and Smart Wizard greeting.
"""
from app.middleware.request_id import get_correlation_id
import logging
import os
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth.dependencies import get_current_user_or_demo
from app.auth.models import User, UserRole
from app.auth.schemas import UserManagementCreate, UserManagementResponse, UserManagementUpdate
from app.shared.tenant_guard import get_verified_company_id
from app.auth.security import generate_secure_token, get_password_hash
from app.domains.communication.services.email_service import EmailService, get_email_service
from app.domains.company.dependencies import (
    get_company_profile_repo,
    get_department_repo,
    get_global_settings_repo,
    get_user_repo,
)
from app.domains.company.repositories.company_profile_repository import CompanyProfileRepository
from app.domains.company.repositories.department_repository import DepartmentRepository
from app.domains.company.repositories.global_settings_repository import GlobalSettingsRepository
from app.domains.company.repositories.user_repository import UserRepository
from app.schemas.company import (
    CatalogStatusResponse,
    CompanyUserResponse,
    CompanyUsersListResponse,
    GlobalSearchSettingsResponse,
    GlobalSearchSettingsUpdate,
    SmartWizardGreetingResponse,
)
from app.domains.company.services.company_configuration_service import company_config_service
from app.shared.security.require_company_id import require_company_id
from app.shared.compliance.audit_service import AuditService  # P1-W2-06
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item

FRONTEND_URL = os.getenv("FRONTEND_URL", "https://plataforma-lia.replit.app")

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/company", tags=["company"])


@router.get("/global-search-settings", response_model=GlobalSearchSettingsResponse)
async def get_global_search_settings(
    company_id: str = Depends(require_company_id),
    gs_repo: GlobalSettingsRepository = Depends(get_global_settings_repo)):
    # multi-tenancy: company_id JWT-only via Depends(require_company_id)
    """Get global search settings for a specific company (multi-tenant isolated)."""
    try:
        settings = await gs_repo.get_for_company(company_id)
        if not settings:
            settings = await gs_repo.create_or_update(company_id, {
                "default_limit": 50,
                "search_type": "fast",
                "show_emails": False,
                "show_phone_numbers": False,
                "high_freshness": False,
                "auto_expand_global": False,
                "confirm_before_search": True,
                "global_search_enabled": True,
            })
            logger.info(f"Created default global search settings for company {company_id}")

        return settings
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching global search settings: {e}")
        raise LIAError(message="Erro interno do servidor")


@router.put("/global-search-settings", response_model=GlobalSearchSettingsResponse)
async def update_global_search_settings(
    data: GlobalSearchSettingsUpdate,
    company_id: str = Depends(require_company_id),
    gs_repo: GlobalSettingsRepository = Depends(get_global_settings_repo)):
    # multi-tenancy: company_id JWT-only via Depends(require_company_id)
    """Update global search settings for a specific company (multi-tenant isolated)."""
    try:
        update_data = data.model_dump(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()
        settings = await gs_repo.create_or_update(company_id, update_data)
        logger.info(f"Updated global search settings for company {company_id}")
        return settings
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating global search settings: {e}")
        raise LIAError(message="Erro interno do servidor")


# ==========================================
# User Management Endpoints
# ==========================================

@router.get("/users", response_model=list[UserManagementResponse])
async def list_users(
    company_id: str = Depends(require_company_id),
    user_repo: UserRepository = Depends(get_user_repo)):
    # multi-tenancy: company_id JWT-only via Depends(require_company_id)
    """List all users for a company.

    Audit Wave 3 (2026-05-21) — P1.A cleanup: removido dead-code branch
    de cross-tenant recovery. require_company_id_strict_match já enforça
    query=JWT antes do handler executar (HTTP 403 retornado pelo gate).
    """
    try:
        return await user_repo.list_for_company(company_id, is_active=None)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        raise LIAError(message="Erro interno do servidor")


@router.post("/users", response_model=UserManagementResponse, status_code=201)
async def create_user(
    data: UserManagementCreate,
    company_id: str = Depends(require_company_id),
    user_repo: UserRepository = Depends(get_user_repo),
    email_svc: EmailService = Depends(get_email_service),
    current_user=Depends(get_current_user_or_demo)):
    # multi-tenancy: company_id JWT-only via Depends(require_company_id)
    """Create a new user with invitation token.

    Audit Wave 3 (2026-05-21) — P0.B + P0.A:
    - company_id removido de UserManagementCreate (R2): vem do query (JWT-validated).
    - Role escalation gate: apenas wedotalent_admin pode atribuir wedotalent_admin.
      Tenant-admin tentando criar staff WeDOTalent recebe HTTP 403.
    """
    try:
        # P0.A — role escalation gate (CLAUDE.md E1)
        if data.role == UserRole.wedotalent_admin:
            current_role = getattr(current_user, "role", None) if current_user else None
            if current_role != UserRole.wedotalent_admin:
                logger.warning(
                    f"Role escalation blocked: user={getattr(current_user, 'id', 'unknown')} "
                    f"tried to assign wedotalent_admin in company={company_id}"
                )
                raise HTTPException(
                    status_code=403,
                    detail="Only WeDOTalent staff (wedotalent_admin) can assign the wedotalent_admin role",
                )

        existing = await user_repo.get_by_email(data.email)
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")

        invitation_token = generate_secure_token()

        user = await user_repo.create({
            "email": data.email,
            "name": data.name,
            "role": data.role,
            "company_id": company_id,
            "password_hash": get_password_hash("temporary_placeholder"),
            "is_active": False,
            "email_verified": False,
            "invitation_token": invitation_token,
            "invitation_sent_at": datetime.utcnow(),
            "permissions": data.permissions or [],
            "department_id": data.department_id,
        })

        invitation_link = f"{FRONTEND_URL}/aceitar-convite?token={invitation_token}"
        await email_svc.send_user_notification(
            db=user_repo.db,
            notification_type="invitation",
            recipient_email=user.email,
            variables={"user_name": user.name, "invitation_link": invitation_link},
        )

        logger.info(f"Created user with invitation: {user.id} for company {company_id}")
        await AuditService().log_action(trace_id=get_correlation_id(), company_id=company_id, action_type="user_invite", actor=str(getattr(current_user, "id", "system")), target_id=str(user.id), target_type="user")  # P1-W2-06
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise LIAError(message="Erro interno do servidor")


@router.put("/users/{user_id}", response_model=UserManagementResponse)
async def update_user(
    user_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    data: UserManagementUpdate,
    user_repo: UserRepository = Depends(get_user_repo),
    current_user=Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: defense-in-depth — company_id JWT + tenant-scoped get_by_id
    """Update a user.

    Audit Wave 3 (2026-05-21) — P0.C + P0.A:
    - get_by_id(user_uuid, company_id=company_id): defense-in-depth canonical
      (CLAUDE.md REGRA 1). RLS já bloqueia cross-tenant, mas scoping explícito
      elimina warning flood + cumpre defense-in-depth contract.
    - Role escalation gate (P0.A): apenas wedotalent_admin pode SET role
      wedotalent_admin via update.
    """
    try:
        # P0.A + P0-W2-05 — role escalation gate (CLAUDE.md E1)
        # ANY role change requires admin or wedotalent_admin.
        # Recruiters/viewers cannot self-promote even to tenant-level admin (OWASP A01).
        if data.role is not None:
            current_role = getattr(current_user, "role", None) if current_user else None
            is_admin_or_staff = current_role in (UserRole.admin, UserRole.wedotalent_admin)
            if not is_admin_or_staff:
                logger.warning(
                    f"Role escalation blocked: user={getattr(current_user, 'id', 'unknown')} "
                    f"role={current_role!r} tried to set role={data.role!r} "
                    f"for user {user_id} in company={company_id}"
                )
                raise HTTPException(
                    status_code=403,
                    detail="Apenas administradores podem alterar roles de usuários",
                )
            # Extra guard: only wedotalent_admin can assign wedotalent_admin
            if data.role == UserRole.wedotalent_admin and current_role != UserRole.wedotalent_admin:
                logger.warning(
                    f"Role escalation blocked: user={getattr(current_user, 'id', 'unknown')} "
                    f"tried to escalate user {user_id} to wedotalent_admin in company={company_id}"
                )
                raise HTTPException(
                    status_code=403,
                    detail="Only WeDOTalent staff (wedotalent_admin) can assign the wedotalent_admin role",
                )

        user_uuid = uuid.UUID(user_id)
        user = await user_repo.get_by_id(user_uuid, company_id=company_id)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if data.email and data.email != user.email:
            existing = await user_repo.get_by_email(data.email)
            if existing and existing.id != user_uuid:
                raise HTTPException(status_code=400, detail="Email already in use")

        update_data = data.model_dump(exclude_unset=True)
        # Handle permissions specially
        if 'permissions' in update_data and update_data['permissions'] is None:
            update_data['permissions'] = user.permissions
        update_data['updated_at'] = datetime.utcnow()

        # A7-BE: PII/grant fields require tenant admin (LGPD Art. 6 III / Art. 5 II).
        # Single source of truth: users table. Gate mirrors client_users pattern but lives here.
        _pii_grant_fields = ("can_view_salary", "can_view_sensitive_pii", "pii_field_visibility")
        if any(f in update_data for f in _pii_grant_fields):
            _cur_role = getattr(current_user, "role", None) if current_user else None
            if _cur_role not in (UserRole.admin, UserRole.wedotalent_admin):
                raise HTTPException(
                    status_code=403,
                    detail="Apenas administradores podem alterar visibilidade de PII",
                )
            if update_data.get("pii_field_visibility") is not None:
                from app.api.v1.pii_visibility_defaults import validate_pii_field_override
from app.shared.errors import LIAError
                validate_pii_field_override(update_data["pii_field_visibility"])

        user = await user_repo.update(user_uuid, update_data, company_id=company_id)
        logger.info(f"Updated user: {user.id} with permissions: {user.permissions}")
        await AuditService().log_action(trace_id=get_correlation_id(), company_id=company_id, action_type="user_update", actor=str(getattr(current_user, "id", "system")), target_id=str(user.id), target_type="user")  # P1-W2-06
        return user
    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        raise LIAError(message="Erro interno do servidor")


@router.delete("/users/{user_id}", status_code=204, response_model=None)
async def delete_user(
    user_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    user_repo: UserRepository = Depends(get_user_repo),
    current_user: User = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: defense-in-depth — company_id JWT + tenant-scoped get_by_id
    """Delete a user.

    P0-W2-01 fix (2026-05-24): current_user adicionado para garantir
    autenticação explícita (defense-in-depth sobre require_company_id).
    Audit Wave 3 (2026-05-21) — P0.C: get_by_id passes company_id (defense-in-depth).
    """
    try:
        user_uuid = uuid.UUID(user_id)
        user = await user_repo.get_by_id(user_uuid, company_id=company_id)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        email = user.email
        await user_repo.delete(user_uuid, company_id=company_id)
        # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
        logger.info(f"Deleted user: {email}")
        await AuditService().log_action(trace_id=get_correlation_id(), company_id=company_id, action_type="user_delete", actor=str(getattr(current_user, "id", "system")), target_id=str(user_uuid), target_type="user")  # P1-W2-06
        return None
    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        raise LIAError(message="Erro interno do servidor")


@router.post("/users/{user_id}/resend-invitation", response_model=None)
async def resend_invitation(
    user_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    user_repo: UserRepository = Depends(get_user_repo),
    email_svc: EmailService = Depends(get_email_service),
    current_user=Depends(get_current_user_or_demo),
    company_id: str = Depends(require_company_id)):
    # multi-tenancy: defense-in-depth — company_id JWT + tenant-scoped get_by_id
    # P1-W2-05 fix (2026-05-24): adicionado current_user dep para autenticacao explicita.
    # Ownership check: get_by_id(uuid, company_id=company_id) garante que user_id
    # pertence ao tenant do requester — retorna None (404) se pertencer a outra empresa.
    # AuditService actor corrigido de "system" para actor real do requester.
    """Resend invitation email to a user who hasn't activated their account yet.

    P1-W2-05 fix (2026-05-24): adicionado current_user dependency para autenticacao
    explicita. Ownership enforced via get_by_id com company_id do JWT — retorna None
    se o user_id pertencer a outra empresa, resultando em 404 (evita enumeration).
    Actor no audit log agora reflete o usuario real que fez o request.

    Audit Wave 3 (2026-05-21) — P0.C: get_by_id passes company_id (defense-in-depth).
    """
    try:
        user_uuid = uuid.UUID(user_id)
        # Ownership check: get_by_id filtra por company_id do JWT.
        # Se user_id pertencer a outra empresa retorna None -> 404 (sem info disclosure).
        user = await user_repo.get_by_id(user_uuid, company_id=company_id)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if user.is_active:
            raise HTTPException(status_code=400, detail="User has already activated their account")

        invitation_token = generate_secure_token()
        user = await user_repo.update(user_uuid, {
            "invitation_token": invitation_token,
            "invitation_sent_at": datetime.utcnow(),
        }, company_id=company_id)

        invitation_link = f"{FRONTEND_URL}/aceitar-convite?token={invitation_token}"
        await email_svc.send_user_notification(
            db=user_repo.db,
            notification_type="invitation",
            recipient_email=user.email,
            variables={"user_name": user.name, "invitation_link": invitation_link},
        )

        actor_id = str(getattr(current_user, "id", "system"))
        logger.info(f"Resent invitation to user: {user.id} by actor: {actor_id}")
        await AuditService().log_action(trace_id=get_correlation_id(), company_id=company_id, action_type="user_invitation_resend", actor=actor_id, target_id=str(user.id), target_type="user")  # P1-W2-05+W2-06
        return {"success": True, "message": "Invitation email resent successfully"}
    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    except Exception as e:
        logger.error(f"Error resending invitation: {e}")
        raise LIAError(message="Erro interno do servidor")


@router.get("/users/list", response_model=CompanyUsersListResponse)
async def list_company_users(
    role: str | None = Query(None, description="Filter by role (recruiter, admin, viewer)"),
    is_active: bool = Query(True, description="Filter by active status"),
    user_repo: UserRepository = Depends(get_user_repo),
    current_user: User = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """List users belonging to the same company as the current user."""
    try:
        # P2-W2-06 fix: usar company_id do JWT (require_company_id Depends) em vez de
        # current_user.company_id que era redundante e podia divergir do JWT canonical.
        # company_id ja vem do Depends(require_company_id) na assinatura do handler.
        users = await user_repo.list_for_company(str(company_id), role=role, is_active=is_active)
        user_emails = [u.email for u in users]
        jobs_by_email = await user_repo.count_active_jobs_by_email(user_emails)

        user_responses = []
        for user in users:
            active_jobs_count = jobs_by_email.get(user.email, 0)
            # P2-5: sem fonte real de performance — nao fabricar valor ficticio
            performance_score = None
            user_responses.append(CompanyUserResponse(
                id=str(user.id),
                name=user.name,
                email=user.email,
                role=user.role.value if hasattr(user.role, 'value') else str(user.role),
                is_active=user.is_active,
                active_jobs_count=active_jobs_count,
                performance_score=performance_score,
            ))

        logger.info(f"Listed {len(user_responses)} users for company {company_id}")
        return CompanyUsersListResponse(users=user_responses, total=len(user_responses))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing company users: {e}")
        raise LIAError(message="Erro interno do servidor")


# ============================================================================
# CATALOG STATUS - Smart Wizard Integration
# ============================================================================

@router.get("/catalog-status", response_model=CatalogStatusResponse)
async def get_catalog_status(
    company_id: str = Depends(get_verified_company_id),
    profile_repo: CompanyProfileRepository = Depends(get_company_profile_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Get the maturity status of company's catalog data for Smart Wizard.

    company_id is resolved from the JWT token via get_verified_company_id.
    Cross-tenant access is blocked automatically.
    """
    try:
        status = await company_config_service.get_catalog_status(company_id, profile_repo.db)
        return CatalogStatusResponse(**status)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting catalog status: {e}")
        raise LIAError(message="Erro interno do servidor")


@router.get("/smart-wizard-greeting", response_model=SmartWizardGreetingResponse)
async def get_smart_wizard_greeting(
    company_id: str = Depends(get_verified_company_id),
    dept_repo: DepartmentRepository = Depends(get_department_repo),
    profile_repo: CompanyProfileRepository = Depends(get_company_profile_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Get personalized greeting for the Smart Wizard based on catalog status.

    company_id is resolved from the JWT token via get_verified_company_id.
    Cross-tenant access is blocked automatically.
    """
    import asyncio

    try:
        status, config = await asyncio.gather(
            company_config_service.get_catalog_status(company_id, profile_repo.db),
            company_config_service.get_configuration(company_id, profile_repo.db),
        )

        base_intro = """Como você gostaria de começar?

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

        departments_list = []
        try:
            from uuid import UUID as UUID_type

            resolved_company_uuid = None
            try:
                resolved_company_uuid = UUID_type(company_id)
            except (ValueError, TypeError):
                profile = await profile_repo.get_default()
                if profile:
                    resolved_company_uuid = profile.id

            if resolved_company_uuid:
                departments = await dept_repo.list_for_company(resolved_company_uuid)
                departments_list = [
                    {"id": str(d.id), "name": d.name, "manager": d.manager_name}
                    for d in departments
                ]
        except Exception as e:
            logger.warning(f"Error fetching departments for prefill: {e}")

        tech_stack = []
        try:
            from uuid import UUID as UUID_type

            try:
                company_uuid = UUID_type(company_id)
                profile = await profile_repo.get_by_id(company_uuid)
            except (ValueError, TypeError):
                profile = await profile_repo.get_default()

            if profile and hasattr(profile, 'tech_stack') and profile.tech_stack:
                tech_stack = profile.tech_stack if isinstance(profile.tech_stack, list) else []
        except Exception as e:
            logger.warning(f"Error fetching tech stack: {e}")

        screening_questions_list = [
            {
                "id": str(idx),
                "question": q.get("question", q.get("text", "")),
                "category": q.get("category", "general"),
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
            "default_pipeline": config.default_pipeline,
        }

        return SmartWizardGreetingResponse(
            greeting_message=greeting,
            catalog_status=CatalogStatusResponse(**status),
            prefill_data=prefill_data,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting smart wizard greeting: {e}")
        raise LIAError(message="Erro interno do servidor")

reorder_collection_before_item(router)

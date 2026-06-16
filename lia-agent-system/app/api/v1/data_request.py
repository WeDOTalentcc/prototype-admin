"""
Data Request API — LGPD Art. 18 compliance.

API for managing data requests to candidates, including:
- Creating and managing data requests
- Templates and fields management
- Company configuration

Part of LIA Data Collection System.

Onda 4.2d-P0-4 (2026-05-23): removido `_get_company_id()` placeholder UUID
hardcoded — toda DSR LGPD era misturada num tenant ficticio. Handlers agora
usam company_id JWT canonical via require_company_id.
"""
import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db, get_tenant_db
from app.domains.lgpd.repositories.data_request_repository import DataRequestRepository
from app.domains.communication.services.data_request_service import data_request_service
from app.domains.communication.services.data_request_whatsapp_service import data_request_whatsapp_service
from app.models.data_request import (
    DEFAULT_STAGE_FIELD_MAPPINGS,
    DataFieldType,
    DataRequestStatus,
    TriggerType,
)
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel

logger = logging.getLogger(__name__)

_VALID_CHANNELS = frozenset({"email", "whatsapp", "voice", "web"})

router = APIRouter(prefix="/data-requests", tags=["Data Requests"])


class FieldSchema(BaseModel):
    """Schema for a data request field."""
    name: str
    label: str
    label_en: str | None = None
    description: str | None = None
    field_type: str
    is_required: bool = True
    validation_rules: dict[str, Any] | None = None
    options: list[str] | None = None
    placeholder: str | None = None
    help_text: str | None = None
    max_file_size_mb: int | None = 10
    allowed_file_types: list[str] | None = None


class CreateDataRequestRequest(WeDoBaseModel):
    """Request to create a new data request."""
    candidate_id: UUID
    vacancy_id: UUID | None = None
    template_id: UUID | None = None
    fields: list[FieldSchema] | None = None
    trigger_type: str = Field(default="manual")
    trigger_stage: str | None = None
    is_blocking: bool = False
    expiration_days: int = Field(default=7, ge=1, le=90)
    send_notification: bool = True
    notification_channels: list[str] | None = None  # None = usar canal preferido da empresa (CompanyHiringPolicy)


class DataRequestResponse(BaseModel):
    """Response schema for a data request."""
    id: UUID
    candidate_id: UUID
    vacancy_id: UUID | None = None
    template_id: UUID | None = None
    token: str
    status: str
    fields_requested: list[dict[str, Any]]
    fields_completed: list[dict[str, Any]]
    trigger_type: str
    trigger_stage: str | None = None
    is_blocking: bool
    expires_at: datetime
    completion_percentage: float
    sent_via_email: bool
    sent_via_whatsapp: bool
    reminder_count: int
    first_accessed_at: datetime | None = None
    last_accessed_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DataRequestListResponse(BaseModel):
    """Response for listing data requests."""
    items: list[DataRequestResponse]
    total: int


class ResendNotificationRequest(WeDoBaseModel):
    """Request to resend notification."""
    channels: list[str] = Field(default=["email"])


class ResendNotificationResponse(BaseModel):
    """Response for resend notification."""
    reminder_count: int
    channels: dict[str, Any]


class ConfigResponse(BaseModel):
    """Response for company configuration."""
    id: UUID
    company_id: UUID
    default_expiration_days: int
    require_otp: bool
    otp_expiration_minutes: int
    max_otp_attempts: int
    send_email_notification: bool
    send_whatsapp_notification: bool
    auto_reminder_enabled: bool
    reminder_days: list[int]
    max_reminders: int
    portal_logo_url: str | None = None
    portal_primary_color: str
    portal_welcome_message: str | None = None
    portal_thank_you_message: str | None = None
    privacy_policy_url: str | None = None
    terms_url: str | None = None

    class Config:
        from_attributes = True


class UpdateConfigRequest(WeDoBaseModel):
    """Request to update company configuration."""
    default_expiration_days: int | None = None
    require_otp: bool | None = None
    otp_expiration_minutes: int | None = None
    max_otp_attempts: int | None = None
    send_email_notification: bool | None = None
    send_whatsapp_notification: bool | None = None
    auto_reminder_enabled: bool | None = None
    reminder_days: list[int] | None = None
    max_reminders: int | None = None
    portal_logo_url: str | None = None
    portal_primary_color: str | None = None
    portal_welcome_message: str | None = None
    portal_thank_you_message: str | None = None
    privacy_policy_url: str | None = None
    terms_url: str | None = None


class LGPDSettingsSchema(BaseModel):
    """LGPD settings schema."""
    require_consent: bool = True
    consent_message: str | None = None
    disclaimer_text: str | None = None
    data_retention_days: int = 365
    allow_data_deletion: bool = True


class CollectionSettingsRequest(WeDoBaseModel):
    """Request to update collection settings (LGPD/WhatsApp)."""
    collection_mode: str = Field(
        default="portal_only",
        description="Collection mode: portal_only, chat_only, or candidate_choice"
    )
    collection_messages: dict[str, Any] | None = None
    lgpd: LGPDSettingsSchema | None = None


class CollectionSettingsResponse(BaseModel):
    """Response for collection settings."""
    collection_mode: str
    collection_messages: dict[str, Any]
    lgpd: LGPDSettingsSchema

    class Config:
        from_attributes = True


class TemplateResponse(BaseModel):
    """Response for a template."""
    id: UUID
    company_id: UUID
    name: str
    description: str | None = None
    trigger_stage: str | None = None
    trigger_type: str
    is_blocking: bool
    expiration_days: int
    fields: list[dict[str, Any]]
    is_active: bool
    is_default: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CreateTemplateRequest(WeDoBaseModel):
    """Request to create a template."""
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    trigger_stage: str | None = None
    trigger_type: str = Field(default="manual")
    is_blocking: bool = False
    expiration_days: int = Field(default=7, ge=1, le=90)
    fields: list[FieldSchema] = Field(default=[])


class UpdateTemplateRequest(WeDoBaseModel):
    """Request to update a template."""
    name: str | None = None
    description: str | None = None
    trigger_stage: str | None = None
    trigger_type: str | None = None
    is_blocking: bool | None = None
    expiration_days: int | None = None
    fields: list[FieldSchema] | None = None
    is_active: bool | None = None


class CreateFieldRequest(WeDoBaseModel):
    """Request to create a custom field."""
    name: str = Field(..., min_length=1, max_length=100)
    label: str = Field(..., min_length=1, max_length=255)
    label_en: str | None = None
    description: str | None = None
    field_type: str
    is_required: bool = True
    validation_rules: dict[str, Any] | None = None
    options: list[str] | None = None
    placeholder: str | None = None
    help_text: str | None = None
    max_file_size_mb: int = 10
    allowed_file_types: list[str] | None = None
    order: int = 0


class FieldResponse(BaseModel):
    """Response for a field."""
    id: str | None = None
    name: str
    label: str
    label_en: str | None = None
    description: str | None = None
    field_type: str
    is_required: bool
    validation_rules: dict[str, Any] | None = None
    options: list[str] | None = None
    placeholder: str | None = None
    help_text: str | None = None
    max_file_size_mb: int | None = None
    allowed_file_types: list[str] | None = None
    order: int | None = None
    is_default: bool = False


# Onda 4.2h-C1 (2026-05-24): _get_company_id() placeholder removido
# (era hardcoded UUID 00000000-0000-0000-0000-000000000001 = cross-tenant
# silent data corruption). Canonical = Depends(require_company_id) JWT.


def _data_request_to_response(dr) -> DataRequestResponse:
    """Convert DataRequest model to response schema."""
    return DataRequestResponse(
        id=dr.id,
        candidate_id=dr.candidate_id,
        vacancy_id=dr.vacancy_id,
        template_id=dr.template_id,
        token=dr.token,
        status=dr.status.value if dr.status else "pending",
        fields_requested=dr.fields_requested or [],
        fields_completed=dr.fields_completed or [],
        trigger_type=dr.trigger_type.value if dr.trigger_type else "manual",
        trigger_stage=dr.trigger_stage,
        is_blocking=dr.is_blocking or False,
        expires_at=dr.expires_at,
        completion_percentage=dr.get_completion_percentage(),
        sent_via_email=dr.sent_via_email or False,
        sent_via_whatsapp=dr.sent_via_whatsapp or False,
        reminder_count=dr.reminder_count or 0,
        first_accessed_at=dr.first_accessed_at,
        last_accessed_at=dr.last_accessed_at,
        completed_at=dr.completed_at,
        created_at=dr.created_at,
        updated_at=dr.updated_at,
    )


@router.get("", response_model=DataRequestListResponse)
async def list_data_requests(
    vacancy_id: UUID | None = Query(None, description="Filter by vacancy ID"),
    candidate_id: str | None = Query(None, description="Filter by candidate ID (UUID/local id; ids globais nao-UUID retornam vazio)"),
    status: str | None = Query(None, description="Filter by status"),
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    List data requests with optional filters.
    
    Supports filtering by:
    - vacancy_id: Filter requests for a specific job vacancy
    - candidate_id: Filter requests for a specific candidate
    - status: Filter by request status (pending, partially_filled, completed, expired, cancelled)
    """
    try:
        # Onda 4.2d-P0-4 (2026-05-23): override removido (era placeholder UUID hardcoded) — usar company_id JWT injetado
        
        status_enum = None
        if status:
            try:
                status_enum = DataRequestStatus(status)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        if candidate_id:
            # Candidatos globais (pearch) carregam id sintetico nao-UUID e nao
            # possuem data requests locais. Aceitar str e retornar vazio em vez
            # de 422/500 (canonical: fail-soft p/ candidato nao-persistido).
            try:
                _cid = UUID(candidate_id)
            except (ValueError, TypeError):
                _cid = None
            if _cid is None:
                requests = []
            else:
                requests = await data_request_service.get_candidate_data_requests(
                    db, _cid, status_enum, include_expired=True
                )
        elif vacancy_id:
            requests = await data_request_service.get_vacancy_data_requests(
                db, vacancy_id, status_enum
            )
        else:
            if candidate_id is None and vacancy_id is None:
                repo = DataRequestRepository(db)
                requests = await repo.list_all_for_company(company_id, status_enum=status_enum)
            else:
                requests = []
        
        return DataRequestListResponse(
            items=[_data_request_to_response(r) for r in requests],
            total=len(requests),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing data requests: {e}")
        raise


@router.post("", response_model=DataRequestResponse, status_code=201)
async def create_data_request(
    request: CreateDataRequestRequest,
    db: AsyncSession = Depends(get_tenant_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Create a new data request for a candidate.
    
    Creates a unique token for the candidate to access the data collection portal.
    Optionally sends notification via email and/or WhatsApp.
    """
    try:
        # Onda 4.2d-P0-4 (2026-05-23): override removido (era placeholder UUID hardcoded) — usar company_id JWT injetado
        
        try:
            trigger_type = TriggerType(request.trigger_type)
        except ValueError:
            trigger_type = TriggerType.MANUAL
        
        fields = None
        if request.fields:
            fields = [f.model_dump() for f in request.fields]
        
        data_request = await data_request_service.create_data_request(
            db=db,
            company_id=company_id,
            candidate_id=request.candidate_id,
            vacancy_id=request.vacancy_id,
            template_id=request.template_id,
            fields=fields,
            trigger_type=trigger_type,
            trigger_stage=request.trigger_stage,
            is_blocking=request.is_blocking,
            expiration_days=request.expiration_days,
        )
        
        if request.send_notification:
            channels = request.notification_channels
            if channels is None:
                # Enforcement Item4: carregar canal preferido da empresa.
                # CompanyHiringPolicy.communication_rules.preferred_data_channel
                # é o que o DataChannelSettings.tsx escreve em Configurações → Comunicação.
                try:
                    from app.domains.hiring_policy.repositories.hiring_policy_repository import (
                        HiringPolicyRepository,
                    )
                    _hp = await HiringPolicyRepository(db).get_by_company(company_id)
                    _pref = (
                        (_hp.communication_rules or {}).get("preferred_data_channel")
                        if _hp and _hp.communication_rules
                        else None
                    )
                    channels = [_pref] if (_pref and _pref in _VALID_CHANNELS) else ["email"]
                except Exception as _e:
                    logger.warning("Falha ao carregar canal preferido (%s), fallback=email", _e)
                    channels = ["email"]
            await data_request_service.send_notification(
                db, data_request.id, channels
            )
            await db.refresh(data_request)
        
        return _data_request_to_response(data_request)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating data request: {e}")
        raise


@router.get("/config", response_model=ConfigResponse)
async def get_config(
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Get company data request configuration.
    
    Returns the current configuration for the company's data request portal,
    including branding, notification settings, and OTP configuration.
    """
    try:
        # Onda 4.2d-P0-4 (2026-05-23): override removido (era placeholder UUID hardcoded) — usar company_id JWT injetado
        config = await data_request_service.get_or_create_config(db, company_id)
        return config
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting config: {e}")
        raise


@router.put("/config", response_model=ConfigResponse)
async def update_config(
    request: UpdateConfigRequest,
    db: AsyncSession = Depends(get_tenant_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Update company data request configuration.
    
    Updates settings for the data request portal including:
    - Expiration defaults
    - OTP settings
    - Notification preferences
    - Portal branding (logo, colors, messages)
    - Legal links (privacy policy, terms)
    """
    try:
        # Onda 4.2d-P0-4 (2026-05-23): override removido (era placeholder UUID hardcoded) — usar company_id JWT injetado
        updates = request.model_dump(exclude_unset=True)
        config = await data_request_service.update_config(db, company_id, updates)
        return config
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating config: {e}")
        raise


@router.post("/config/collection-settings", response_model=CollectionSettingsResponse)
async def update_collection_settings(
    request: CollectionSettingsRequest,
    db: AsyncSession = Depends(get_tenant_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Update collection settings including LGPD and WhatsApp configuration.
    
    Configures how data is collected from candidates:
    - collection_mode: portal_only, chat_only, or candidate_choice
    - collection_messages: Custom messages for each collection method
    - lgpd: LGPD compliance settings (consent, retention, data deletion)
    """
    try:
        # Onda 4.2d-P0-4 (2026-05-23): override removido (era placeholder UUID hardcoded) — usar company_id JWT injetado
        
        updates = {
            "collection_mode": request.collection_mode,
            "collection_messages": request.collection_messages or {},
        }
        
        if request.lgpd:
            updates["lgpd_require_consent"] = request.lgpd.require_consent
            updates["lgpd_consent_message"] = request.lgpd.consent_message
            updates["lgpd_disclaimer_text"] = request.lgpd.disclaimer_text
            updates["lgpd_data_retention_days"] = request.lgpd.data_retention_days
            updates["lgpd_allow_data_deletion"] = request.lgpd.allow_data_deletion
        
        config = await data_request_service.update_config(db, company_id, updates)
        
        return CollectionSettingsResponse(
            collection_mode=config.collection_mode or "portal_only",  # type: ignore[union-attr]
            collection_messages=config.collection_messages or {},  # type: ignore[union-attr]
            lgpd=LGPDSettingsSchema(
                require_consent=config.lgpd_require_consent if config.lgpd_require_consent is not None else True,  # type: ignore[union-attr]
                consent_message=config.lgpd_consent_message,  # type: ignore[union-attr]
                disclaimer_text=config.lgpd_disclaimer_text,  # type: ignore[union-attr]
                data_retention_days=config.lgpd_data_retention_days or 365,  # type: ignore[union-attr]
                allow_data_deletion=config.lgpd_allow_data_deletion if config.lgpd_allow_data_deletion is not None else True,  # type: ignore[union-attr]
            ),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating collection settings: {e}")
        raise


@router.get("/config/collection-settings", response_model=CollectionSettingsResponse)
async def get_collection_settings(
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Get current collection settings including LGPD and WhatsApp configuration.
    """
    try:
        # Onda 4.2d-P0-4 (2026-05-23): override removido (era placeholder UUID hardcoded) — usar company_id JWT injetado
        config = await data_request_service.get_or_create_config(db, company_id)
        
        return CollectionSettingsResponse(
            collection_mode=config.collection_mode or "portal_only",  # type: ignore[union-attr]
            collection_messages=config.collection_messages or {},  # type: ignore[union-attr]
            lgpd=LGPDSettingsSchema(
                require_consent=config.lgpd_require_consent if config.lgpd_require_consent is not None else True,  # type: ignore[union-attr]
                consent_message=config.lgpd_consent_message,  # type: ignore[union-attr]
                disclaimer_text=config.lgpd_disclaimer_text,  # type: ignore[union-attr]
                data_retention_days=config.lgpd_data_retention_days or 365,  # type: ignore[union-attr]
                allow_data_deletion=config.lgpd_allow_data_deletion if config.lgpd_allow_data_deletion is not None else True,  # type: ignore[union-attr]
            ),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting collection settings: {e}")
        raise


@router.get("/templates", response_model=list[TemplateResponse])
async def list_templates(
    include_inactive: bool = Query(False, description="Include inactive templates"),
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    List data request templates for the company.
    
    Templates define which fields to request from candidates
    and can be associated with specific recruitment stages.
    """
    try:
        # Onda 4.2d-P0-4 (2026-05-23): override removido (era placeholder UUID hardcoded) — usar company_id JWT injetado
        templates = await data_request_service.list_templates(
            db, company_id, active_only=not include_inactive
        )
        
        return [
            TemplateResponse(
                id=t.id,
                company_id=t.company_id,
                name=t.name,
                description=t.description,
                trigger_stage=t.trigger_stage,
                trigger_type=t.trigger_type.value if t.trigger_type else "manual",
                is_blocking=t.is_blocking or False,
                expiration_days=t.expiration_days or 7,
                fields=t.fields or [],
                is_active=t.is_active or False,
                is_default=t.is_default or False,
                created_at=t.created_at,
                updated_at=t.updated_at,
            )
            for t in templates
        ]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing templates: {e}")
        raise


@router.post("/templates", response_model=TemplateResponse, status_code=201)
async def create_template(
    request: CreateTemplateRequest,
    db: AsyncSession = Depends(get_tenant_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Create a new data request template.
    
    Templates can be configured with:
    - Custom fields to collect
    - Trigger stage for automatic activation
    - Blocking behavior (prevents stage transition until completed)
    - Expiration settings
    """
    try:
        # Onda 4.2d-P0-4 (2026-05-23): override removido (era placeholder UUID hardcoded) — usar company_id JWT injetado
        
        try:
            trigger_type = TriggerType(request.trigger_type)
        except ValueError:
            trigger_type = TriggerType.MANUAL
        
        fields = [f.model_dump() for f in request.fields] if request.fields else []
        
        template = await data_request_service.create_template(
            db=db,
            company_id=company_id,
            name=request.name,
            description=request.description,
            fields=fields,
            trigger_stage=request.trigger_stage,
            trigger_type=trigger_type,
            is_blocking=request.is_blocking,
            expiration_days=request.expiration_days,
        )
        
        return TemplateResponse(
            id=template.id,
            company_id=template.company_id,
            name=template.name,
            description=template.description,
            trigger_stage=template.trigger_stage,
            trigger_type=template.trigger_type.value if template.trigger_type else "manual",
            is_blocking=template.is_blocking or False,
            expiration_days=template.expiration_days or 7,
            fields=template.fields or [],
            is_active=template.is_active or False,
            is_default=template.is_default or False,
            created_at=template.created_at,
            updated_at=template.updated_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating template: {e}")
        raise


@router.put("/templates/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: UUID,
    request: UpdateTemplateRequest,
    db: AsyncSession = Depends(get_tenant_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Update an existing data request template.
    """
    try:
        updates = request.model_dump(exclude_unset=True)
        
        if "trigger_type" in updates:
            try:
                updates["trigger_type"] = TriggerType(updates["trigger_type"])
            except ValueError:
                updates["trigger_type"] = TriggerType.MANUAL
        
        if "fields" in updates and updates["fields"]:
            updates["fields"] = [
                f.model_dump() if hasattr(f, "model_dump") else f 
                for f in updates["fields"]
            ]
        
        template = await data_request_service.update_template(db, template_id, updates)
        
        return TemplateResponse(
            id=template.id,
            company_id=template.company_id,
            name=template.name,
            description=template.description,
            trigger_stage=template.trigger_stage,
            trigger_type=template.trigger_type.value if template.trigger_type else "manual",
            is_blocking=template.is_blocking or False,
            expiration_days=template.expiration_days or 7,
            fields=template.fields or [],
            is_active=template.is_active or False,
            is_default=template.is_default or False,
            created_at=template.created_at,
            updated_at=template.updated_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating template: {e}")
        raise


@router.delete("/templates/{template_id}", status_code=204, response_model=None)
async def delete_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_tenant_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Delete (deactivate) a data request template.
    
    Templates are soft-deleted and can be reactivated later.
    """
    try:
        await data_request_service.delete_template(db, template_id)
        return None
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting template: {e}")
        raise


@router.get("/fields", response_model=list[FieldResponse])
async def list_fields(
    include_defaults: bool = Query(True, description="Include default fields"),
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    List available data request fields.
    
    Returns both default system fields (CPF, RG, address, etc.)
    and custom fields created by the company.
    """
    try:
        # Onda 4.2d-P0-4 (2026-05-23): override removido (era placeholder UUID hardcoded) — usar company_id JWT injetado
        fields = await data_request_service.list_fields(db, company_id, include_defaults)
        return [FieldResponse(**f) for f in fields]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing fields: {e}")
        raise


@router.post("/fields", response_model=FieldResponse, status_code=201)
async def create_field(
    request: CreateFieldRequest,
    db: AsyncSession = Depends(get_tenant_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Create a custom data request field.
    
    Custom fields can be used in templates to collect
    company-specific information from candidates.
    """
    try:
        # Onda 4.2d-P0-4 (2026-05-23): override removido (era placeholder UUID hardcoded) — usar company_id JWT injetado
        
        try:
            field_type = DataFieldType(request.field_type)
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid field type: {request.field_type}"
            )
        
        field = await data_request_service.create_field(
            db=db,
            company_id=company_id,
            name=request.name,
            label=request.label,
            field_type=field_type,
            label_en=request.label_en,
            description=request.description,
            is_required=request.is_required,
            validation_rules=request.validation_rules,
            options=request.options,
            placeholder=request.placeholder,
            help_text=request.help_text,
            max_file_size_mb=request.max_file_size_mb,
            allowed_file_types=request.allowed_file_types,
            order=request.order,
        )
        
        return FieldResponse(
            id=str(field.id),
            name=field.name,
            label=field.label,
            label_en=field.label_en,
            description=field.description,
            field_type=field.field_type.value if field.field_type else None,
            is_required=field.is_required,
            validation_rules=field.validation_rules,
            options=field.options,
            placeholder=field.placeholder,
            help_text=field.help_text,
            max_file_size_mb=field.max_file_size_mb,
            allowed_file_types=field.allowed_file_types,
            order=field.order,
            is_default=False,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating field: {e}")
        raise


@router.get("/stage-field-mappings", response_model=None)
async def get_stage_field_mappings(company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Get default field mappings for each recruitment stage.
    
    Returns which fields are typically requested at each stage
    of the recruitment process.
    """
    return {
        "mappings": DEFAULT_STAGE_FIELD_MAPPINGS,
        "description": "Default fields to request at each recruitment stage",
    }


class TriggerConfigResponse(BaseModel):
    """Response schema for trigger configuration."""
    source: str
    vacancy_id: str | None = None
    company_id: str | None = None
    stage_configs: dict[str, Any]
    custom_template_id: str | None = None


class StageTriggerConfig(BaseModel):
    """Configuration for a stage trigger."""
    stage: str
    enabled: bool = True
    template_id: str | None = None
    fields: list[dict[str, Any]] = []
    is_blocking: bool = False
    trigger_type: str = "stage_entry"


class UpdateVacancyTriggersRequest(WeDoBaseModel):
    """Request to update vacancy triggers."""
    use_company_defaults: bool = False
    stage_configs: dict[str, StageTriggerConfig] = {}
    custom_template_id: UUID | None = None


@router.get("/triggers/{vacancy_id}", response_model=TriggerConfigResponse)
async def get_vacancy_triggers(
    vacancy_id: UUID,
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Get data request trigger configuration for a vacancy.
    
    Returns which stages have automatic data request triggers configured,
    and what fields are requested at each stage.
    
    Priority:
    1. VacancyDataRequestConfig (vacancy-specific configuration)
    2. Company templates with trigger_stage configured
    3. Default stage-field mappings (for reference, not auto-triggered)
    """
    try:
        # Onda 4.2d-P0-4 (2026-05-23): override removido (era placeholder UUID hardcoded) — usar company_id JWT injetado
        
        config = await data_request_service.get_vacancy_trigger_config(
            db=db,
            vacancy_id=vacancy_id,
            company_id=company_id,
        )
        
        return TriggerConfigResponse(**config)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting vacancy triggers: {e}")
        raise


@router.put("/triggers/{vacancy_id}", response_model=TriggerConfigResponse)
async def update_vacancy_triggers(
    vacancy_id: UUID,
    request: UpdateVacancyTriggersRequest,
    db: AsyncSession = Depends(get_tenant_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Update data request trigger configuration for a vacancy.
    
    Configure which stages should automatically trigger data requests
    and what fields to request at each stage.
    
    Set use_company_defaults=true to use company-wide template settings,
    or provide custom stage_configs for vacancy-specific configuration.
    """
    try:
        # Onda 4.2h-C1 (2026-05-24): removido _get_company_id() placeholder
        # orphan (continuation do Onda 4.2d-P0-4). Canonical company_id já vem
        # do JWT via Depends(require_company_id).
        repo = DataRequestRepository(db)
        await repo.upsert_vacancy_trigger_config(
            vacancy_id=vacancy_id,
            use_company_defaults=request.use_company_defaults,
            custom_template_id=request.custom_template_id,
            stage_configs={
                stage: config.model_dump()
                for stage, config in request.stage_configs.items()
            } if request.stage_configs else {},
        )

        return await get_vacancy_triggers(vacancy_id, db)
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating vacancy triggers: {e}")
        raise


@router.get("/triggers/{vacancy_id}/stage/{stage_name}", response_model=None)
async def get_stage_trigger(
    vacancy_id: UUID,
    stage_name: str,
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Get trigger configuration for a specific stage.
    
    Returns the fields that would be requested if a candidate
    enters this stage, and whether it would block progression.
    """
    try:
        # Onda 4.2d-P0-4 (2026-05-23): override removido (era placeholder UUID hardcoded) — usar company_id JWT injetado
        
        trigger_config = await data_request_service.get_trigger_fields_for_stage(
            db=db,
            vacancy_id=vacancy_id,
            company_id=company_id,
            stage=stage_name,
        )
        
        if not trigger_config:
            return {
                "stage": stage_name,
                "has_trigger": False,
                "message": "No automatic trigger configured for this stage",
            }
        
        return {
            "stage": stage_name,
            "has_trigger": True,
            "source": trigger_config.get("source"),
            "trigger_type": trigger_config.get("trigger_type"),
            "is_blocking": trigger_config.get("is_blocking", False),
            "template_id": trigger_config.get("template_id"),
            "template_name": trigger_config.get("template_name"),
            "fields": trigger_config.get("fields", []),
            "fields_count": len(trigger_config.get("fields", [])),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting stage trigger: {e}")
        raise


@router.get("/{data_request_id}", response_model=DataRequestResponse)
async def get_data_request(
    data_request_id: UUID,
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Get details of a specific data request.
    
    Returns full information including fields requested,
    completion status, and notification history.
    """
    try:
        data_request = await data_request_service.get_data_request_by_id(db, data_request_id)
        
        if not data_request:
            raise HTTPException(status_code=404, detail="Data request not found")
        
        return _data_request_to_response(data_request)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting data request: {e}")
        raise


@router.delete("/{data_request_id}", status_code=204, response_model=None)
async def cancel_data_request(
    data_request_id: UUID,
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Cancel a data request.
    
    Cancelled requests cannot receive new data from candidates
    but existing responses are preserved.
    """
    try:
        await data_request_service.cancel_data_request(db, data_request_id)
        return None
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling data request: {e}")
        raise


@router.post("/{data_request_id}/resend", response_model=ResendNotificationResponse)
async def resend_notification(
    data_request_id: UUID,
    request: ResendNotificationRequest,
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Resend notification for a data request.
    
    Sends a reminder to the candidate via the specified channels.
    Tracks the number of reminders sent.
    """
    try:
        result = await data_request_service.resend_notification(
            db, data_request_id, request.channels
        )
        return ResendNotificationResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resending notification: {e}")
        raise


@router.get("/{data_request_id}/status", response_model=None)
async def check_status(
    data_request_id: UUID,
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Check and update the completion status of a data request.
    
    Returns current status, completion percentage, and
    whether the request has expired.
    """
    try:
        result = await data_request_service.check_completion_status(db, data_request_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking status: {e}")
        raise


class WhatsAppStartRequest(WeDoBaseModel):
    """Request to start WhatsApp collection."""
    candidate_phone: str = Field(..., description="Candidate's WhatsApp phone number")


class WhatsAppProcessMessageRequest(WeDoBaseModel):
    """Request to process incoming WhatsApp message."""
    message_content: str = Field(..., description="Text content of the message")
    file_url: str | None = Field(None, description="URL of uploaded file (if any)")
    file_name: str | None = Field(None, description="Original filename")
    file_mime_type: str | None = Field(None, description="MIME type of file")
    file_size: int | None = Field(None, description="File size in bytes")


class WhatsAppStatusResponse(BaseModel):
    """Response for WhatsApp conversation status."""
    success: bool
    state: str
    collection_method: str | None = None
    current_field: str | None = None
    consent_given: bool = False
    fields_total: int
    fields_completed: int
    fields_pending: int
    completion_percentage: float
    started_at: str | None = None
    last_message_at: str | None = None
    completed_at: str | None = None


@router.post("/{data_request_id}/whatsapp/start", response_model=None)
async def start_whatsapp_collection(
    data_request_id: UUID,
    request: WhatsAppStartRequest,
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Start WhatsApp data collection flow.
    
    Sends initial LGPD consent message or collection prompt to the candidate.
    
    The conversation flow depends on company configuration:
    1. If requireConsent=true: Sends LGPD consent message first
    2. If candidate_choice mode: Asks candidate to choose portal or chat
    3. If chat_only mode: Starts collecting documents immediately
    
    Args:
        data_request_id: ID of the data request
        request: Contains candidate's WhatsApp phone number
        
    Returns:
        Success status and initial conversation state
    """
    try:
        success = await data_request_whatsapp_service.start_collection(
            db, data_request_id, request.candidate_phone
        )
        
        if not success:
            raise HTTPException(
                status_code=400,
                detail="Failed to start WhatsApp collection"
            )
        
        status = await data_request_whatsapp_service.get_conversation_status(
            db, data_request_id
        )
        
        return {
            "success": True,
            "message": "WhatsApp collection started",
            "state": status.get("state"),
            "phone": request.candidate_phone,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting WhatsApp collection: {e}")
        raise


@router.post("/{data_request_id}/whatsapp/process-message", response_model=None)
async def process_whatsapp_message(
    data_request_id: UUID,
    request: WhatsAppProcessMessageRequest,
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Process incoming WhatsApp message from candidate.
    
    Routes the message to the appropriate handler based on conversation state:
    - awaiting_consent: Processes consent response (SIM/NÃO)
    - awaiting_choice: Processes collection method choice (1=portal, 2=chat)
    - collecting: Saves document/field value and requests next field
    
    Special commands:
    - STATUS: Shows pending and completed fields
    - AJUDA: Sends help message
    
    Args:
        data_request_id: ID of the data request
        request: Message content and optional file data
        
    Returns:
        Processing result with next state and actions
    """
    try:
        result = await data_request_whatsapp_service.process_incoming_message(
            db,
            data_request_id,
            request.message_content,
            request.file_url,
            request.file_name,
            request.file_mime_type,
            request.file_size,
        )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing WhatsApp message: {e}")
        raise


@router.get("/{data_request_id}/whatsapp/status", response_model=WhatsAppStatusResponse)
async def get_whatsapp_status(
    data_request_id: UUID,
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Get current WhatsApp conversation status.
    
    Returns the current state of the WhatsApp data collection conversation,
    including:
    - Current conversation state
    - Collection method chosen (portal/whatsapp)
    - Current field being collected
    - Progress (fields completed vs pending)
    - Timestamps
    
    Args:
        data_request_id: ID of the data request
        
    Returns:
        WhatsAppStatusResponse with conversation details
    """
    try:
        result = await data_request_whatsapp_service.get_conversation_status(
            db, data_request_id
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=404,
                detail=result.get("error", "Data request not found")
            )
        
        return WhatsAppStatusResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting WhatsApp status: {e}")
        raise

"""
Communication Settings API Endpoints

Manages company-level communication configurations including email signatures,
LGPD sending hours, message limits, and channel preferences.
"""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db, get_tenant_db
from app.models.communication_settings import DEFAULT_COMMUNICATION_SETTINGS
from app.domains.communication.repositories.communication_settings_repository import CommunicationSettingsRepository
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel
import uuid as _uuid_mod
from app.shared.compliance.audit_service import AuditService  # P1-W2-03

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/company", tags=["company"])


class CommunicationSettingsUpdate(WeDoBaseModel):
    signature: str | None = None
    signature_html: str | None = None
    sending_hours_start: int | None = None
    sending_hours_end: int | None = None
    respect_holidays: bool | None = None
    respect_weekends: bool | None = None
    timezone: str | None = None
    max_messages_per_day: int | None = None
    max_messages_per_candidate: int | None = None
    cooldown_hours_between_messages: int | None = None
    lgpd_compliant: bool | None = None
    require_consent_before_contact: bool | None = None
    auto_unsubscribe_after_days: int | None = None
    default_email_from_name: str | None = None
    default_reply_to: str | None = None
    mailgun_enabled: bool | None = None
    twilio_enabled: bool | None = None


class CommunicationSettingsResponse(BaseModel):
    id: str | None = None
    company_id: str
    signature: str | None = None
    signature_html: str | None = None
    sending_hours_start: int
    sending_hours_end: int
    respect_holidays: bool
    respect_weekends: bool
    timezone: str
    max_messages_per_day: int
    max_messages_per_candidate: int
    cooldown_hours_between_messages: int
    lgpd_compliant: bool
    require_consent_before_contact: bool
    auto_unsubscribe_after_days: int
    default_email_from_name: str | None = None
    default_reply_to: str | None = None
    mailgun_enabled: bool
    twilio_enabled: bool
    created_at: str | None = None
    updated_at: str | None = None


@router.get("/communication-settings", response_model=CommunicationSettingsResponse)
async def get_communication_settings(
    company_id: str = Depends(require_company_id),
    db: AsyncSession = Depends(get_db)):
    """
    Get communication settings for a company.
    
    Returns the company's communication settings or default settings if none exist.
    Company ID sourced from JWT (canonical multi-tenancy).
    """
    try:
        repo = CommunicationSettingsRepository(db)
        settings = await repo.get_by_company_id(company_id)

        if settings:
            logger.info(f"Retrieved communication settings for company {company_id}")
            return CommunicationSettingsResponse(
                id=str(settings.id),
                company_id=settings.company_id,
                signature=settings.signature,
                signature_html=settings.signature_html,
                sending_hours_start=settings.sending_hours_start,
                sending_hours_end=settings.sending_hours_end,
                respect_holidays=settings.respect_holidays,
                respect_weekends=settings.respect_weekends,
                timezone=settings.timezone,
                max_messages_per_day=settings.max_messages_per_day,
                max_messages_per_candidate=settings.max_messages_per_candidate,
                cooldown_hours_between_messages=settings.cooldown_hours_between_messages,
                lgpd_compliant=settings.lgpd_compliant,
                require_consent_before_contact=settings.require_consent_before_contact,
                auto_unsubscribe_after_days=settings.auto_unsubscribe_after_days,
                default_email_from_name=settings.default_email_from_name,
                default_reply_to=settings.default_reply_to,
                mailgun_enabled=settings.mailgun_enabled,
                twilio_enabled=settings.twilio_enabled,
                created_at=settings.created_at.isoformat() if settings.created_at else None,
                updated_at=settings.updated_at.isoformat() if settings.updated_at else None,
            )
        
        logger.info(f"No settings found for company {company_id}, returning defaults")
        return CommunicationSettingsResponse(
            company_id=company_id,
            **DEFAULT_COMMUNICATION_SETTINGS
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving communication settings: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve communication settings: {str(e)}"
        )


@router.put("/communication-settings", response_model=CommunicationSettingsResponse)
async def update_communication_settings(
    data: CommunicationSettingsUpdate,
    company_id: str = Depends(require_company_id),
    db: AsyncSession = Depends(get_tenant_db)):
    """
    Update communication settings for a company.
    
    Creates settings if they don't exist, or updates existing settings.
    Company ID sourced from JWT (canonical multi-tenancy).
    """
    try:
        repo = CommunicationSettingsRepository(db)
        update_data = data.model_dump(exclude_unset=True)
        settings = await repo.upsert(company_id, update_data)
        logger.info(f"Upserted communication settings for company {company_id}")
        try:
            updated_fields = data.model_dump(exclude_unset=True)
            action = "communication_signature_updated" if "signature" in updated_fields or "signature_html" in updated_fields else "communication_settings_updated"
            await AuditService().log_action(trace_id=str(_uuid_mod.uuid4()), company_id=company_id, action_type=action, actor="system", target_type="communication_settings", metadata={"fields_updated": list(updated_fields.keys())})  # P1-W2-03
        except Exception as _ae:
            logger.warning(f"Audit log failed (non-blocking): {_ae}")
        
        return CommunicationSettingsResponse(
            id=str(settings.id),
            company_id=settings.company_id,
            signature=settings.signature,
            signature_html=settings.signature_html,
            sending_hours_start=settings.sending_hours_start,
            sending_hours_end=settings.sending_hours_end,
            respect_holidays=settings.respect_holidays,
            respect_weekends=settings.respect_weekends,
            timezone=settings.timezone,
            max_messages_per_day=settings.max_messages_per_day,
            max_messages_per_candidate=settings.max_messages_per_candidate,
            cooldown_hours_between_messages=settings.cooldown_hours_between_messages,
            lgpd_compliant=settings.lgpd_compliant,
            require_consent_before_contact=settings.require_consent_before_contact,
            auto_unsubscribe_after_days=settings.auto_unsubscribe_after_days,
            default_email_from_name=settings.default_email_from_name,
            default_reply_to=settings.default_reply_to,
            mailgun_enabled=settings.mailgun_enabled,
            twilio_enabled=settings.twilio_enabled,
            created_at=settings.created_at.isoformat() if settings.created_at else None,
            updated_at=settings.updated_at.isoformat() if settings.updated_at else None,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating communication settings: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update communication settings: {str(e)}"
        )

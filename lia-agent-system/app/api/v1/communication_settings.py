"""
Communication Settings API Endpoints

Manages company-level communication configurations including email signatures,
LGPD sending hours, message limits, and channel preferences.
"""

from fastapi import APIRouter, HTTPException, Query, Header, Depends, status
from pydantic import BaseModel
from typing import Optional, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from datetime import datetime

from app.models.communication_settings import CommunicationSettings, DEFAULT_COMMUNICATION_SETTINGS
from app.core.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/company", tags=["company"])


class CommunicationSettingsUpdate(BaseModel):
    signature: Optional[str] = None
    signature_html: Optional[str] = None
    sending_hours_start: Optional[int] = None
    sending_hours_end: Optional[int] = None
    respect_holidays: Optional[bool] = None
    respect_weekends: Optional[bool] = None
    timezone: Optional[str] = None
    max_messages_per_day: Optional[int] = None
    max_messages_per_candidate: Optional[int] = None
    cooldown_hours_between_messages: Optional[int] = None
    lgpd_compliant: Optional[bool] = None
    require_consent_before_contact: Optional[bool] = None
    auto_unsubscribe_after_days: Optional[int] = None
    default_email_from_name: Optional[str] = None
    default_reply_to: Optional[str] = None
    mailgun_enabled: Optional[bool] = None
    twilio_enabled: Optional[bool] = None


class CommunicationSettingsResponse(BaseModel):
    id: Optional[str] = None
    company_id: str
    signature: Optional[str] = None
    signature_html: Optional[str] = None
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
    default_email_from_name: Optional[str] = None
    default_reply_to: Optional[str] = None
    mailgun_enabled: bool
    twilio_enabled: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


def get_company_id(
    x_company_id: Optional[str] = Header(None, alias="X-Company-ID"),
    company_id: Optional[str] = Query(None, description="Company ID")
) -> str:
    """Get company_id from header or query param, with validation."""
    resolved_company_id = x_company_id or company_id
    if not resolved_company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Company ID required. Provide X-Company-ID header or company_id query parameter."
        )
    return resolved_company_id


@router.get("/communication-settings", response_model=CommunicationSettingsResponse)
async def get_communication_settings(
    company_id: str = Depends(get_company_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get communication settings for a company.
    
    Returns the company's communication settings or default settings if none exist.
    Company ID can be provided via X-Company-ID header or company_id query param.
    """
    try:
        result = await db.execute(
            select(CommunicationSettings).where(
                CommunicationSettings.company_id == company_id
            )
        )
        settings = result.scalar_one_or_none()
        
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
    company_id: str = Depends(get_company_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Update communication settings for a company.
    
    Creates settings if they don't exist, or updates existing settings.
    Company ID can be provided via X-Company-ID header or company_id query param.
    """
    try:
        result = await db.execute(
            select(CommunicationSettings).where(
                CommunicationSettings.company_id == company_id
            )
        )
        settings = result.scalar_one_or_none()
        
        if settings:
            update_data = data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(settings, field, value)
            settings.updated_at = datetime.utcnow()
            logger.info(f"Updated communication settings for company {company_id}")
        else:
            settings_data = {**DEFAULT_COMMUNICATION_SETTINGS}
            update_data = data.model_dump(exclude_unset=True)
            settings_data.update(update_data)
            settings_data["company_id"] = company_id
            
            settings = CommunicationSettings(**settings_data)
            db.add(settings)
            logger.info(f"Created communication settings for company {company_id}")
        
        await db.commit()
        await db.refresh(settings)
        
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

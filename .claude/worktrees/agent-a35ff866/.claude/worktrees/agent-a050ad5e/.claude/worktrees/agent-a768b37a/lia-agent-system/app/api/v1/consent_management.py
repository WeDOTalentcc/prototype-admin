"""
Consent Management API Endpoints.

Provides endpoints for advanced LGPD consent management:
- Consent Version Management (versioned terms)
- Consent Event Tracking (grant, revoke, renew, expire)
- Subject History
- Consent Statistics
"""
from fastapi import APIRouter, HTTPException, Query, Depends, Header, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc, or_
from typing import Optional
from datetime import datetime, timedelta
import hashlib
import logging
from uuid import UUID

from app.core.database import get_db
from app.models.observability import ConsentVersion, ConsentEvent
from app.schemas.consent_management import (
    ConsentVersionCreate, ConsentVersionResponse, ConsentVersionListResponse,
    ConsentEventCreate, ConsentEventResponse, ConsentEventListResponse,
    ConsentSubjectHistory, ConsentSubjectEvent, ConsentRevokeRequest, ConsentStats, ConsentTypeStats
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/consent", tags=["consent-management"])


def get_company_id_from_header(
    x_company_id: Optional[str] = Header(None, alias="X-Company-ID")
) -> str:
    """Extract and validate company ID from header."""
    if not x_company_id:
        logger.warning("SECURITY: Request without X-Company-ID header rejected")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-Company-ID header required for authentication"
        )
    try:
        UUID(x_company_id)
    except ValueError:
        logger.warning(f"SECURITY: Invalid company ID format attempted: {x_company_id[:50] if x_company_id else 'None'}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid X-Company-ID format"
        )
    return x_company_id


def calculate_content_hash(content_html: str, content_text: str) -> str:
    """Calculate SHA256 hash of consent content."""
    combined = f"{content_html}|{content_text}"
    return hashlib.sha256(combined.encode()).hexdigest()


def calculate_proof_hash(
    consent_version_id: str,
    subject_email: str,
    subject_identifier: str,
    event_type: str,
    consent_given: bool,
    timestamp: datetime
) -> str:
    """Calculate SHA256 proof hash for consent event."""
    combined = f"{consent_version_id}|{subject_email}|{subject_identifier}|{event_type}|{consent_given}|{timestamp.isoformat()}"
    return hashlib.sha256(combined.encode()).hexdigest()


@router.post("/versions/", response_model=ConsentVersionResponse, status_code=status.HTTP_201_CREATED, summary="Create consent version")
async def create_consent_version(
    data: ConsentVersionCreate,
    company_id: str = Depends(get_company_id_from_header),
    db: AsyncSession = Depends(get_db)
):
    """Create a new consent version. Marks previous versions of the same type as not current."""
    try:
        company_uuid = UUID(company_id)
        
        content_hash = calculate_content_hash(data.content_html, data.content_text)
        
        update_query = select(ConsentVersion).where(
            and_(
                ConsentVersion.company_id == company_uuid,
                ConsentVersion.consent_type == data.consent_type,
                ConsentVersion.is_current == True
            )
        )
        result = await db.execute(update_query)
        previous_versions = result.scalars().all()
        
        for prev in previous_versions:
            prev.is_current = False
            prev.effective_until = data.effective_from
        
        version = ConsentVersion(
            company_id=company_uuid,
            consent_type=data.consent_type,
            version=data.version,
            title=data.title,
            content_html=data.content_html,
            content_text=data.content_text,
            hash=content_hash,
            effective_from=data.effective_from,
            is_current=True,
            requires_explicit_consent=data.requires_explicit_consent,
            renewal_period_days=data.renewal_period_days
        )
        
        db.add(version)
        await db.commit()
        await db.refresh(version)
        
        logger.info(f"Created consent version {version.id} for company {company_id}, type {data.consent_type}")
        return ConsentVersionResponse(**version.to_dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid data: {str(e)}")
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating consent version: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/versions/", response_model=ConsentVersionListResponse, summary="List consent versions")
async def list_consent_versions(
    consent_type: Optional[str] = Query(None, description="Filter by consent type"),
    is_current: Optional[bool] = Query(None, description="Filter by current status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    company_id: str = Depends(get_company_id_from_header),
    db: AsyncSession = Depends(get_db)
):
    """List consent versions with optional filters and pagination."""
    try:
        company_uuid = UUID(company_id)
        
        conditions = [ConsentVersion.company_id == company_uuid]
        if consent_type:
            conditions.append(ConsentVersion.consent_type == consent_type)
        if is_current is not None:
            conditions.append(ConsentVersion.is_current == is_current)
        
        query = select(ConsentVersion).where(and_(*conditions)).order_by(desc(ConsentVersion.created_at)).limit(limit).offset(offset)
        result = await db.execute(query)
        versions = result.scalars().all()
        
        count_query = select(func.count(ConsentVersion.id)).where(and_(*conditions))
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0
        
        return ConsentVersionListResponse(
            versions=[ConsentVersionResponse(**v.to_dict()) for v in versions],
            total=total,
            limit=limit,
            offset=offset
        )
    except Exception as e:
        logger.error(f"Error listing consent versions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/versions/current/{consent_type}", response_model=ConsentVersionResponse, summary="Get current version by type")
async def get_current_consent_version(
    consent_type: str,
    company_id: str = Depends(get_company_id_from_header),
    db: AsyncSession = Depends(get_db)
):
    """Get the current (active) consent version for a specific type."""
    try:
        company_uuid = UUID(company_id)
        
        query = select(ConsentVersion).where(
            and_(
                ConsentVersion.company_id == company_uuid,
                ConsentVersion.consent_type == consent_type,
                ConsentVersion.is_current == True
            )
        )
        result = await db.execute(query)
        version = result.scalar_one_or_none()
        
        if not version:
            raise HTTPException(status_code=404, detail=f"No current consent version found for type: {consent_type}")
        
        return ConsentVersionResponse(**version.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting current consent version: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/versions/{version_id}", response_model=ConsentVersionResponse, summary="Get consent version by ID")
async def get_consent_version(
    version_id: str,
    company_id: str = Depends(get_company_id_from_header),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific consent version by ID."""
    try:
        version_uuid = UUID(version_id)
        company_uuid = UUID(company_id)
        
        query = select(ConsentVersion).where(
            and_(
                ConsentVersion.id == version_uuid,
                ConsentVersion.company_id == company_uuid
            )
        )
        result = await db.execute(query)
        version = result.scalar_one_or_none()
        
        if not version:
            raise HTTPException(status_code=404, detail="Consent version not found")
        
        return ConsentVersionResponse(**version.to_dict())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid version ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting consent version: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/events/", response_model=ConsentEventResponse, status_code=status.HTTP_201_CREATED, summary="Register consent event")
async def create_consent_event(
    data: ConsentEventCreate,
    company_id: str = Depends(get_company_id_from_header),
    db: AsyncSession = Depends(get_db)
):
    """Register a consent event (grant, revoke, renew, expire). Public endpoint for WhatsApp integration."""
    try:
        company_uuid = UUID(company_id)
        consent_version_uuid = UUID(data.consent_version_id)
        
        version_query = select(ConsentVersion).where(
            and_(
                ConsentVersion.id == consent_version_uuid,
                ConsentVersion.company_id == company_uuid
            )
        )
        version_result = await db.execute(version_query)
        version = version_result.scalar_one_or_none()
        
        if not version:
            raise HTTPException(status_code=404, detail="Consent version not found")
        
        now = datetime.utcnow()
        
        proof_hash = calculate_proof_hash(
            data.consent_version_id,
            data.subject_email,
            data.subject_identifier,
            data.event_type.value,
            data.consent_given,
            now
        )
        
        expires_at = None
        if data.consent_given and version.renewal_period_days:
            expires_at = now + timedelta(days=version.renewal_period_days)
        
        event = ConsentEvent(
            company_id=company_uuid,
            consent_version_id=consent_version_uuid,
            subject_email=data.subject_email,
            subject_identifier=data.subject_identifier,
            event_type=data.event_type.value,
            consent_given=data.consent_given,
            ip_address=data.ip_address,
            user_agent=data.user_agent,
            device_info=data.device_info or {},
            channel=data.channel.value,
            proof_hash=proof_hash,
            expires_at=expires_at
        )
        
        db.add(event)
        await db.commit()
        await db.refresh(event)
        
        logger.info(f"Created consent event {event.id} for subject {data.subject_identifier}, type {data.event_type.value}")
        return ConsentEventResponse(**event.to_dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid data: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating consent event: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/events/", response_model=ConsentEventListResponse, summary="List consent events")
async def list_consent_events(
    consent_version_id: Optional[str] = Query(None, description="Filter by consent version ID"),
    subject_email: Optional[str] = Query(None, description="Filter by subject email"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    date_from: Optional[datetime] = Query(None, description="Filter events from this date"),
    date_to: Optional[datetime] = Query(None, description="Filter events until this date"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    company_id: str = Depends(get_company_id_from_header),
    db: AsyncSession = Depends(get_db)
):
    """List consent events with optional filters and pagination."""
    try:
        company_uuid = UUID(company_id)
        
        conditions = [ConsentEvent.company_id == company_uuid]
        
        if consent_version_id:
            conditions.append(ConsentEvent.consent_version_id == UUID(consent_version_id))
        if subject_email:
            conditions.append(ConsentEvent.subject_email == subject_email)
        if event_type:
            conditions.append(ConsentEvent.event_type == event_type)
        if date_from:
            conditions.append(ConsentEvent.created_at >= date_from)
        if date_to:
            conditions.append(ConsentEvent.created_at <= date_to)
        
        query = select(ConsentEvent).where(and_(*conditions)).order_by(desc(ConsentEvent.created_at)).limit(limit).offset(offset)
        result = await db.execute(query)
        events = result.scalars().all()
        
        count_query = select(func.count(ConsentEvent.id)).where(and_(*conditions))
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0
        
        return ConsentEventListResponse(
            events=[ConsentEventResponse(**e.to_dict()) for e in events],
            total=total,
            limit=limit,
            offset=offset
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid data: {str(e)}")
    except Exception as e:
        logger.error(f"Error listing consent events: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/events/subject/{subject_identifier}", response_model=ConsentSubjectHistory, summary="Get subject consent history")
async def get_subject_consent_history(
    subject_identifier: str,
    company_id: str = Depends(get_company_id_from_header),
    db: AsyncSession = Depends(get_db)
):
    """Get complete consent history for a data subject."""
    try:
        company_uuid = UUID(company_id)
        
        events_query = select(ConsentEvent).where(
            and_(
                ConsentEvent.company_id == company_uuid,
                ConsentEvent.subject_identifier == subject_identifier
            )
        ).order_by(desc(ConsentEvent.created_at))
        
        events_result = await db.execute(events_query)
        events = events_result.scalars().all()
        
        if not events:
            raise HTTPException(status_code=404, detail="No consent history found for this subject")
        
        version_ids = list(set(e.consent_version_id for e in events))
        versions_query = select(ConsentVersion).where(ConsentVersion.id.in_(version_ids))
        versions_result = await db.execute(versions_query)
        versions = {v.id: v for v in versions_result.scalars().all()}
        
        current_consents: dict = {}
        now = datetime.utcnow()
        
        subject_events = []
        for event in events:
            version = versions.get(event.consent_version_id)
            consent_type = version.consent_type if version else "unknown"
            consent_version_str = version.version if version else "unknown"
            
            is_expired = False
            if event.expires_at:
                is_expired = now > event.expires_at
            
            is_current = False
            if consent_type not in current_consents:
                if event.event_type == "granted" and event.consent_given and not is_expired:
                    current_consents[consent_type] = True
                    is_current = True
                elif event.event_type == "revoked":
                    current_consents[consent_type] = False
            
            subject_events.append(ConsentSubjectEvent(
                id=str(event.id),
                consent_type=consent_type,
                consent_version=consent_version_str,
                event_type=event.event_type,
                consent_given=event.consent_given,
                channel=event.channel,
                created_at=event.created_at,
                expires_at=event.expires_at,
                is_expired=is_expired,
                is_current=is_current
            ))
        
        return ConsentSubjectHistory(
            subject_identifier=subject_identifier,
            subject_email=events[0].subject_email if events else "",
            events=subject_events,
            current_consents=current_consents,
            total_events=len(events)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting subject consent history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/events/revoke", response_model=ConsentEventResponse, status_code=status.HTTP_201_CREATED, summary="Revoke consent")
async def revoke_consent(
    data: ConsentRevokeRequest,
    company_id: str = Depends(get_company_id_from_header),
    db: AsyncSession = Depends(get_db)
):
    """Revoke consent for a data subject. Creates a revocation event."""
    try:
        company_uuid = UUID(company_id)
        
        if not data.consent_type and not data.consent_version_id:
            raise HTTPException(
                status_code=400,
                detail="Either consent_type or consent_version_id must be provided"
            )
        
        if data.consent_version_id:
            version_uuid = UUID(data.consent_version_id)
            version_query = select(ConsentVersion).where(
                and_(
                    ConsentVersion.id == version_uuid,
                    ConsentVersion.company_id == company_uuid
                )
            )
        else:
            version_query = select(ConsentVersion).where(
                and_(
                    ConsentVersion.company_id == company_uuid,
                    ConsentVersion.consent_type == data.consent_type,
                    ConsentVersion.is_current == True
                )
            )
        
        version_result = await db.execute(version_query)
        version = version_result.scalar_one_or_none()
        
        if not version:
            raise HTTPException(status_code=404, detail="Consent version not found")
        
        last_event_query = select(ConsentEvent).where(
            and_(
                ConsentEvent.company_id == company_uuid,
                ConsentEvent.consent_version_id == version.id,
                ConsentEvent.subject_identifier == data.subject_identifier,
                ConsentEvent.event_type == "granted",
                ConsentEvent.consent_given == True
            )
        ).order_by(desc(ConsentEvent.created_at)).limit(1)
        
        last_event_result = await db.execute(last_event_query)
        last_event = last_event_result.scalar_one_or_none()
        
        if not last_event:
            raise HTTPException(
                status_code=404,
                detail="No active consent found to revoke for this subject"
            )
        
        now = datetime.utcnow()
        
        proof_hash = calculate_proof_hash(
            str(version.id),
            last_event.subject_email,
            data.subject_identifier,
            "revoked",
            False,
            now
        )
        
        revoke_event = ConsentEvent(
            company_id=company_uuid,
            consent_version_id=version.id,
            subject_email=last_event.subject_email,
            subject_identifier=data.subject_identifier,
            event_type="revoked",
            consent_given=False,
            ip_address=data.ip_address,
            user_agent=data.user_agent,
            device_info={},
            channel=data.channel.value,
            proof_hash=proof_hash,
            expires_at=None
        )
        
        db.add(revoke_event)
        await db.commit()
        await db.refresh(revoke_event)
        
        logger.info(f"Revoked consent {revoke_event.id} for subject {data.subject_identifier}")
        return ConsentEventResponse(**revoke_event.to_dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid data: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error revoking consent: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=ConsentStats, summary="Get consent statistics")
async def get_consent_stats(
    company_id: str = Depends(get_company_id_from_header),
    db: AsyncSession = Depends(get_db)
):
    """Get aggregated consent statistics for the company."""
    try:
        company_uuid = UUID(company_id)
        now = datetime.utcnow()
        
        versions_count_query = select(func.count(ConsentVersion.id)).where(
            ConsentVersion.company_id == company_uuid
        )
        versions_result = await db.execute(versions_count_query)
        total_versions = versions_result.scalar() or 0
        
        events_count_query = select(func.count(ConsentEvent.id)).where(
            ConsentEvent.company_id == company_uuid
        )
        events_result = await db.execute(events_count_query)
        total_events = events_result.scalar() or 0
        
        subjects_query = select(func.count(func.distinct(ConsentEvent.subject_identifier))).where(
            ConsentEvent.company_id == company_uuid
        )
        subjects_result = await db.execute(subjects_query)
        total_subjects = subjects_result.scalar() or 0
        
        granted_query = select(func.count(ConsentEvent.id)).where(
            and_(
                ConsentEvent.company_id == company_uuid,
                ConsentEvent.event_type == "granted",
                ConsentEvent.consent_given == True
            )
        )
        granted_result = await db.execute(granted_query)
        total_granted = granted_result.scalar() or 0
        
        revoked_query = select(func.count(ConsentEvent.id)).where(
            and_(
                ConsentEvent.company_id == company_uuid,
                ConsentEvent.event_type == "revoked"
            )
        )
        revoked_result = await db.execute(revoked_query)
        total_revoked = revoked_result.scalar() or 0
        
        expired_query = select(func.count(ConsentEvent.id)).where(
            and_(
                ConsentEvent.company_id == company_uuid,
                ConsentEvent.event_type == "granted",
                ConsentEvent.expires_at != None,
                ConsentEvent.expires_at < now
            )
        )
        expired_result = await db.execute(expired_query)
        total_expired = expired_result.scalar() or 0
        
        types_query = select(ConsentVersion.consent_type).where(
            ConsentVersion.company_id == company_uuid
        ).distinct()
        types_result = await db.execute(types_query)
        consent_types = [row[0] for row in types_result.fetchall()]
        
        by_type = []
        for consent_type in consent_types:
            version_ids_query = select(ConsentVersion.id).where(
                and_(
                    ConsentVersion.company_id == company_uuid,
                    ConsentVersion.consent_type == consent_type
                )
            )
            version_ids_result = await db.execute(version_ids_query)
            version_ids = [row[0] for row in version_ids_result.fetchall()]
            
            if not version_ids:
                continue
            
            type_granted_query = select(func.count(ConsentEvent.id)).where(
                and_(
                    ConsentEvent.consent_version_id.in_(version_ids),
                    ConsentEvent.event_type == "granted",
                    ConsentEvent.consent_given == True
                )
            )
            type_granted_result = await db.execute(type_granted_query)
            type_granted = type_granted_result.scalar() or 0
            
            type_revoked_query = select(func.count(ConsentEvent.id)).where(
                and_(
                    ConsentEvent.consent_version_id.in_(version_ids),
                    ConsentEvent.event_type == "revoked"
                )
            )
            type_revoked_result = await db.execute(type_revoked_query)
            type_revoked = type_revoked_result.scalar() or 0
            
            type_expired_query = select(func.count(ConsentEvent.id)).where(
                and_(
                    ConsentEvent.consent_version_id.in_(version_ids),
                    ConsentEvent.event_type == "granted",
                    ConsentEvent.expires_at != None,
                    ConsentEvent.expires_at < now
                )
            )
            type_expired_result = await db.execute(type_expired_query)
            type_expired = type_expired_result.scalar() or 0
            
            type_active = type_granted - type_revoked - type_expired
            consent_rate = (type_granted / (type_granted + type_revoked)) * 100 if (type_granted + type_revoked) > 0 else 0.0
            
            by_type.append(ConsentTypeStats(
                consent_type=consent_type,
                total_granted=type_granted,
                total_revoked=type_revoked,
                total_expired=type_expired,
                total_active=max(0, type_active),
                consent_rate=round(consent_rate, 2)
            ))
        
        channel_query = select(
            ConsentEvent.channel,
            func.count(ConsentEvent.id)
        ).where(
            ConsentEvent.company_id == company_uuid
        ).group_by(ConsentEvent.channel)
        channel_result = await db.execute(channel_query)
        by_channel = {row[0]: row[1] for row in channel_result.fetchall()}
        
        return ConsentStats(
            total_consent_versions=total_versions,
            total_consent_events=total_events,
            total_subjects=total_subjects,
            total_granted=total_granted,
            total_revoked=total_revoked,
            total_expired=total_expired,
            by_type=by_type,
            by_channel=by_channel
        )
    except Exception as e:
        logger.error(f"Error getting consent stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

"""
Consent Management API Endpoints.

Provides endpoints for advanced LGPD consent management:
- Consent Version Management (versioned terms)
- Consent Event Tracking (grant, revoke, renew, expire)
- Subject History
- Consent Statistics
"""
import hashlib
import logging
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.domains.consent.dependencies import get_consent_repo
from app.domains.consent.repositories.consent_repository import ConsentRepository
from app.schemas.consent_management import (
    ConsentEventCreate,
    ConsentEventListResponse,
    ConsentEventResponse,
    ConsentRevokeRequest,
    ConsentStats,
    ConsentSubjectEvent,
    ConsentSubjectHistory,
    ConsentTypeStats,
    ConsentVersionCreate,
    ConsentVersionListResponse,
    ConsentVersionResponse,
)
from app.shared.tenant_guard import get_verified_company_id
from app.shared.security.require_company_id import require_company_id
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/consent", tags=["consent-management"])


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


@router.post(
    "/versions/",
    response_model=ConsentVersionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create consent version",
)
async def create_consent_version(
    data: ConsentVersionCreate,
    company_id: str = Depends(get_verified_company_id),
    repo: ConsentRepository = Depends(get_consent_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Create a new consent version. Marks previous versions of the same type as not current."""
    try:
        company_uuid = UUID(company_id)

        content_hash = calculate_content_hash(data.content_html, data.content_text)

        previous_versions = await repo.get_current_versions_of_type(
            company_uuid, data.consent_type
        )
        for prev in previous_versions:
            await repo.update_version(
                prev,
                {"is_current": False, "effective_until": data.effective_from},
            )

        version = await repo.create_version(
            company_uuid=company_uuid,
            consent_type=data.consent_type,
            version=data.version,
            title=data.title,
            content_html=data.content_html,
            content_text=data.content_text,
            content_hash=content_hash,
            effective_from=data.effective_from,
            requires_explicit_consent=data.requires_explicit_consent,
            renewal_period_days=data.renewal_period_days,
        )

        logger.info(
            f"Created consent version {version.id} for company {company_id}, type {data.consent_type}"
        )
        return ConsentVersionResponse(**version.to_dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid data: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        await repo.rollback()
        logger.error(f"Error creating consent version: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/versions/",
    response_model=ConsentVersionListResponse,
    summary="List consent versions",
)
async def list_consent_versions(
    consent_type: str | None = Query(None, description="Filter by consent type"),
    is_current: bool | None = Query(None, description="Filter by current status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    company_id: str = Depends(get_verified_company_id),
    repo: ConsentRepository = Depends(get_consent_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """List consent versions with optional filters and pagination."""
    try:
        company_uuid = UUID(company_id)

        versions, total = await repo.list_versions(
            company_uuid,
            consent_type=consent_type,
            is_current=is_current,
            limit=limit,
            offset=offset,
        )

        return ConsentVersionListResponse(
            versions=[ConsentVersionResponse(**v.to_dict()) for v in versions],
            total=total,
            limit=limit,
            offset=offset,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing consent versions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/versions/current/{consent_type}",
    response_model=ConsentVersionResponse,
    summary="Get current version by type",
)
async def get_current_consent_version(
    consent_type: str,
    company_id: str = Depends(get_verified_company_id),
    repo: ConsentRepository = Depends(get_consent_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Get the current (active) consent version for a specific type."""
    try:
        company_uuid = UUID(company_id)

        version = await repo.get_active_version(company_uuid, consent_type)

        if not version:
            raise HTTPException(
                status_code=404,
                detail=f"No current consent version found for type: {consent_type}",
            )

        return ConsentVersionResponse(**version.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting current consent version: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/versions/{version_id}",
    response_model=ConsentVersionResponse,
    summary="Get consent version by ID",
)
async def get_consent_version(
    version_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    company_id: str = Depends(get_verified_company_id),
    repo: ConsentRepository = Depends(get_consent_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Get a specific consent version by ID."""
    try:
        version_uuid = UUID(version_id)
        company_uuid = UUID(company_id)

        version = await repo.get_version(version_uuid, company_uuid)

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


@router.post(
    "/events/",
    response_model=ConsentEventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register consent event",
)
async def create_consent_event(
    data: ConsentEventCreate,
    company_id: str = Depends(get_verified_company_id),
    repo: ConsentRepository = Depends(get_consent_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Register a consent event (grant, revoke, renew, expire). Public endpoint for WhatsApp integration."""
    try:
        company_uuid = UUID(company_id)
        consent_version_uuid = UUID(data.consent_version_id)

        version = await repo.get_version(consent_version_uuid, company_uuid)

        if not version:
            raise HTTPException(status_code=404, detail="Consent version not found")

        now = datetime.utcnow()

        proof_hash = calculate_proof_hash(
            data.consent_version_id,
            data.subject_email,
            data.subject_identifier,
            data.event_type.value,
            data.consent_given,
            now,
        )

        expires_at = None
        if data.consent_given and version.renewal_period_days:
            expires_at = now + timedelta(days=version.renewal_period_days)

        event = await repo.create_event(
            company_uuid=company_uuid,
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
            expires_at=expires_at,
        )

        logger.info(
            f"Created consent event {event.id} for subject {data.subject_identifier}, type {data.event_type.value}"
        )
        return ConsentEventResponse(**event.to_dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid data: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        await repo.rollback()
        logger.error(f"Error creating consent event: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/events/",
    response_model=ConsentEventListResponse,
    summary="List consent events",
)
async def list_consent_events(
    consent_version_id: str | None = Query(None, description="Filter by consent version ID"),
    subject_email: str | None = Query(None, description="Filter by subject email"),
    event_type: str | None = Query(None, description="Filter by event type"),
    date_from: datetime | None = Query(None, description="Filter events from this date"),
    date_to: datetime | None = Query(None, description="Filter events until this date"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    company_id: str = Depends(get_verified_company_id),
    repo: ConsentRepository = Depends(get_consent_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """List consent events with optional filters and pagination."""
    try:
        company_uuid = UUID(company_id)

        consent_version_uuid = UUID(consent_version_id) if consent_version_id else None

        events, total = await repo.list_events(
            company_uuid,
            consent_version_id=consent_version_uuid,
            subject_email=subject_email,
            event_type=event_type,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
            offset=offset,
        )

        return ConsentEventListResponse(
            events=[ConsentEventResponse(**e.to_dict()) for e in events],
            total=total,
            limit=limit,
            offset=offset,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid data: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing consent events: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/events/subject/{subject_identifier}",
    response_model=ConsentSubjectHistory,
    summary="Get subject consent history",
)
async def get_subject_consent_history(
    subject_identifier: str,
    company_id: str = Depends(get_verified_company_id),
    repo: ConsentRepository = Depends(get_consent_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Get complete consent history for a data subject."""
    try:
        company_uuid = UUID(company_id)

        events = await repo.get_subject_events(company_uuid, subject_identifier)

        if not events:
            raise HTTPException(
                status_code=404,
                detail="No consent history found for this subject",
            )

        version_ids = list(set(e.consent_version_id for e in events))
        versions = await repo.get_versions_by_ids(version_ids)

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

            subject_events.append(
                ConsentSubjectEvent(
                    id=str(event.id),
                    consent_type=consent_type,
                    consent_version=consent_version_str,
                    event_type=event.event_type,
                    consent_given=event.consent_given,
                    channel=event.channel,
                    created_at=event.created_at,
                    expires_at=event.expires_at,
                    is_expired=is_expired,
                    is_current=is_current,
                )
            )

        return ConsentSubjectHistory(
            subject_identifier=subject_identifier,
            subject_email=events[0].subject_email if events else "",
            events=subject_events,
            current_consents=current_consents,
            total_events=len(events),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting subject consent history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/events/revoke",
    response_model=ConsentEventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Revoke consent",
)
async def revoke_consent(
    data: ConsentRevokeRequest,
    company_id: str = Depends(get_verified_company_id),
    repo: ConsentRepository = Depends(get_consent_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Revoke consent for a data subject. Creates a revocation event."""
    try:
        company_uuid = UUID(company_id)

        if not data.consent_type and not data.consent_version_id:
            raise HTTPException(
                status_code=400,
                detail="Either consent_type or consent_version_id must be provided",
            )

        if data.consent_version_id:
            version_uuid = UUID(data.consent_version_id)
            version = await repo.get_version(version_uuid, company_uuid)
        else:
            version = await repo.get_active_version(company_uuid, data.consent_type)

        if not version:
            raise HTTPException(status_code=404, detail="Consent version not found")

        last_event = await repo.get_last_granted_event(
            company_uuid, version.id, data.subject_identifier
        )

        if not last_event:
            raise HTTPException(
                status_code=404,
                detail="No active consent found to revoke for this subject",
            )

        now = datetime.utcnow()

        proof_hash = calculate_proof_hash(
            str(version.id),
            last_event.subject_email,
            data.subject_identifier,
            "revoked",
            False,
            now,
        )

        revoke_event = await repo.create_event(
            company_uuid=company_uuid,
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
            expires_at=None,
        )

        logger.info(f"Revoked consent {revoke_event.id} for subject {data.subject_identifier}")
        return ConsentEventResponse(**revoke_event.to_dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid data: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        await repo.rollback()
        logger.error(f"Error revoking consent: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=ConsentStats, summary="Get consent statistics")
async def get_consent_stats(
    company_id: str = Depends(get_verified_company_id),
    repo: ConsentRepository = Depends(get_consent_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Get aggregated consent statistics for the company."""
    try:
        company_uuid = UUID(company_id)
        now = datetime.utcnow()

        total_versions = await repo.count_versions(company_uuid)
        total_events = await repo.count_events(company_uuid)
        total_subjects = await repo.count_distinct_subjects(company_uuid)
        total_granted = await repo.count_granted(company_uuid)
        total_revoked = await repo.count_revoked(company_uuid)
        total_expired = await repo.count_expired(company_uuid, now)

        consent_types = await repo.get_distinct_consent_types(company_uuid)

        by_type = []
        for consent_type in consent_types:
            version_ids = await repo.get_version_ids_for_type(company_uuid, consent_type)

            if not version_ids:
                continue

            type_granted = await repo.count_granted_for_versions(version_ids)
            type_revoked = await repo.count_revoked_for_versions(version_ids)
            type_expired = await repo.count_expired_for_versions(version_ids, now)

            type_active = type_granted - type_revoked - type_expired
            consent_rate = (
                (type_granted / (type_granted + type_revoked)) * 100
                if (type_granted + type_revoked) > 0
                else 0.0
            )

            by_type.append(
                ConsentTypeStats(
                    consent_type=consent_type,
                    total_granted=type_granted,
                    total_revoked=type_revoked,
                    total_expired=type_expired,
                    total_active=max(0, type_active),
                    consent_rate=round(consent_rate, 2),
                )
            )

        by_channel = await repo.get_events_by_channel(company_uuid)

        return ConsentStats(
            total_consent_versions=total_versions,
            total_consent_events=total_events,
            total_subjects=total_subjects,
            total_granted=total_granted,
            total_revoked=total_revoked,
            total_expired=total_expired,
            by_type=by_type,
            by_channel=by_channel,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting consent stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

reorder_collection_before_item(router)

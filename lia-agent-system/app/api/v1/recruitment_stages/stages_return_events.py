"""
Return event endpoints (post-transition candidate completion signals).

- POST /transition/return-event          (process single event)
- POST /transition/return-event/bulk     (process multiple events)
- GET  /transition/return-event/recent   (polling)
- GET  /transition/return-event/types    (list supported types)
"""
import asyncio
import json
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from starlette.responses import StreamingResponse

from ._shared import (
    RETURN_EVENT_CONFIG,
    ReturnEventRequest,
    ReturnEventResponse,
    BulkReturnEventRequest,
    ReturnEventService,
    get_current_active_user,
    get_user_company_id,
    get_stage_repo,
    RecruitmentStageRepository,
    User,
)
from app.shared.security.require_company_id import require_company_id, require_company_id_strict_match

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Recruitment Stages - Return Events"])


@router.get("/transition/return-event/stream", response_model=None)
async def stream_return_events(
    job_id: str | None = None,
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(require_company_id),
):
    """SSE stream return events.

    Onda 4.2b-P0-9 (2026-05-23): removido company_id como query param que
    sobrescrevia o JWT. Antes user passava ?company_id=other-tenant-uuid e
    streamava activity feed de outra empresa (LGPD critical).
    company_id agora vem APENAS do JWT (Depends).
    """
    from sqlalchemy import and_ as sa_and
    from sqlalchemy import select as sa_select

    from app.core.database import async_session_factory
    from app.models.activity_feed import ActivityFeed

    effective_company_id = company_id

    async def event_generator():
        last_check = datetime.utcnow()
        while True:
            try:
                async with async_session_factory() as session:
                    filters = [
                        ActivityFeed.activity_type.like("return_event_%"),
                        ActivityFeed.created_at > last_check,
                        ActivityFeed.is_visible,
                    ]

                    if effective_company_id:
                        filters.append(
                            ActivityFeed.extra_data["company_id"].as_string() == effective_company_id
                        )

                    if job_id:
                        filters.append(
                            ActivityFeed.extra_data["job_id"].as_string() == job_id
                        )

                    query = sa_select(ActivityFeed).where(sa_and(*filters))
                    query = query.order_by(ActivityFeed.created_at.desc()).limit(20)

                    result = await session.execute(query)
                    activities = result.scalars().all()

                    if activities:
                        last_check = datetime.utcnow()
                        for activity in activities:
                            extra = activity.extra_data or {} if hasattr(activity, 'extra_data') else {}
                            event = {
                                "id": str(activity.id),
                                "event_type": extra.get("event_type", activity.activity_type.replace("return_event_", "")),
                                "vacancy_candidate_id": extra.get("vacancy_candidate_id", ""),
                                "candidate_name": getattr(activity, 'actor_name', '') or "",
                                "new_sub_status": extra.get("sub_status", ""),
                                "new_stage": extra.get("new_stage"),
                                "auto_moved": extra.get("new_stage") is not None,
                                "notification_type": extra.get("notification_type", "info"),
                                "title": getattr(activity, 'title', '') or "",
                                "description": getattr(activity, 'description', '') or "",
                                "action_label": getattr(activity, 'action_label', 'Ver Candidato') or "Ver Candidato",
                                "action_url": getattr(activity, 'action_url', '') or "",
                                "category": getattr(activity, 'category', '') or "",
                                "timestamp": activity.created_at.isoformat() if hasattr(activity, 'created_at') and activity.created_at else "",
                            }
                            yield f"data: {json.dumps(event)}\n\n"
                    else:
                        yield ": keepalive\n\n"
            except Exception as e:
                logger.error(f"SSE error: {e}")
                yield ": error\n\n"
            await asyncio.sleep(5)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.post("/transition/return-event", response_model=ReturnEventResponse)
async def process_return_event(
    request: ReturnEventRequest,
    stage_repo: RecruitmentStageRepository = Depends(get_stage_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Process a candidate return event.

    Used when a candidate completes an action (screening, interview confirmation,
    test submission, document upload, offer response) to update their sub-status,
    optionally auto-move to a new stage, and notify the recruiter.

    Valid event_types:
    - screening_complete, screening_expired
    - interview_confirmed, interview_declined, interview_completed, interview_no_show
    - test_submitted, test_expired
    - documents_received
    - offer_accepted, offer_declined

    Auto-move rules:
    - offer_accepted → moves candidate to "hired" stage
    - offer_declined → moves candidate to "offer_declined" stage
    - All other events → only update sub-status (no stage change)
    """
    try:
        # Onda 4.2b-P0-10 (2026-05-23): cross-tenant pre-check.
        # Antes user empresa A podia disparar event em candidato empresa B
        # (offer_accepted → auto-move pra hired + notificacao).
        from sqlalchemy import select as sa_select
        from app.models.candidate import VacancyCandidate

        vc_check = await stage_repo.db.execute(
            sa_select(VacancyCandidate.id).where(
                VacancyCandidate.id == request.vacancy_candidate_id,
                VacancyCandidate.company_id == company_id,
            )
        )
        if not vc_check.scalar_one_or_none():
            raise HTTPException(
                status_code=404,
                detail="Candidate not found in this tenant",
            )

        service = ReturnEventService(stage_repo.db)
        result = await service.process_event(
            vacancy_candidate_id=request.vacancy_candidate_id,
            event_type=request.event_type,
            metadata=request.metadata,
            triggered_by=request.triggered_by,
        )

        auto_moved = result.get("new_stage") is not None and result.get("success", False)

        logger.info(
            f"Return event processed: type={request.event_type}, "
            f"candidate={request.vacancy_candidate_id}, "
            f"success={result.get('success')}, auto_moved={auto_moved}"
        )

        return ReturnEventResponse(
            success=result.get("success", False),
            event_type=result.get("event_type", request.event_type),
            new_sub_status=result.get("new_sub_status"),
            new_stage=result.get("new_stage"),
            activity_id=result.get("activity_id"),
            notification_sent=result.get("notification_sent", False),
            auto_moved=auto_moved,
            error=result.get("error"),
        )
    except Exception as e:
        logger.error(f"Error processing return event: {e}", exc_info=True)
        return ReturnEventResponse(
            success=False,
            event_type=request.event_type,
            error=str(e),
        )


@router.post("/transition/return-event/bulk", response_model=None)
async def process_bulk_return_events(
    request: BulkReturnEventRequest,
    stage_repo: RecruitmentStageRepository = Depends(get_stage_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Process multiple return events in batch.
    Useful for webhook payloads that report multiple candidate completions at once.
    """
    # Onda 4.2b-P0-10 (2026-05-23): cross-tenant pre-check em batch.
    from sqlalchemy import select as sa_select
    from app.models.candidate import VacancyCandidate

    requested_ids = [event.vacancy_candidate_id for event in request.events]
    tenant_check = await stage_repo.db.execute(
        sa_select(VacancyCandidate.id).where(
            VacancyCandidate.id.in_(requested_ids),
            VacancyCandidate.company_id == company_id,
        )
    )
    allowed_ids = {str(r[0]) for r in tenant_check.all()}

    results = []
    service = ReturnEventService(stage_repo.db)

    for event in request.events:
        if str(event.vacancy_candidate_id) not in allowed_ids:
            results.append({
                "vacancy_candidate_id": event.vacancy_candidate_id,
                "event_type": event.event_type,
                "success": False,
                "error": "Candidate not in your tenant",
            })
            continue
        try:
            result = await service.process_event(
                vacancy_candidate_id=event.vacancy_candidate_id,
                event_type=event.event_type,
                metadata=event.metadata,
                triggered_by=event.triggered_by,
            )
            results.append({
                "vacancy_candidate_id": event.vacancy_candidate_id,
                "event_type": event.event_type,
                **result,
            })
        except Exception as e:
            results.append({
                "vacancy_candidate_id": event.vacancy_candidate_id,
                "event_type": event.event_type,
                "success": False,
                "error": str(e),
            })

    success_count = sum(1 for r in results if r.get("success"))
    logger.info(f"Bulk return events processed: {success_count}/{len(results)} successful")

    return {
        "total": len(results),
        "success_count": success_count,
        "failure_count": len(results) - success_count,
        "results": results,
    }


@router.get("/transition/return-event/recent", response_model=None)
async def get_recent_return_events(
    since: str | None = Query(None, description="ISO timestamp to fetch events since"),
    job_id: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    stage_repo: RecruitmentStageRepository = Depends(get_stage_repo),
    company_id: str = Depends(require_company_id),
):
    """Get recent return events for polling/real-time updates.

    Onda 4.2b-P0-11 (2026-05-23): removido company_id query param + filter
    NULL (was dead code). Antes vazava events de TODAS empresas misturados
    (LGPD critical). Agora filtra por JWT company_id.
    """
    try:
        from sqlalchemy import select as sa_select

        from app.models.activity_feed import ActivityFeed

        query = sa_select(ActivityFeed).where(
            ActivityFeed.activity_type.like("return_event_%"),  # type: ignore[union-attr]
            # Onda 4.2b-P0-11 (2026-05-23): filtro tenant obrigatorio.
            ActivityFeed.extra_data["company_id"].as_string() == company_id,
        )

        if since:
            from datetime import datetime as dt
            try:
                since_dt = dt.fromisoformat(since.replace('Z', '+00:00'))
                query = query.where(ActivityFeed.created_at > since_dt)  # type: ignore[operator]
            except ValueError:
                pass

        if job_id:
            query = query.where(
                ActivityFeed.extra_data["job_id"].as_string() == job_id
            )

        query = query.order_by(ActivityFeed.created_at.desc()).limit(limit)  # type: ignore[union-attr]

        result = await stage_repo.db.execute(query)
        activities = result.scalars().all()

        events = []
        for activity in activities:
            extra = activity.extra_data or {} if hasattr(activity, 'extra_data') else {}
            events.append({
                "id": str(activity.id),
                "event_type": extra.get("event_type", activity.activity_type.replace("return_event_", "")),
                "vacancy_candidate_id": extra.get("vacancy_candidate_id", ""),
                "candidate_name": getattr(activity, 'actor_name', '') or "",
                "new_sub_status": extra.get("sub_status", ""),
                "new_stage": extra.get("new_stage"),
                "auto_moved": extra.get("new_stage") is not None,
                "notification_type": extra.get("notification_type", "info"),
                "title": getattr(activity, 'title', '') or "",
                "description": getattr(activity, 'description', '') or "",
                "action_label": getattr(activity, 'action_label', 'Ver Candidato') or "Ver Candidato",
                "action_url": getattr(activity, 'action_url', '') or "",
                "category": getattr(activity, 'category', '') or "",
                "timestamp": activity.created_at.isoformat() if hasattr(activity, 'created_at') and activity.created_at else "",
            })

        return {
            "events": events,
            "total": len(events),
            "since": since,
        }
    except Exception as e:
        logger.error(f"Error fetching recent return events: {e}", exc_info=True)
        return {"events": [], "total": 0, "since": since, "error": str(e)}


@router.get("/transition/return-event/types", response_model=None)
async def list_return_event_types(company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    List all supported return event types with their configurations.
    Useful for frontend to know which events are available and their effects.
    """
    event_types = []
    for event_type, config in RETURN_EVENT_CONFIG.items():
        event_types.append({
            "event_type": event_type,
            "sub_status": config["sub_status"],
            "auto_moves_to_stage": config.get("stage"),
            "category": config.get("category"),
            "priority": config.get("priority", "normal"),
            "description": config.get("description_template", "").replace("{candidate_name}", "[candidato]"),
        })

    return {
        "event_types": event_types,
        "total": len(event_types),
    }

"""
Search endpoints for candidates: local search, global (Pearch AI) search, and health check.
"""
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query

from ._shared import (
    AuditService,
    CandidateRepository,
    CandidateSearch,
    CandidateSearchRequest,
    CandidateSearchResponse,
    PearchSearchRequest,
    PearchSearchResponse,
    PearchService,
    get_audit_service,
    get_candidate_repo,
    get_current_user_or_demo,
    get_pearch_service,
    logger,
    User,
)
from app.shared.security.require_company_id import require_company_id

router = APIRouter()


@router.post("/search/local", response_model=CandidateSearchResponse)
async def search_candidates_local(
    request: CandidateSearchRequest,
    current_user: User = Depends(get_current_user_or_demo),
    candidate_repo: CandidateRepository = Depends(get_candidate_repo),
    audit_svc: AuditService = Depends(get_audit_service),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Search candidates in proprietary PostgreSQL database (FREE - no credits consumed).

    This is ALWAYS the first search tier. Only suggest global search if local results
    are insufficient.
    """
    start_time = datetime.utcnow()
    filters = request.filters

    try:
        candidates_db, total_count = await candidate_repo.search_local(filters)
        from app.schemas.candidate import CandidateResponse
        candidates = [CandidateResponse.model_validate(c) for c in candidates_db]

        search_duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        # RLS-EXEMPT: candidate_searches has no company_id column and no RLS policy (per-user saved-search metadata, not tenant-scoped row data)  WT-LEGACY-RLS-EXEMPT exp:2026-11-30
        search_record = CandidateSearch(
            id=uuid.uuid4(),
            user_id=str(current_user.id),
            conversation_id=request.conversation_id,
            search_query=filters.query or "structured_search",
            search_filters=filters.model_dump(),
            local_results_count=len(candidates),
            global_results_count=0,
            total_results=total_count or 0,
            used_global_search=False,
            credits_consumed=0,
            search_source="local",
            search_duration_ms=search_duration_ms,
            created_at=datetime.utcnow(),
        )
        search_record = await candidate_repo.record_search(search_record)
        logger.info(f"Local search completed: {len(candidates)} results in {search_duration_ms}ms")

        try:
            _company = getattr(current_user, "company_id", None)
            active_filters = [k for k, v in (filters.model_dump() or {}).items() if v]
            await audit_svc.log_decision(
                company_id=str(_company) if _company else None,
                agent_name="candidate_search",
                decision_type="search_candidates",
                action="local_search",
                decision="executed",
                reasoning=[
                    f"Local search returned {len(candidates)} results",
                    f"Duration: {search_duration_ms}ms",
                    f"Active filters: {len(active_filters)}",
                    f"Total matches: {total_count or 0}",
                ],
                criteria_used=active_filters or ["no_filters"],
                score=float(len(candidates)),
                confidence=1.0,
                human_review_required=False,
            )
        except Exception as audit_err:
            logger.warning(f"Audit log failed for local_search: {audit_err}")

        return CandidateSearchResponse(
            candidates=candidates,
            total_count=total_count or 0,
            local_count=len(candidates),
            global_count=0,
            search_id=uuid.UUID(str(search_record.id)),
            credits_consumed=0,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Local search failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/search", response_model=PearchSearchResponse)
async def search_candidates(
    request: PearchSearchRequest,
    audit_svc: AuditService = Depends(get_audit_service),
    pearch_svc: PearchService = Depends(get_pearch_service),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Search for candidates using natural language query (Pearch AI - PAID)."""
    try:
        _timeout = getattr(request, "timeout", 60) or 60
        import time as _time
        _gs_start = _time.monotonic()
        result = await pearch_svc.search_candidates(
            request=request,
            timeout=_timeout,
        )
        _gs_duration_ms = round((_time.monotonic() - _gs_start) * 1000, 1)
        try:
            _result_count = len(getattr(result, "candidates", [])) if result else 0
            await audit_svc.log_decision(
                company_id=None,
                agent_name="candidate_search",
                decision_type="search_candidates",
                action="global_search",
                decision="executed",
                reasoning=[
                    f"Global search ({request.type}) executed",
                    f"Results returned: {_result_count}",
                    f"Duration: {_gs_duration_ms}ms",
                    f"Query length: {len(request.query)} chars",
                    f"Limit: {request.limit}",
                    f"Timeout: {_timeout}s",
                ],
                criteria_used=["query", "search_type", "limit", "timeout"],
                score=float(_result_count),
                human_review_required=False,
            )
        except Exception as audit_err:
            logger.warning(f"Audit log failed for global_search: {audit_err}")
        return result
    except ValueError as e:
        raise HTTPException(status_code=500, detail="Internal server error")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Candidate search failed: {e}")
        raise HTTPException(status_code=500, detail="Candidate search failed")


@router.get("/search", response_model=PearchSearchResponse)
async def search_candidates_get(
    query: str = Query(..., description="Natural language search query"),
    search_type: str = Query("fast", description="Search type: 'fast' or 'deep'"),
    limit: int = Query(10, ge=1, le=100, description="Number of results"),
    timeout: int = Query(60, ge=10, le=1800, description="Timeout in seconds"),
    pearch_svc: PearchService = Depends(get_pearch_service),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Search for candidates using GET request (convenient for testing)."""
    try:
        from lia_models.pearch import SearchType as _ST
        _type = _ST.FAST
        req = PearchSearchRequest(query=query, type=_type, limit=limit)
        return await pearch_svc.search_candidates(request=req, timeout=timeout)
    except ValueError as e:
        raise HTTPException(status_code=500, detail="Internal server error")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Candidate search failed: {e}")
        raise HTTPException(status_code=500, detail="Candidate search failed")


@router.post("/search/by-job-description", response_model=PearchSearchResponse)
async def search_by_job_description(
    job_description: str,
    location: str | None = None,
    limit: int = Query(20, ge=1, le=100),
    pearch_svc: PearchService = Depends(get_pearch_service),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Search candidates by pasting a full job description."""
    try:
        return await pearch_svc.search_by_job_description(
            job_description=job_description, location=location, limit=limit
        )
    except ValueError as e:
        raise HTTPException(status_code=500, detail="Internal server error")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Job description search failed: {e}")
        raise HTTPException(status_code=500, detail="Job description search failed")


@router.get("/health", response_model=None)
async def health_check(company_id: str = Depends(require_company_id)):
    # multi-tenancy: public endpoint (health) — no tenant data
    """Check if Pearch AI integration is properly configured."""
    import os
    api_key_configured = bool(os.getenv("PEARCH_API_KEY"))
    return {
        "service": "Pearch AI Candidate Search",
        "status": "configured" if api_key_configured else "not_configured",
        "api_key_set": api_key_configured,
        "message": (
            "Ready to search 190M+ candidate profiles"
            if api_key_configured
            else "PEARCH_API_KEY not configured"
        ),
    }

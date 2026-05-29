"""
Sourcing API - Endpoints for candidate sourcing, matching, and suggestions.

Provides:
- POST /api/v1/sourcing/search - Search candidates with boolean queries
- POST /api/v1/sourcing/match-candidates - Match candidates to job requirements
- GET /api/v1/sourcing/suggestions/{job_id} - Get suggested candidates for a job
- POST /api/v1/sourcing/boolean-query - Generate boolean search string
- POST /api/v1/sourcing/proactive-suggest - Trigger proactive suggestions
"""
import logging
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel, Field
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.sourcing.services.query_builders import (
    BooleanQueryBuilder,
    CandidateMatcher,
)
from app.models.candidate import Candidate
from app.models.job_vacancy import JobVacancy
from app.api.v1._path_patterns import (
    DUAL_ID_PATH_PATTERN,
    reorder_collection_before_item,
)
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sourcing", tags=["sourcing"])


class SourcingSearchRequest(WeDoBaseModel):
    """Request for candidate sourcing search."""
    query: str | None = Field(None, description="Free text search query")
    title: str | None = Field(None, description="Job title to search")
    skills: list[str] = Field(default_factory=list, description="Required skills")
    companies: list[str] = Field(default_factory=list, description="Target companies")
    industries: list[str] = Field(default_factory=list, description="Target industries")
    location: str | None = Field(None, description="Location preference")
    seniority: str | None = Field(None, description="Seniority level: junior, pleno, senior, manager, director")
    min_experience: int | None = Field(None, ge=0, le=50, description="Minimum years of experience")
    max_experience: int | None = Field(None, ge=0, le=50, description="Maximum years of experience")
    exclude_terms: list[str] = Field(default_factory=list, description="Terms to exclude")
    job_id: str | None = Field(None, description="Job ID to link search results")
    limit: int = Field(default=20, ge=1, le=100, description="Maximum results to return")
    include_boolean_queries: bool = Field(default=True, description="Include generated boolean queries")


class SourcingSearchResponse(BaseModel):
    """Response from candidate sourcing search."""
    success: bool
    query: str | None = None
    boolean_queries: dict[str, str] | None = None
    candidates_found: int
    candidates: list[dict[str, Any]]
    job_id: str | None = None
    search_time_ms: int = 0


class MatchCandidatesRequest(WeDoBaseModel):
    """Request to match candidates against job requirements."""
    job_id: str = Field(..., description="Job ID to match against")
    candidate_ids: list[str] = Field(default_factory=list, description="Specific candidate IDs to evaluate")
    limit: int = Field(default=50, ge=1, le=200, description="Maximum candidates to evaluate")
    min_score: float = Field(default=0, ge=0, le=100, description="Minimum score threshold")
    weights: dict[str, float] | None = Field(None, description="Custom weights: skills, experience, location")


class MatchResult(BaseModel):
    """Individual candidate match result."""
    candidate_id: str
    candidate_name: str | None = None
    overall_score: float
    tier: str
    recommendation: str
    breakdown: dict[str, Any]
    missing_skills: list[str] = Field(default_factory=list)


class MatchCandidatesResponse(BaseModel):
    """Response from candidate matching."""
    success: bool
    job_id: str
    job_title: str | None = None
    total_evaluated: int
    tier_summary: dict[str, int]
    results: list[MatchResult]
    processing_time_ms: int = 0


class SuggestionResponse(BaseModel):
    """Response with suggested candidates for a job."""
    success: bool
    job_id: str
    job_title: str | None = None
    suggestions_count: int
    suggestions: list[dict[str, Any]]
    criteria_used: dict[str, Any]


class BooleanQueryRequest(WeDoBaseModel):
    """Request to generate boolean search query."""
    title: str | None = Field(None, description="Job title")
    skills: list[str] = Field(default_factory=list, description="Required skills")
    companies: list[str] = Field(default_factory=list, description="Target companies")
    industries: list[str] = Field(default_factory=list, description="Target industries")
    location: str | None = Field(None, description="Location")
    seniority: str | None = Field(None, description="Seniority level")
    exclude_terms: list[str] = Field(default_factory=list, description="Terms to exclude")
    expand_synonyms: bool = Field(default=True, description="Expand skills with synonyms")


class BooleanQueryResponse(BaseModel):
    """Response with generated boolean queries."""
    success: bool
    queries: dict[str, str]
    synonyms_expanded: list[dict[str, Any]] = Field(default_factory=list)


class ProactiveSuggestRequest(WeDoBaseModel):
    """Request to trigger proactive suggestions."""
    job_id: str = Field(..., description="Job ID for suggestions")
    trigger: str = Field(default="manual", description="Trigger type: new_job, manual, scheduled")


@router.post("/search", response_model=SourcingSearchResponse)
async def search_candidates(
    request: SourcingSearchRequest,
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Search candidates with advanced boolean query building.
    
    Searches the local candidate database using the provided criteria.
    Returns candidates with generated boolean queries for other platforms.
    """
    import time
    start_time = time.time()
    
    boolean_queries = None
    if request.include_boolean_queries:
        builder = BooleanQueryBuilder()
        raw_queries = builder.build_query(
            title=request.title or request.query,
            skills=request.skills,
            companies=request.companies,
            industries=request.industries,
            location=request.location,
            seniority=request.seniority,
            exclude_terms=request.exclude_terms
        )
        boolean_queries = {k: v for k, v in raw_queries.items() if k != "raw_parts"}
    
    query = select(Candidate).where(Candidate.company_id == company_id).limit(request.limit)
    
    conditions = []
    
    if request.query:
        search_pattern = f"%{request.query}%"
        conditions.append(
            or_(
                Candidate.name.ilike(search_pattern),
                Candidate.current_title.ilike(search_pattern),
                Candidate.headline.ilike(search_pattern)
            )
        )
    
    if request.title:
        title_pattern = f"%{request.title}%"
        conditions.append(
            or_(
                Candidate.current_title.ilike(title_pattern),
                Candidate.headline.ilike(title_pattern)
            )
        )
    
    if request.location:
        location_pattern = f"%{request.location}%"
        conditions.append(
            or_(
                Candidate.location_city.ilike(location_pattern),
                Candidate.location_state.ilike(location_pattern),
                Candidate.location_country.ilike(location_pattern)
            )
        )
    
    if request.min_experience is not None:
        conditions.append(Candidate.years_of_experience >= request.min_experience)
    
    if request.max_experience is not None:
        conditions.append(Candidate.years_of_experience <= request.max_experience)
    
    if conditions:
        query = query.where(and_(*conditions))
    
    result = await db.execute(query)
    candidates = result.scalars().all()
    
    candidates_data = []
    for c in candidates:
        candidate_dict = {
            "id": str(c.id),
            "name": c.name,
            "email": c.email,
            "current_title": c.current_title,
            "headline": c.headline,
            "location_city": c.location_city,
            "location_state": c.location_state,
            "location_country": c.location_country,
            "years_of_experience": c.years_of_experience,
            "technical_skills": c.technical_skills or [],
            "linkedin_url": c.linkedin_url,
            "avatar_url": c.avatar_url
        }
        candidates_data.append(candidate_dict)
    
    search_time_ms = int((time.time() - start_time) * 1000)
    
    return SourcingSearchResponse(
        success=True,
        query=request.query,
        boolean_queries=boolean_queries,
        candidates_found=len(candidates_data),
        candidates=candidates_data,
        job_id=request.job_id,
        search_time_ms=search_time_ms
    )


@router.post("/match-candidates", response_model=MatchCandidatesResponse)
async def match_candidates(
    request: MatchCandidatesRequest,
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Match and score candidates against job requirements.
    
    Evaluates candidates using weighted scoring for:
    - Skills match (default 50%)
    - Experience match (default 30%)
    - Location match (default 20%)
    
    Returns tiered results (A, B, C, D) with detailed breakdown.
    """
    import time

# RAILS-DEPRECATED: This endpoint manages Rails-owned entities (candidates/jobs/applies/users).
# Direct DB calls will be replaced by RailsAdapter after ats-api-rails handoff.
# See: app/domains/integrations_hub/services/rails_adapter.py
    start_time = time.time()
    
    job_result = await db.execute(
        select(JobVacancy).where(JobVacancy.id == request.job_id, JobVacancy.company_id == company_id)
    )
    job = job_result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {request.job_id} not found")
    
    required_skills = job.technical_requirements or []
    nice_to_have_skills = job.nice_to_have_skills or []
    min_experience = job.min_experience_years
    max_experience = job.max_experience_years
    job_city = job.location_city
    job_state = job.location_state
    job_country = job.location_country
    allows_remote = job.allows_remote or job.work_model == "remote"
    work_model = job.work_model
    
    if request.candidate_ids:
        candidates_query = select(Candidate).where(
            Candidate.id.in_(request.candidate_ids),
            Candidate.company_id == company_id,
        ).limit(request.limit)
    else:
        candidates_query = select(Candidate).where(Candidate.company_id == company_id).limit(request.limit)
    
    candidates_result = await db.execute(candidates_query)
    candidates = candidates_result.scalars().all()
    
    matcher = CandidateMatcher()
    results = []
    
    for candidate in candidates:
        candidate_skills = (candidate.technical_skills or []) + (candidate.soft_skills or [])
        
        skills_match = matcher.calculate_skills_match(
            candidate_skills=candidate_skills,
            required_skills=required_skills,
            nice_to_have_skills=nice_to_have_skills
        )
        
        experience_match = matcher.calculate_experience_match(
            candidate_years=candidate.years_of_experience,
            required_min=min_experience,
            required_max=max_experience
        )
        
        location_match = matcher.calculate_location_match(
            candidate_city=candidate.location_city,
            candidate_state=candidate.location_state,
            candidate_country=candidate.location_country,
            candidate_is_remote=getattr(candidate, 'prefers_remote', False),
            job_city=job_city,
            job_state=job_state,
            job_country=job_country,
            job_allows_remote=allows_remote,
            job_work_model=work_model
        )
        
        weights = request.weights or {"skills": 0.50, "experience": 0.30, "location": 0.20}
        overall = matcher.calculate_overall_score(
            skills_match=skills_match,
            experience_match=experience_match,
            location_match=location_match,
            weights=weights
        )
        
        if overall["overall_score"] >= request.min_score:
            results.append(MatchResult(
                candidate_id=str(candidate.id),
                candidate_name=candidate.name,
                overall_score=overall["overall_score"],
                tier=overall["tier"],
                recommendation=overall["recommendation"],
                breakdown={
                    "skills": skills_match,
                    "experience": experience_match,
                    "location": location_match
                },
                missing_skills=skills_match.get("missing_required", [])
            ))
    
    results.sort(key=lambda x: x.overall_score, reverse=True)
    
    tier_summary = {
        "A": len([r for r in results if r.tier == "A"]),
        "B": len([r for r in results if r.tier == "B"]),
        "C": len([r for r in results if r.tier == "C"]),
        "D": len([r for r in results if r.tier == "D"])
    }
    
    processing_time_ms = int((time.time() - start_time) * 1000)
    
    return MatchCandidatesResponse(
        success=True,
        job_id=request.job_id,
        job_title=job.title,
        total_evaluated=len(results),
        tier_summary=tier_summary,
        results=results,
        processing_time_ms=processing_time_ms
    )


@router.get("/suggestions/{job_id}", response_model=SuggestionResponse)
async def get_suggested_candidates(
    job_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    limit: int = Query(default=20, ge=1, le=100),
    min_score: float = Query(default=55.0, ge=0, le=100),
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Get suggested candidates for a job from the talent pool.
    
    Returns candidates scored and ranked by match with job requirements.
    Only includes candidates with score >= min_score (default 55%).
    """
    job_result = await db.execute(
        select(JobVacancy).where(JobVacancy.id == job_id, JobVacancy.company_id == company_id)
    )
    job = job_result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    criteria = {
        "required_skills": job.technical_requirements or [],
        "nice_to_have_skills": job.nice_to_have_skills or [],
        "min_experience": job.min_experience_years,
        "max_experience": job.max_experience_years,
        "location": {
            "city": job.location_city,
            "state": job.location_state,
            "country": job.location_country
        },
        "allows_remote": job.allows_remote or job.work_model == "remote",
        "work_model": job.work_model
    }
    
    candidates_query = select(Candidate).where(Candidate.company_id == company_id).limit(limit * 3)
    candidates_result = await db.execute(candidates_query)
    candidates = candidates_result.scalars().all()
    
    matcher = CandidateMatcher()
    scored_candidates = []
    
    for candidate in candidates:
        candidate_skills = (candidate.technical_skills or []) + (candidate.soft_skills or [])
        
        skills_match = matcher.calculate_skills_match(
            candidate_skills=candidate_skills,
            required_skills=criteria["required_skills"],
            nice_to_have_skills=criteria["nice_to_have_skills"]
        )
        
        experience_match = matcher.calculate_experience_match(
            candidate_years=candidate.years_of_experience,
            required_min=criteria["min_experience"],
            required_max=criteria["max_experience"]
        )
        
        location_match = matcher.calculate_location_match(
            candidate_city=candidate.location_city,
            candidate_state=candidate.location_state,
            candidate_country=candidate.location_country,
            candidate_is_remote=getattr(candidate, 'prefers_remote', False),
            job_city=criteria["location"]["city"],
            job_state=criteria["location"]["state"],
            job_country=criteria["location"]["country"],
            job_allows_remote=criteria["allows_remote"],
            job_work_model=criteria["work_model"]
        )
        
        overall = matcher.calculate_overall_score(
            skills_match=skills_match,
            experience_match=experience_match,
            location_match=location_match
        )
        
        if overall["overall_score"] >= min_score:
            scored_candidates.append({
                "candidate_id": str(candidate.id),
                "name": candidate.name,
                "email": candidate.email,
                "current_position": candidate.current_position,
                "location": candidate.location,
                "years_of_experience": candidate.years_of_experience,
                "linkedin_url": candidate.linkedin_url,
                "avatar_url": candidate.avatar_url,
                "overall_score": overall["overall_score"],
                "tier": overall["tier"],
                "recommendation": overall["recommendation"],
                "matched_skills": skills_match.get("matched_required", []),
                "missing_skills": skills_match.get("missing_required", [])
            })
    
    scored_candidates.sort(key=lambda x: x["overall_score"], reverse=True)
    suggestions = scored_candidates[:limit]
    
    return SuggestionResponse(
        success=True,
        job_id=job_id,
        job_title=job.title,
        suggestions_count=len(suggestions),
        suggestions=suggestions,
        criteria_used=criteria
    )


@router.post("/boolean-query", response_model=BooleanQueryResponse)
async def generate_boolean_query(request: BooleanQueryRequest, company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Generate boolean search strings for various platforms.
    
    Returns optimized boolean queries for:
    - LinkedIn Recruiter
    - Internal database
    - Pearch AI
    """
    builder = BooleanQueryBuilder()
    
    queries = builder.build_query(
        title=request.title,
        skills=request.skills,
        companies=request.companies,
        industries=request.industries,
        location=request.location,
        seniority=request.seniority,
        exclude_terms=request.exclude_terms
    )
    
    synonyms_expanded = []
    if request.expand_synonyms:
        for skill in request.skills[:5]:
            synonyms = builder.expand_synonyms(skill)
            if len(synonyms) > 1:
                synonyms_expanded.append({
                    "term": skill,
                    "synonyms": synonyms[1:]
                })
    
    return BooleanQueryResponse(
        success=True,
        queries={
            "linkedin": queries["linkedin"],
            "database": queries["database"],
            "pearch": queries["pearch"]
        },
        synonyms_expanded=synonyms_expanded
    )


@router.post("/proactive-suggest", response_model=None)
async def trigger_proactive_suggestions(
    request: ProactiveSuggestRequest,
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Trigger proactive candidate suggestions for a job.
    
    Used when:
    - A new job is created (trigger=new_job)
    - Recruiter manually requests (trigger=manual)
    - Scheduled pipeline runs (trigger=scheduled)
    """
    job_result = await db.execute(
        select(JobVacancy).where(JobVacancy.id == request.job_id, JobVacancy.company_id == company_id)
    )
    job = job_result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {request.job_id} not found")
    
    suggestions_response = await get_suggested_candidates(
        job_id=request.job_id,
        limit=10,
        min_score=70.0,
        db=db
    )
    
    tier_a_count = len([s for s in suggestions_response.suggestions if s.get("tier") == "A"])
    tier_b_count = len([s for s in suggestions_response.suggestions if s.get("tier") == "B"])
    
    return {
        "success": True,
        "job_id": request.job_id,
        "job_title": job.title,
        "trigger": request.trigger,
        "triggered_at": datetime.utcnow().isoformat(),
        "suggestions_found": suggestions_response.suggestions_count,
        "tier_a_candidates": tier_a_count,
        "tier_b_candidates": tier_b_count,
        "top_suggestions": suggestions_response.suggestions[:5],
        "message": f"Found {tier_a_count} strong matches and {tier_b_count} good matches for {job.title}"
    }


@router.get("/health", response_model=None)
async def sourcing_health_check(company_id: str = Depends(require_company_id)):
    # multi-tenancy: public endpoint (health) — no tenant data
    """Health check for sourcing endpoints."""
    return {
        "status": "healthy",
        "service": "sourcing",
        "capabilities": [
            "search_candidates",
            "match_candidates",
            "suggest_candidates",
            "boolean_query_builder",
            "proactive_suggestions"
        ],
        "timestamp": datetime.utcnow().isoformat()
    }


# Task #455/#458 blindagem: garante que rotas collection-scoped sejam
# registradas ANTES das item-scoped ({job_id}), evitando shadowing.
# Roda uma vez ao fim do modulo apos todas as rotas declaradas.
reorder_collection_before_item(router)

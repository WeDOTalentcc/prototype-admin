"""
Talent Funnel Phase 2 API (WDT-011/012/014/015)
Endpoints for score analysis, gap analysis, WRF configuration, and pre-WRF filtering.
"""
import logging

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.shared.services.es_score_drop_analyzer import es_score_drop_analyzer
from app.shared.services.pgv_gap_analyzer import pgv_gap_analyzer
from app.shared.services.pre_wrf_filter_service import pre_wrf_filter_service
from app.shared.services.wrf_dynamic_k_service import wrf_dynamic_k_service
from fastapi import Depends
from app.shared.security.require_company_id import require_company_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/talent-funnel", tags=["talent-funnel"])


class CandidateInput(BaseModel):
    id: str
    name: str | None = None
    score: float | None = None
    es_score: float | None = None
    es_rank: int | None = None
    pgv_distance: float | None = None
    pgv_rank: int | None = None
    distance: float | None = None


class ScoreDropRequest(BaseModel):
    candidates: list[CandidateInput]
    qualification_level: str | None = Field("media", pattern="^(alta|media|baixa)$")


class GapAnalysisRequest(BaseModel):
    candidates: list[CandidateInput]
    qualification_level: str | None = Field("media", pattern="^(alta|media|baixa)$")


class WRFRankRequest(BaseModel):
    candidates: list[CandidateInput]
    qualification_level: str | None = Field("media", pattern="^(alta|media|baixa)$")


class PreWRFRequest(BaseModel):
    es_candidates: list[CandidateInput]
    pgv_candidates: list[CandidateInput]
    qualification_level: str | None = Field("media", pattern="^(alta|media|baixa)$")


@router.post("/analyze-score-drop", response_model=None)
async def analyze_score_drop(body: ScoreDropRequest, company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    candidates = [c.model_dump() for c in body.candidates]
    result = es_score_drop_analyzer.analyze(candidates, body.qualification_level)
    return {
        "filtered_candidates": result["filtered_candidates"],
        "cutoff_index": result["cutoff_index"],
        "cutoff_score": result["cutoff_score"],
        "top_score": result["top_score"],
        "threshold_used": result["threshold_used"],
        "total_input": result["total_input"],
        "total_output": result["total_output"],
        "analysis": result["analysis"],
    }


@router.post("/analyze-semantic-gap", response_model=None)
async def analyze_semantic_gap(body: GapAnalysisRequest, company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    candidates = [c.model_dump() for c in body.candidates]
    result = pgv_gap_analyzer.analyze(candidates, body.qualification_level)
    return {
        "filtered_candidates": result["filtered_candidates"],
        "gap_index": result["gap_index"],
        "gap_threshold": result["gap_threshold"],
        "multiplier_used": result["multiplier_used"],
        "total_input": result["total_input"],
        "total_output": result["total_output"],
        "analysis": result["analysis"],
    }


@router.post("/wrf-rank", response_model=None)
async def wrf_rank(body: WRFRankRequest, company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    candidates = [c.model_dump() for c in body.candidates]
    ranked = wrf_dynamic_k_service.rank_candidates(candidates, body.qualification_level)
    k = wrf_dynamic_k_service.get_k(body.qualification_level)
    weights = wrf_dynamic_k_service.get_weights(body.qualification_level)
    return {
        "candidates": ranked,
        "k_used": k,
        "weights": weights,
        "total": len(ranked),
    }


@router.get("/wrf-config", response_model=None)
async def get_wrf_config(company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    return wrf_dynamic_k_service.get_config()


@router.post("/pre-wrf-filter", response_model=None)
async def pre_wrf_filter(body: PreWRFRequest, company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    es_candidates = [c.model_dump() for c in body.es_candidates]
    pgv_candidates = [c.model_dump() for c in body.pgv_candidates]
    result = pre_wrf_filter_service.orchestrate(es_candidates, pgv_candidates, body.qualification_level)
    return result

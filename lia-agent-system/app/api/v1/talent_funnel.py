"""
Talent Funnel Phase 2 API (WDT-011/012/014/015)
Endpoints for score analysis, gap analysis, WRF configuration, and pre-WRF filtering.
"""
import logging

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.shared.security.require_company_id import require_company_id
from app.shared.services.es_score_drop_analyzer import es_score_drop_analyzer
from app.shared.services.pgv_gap_analyzer import pgv_gap_analyzer
from app.shared.services.pre_wrf_filter_service import pre_wrf_filter_service
from app.shared.services.wrf_dynamic_k_service import wrf_dynamic_k_service
from app.shared.types import WeDoBaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/talent-funnel", tags=["talent-funnel"])


class CandidateInput(WeDoBaseModel):
    id: str
    name: str | None = None
    score: float | None = None
    es_score: float | None = None
    es_rank: int | None = None
    pgv_distance: float | None = None
    pgv_rank: int | None = None
    distance: float | None = None


class ScoreDropRequest(WeDoBaseModel):
    candidates: list[CandidateInput]
    qualification_level: str | None = Field('media', pattern="^(alta|media|baixa)$")


class GapAnalysisRequest(WeDoBaseModel):
    candidates: list[CandidateInput]
    qualification_level: str | None = Field("media", pattern="^(alta|media|baixa)$")


class WRFRankRequest(WeDoBaseModel):
    candidates: list[CandidateInput]
    qualification_level: str | None = Field("media", pattern="^(alta|media|baixa)$")


class PreWRFRequest(WeDoBaseModel):
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
async def wrf_rank(
    body: WRFRankRequest,
    company_id: str = Depends(require_company_id),
    db: AsyncSession = Depends(get_db),
):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    candidates = [c.model_dump() for c in body.candidates]
    ranked = wrf_dynamic_k_service.rank_candidates(candidates, body.qualification_level)
    k = wrf_dynamic_k_service.get_k(body.qualification_level)
    weights = wrf_dynamic_k_service.get_weights(body.qualification_level)

    # WT-2022 P0.C: LGPD Art. 20 + EU AI Act Art. 13 audit trail para ranking
    # automatizado de candidatos via Weighted Rank Fusion (WRF) dinamico.
    try:
        from app.shared.services.automated_decision_logger import (
            PROTECTED_CRITERIA_PT,
            log_automated_decision,
        )
        candidate_ids = [str(c.id) for c in body.candidates if c.id]
        top_summary = [
            {
                "candidate_id": item.get("id"),
                "rank": item.get("wrf_rank"),
                "score": item.get("wrf_score"),
            }
            for item in ranked[:10]
        ]
        await log_automated_decision(
            db=db,
            company_id=company_id,
            decision_type="candidate_ranking_wrf",
            ai_model_used="wrf_dynamic_k_service_deterministic",
            explanation_text=(
                f"Ranking WRF dinamico: {len(candidates)} candidatos rankeados"
                f" com qualification_level={body.qualification_level or 'media'},"
                f" K={k}, weights={weights}."
            ),
            criteria_used=[
                "es_rank",
                "pgv_rank",
                "qualification_level",
                "wrf_dynamic_k",
                "score_weights",
            ],
            criteria_ignored=PROTECTED_CRITERIA_PT,
            review_eligible=True,
            extra_metadata={
                "qualification_level": body.qualification_level,
                "k_used": k,
                "weights": weights,
                "total_ranked": len(ranked),
                "candidate_ids": candidate_ids,
                "top_10_ranked": top_summary,
            },
        )
    except Exception as exc:  # noqa: BLE001 - fail-safe, decisao IA nao pode quebrar por log
        logger.warning("WT-2022 P0.C: wrf_rank audit log failed: %s", exc, exc_info=True)

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
async def pre_wrf_filter(
    body: PreWRFRequest,
    company_id: str = Depends(require_company_id),
    db: AsyncSession = Depends(get_db),
):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    es_candidates = [c.model_dump() for c in body.es_candidates]
    pgv_candidates = [c.model_dump() for c in body.pgv_candidates]
    result = pre_wrf_filter_service.orchestrate(es_candidates, pgv_candidates, body.qualification_level)

    # WT-2022 P0.C: LGPD Art. 20 audit trail para decisão automatizada de pre-WRF filter
    try:
        from app.shared.services.automated_decision_logger import (
            PROTECTED_CRITERIA_PT,
            log_automated_decision,
        )
        input_total = len(es_candidates) + len(pgv_candidates)
        passed = result.get("filtered_candidates") if isinstance(result, dict) else None
        passed_total = len(passed) if isinstance(passed, list) else None
        await log_automated_decision(
            db=db,
            company_id=company_id,
            decision_type="cv_pre_wrf_filter",
            ai_model_used="pre_wrf_filter_deterministic",
            explanation_text=(
                f"Pre-WRF filter: {input_total} candidatos de entrada"
                + (f" → {passed_total} aprovados." if passed_total is not None else ".")
                + f" qualification_level={body.qualification_level}."
            ),
            criteria_used=["es_score", "pgv_distance", "qualification_level"],
            criteria_ignored=PROTECTED_CRITERIA_PT,
            review_eligible=True,
        )
    except Exception as _adl_exc:  # fail-safe: gap de log não bloqueia decisão
        logger.warning(
            "WT-2022 P0.C: pre_wrf_filter audit log failed (fail-safe): %s", _adl_exc,
        )

    return result

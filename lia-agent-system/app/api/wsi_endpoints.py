"""

# TODO(phase2-repo-extraction): 25 direct DB calls in this file.
# Domain: wsi | No repository exists yet.
# Action: Create app/domains/wsi/repositories/wsi_repository.py
WSI (WeDoTalent Skill Index) API Endpoints.

Provides RESTful API for WSI screening workflow:
1. Analyze JD → Suggest competencies
2. Generate questions → WSI questions
3. Analyze responses → Scores 1-5
4. Calculate WSI → Final scores
5. Generate reports → Structured output
6. Generate feedback → Candidate feedback
"""
import json
import logging
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.shared.types import WeDoBaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db, get_tenant_db
from app.domains.cv_screening.services.screening_question_set_service import (
    ScreeningQuestionSetService,
    get_screening_question_set_service,
)
from app.domains.cv_screening.services.seniority_context_calibrator import (
    WSI_CONTEXTUAL_CALIBRATION_ENABLED,
    CalibrationContext,
    calibrate_or_fallback,
)
from app.domains.cv_screening.services.seniority_utils import normalize_seniority
from app.domains.cv_screening.services.wsi_service import (
    Competency,
    ResponseAnalysis,
    WSIQuestion,
)
from app.core.config import settings
from app.domains.cv_screening.dependencies import WSIService, get_wsi_service
from app.domains.cv_screening.services.wsi_voice_orchestrator import (
    wsi_voice_orchestrator,
)
from app.domains.voice.repositories.wsi_repository import WsiRepository
from app.shared.security.require_company_id import require_company_id
from app.shared.services.automated_decision_logger import (
    PROTECTED_CRITERIA_PT,
    log_automated_decision,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/wsi", tags=["WSI"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class AnalyzeJDRequest(WeDoBaseModel):
    """Request to analyze job description and suggest competencies."""
    job_description: str = Field(..., description="Full job description text")
    seniority_level: str = Field(..., description="junior, pleno, senior, lead, executive")
    department: str | None = Field(None, description="Department (e.g., Engineering, Product)")


# DUPLICATE_OF_INTENT: app/api/v1/skills_catalog.py:147 — legacy wsi_endpoints.py wire shape (Sprint Q.4 cleanup)
class CompetencySuggestionResponse(BaseModel):
    """Suggested competencies from JD analysis."""
    technical_competencies: list[dict[str, Any]]
    behavioral_competencies: list[dict[str, Any]]
    cultural_competencies: list[dict[str, Any]]
    suggested_weights: dict[str, float]
    confidence_score: float


# Sprint E.1 #44: canonical GenerateQuestionsRequest lives in app/api/v1/wsi/_shared.py.
from app.api.v1.wsi._shared import GenerateQuestionsRequest  # noqa: F401


# DUPLICATE_OF_INTENT: app/api/v1/wsi/_shared.py:128 — legacy wsi_endpoints.py wire shape (Sprint Q.4 cleanup)
class GenerateQuestionsResponse(BaseModel):
    """Generated WSI questions."""
    session_id: str
    questions: list[dict[str, Any]]
    total_questions: int


# DUPLICATE_OF_INTENT: app/api/v1/wsi/_shared.py:169 — legacy wsi_endpoints.py wire shape (Sprint Q.4 cleanup)
class AnalyzeResponseRequest(WeDoBaseModel):
    """Request to analyze a candidate response."""
    session_id: str
    question_id: str
    candidate_id: str
    job_vacancy_id: str
    question_text: str
    response_text: str
    response_audio_url: str | None = None
    competency: str
    framework: str


class AnalyzeResponseResponse(BaseModel):
    """Analyzed response with scores."""
    analysis_id: str
    competency: str
    autodeclaration_score: float | None
    context_score: float | None
    bloom_level: int | None
    dreyfus_level: int | None
    evidences: list[str]
    red_flags: list[str]
    final_score: float
    justification: str


# DUPLICATE_OF_INTENT: app/api/v1/interview_notes.py:156 — legacy wsi_endpoints.py wire shape (Sprint Q.4 cleanup)
class CalculateWSIRequest(WeDoBaseModel):
    """Request to calculate final WSI."""
    session_id: str
    candidate_id: str
    job_vacancy_id: str
    weights: dict[str, float]


class CalculateWSIResponse(BaseModel):
    """Final WSI result."""
    result_id: str
    candidate_id: str
    job_vacancy_id: str
    technical_wsi: float
    behavioral_wsi: float
    overall_wsi: float
    classification: str
    percentile: int | None


class GenerateReportRequest(WeDoBaseModel):
    """Request to generate structured report."""
    wsi_result_id: str
    candidate_id: str


class GenerateReportResponse(BaseModel):
    """Structured report for recruiters."""
    report_id: str
    executive_summary: str
    technical_analysis: dict[str, Any]
    behavioral_analysis: dict[str, Any]
    cultural_fit: dict[str, Any]
    recommendation: dict[str, Any]


class GenerateFeedbackRequest(WeDoBaseModel):
    """Request to generate candidate feedback."""
    wsi_result_id: str
    decision: str = Field(..., description="aprovado, aguardando, nao_aprovado")


class GenerateFeedbackResponse(BaseModel):
    """Candidate feedback."""
    feedback_id: str
    decision: str
    main_message: str
    technical_strengths: list[str]
    development_opportunities: list[str]
    behavioral_strengths: list[str]
    next_steps: str


class StartVoiceScreeningRequest(WeDoBaseModel):
    """Request to start a voice screening session."""
    candidate_id: str = Field(..., description="Internal candidate ID")
    job_vacancy_id: str = Field(..., description="Job vacancy ID")
    competencies: list[dict[str, Any]] = Field(..., description="Competencies to assess")
    candidate_phone: str = Field(..., description="Phone number (+5511999999999)")
    candidate_name: str = Field(..., description="Candidate full name")
    job_title: str | None = Field(None, description="Job title for context")
    job_description: str | None = Field(None, description="Job description for context")
    mode: str = Field(default="compact", description="compact (6-8 questions) or compact_plus (8-10)")


class StartVoiceScreeningResponse(BaseModel):
    """Response from starting a voice screening."""
    session_id: str
    call_id: str
    agent_id: str
    candidate_id: str
    job_vacancy_id: str
    status: str
    questions_generated: int


class VoiceScreeningStatusResponse(BaseModel):
    """Voice screening session status."""
    session_id: str
    candidate_id: str
    job_vacancy_id: str
    screening_type: str
    mode: str
    status: str
    call_id: str | None
    agent_id: str | None
    started_at: str | None
    completed_at: str | None
    result: dict[str, Any] | None


# ============================================================================
# API ENDPOINTS
# ============================================================================

# Note: analyze_jd endpoint removed for MVP - will be implemented in Job Intake Agent


# TODO(phase2): extract to WsiRepository — WSI endpoint DB calls
def _convert_snapshot_to_wsi_questions(snapshot: list) -> list:
    converted = []
    for idx, q in enumerate(snapshot):
        text = q.get("text", q.get("question", q.get("question_text", "")))
        if not text:
            continue
        category = q.get("category", "technical")
        framework_map = {
            "eligibility": "CBI",
            "technical": "Bloom",
            "behavioral": "BigFive",
        }
        type_map = {
            "eligibility": "contextual",
            "technical": "autodeclaration",
            "behavioral": "situational",
        }
        question = WSIQuestion(
            id=q.get("id", f"qs_{idx}"),
            competency=q.get("skill_targeted", q.get("competency_validated", category)),
            framework=framework_map.get(category, "Bloom"),
            question_type=type_map.get(category, "contextual"),
            question_text=text,
            weight=float(q.get("weight", 0.75)),
            expected_signals=q.get("expected_signals", []),
            scoring_criteria=q.get("scoring_criteria", {}),
        )
        converted.append(question)
    return converted


@router.post("/generate-questions", response_model=GenerateQuestionsResponse)
async def generate_questions(
    request: GenerateQuestionsRequest,
    db: AsyncSession = Depends(get_tenant_db),
    sqs_svc: ScreeningQuestionSetService = Depends(get_screening_question_set_service),
    wsi_svc: WSIService = Depends(get_wsi_service),
    company_id: str = Depends(require_company_id),
):
    """
    Generate WSI questions for screening session.

    This is STEP 2 of WSI workflow.

    Saves questions to database with session_id.
    """
    try:
        repo = WsiRepository(db)
        active_qs = await sqs_svc.get_active_version(db, request.job_vacancy_id)

        ia_invoked = False
        if active_qs and active_qs.questions_snapshot:
            questions = _convert_snapshot_to_wsi_questions(active_qs.questions_snapshot)
            qs_version = active_qs.version
            qs_id = str(active_qs.id)
            logger.info(f"Using versioned question set v{qs_version} with {len(questions)} questions for chat screening")
        else:
            competencies_list = []
            for comp_dict in request.competencies:
                comp = Competency(**comp_dict)
                competencies_list.append(comp)

            questions = await wsi_svc.generate_screening_questions(
                competencies=competencies_list,
                mode=request.mode,
                job_description=request.job_description,
                seniority=request.seniority,
                enriched_jd=request.enriched_jd,
            )
            qs_version = None
            qs_id = None
            ia_invoked = True
            logger.info(f"No versioned question set found, generated {len(questions)} questions dynamically")

        await repo.upsert_session(
            session_id=request.session_id,
            candidate_id=request.candidate_id,
            job_vacancy_id=request.job_vacancy_id,
            screening_type="chat",
            mode=request.mode,
            status="in_progress",
            question_set_version=qs_version,
            question_set_id=qs_id,
        )

        for idx, question in enumerate(questions):
            await repo.insert_question(
                question_id=question.id,
                session_id=request.session_id,
                competency=question.competency,
                framework=question.framework,
                question_type=question.question_type,
                question_text=question.question_text,
                weight=question.weight,
                expected_signals=question.expected_signals,
                scoring_criteria=question.scoring_criteria,
                sequence_order=idx + 1,
                is_critical=getattr(question, "is_critical", False),
            )

        # WT-2022 P0.C wave 2 / LGPD Art. 20 + EU AI Act Art. 13.
        # /api/wsi/generate-questions e o STEP 2 do WSI workflow. So
        # logamos quando houve invocacao IA (snapshot ausente). Quando
        # versioned set ja existe, decisao IA original ja foi logada na
        # criacao desse snapshot.
        if ia_invoked:
            try:
                await log_automated_decision(
                    db=db,
                    company_id=company_id,
                    candidate_id=request.candidate_id,
                    job_id=request.job_vacancy_id,
                    decision_type="wsi_legacy_questions",
                    ai_model_used=getattr(settings, "LLM_PRIMARY_MODEL", "claude-sonnet-4-6"),
                    explanation_text=(
                        f'Gerou {len(questions)} pergunta(s) WSI dinamicamente para session '
                        f'{request.session_id} (job_vacancy_id={request.job_vacancy_id}, '
                        f'candidate_id={request.candidate_id}) via /api/wsi/generate-questions '
                        f'(STEP 2 workflow). Mode={request.mode}, seniority={request.seniority}. '
                        f'Versioned question set ausente — fallback dinamico ativado.'
                    ),
                    criteria_used=[
                        *[f"competency:{c.get('name', '?')}" for c in request.competencies],
                        f"seniority:{request.seniority}",
                        f"mode:{request.mode}",
                    ],
                    criteria_ignored=list(PROTECTED_CRITERIA_PT),
                    confidence_score=None,
                    review_eligible=True,
                    extra_metadata={
                        "endpoint": "/api/wsi/generate-questions",
                        "session_id": request.session_id,
                        "job_vacancy_id": request.job_vacancy_id,
                        "candidate_id": request.candidate_id,
                        "questions_count": len(questions),
                        "mode": request.mode,
                        "seniority": request.seniority,
                        "enriched_jd": bool(request.enriched_jd),
                        "fallback_dynamic": True,
                        "prompt_template_version": "wsi_F6_pipeline_v2",
                        "llm_model": getattr(settings, "LLM_PRIMARY_MODEL", "claude-sonnet-4-6"),
                        "legacy": True,
                    },
                )
            except ValueError:
                raise
            except Exception as audit_err:
                logger.error(
                    "WT-2022 P0.C wave 2: log_automated_decision falhou em /api/wsi/generate-questions "
                    "(LGPD Art. 20 audit gap, session_id=%s, company=%s): %s",
                    request.session_id, company_id, audit_err, exc_info=True,
                )

        return GenerateQuestionsResponse(
            session_id=request.session_id,
            questions=[q.dict() for q in questions],
            total_questions=len(questions)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate questions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/analyze-response", response_model=AnalyzeResponseResponse)
async def analyze_response(
    request: AnalyzeResponseRequest,
    db: AsyncSession = Depends(get_tenant_db)
):
    """
    Analyze a candidate response and assign scores.
    
    This is STEP 3 of WSI workflow (called for each question).
    
    Saves response analysis to database.
    """
    try:
        repo = WsiRepository(db)
        analysis = ResponseAnalysis(
            question_id=request.question_id,
            competency=request.competency,
            response_text=request.response_text,
            autodeclaration_score=3.5,
            context_score=3.5,
            bloom_level=3,
            dreyfus_level=3,
            evidences=["Mock evidence"],
            red_flags=[],
            final_score=3.5,
            justification="Mock analysis - will be replaced with real WSI analysis"
        )
        
        analysis_id = str(uuid.uuid4())
        await repo.insert_response_analysis(
            analysis_id=analysis_id,
            session_id=request.session_id,
            question_id=request.question_id,
            candidate_id=request.candidate_id,
            job_vacancy_id=request.job_vacancy_id,
            competency=analysis.competency,
            response_text=analysis.response_text,
            response_audio_url=request.response_audio_url,
            autodeclaration_score=analysis.autodeclaration_score,
            context_score=analysis.context_score,
            bloom_level=analysis.bloom_level,
            dreyfus_level=analysis.dreyfus_level,
            evidences=analysis.evidences,
            red_flags=analysis.red_flags,
            consistency_penalty=analysis.consistency_penalty,
            final_score=analysis.final_score,
            justification=analysis.justification,
        )
        
        
        return AnalyzeResponseResponse(
            analysis_id=analysis_id,
            competency=analysis.competency,
            autodeclaration_score=analysis.autodeclaration_score,
            context_score=analysis.context_score,
            bloom_level=analysis.bloom_level,
            dreyfus_level=analysis.dreyfus_level,
            evidences=analysis.evidences,
            red_flags=analysis.red_flags,
            final_score=analysis.final_score,
            justification=analysis.justification
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to analyze response: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/calculate-wsi", response_model=CalculateWSIResponse)
async def calculate_wsi(
    request: CalculateWSIRequest,
    db: AsyncSession = Depends(get_tenant_db),
    wsi_svc: WSIService = Depends(get_wsi_service),
):
    """
    Calculate final WSI scores.
    
    This is STEP 4 of WSI workflow (after all responses analyzed).
    
    Saves WSI result to database.
    """
    try:
        repo = WsiRepository(db)
        rows = await repo.get_response_scores_for_session(request.session_id)
        
        responses = [
            ResponseAnalysis(
                question_id="temp",
                competency=row[0],
                response_text="",
                final_score=row[1],
                autodeclaration_score=None,
                context_score=None,
                bloom_level=None,
                dreyfus_level=None,
                evidences=[],
                red_flags=[],
                justification=""
            )
            for row in rows
        ]
        
        wsi_result = wsi_svc.calculate_wsi(
            candidate_id=request.candidate_id,
            job_vacancy_id=request.job_vacancy_id,
            responses=responses,
            weights=request.weights
        )
        
        result_id = str(uuid.uuid4())
        await repo.insert_result(
            result_id=result_id,
            session_id=request.session_id,
            candidate_id=wsi_result.candidate_id,
            job_vacancy_id=wsi_result.job_vacancy_id,
            technical_wsi=wsi_result.technical_wsi,
            behavioral_wsi=wsi_result.behavioral_wsi,
            overall_wsi=wsi_result.overall_wsi,
            classification=wsi_result.classification,
            percentile=wsi_result.percentile,
        )
        await repo.complete_session(request.session_id)
        
        
        return CalculateWSIResponse(
            result_id=result_id,
            candidate_id=wsi_result.candidate_id,
            job_vacancy_id=wsi_result.job_vacancy_id,
            technical_wsi=wsi_result.technical_wsi,
            behavioral_wsi=wsi_result.behavioral_wsi,
            overall_wsi=wsi_result.overall_wsi,
            classification=wsi_result.classification,
            percentile=wsi_result.percentile
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to calculate WSI: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/sessions/{session_id}", response_model=None)
async def get_session(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get WSI session details with questions and responses."""
    try:
        repo = WsiRepository(db)
        session = await repo.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        questions = await repo.get_questions_for_session(session_id)
        responses = await repo.get_responses_for_session_summary(session_id)
        
        return {
            "session": {
                "id": session[0],
                "candidate_id": session[1],
                "job_vacancy_id": session[2],
                "screening_type": session[3],
                "mode": session[4],
                "status": session[5],
                "started_at": session[6].isoformat() if session[6] else None,
                "completed_at": session[7].isoformat() if session[7] else None
            },
            "questions": [
                {
                    "id": q[0],
                    "competency": q[1],
                    "framework": q[2],
                    "question_type": q[3],
                    "question_text": q[4],
                    "weight": float(q[5]),
                    "sequence_order": q[6]
                }
                for q in questions
            ],
            "responses": [
                {
                    "question_id": r[0],
                    "competency": r[1],
                    "final_score": float(r[2]),
                    "justification": r[3]
                }
                for r in responses
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/results/candidate/{candidate_id}", response_model=None)
async def get_candidate_results(
    candidate_id: str,
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """Get WSI results for a candidate."""
    try:
        repo = WsiRepository(db)
        results = await repo.get_results_for_candidate(candidate_id, limit=limit)
        
        return {
            "candidate_id": candidate_id,
            "total_screenings": len(results),
            "results": [
                {
                    "result_id": r[0],
                    "job_vacancy_id": r[1],
                    "overall_wsi": float(r[2]),
                    "technical_wsi": float(r[3]),
                    "behavioral_wsi": float(r[4]),
                    "classification": r[5],
                    "percentile": r[6],
                    "created_at": r[7].isoformat() if r[7] else None,
                    "screening_type": r[8]
                }
                for r in results
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get candidate results: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/results/{result_id}/details", response_model=None)
async def get_result_details(
    result_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get complete WSI result details including transcript, report, feedback, and response analyses."""
    try:
        repo = WsiRepository(db)
        row = await repo.get_result_with_session(result_id)
        if not row:
            raise HTTPException(status_code=404, detail="WSI result not found")

        session_id = str(row[1])
        candidate_id = str(row[2])
        job_vacancy_id = str(row[3])

        responses = await repo.get_responses_for_session(session_id)
        report_row = await repo.get_report_for_result(result_id)
        feedback_row = await repo.get_feedback_for_result(result_id)

        duration_minutes = None
        if row[12] and row[13]:
            duration_minutes = int((row[13] - row[12]).total_seconds() / 60)

        return {
            "result_id": str(row[0]),
            "session_id": session_id,
            "candidate_id": candidate_id,
            "job_vacancy_id": job_vacancy_id,
            "scores": {
                "technical_wsi": float(row[4]),
                "behavioral_wsi": float(row[5]),
                "overall_wsi": float(row[6]),
                "classification": row[7],
                "percentile": row[8]
            },
            "session": {
                "screening_type": row[10],
                "mode": row[11],
                "started_at": row[12].isoformat() if row[12] else None,
                "completed_at": row[13].isoformat() if row[13] else None,
                "duration_minutes": duration_minutes
            },
            "responses": [
                {
                    "competency": r[0],
                    "response_text": r[1],
                    "scores": {
                        "autodeclaration": float(r[2]) if r[2] else None,
                        "context": float(r[3]) if r[3] else None,
                        "bloom_level": r[4],
                        "dreyfus_level": r[5],
                        "final_score": float(r[9])
                    },
                    "evidences": r[6] if r[6] else [],
                    "red_flags": r[7] if r[7] else [],
                    "consistency_penalty": float(r[8]) if r[8] else 0,
                    "justification": r[10],
                    "question": {
                        "text": r[12],
                        "framework": r[13],
                        "type": r[14],
                        "weight": float(r[15]) if r[15] else 0,
                        "expected_signals": r[16] if r[16] else [],
                        "sequence": r[17]
                    }
                }
                for r in responses
            ],
            "report": {
                "executive_summary": report_row[0] if report_row else None,
                "technical_analysis": report_row[1] if report_row else {},
                "behavioral_analysis": report_row[2] if report_row else {},
                "cultural_fit": report_row[3] if report_row else {},
                "recommendation": report_row[4] if report_row else {}
            } if report_row else None,
            "feedback": {
                "decision": feedback_row[0] if feedback_row else None,
                "main_message": feedback_row[1] if feedback_row else None,
                "technical_strengths": feedback_row[2] if feedback_row else [],
                "development_opportunities": feedback_row[3] if feedback_row else [],
                "behavioral_strengths": feedback_row[4] if feedback_row else [],
                "next_steps": feedback_row[5] if feedback_row else None,
                "personalized_tip": feedback_row[6] if feedback_row else None,
                "development_plan": feedback_row[7] if feedback_row else {},
                "recommended_resources": feedback_row[8] if feedback_row else []
            } if feedback_row else None,
            "created_at": row[9].isoformat() if row[9] else None
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get result details: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/ranking/{job_vacancy_id}", response_model=None)
async def get_vacancy_ranking(
    job_vacancy_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get ranked candidates for a job vacancy based on WSI scores."""
    try:
        repo = WsiRepository(db)
        rows = await repo.get_vacancy_ranking(job_vacancy_id)

        if not rows:
            return {"job_vacancy_id": job_vacancy_id, "total_screened": 0, "ranking": []}

        total = int(rows[0][12]) if rows else 0
        avg_row = await repo.get_vacancy_averages(job_vacancy_id)

        return {
            "job_vacancy_id": job_vacancy_id,
            "total_screened": total,
            "averages": {
                "overall": float(avg_row[0]) if avg_row and avg_row[0] else 0,
                "technical": float(avg_row[1]) if avg_row and avg_row[1] else 0,
                "behavioral": float(avg_row[2]) if avg_row and avg_row[2] else 0
            },
            "ranking": [
                {
                    "rank": int(r[11]),
                    "total": total,
                    "result_id": str(r[0]),
                    "candidate_id": str(r[1]),
                    "candidate_name": r[9],
                    "candidate_title": r[10],
                    "overall_wsi": float(r[2]),
                    "technical_wsi": float(r[3]),
                    "behavioral_wsi": float(r[4]),
                    "classification": r[5],
                    "percentile": r[6],
                    "screening_type": r[8],
                    "created_at": r[7].isoformat() if r[7] else None
                }
                for r in rows
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get vacancy ranking: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/candidate/{candidate_id}/ranking/{job_vacancy_id}", response_model=None)
async def get_candidate_ranking_in_vacancy(
    candidate_id: str,
    job_vacancy_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific candidate's rank position within a job vacancy."""
    try:
        repo = WsiRepository(db)
        row = await repo.get_candidate_rank_in_vacancy(candidate_id, job_vacancy_id)

        if not row:
            return {"candidate_id": candidate_id, "job_vacancy_id": job_vacancy_id, "ranked": False}

        return {
            "candidate_id": candidate_id,
            "job_vacancy_id": job_vacancy_id,
            "ranked": True,
            "rank": int(row[0]),
            "total": int(row[1]),
            "overall_wsi": float(row[2])
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get candidate ranking: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# VOICE SCREENING ENDPOINTS
# ============================================================================

@router.post("/start-voice-screening", response_model=StartVoiceScreeningResponse)
async def start_voice_screening(
    request: StartVoiceScreeningRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Start a WSI voice screening session.
    
    This endpoint orchestrates:
    1. Generates WSI questions based on competencies
    2. Creates a WSI session with screening_type="voice"
    3. Initiates a Twilio voice call with the questions
    4. Initiates the voice call to the candidate
    5. Returns session_id and call_id for tracking
    
    Example request:
    ```json
    {
        "candidate_id": "cand_123",
        "job_vacancy_id": "job_456",
        "competencies": [
            {"name": "Python", "type": "technical", "level": "senior", "weight": 0.25},
            {"name": "Comunicação", "type": "behavioral", "weight": 0.15}
        ],
        "candidate_phone": "+5511999999999",
        "candidate_name": "João Silva",
        "job_title": "Backend Engineer Sênior",
        "mode": "compact"
    }
    ```
    """
    try:
        competencies_list = []
        for comp_dict in request.competencies:
            comp = Competency(**comp_dict)
            competencies_list.append(comp)
        
        result = await wsi_voice_orchestrator.start_voice_screening(
            candidate_id=request.candidate_id,
            job_vacancy_id=request.job_vacancy_id,
            competencies=competencies_list,
            candidate_phone=request.candidate_phone,
            candidate_name=request.candidate_name,
            job_title=request.job_title,
            job_description=request.job_description,
            mode=request.mode,
            db=db
        )
        
        return StartVoiceScreeningResponse(
            session_id=result.session_id,
            call_id=result.call_id,
            agent_id=result.agent_id,
            candidate_id=result.candidate_id,
            job_vacancy_id=result.job_vacancy_id,
            status=result.status,
            questions_generated=result.questions_generated
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start voice screening: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/voice-screening/{session_id}", response_model=VoiceScreeningStatusResponse)
async def get_voice_screening_status(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get the status of a voice screening session.
    
    Returns session details, call status, and WSI results if completed.
    """
    try:
        status = await wsi_voice_orchestrator.get_session_status(session_id, db=db)
        
        if not status:
            raise HTTPException(status_code=404, detail="Voice screening session not found")
        
        return VoiceScreeningStatusResponse(**status)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get voice screening status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/voice-screening/by-call/{call_id}", response_model=None)
async def get_voice_screening_by_call(
    call_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get voice screening session by voice call ID.
    
    Useful for correlating webhook events with WSI sessions.
    """
    try:
        status = await wsi_voice_orchestrator.get_session_by_call_id(call_id, db=db)
        
        if not status:
            raise HTTPException(status_code=404, detail="No WSI session found for this call ID")
        
        return status
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get voice screening: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# JOB CREATION WSI SCREENING QUESTIONS
# ============================================================================

class GenerateJobScreeningQuestionsRequest(WeDoBaseModel):
    """Request to generate WSI screening questions for job creation wizard."""
    job_title: str = Field(..., description="Job title")
    job_description: str | None = Field(None, description="Full job description")
    technical_skills: list[str] = Field(default=[], description="Required technical skills")
    behavioral_competencies: list[str] = Field(default=[], description="Required behavioral competencies")
    seniority_level: str = Field(default="pleno", description="junior, pleno, senior, lead")
    work_model: str | None = Field(None, description="remote, hybrid, onsite")
    location: str | None = Field(None, description="Job location")
    count: int = Field(default=7, ge=3, le=10, description="Number of questions to generate")


class ScreeningQuestionItem(BaseModel):
    """A single WSI screening question."""
    id: str
    question: str
    type: str = Field(description="open, yes-no, numeric, multiple-choice")
    required: bool = True
    options: list[str] | None = None
    expected_answer: Any | None = None
    correct_option_index: int | None = None
    competency: str | None = None
    framework: str | None = Field(None, description="CBI, Bloom, Dreyfus, BigFive, or Fit")
    category: str | None = Field(None, description="autodeclaracao_contexto, micro_case, situacional, fit, autodeclaracao")
    bloom_level: int | None = Field(None, ge=1, le=6, description="Bloom Taxonomy level: 1=Lembrar, 2=Compreender, 3=Aplicar, 4=Analisar, 5=Avaliar, 6=Criar")
    bloom_level_name: str | None = Field(None, description="Bloom level name in Portuguese")
    dreyfus_stage: int | None = Field(None, ge=1, le=5, description="Dreyfus stage: 1=Novato, 2=Iniciante Avançado, 3=Competente, 4=Proficiente, 5=Especialista")
    dreyfus_stage_name: str | None = Field(None, description="Dreyfus stage name in Portuguese")


class GenerateJobScreeningQuestionsResponse(BaseModel):
    """Generated WSI screening questions for job creation."""
    questions: list[ScreeningQuestionItem]
    total_generated: int
    methodology: str = "WSI (Work Sample Interview)"
    seniority_calibration: dict[str, Any] | None = Field(None, description="Bloom and Dreyfus calibration based on seniority")


@router.post("/generate-job-screening-questions", response_model=GenerateJobScreeningQuestionsResponse)
async def generate_job_screening_questions(request: GenerateJobScreeningQuestionsRequest):
    """
    Generate WSI-based screening questions for job creation wizard.
    
    Uses LLM to create intelligent screening questions based on:
    - Job title and description
    - Technical skills requirements
    - Behavioral competencies
    - Seniority level
    
    Questions follow WSI methodology for effective candidate screening.
    """
    from app.domains.ai.services.llm import llm_service
    
    try:
        from app.domains.cv_screening.constants.wsi_constants import (
            BLOOM_LEVEL_LABELS,
            DREYFUS_STAGE_LABELS,
        )
        from app.domains.cv_screening.constants.wsi_constants import (
            SENIORITY_TO_BLOOM as _BASE_S2B,
        )
        from app.domains.cv_screening.constants.wsi_constants import (
            SENIORITY_TO_DREYFUS as _BASE_S2D,
        )
        _BLOOM_TARGET = {"junior": 2, "pleno": 3, "senior": 4, "lead": 5, "executive": 6}
        SENIORITY_TO_BLOOM = {
            k: {"range": v, "target": _BLOOM_TARGET.get(k, v[0])} for k, v in _BASE_S2B.items()
        }
        SENIORITY_TO_DREYFUS = {
            k: {"stage": v, "name": DREYFUS_STAGE_LABELS.get(v, "Intermediário")}
            for k, v in _BASE_S2D.items()
        }
        BLOOM_NAMES = BLOOM_LEVEL_LABELS
        DREYFUS_NAMES = DREYFUS_STAGE_LABELS
        
        seniority = normalize_seniority(request.seniority_level) if request.seniority_level else "pleno"
        
        if WSI_CONTEXTUAL_CALIBRATION_ENABLED:
            try:
                _cal_ctx = CalibrationContext(
                    seniority=seniority,
                    job_title=request.job_title if hasattr(request, 'job_title') else '',
                )
                _cal_result = calibrate_or_fallback(_cal_ctx)
                bloom_info = {"range": _cal_result.bloom_levels, "target": _cal_result.bloom_levels[0] if _cal_result.bloom_levels else 3}
                dreyfus_info = {"stage": _cal_result.dreyfus_target, "name": DREYFUS_NAMES.get(_cal_result.dreyfus_target, "Competente")}
            except Exception:
                bloom_info = SENIORITY_TO_BLOOM.get(seniority, SENIORITY_TO_BLOOM["pleno"])
                dreyfus_info = SENIORITY_TO_DREYFUS.get(seniority, SENIORITY_TO_DREYFUS["pleno"])
        else:
            bloom_info = SENIORITY_TO_BLOOM.get(seniority, SENIORITY_TO_BLOOM["pleno"])
            dreyfus_info = SENIORITY_TO_DREYFUS.get(seniority, SENIORITY_TO_DREYFUS["pleno"])
        
        prompt = f"""Você é um especialista em recrutamento usando a metodologia WSI (WeDoTalent Skill Index).

A metodologia WSI integra 4 PILARES CIENTÍFICOS para avaliação completa:

1. **CBI (Competency-Based Interviewing)**: Entender comportamento passado para prever performance futura
2. **Taxonomia de Bloom**: Medir profundidade do conhecimento técnico
   - Nível 1: Lembrar (recordar fatos)
   - Nível 2: Compreender (explicar conceitos)
   - Nível 3: Aplicar (usar em situações novas)
   - Nível 4: Analisar (fazer conexões)
   - Nível 5: Avaliar (justificar decisões)
   - Nível 6: Criar (produzir algo novo)
3. **Modelo Dreyfus**: Classificar maturidade e autonomia
   - Estágio 1: Novato (segue regras rígidas)
   - Estágio 2: Iniciante Avançado (reconhece situações)
   - Estágio 3: Competente (planeja conscientemente)
   - Estágio 4: Proficiente (visão holística, adaptação fluida)
   - Estágio 5: Especialista (intuição profunda)
4. **Big Five (OCEAN)**: Avaliar aderência comportamental e fit cultural

CALIBRAÇÃO POR SENIORIDADE ({request.seniority_level}):
- Para este nível, use Bloom níveis {bloom_info['range'][0]}-{bloom_info['range'][1]} (foco em {BLOOM_NAMES[bloom_info['target']]})
- Dreyfus esperado: Estágio {dreyfus_info['stage']} ({dreyfus_info['name']})

TIPOS DE PERGUNTAS WSI:
- **Autodeclaração + Contexto**: "De 1 a 5, qual seu domínio em X? Conte sobre um projeto em que você o utilizou."
- **Micro-Case Técnico**: Situações práticas que testam conhecimento aplicado
- **Situacional/CBI**: Evidências de comportamento passado

REGRAS IMPORTANTES:
- NÃO use perguntas hipotéticas genéricas
- FOQUE em evidências comportamentais e técnicas reais
- Perguntas devem ser respondíveis via WhatsApp (concisas)
- INCLUA bloom_level (1-6) e dreyfus_stage (1-5) para cada pergunta

Gere {request.count} perguntas de triagem para:

**Cargo:** {request.job_title}
**Descrição:** {request.job_description or 'Não fornecida'}
**Skills Técnicos:** {', '.join(request.technical_skills) if request.technical_skills else 'Não especificados'}
**Competências Comportamentais:** {', '.join(request.behavioral_competencies) if request.behavioral_competencies else 'Não especificadas'}
**Senioridade:** {request.seniority_level}
**Modelo de Trabalho:** {request.work_model or 'Não especificado'}
**Localização:** {request.location or 'Não especificada'}

DISTRIBUIÇÃO RECOMENDADA (70% técnico, 30% comportamental):
- 2-3 perguntas de Autodeclaração + Contexto (técnicas)
- 1-2 Micro-Cases técnicos
- 2 perguntas Situacionais/CBI (comportamentais)
- 1 pergunta de fit/disponibilidade

Responda APENAS com JSON válido:
{{
  "questions": [
    {{
      "id": "wsi-1",
      "question": "De 1 a 5, qual seu nível de domínio em Python? Descreva brevemente um projeto desafiador em que você o utilizou.",
      "type": "open",
      "required": true,
      "expectedAnswer": "Espera-se score 4+ com exemplo concreto incluindo desafios técnicos e resultados",
      "competency": "Python",
      "framework": "Dreyfus",
      "category": "autodeclaracao_contexto",
      "bloom_level": 3,
      "dreyfus_stage": 3
    }},
    {{
      "id": "wsi-2",
      "question": "Se você precisa otimizar uma API que está demorando 5 segundos para responder, quais seriam suas 3 primeiras ações de diagnóstico?",
      "type": "open",
      "required": true,
      "expectedAnswer": "Profiling, análise de queries, verificação de cache - respostas estruturadas indicam nível Competente+",
      "competency": "Performance",
      "framework": "Bloom",
      "category": "micro_case",
      "bloom_level": 4,
      "dreyfus_stage": 3
    }},
    {{
      "id": "wsi-3",
      "question": "Conte sobre uma situação em que você discordou de uma decisão técnica do time. Como você lidou?",
      "type": "open",
      "required": true,
      "expectedAnswer": "Buscar evidências de comunicação assertiva, argumentação baseada em dados e abertura para consenso",
      "competency": "Comunicação Eficaz",
      "framework": "CBI",
      "category": "situacional",
      "bloom_level": 4,
      "dreyfus_stage": 3
    }},
    {{
      "id": "wsi-4",
      "question": "Você tem disponibilidade para trabalho híbrido (3x presencial)?",
      "type": "yes-no",
      "required": true,
      "expectedAnswer": true,
      "competency": "Disponibilidade",
      "framework": "Fit",
      "category": "fit",
      "bloom_level": 1,
      "dreyfus_stage": 1
    }},
    {{
      "id": "wsi-5",
      "question": "Qual seu nível de inglês para comunicação técnica?",
      "type": "multiple-choice",
      "required": true,
      "options": ["Básico - leio documentação com dificuldade", "Intermediário - leio e escrevo bem", "Avançado - converso fluentemente", "Fluente/Nativo"],
      "correctOptionIndex": 2,
      "competency": "Inglês",
      "framework": "Dreyfus",
      "category": "autodeclaracao",
      "bloom_level": 2,
      "dreyfus_stage": 3
    }}
  ]
}}"""

        response = await llm_service.generate(prompt)
        
        # Parse JSON response
        import re
        json_match = re.search(r'\{[\s\S]*\}', response)
        if not json_match:
            raise ValueError("No valid JSON found in LLM response")
        
        data = json.loads(json_match.group())
        
        # Valid categories and frameworks for WSI methodology
        VALID_CATEGORIES = {'autodeclaracao_contexto', 'micro_case', 'situacional', 'fit', 'autodeclaracao'}
        VALID_FRAMEWORKS = {'CBI', 'Bloom', 'Dreyfus', 'BigFive', 'Fit'}
        TECHNICAL_CATEGORIES = {'autodeclaracao_contexto', 'micro_case', 'autodeclaracao'}
        BEHAVIORAL_CATEGORIES = {'situacional', 'fit'}
        
        questions = []
        for idx, q in enumerate(data.get("questions", [])):
            # Normalize category
            raw_category = q.get("category", "").lower().replace("-", "_").replace(" ", "_")
            normalized_category = raw_category if raw_category in VALID_CATEGORIES else None
            
            # Normalize framework
            raw_framework = q.get("framework", "")
            normalized_framework = None
            for valid_fw in VALID_FRAMEWORKS:
                if valid_fw.lower() == raw_framework.lower():
                    normalized_framework = valid_fw
                    break
            
            # Infer category from framework if missing
            if not normalized_category and normalized_framework:
                if normalized_framework in ('CBI', 'BigFive'):
                    normalized_category = 'situacional'
                elif normalized_framework in ('Bloom', 'Dreyfus'):
                    normalized_category = 'autodeclaracao_contexto'
                elif normalized_framework == 'Fit':
                    normalized_category = 'fit'
            
            # Default values if still missing (ensure all questions have valid metadata)
            if not normalized_category:
                # Infer from question type or default to autodeclaracao
                q_type = q.get("type", "open")
                if q_type == "yes-no":
                    normalized_category = 'fit'
                elif q_type == "open":
                    normalized_category = 'autodeclaracao_contexto'
                else:
                    normalized_category = 'autodeclaracao'
            
            if not normalized_framework:
                # Default framework based on category
                if normalized_category in ('situacional',):
                    normalized_framework = 'CBI'
                elif normalized_category in ('fit',):
                    normalized_framework = 'Fit'
                else:
                    normalized_framework = 'Dreyfus'
            
            # Get bloom_level from LLM response or infer from seniority/category
            raw_bloom = q.get("bloom_level")
            if isinstance(raw_bloom, int) and 1 <= raw_bloom <= 6:
                bloom_level = raw_bloom
            else:
                # Infer bloom level based on category and seniority
                if normalized_category == 'fit':
                    bloom_level = 1  # Fit questions are simple recall
                elif normalized_category == 'autodeclaracao':
                    bloom_level = 2  # Self-declaration is understanding
                elif normalized_category == 'autodeclaracao_contexto':
                    bloom_level = bloom_info['target']  # Based on seniority
                elif normalized_category == 'micro_case':
                    bloom_level = min(bloom_info['target'] + 1, 6)  # Micro-cases are one level up
                elif normalized_category == 'situacional':
                    bloom_level = bloom_info['target']  # CBI at target level
                else:
                    bloom_level = bloom_info['target']
            
            bloom_level_name = BLOOM_NAMES.get(bloom_level, "Aplicar")
            
            # Get dreyfus_stage from LLM response or infer from seniority
            raw_dreyfus = q.get("dreyfus_stage")
            if isinstance(raw_dreyfus, int) and 1 <= raw_dreyfus <= 5:
                dreyfus_stage = raw_dreyfus
            else:
                # Infer dreyfus stage based on category and seniority
                if normalized_category == 'fit':
                    dreyfus_stage = 1  # Fit questions don't measure expertise
                else:
                    dreyfus_stage = dreyfus_info['stage']
            
            dreyfus_stage_name = DREYFUS_NAMES.get(dreyfus_stage, "Competente")
            
            questions.append(ScreeningQuestionItem(
                id=q.get("id", f"wsi-{idx+1}"),
                question=q["question"],
                type=q.get("type", "open"),
                required=q.get("required", True),
                options=q.get("options"),
                expected_answer=q.get("expectedAnswer"),
                correct_option_index=q.get("correctOptionIndex"),
                competency=q.get("competency"),
                framework=normalized_framework,
                category=normalized_category,
                bloom_level=bloom_level,
                bloom_level_name=bloom_level_name,
                dreyfus_stage=dreyfus_stage,
                dreyfus_stage_name=dreyfus_stage_name
            ))
        
        # Calculate actual distribution for logging
        technical_count = sum(1 for q in questions if q.category in TECHNICAL_CATEGORIES)
        behavioral_count = sum(1 for q in questions if q.category in BEHAVIORAL_CATEGORIES)
        total = len(questions)
        if total > 0:
            tech_pct = (technical_count / total) * 100
            logger.info(f"WSI Question distribution: {technical_count} technical ({tech_pct:.0f}%), {behavioral_count} behavioral ({100-tech_pct:.0f}%)")
        
        return GenerateJobScreeningQuestionsResponse(
            questions=questions,
            total_generated=len(questions),
            methodology="WSI (Work Sample Interview)",
            seniority_calibration={
                "seniority": seniority,
                "bloom_range": bloom_info['range'],
                "bloom_target": bloom_info['target'],
                "bloom_target_name": BLOOM_NAMES[bloom_info['target']],
                "dreyfus_expected": dreyfus_info['stage'],
                "dreyfus_expected_name": dreyfus_info['name']
            }
        )
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response as JSON: {e}")
        raise HTTPException(status_code=500, detail="Failed to parse AI response")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate screening questions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/results/{result_id}/trigger-feedback", response_model=None)
async def trigger_post_screening_feedback(
    result_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Trigger automated feedback to candidate after WSI screening completion."""
    try:
        from app.domains.candidates.services.candidate_feedback_service import candidate_feedback_service
        repo = WsiRepository(db)
        wsi_row = await repo.get_result_summary(result_id)
        if not wsi_row:
            raise HTTPException(status_code=404, detail="WSI result not found")

        candidate_id = str(wsi_row[0])
        job_vacancy_id = str(wsi_row[1])
        overall_wsi = float(wsi_row[2]) if wsi_row[2] is not None else 0.0
        classification = wsi_row[3] or "não_classificado"
        score_percent = round((overall_wsi / 5) * 100, 1)

        if classification in ("alto", "excelente"):
            return {
                "result_id": result_id,
                "candidate_id": candidate_id,
                "classification": classification,
                "score_percent": score_percent,
                "feedback_triggered": False,
                "feedback_result": None,
                "reason": "Score above threshold"
            }

        development_areas: list[str] = []
        try:
            report_row = await repo.get_report_content(result_id)
            if report_row and report_row[0]:
                content = report_row[0] if isinstance(report_row[0], dict) else json.loads(report_row[0])
                development_areas = content.get("development_areas", [])
                if not development_areas:
                    tech = content.get("technical_analysis", {})
                    development_areas = tech.get("gaps", [])
        except Exception as e:
            logger.warning(f"Could not extract development areas from report: {e}")

        candidate_name = None
        candidate_email = None
        candidate_phone = None
        try:
            cand_row = await repo.get_candidate_contact(candidate_id)
            if cand_row:
                candidate_name = cand_row[0]
                candidate_email = cand_row[1]
                candidate_phone = cand_row[2]
        except Exception as e:
            logger.warning(f"Could not fetch candidate info: {e}")

        vacancy_title = None
        company_name = None
        try:
            vac_row = await repo.get_vacancy_title(job_vacancy_id)
            if vac_row:
                vacancy_title = vac_row[0]
                company_name = vac_row[1]
        except Exception as e:
            logger.warning(f"Could not fetch vacancy info: {e}")

        feedback_result = await candidate_feedback_service.check_and_send_feedback(
            candidate_id=candidate_id,
            vacancy_id=job_vacancy_id,
            adherence_score=score_percent,
            candidate_email=candidate_email,
            candidate_phone=candidate_phone,
            candidate_name=candidate_name,
            vacancy_title=vacancy_title,
            company_name=company_name or "Nossa Empresa",
            missing_skills=development_areas if development_areas else None,
        )

        return {
            "result_id": result_id,
            "candidate_id": candidate_id,
            "classification": classification,
            "score_percent": score_percent,
            "feedback_triggered": feedback_result.get("feedback_sent", False),
            "feedback_result": feedback_result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to trigger post-screening feedback: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/results/{result_id}/feedback-status", response_model=None)
async def get_feedback_status(
    result_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Check feedback status for a WSI result."""
    try:
        repo = WsiRepository(db)
        wsi_row = await repo.get_result_candidate_vacancy(result_id)
        if not wsi_row:
            raise HTTPException(status_code=404, detail="WSI result not found")

        candidate_id = str(wsi_row[0])
        job_vacancy_id = str(wsi_row[1])

        feedback_content = None
        try:
            fb_row = await repo.get_wsi_feedback_detail(result_id)
            if fb_row:
                feedback_content = {
                    "feedback_id": str(fb_row[0]),
                    "decision": fb_row[1],
                    "main_message": fb_row[2],
                    "technical_strengths": fb_row[3],
                    "development_opportunities": fb_row[4],
                    "behavioral_strengths": fb_row[5],
                    "next_steps": fb_row[6],
                    "personalized_tip": fb_row[7],
                }
        except Exception as e:
            logger.warning(f"Could not fetch wsi_feedbacks: {e}")

        from sqlalchemy import and_, select

        from app.models.candidate_feedback import CandidateFeedback
        # TODO(phase2-repo-extraction): CandidateFeedback is a Rails-owned model;
        # this query should move to a CandidateFeedbackRepository or Rails adapter.
        sent_result = await db.execute(
            select(CandidateFeedback).where(
                and_(
                    CandidateFeedback.candidate_id == candidate_id,
                    CandidateFeedback.vacancy_id == job_vacancy_id,
                )
            ).order_by(CandidateFeedback.created_at.desc()).limit(1)
        )
        sent_feedback = sent_result.scalar_one_or_none()

        feedback_sent = sent_feedback is not None
        channels_used = sent_feedback.channels_sent if sent_feedback and sent_feedback.channels_sent else []
        channels_failed = sent_feedback.channels_failed if sent_feedback and sent_feedback.channels_failed else []
        sent_at = sent_feedback.sent_at.isoformat() if sent_feedback and sent_feedback.sent_at else None

        return {
            "result_id": result_id,
            "candidate_id": candidate_id,
            "job_vacancy_id": job_vacancy_id,
            "feedback_sent": feedback_sent,
            "channels_used": channels_used,
            "channels_failed": channels_failed,
            "sent_at": sent_at,
            "wsi_feedback": feedback_content
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get feedback status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/candidates/{job_vacancy_id}/scores", response_model=None)
async def get_candidates_wsi_scores(
    job_vacancy_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Returns WSI scores for all candidates in a vacancy, converted to 0-100 scale."""
    try:
        repo = WsiRepository(db)
        rows = await repo.get_latest_scores_per_candidate(job_vacancy_id)

        candidates: dict[str, Any] = {}
        for row in rows:
            candidate_id = str(row[0])
            overall_raw = float(row[1]) if row[1] is not None else 0.0
            technical_raw = float(row[2]) if row[2] is not None else 0.0
            behavioral_raw = float(row[3]) if row[3] is not None else 0.0
            classification = row[4] or "não_classificado"
            percentile = row[5]

            candidates[candidate_id] = {
                "overall_wsi": round(overall_raw * 20, 1),
                "technical_wsi": round(technical_raw * 20, 1),
                "behavioral_wsi": round(behavioral_raw * 20, 1),
                "classification": classification,
                "percentile": percentile
            }

        return {"candidates": candidates}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get candidates WSI scores: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

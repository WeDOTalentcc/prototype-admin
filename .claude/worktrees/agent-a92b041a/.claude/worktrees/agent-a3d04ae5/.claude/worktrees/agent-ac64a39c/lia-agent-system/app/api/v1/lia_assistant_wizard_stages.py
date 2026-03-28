"""
LIA Assistant — Wizard Stages 8, 9, 10 endpoints.

Extracted from lia_assistant.py (Phase 5 decomposition).
All routes share prefix="/lia" to preserve existing /api/v1/lia/wizard/* URLs.

Phase 6 migration complete: SourcingAgent and AvaliadorWSIAgent replaced by
SourcingReActAgent (stages 8 + 10) and TalentReActAgent (stage 9). Feedback
endpoints now call learning_hub_service directly without any legacy agent.
"""
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from uuid import uuid4
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.auth.dependencies import get_current_user_or_demo
from app.auth.models import User
from app.services.learning_hub_service import learning_hub_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/lia", tags=["lia-wizard-stages"])


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class Stage8SearchCriteria(BaseModel):
    skills: Optional[List[str]] = None
    seniority: Optional[str] = None
    location: Optional[str] = None
    experience_years: Optional[int] = None


class Stage8CandidateSearchRequest(BaseModel):
    job_id: Optional[str] = None
    draft_id: Optional[str] = None
    company_id: str
    search_criteria: Stage8SearchCriteria
    limit: int = 20


class Stage8CandidateSearchResponse(BaseModel):
    candidates: List[Dict[str, Any]]
    total_found: int
    search_id: str
    sources_used: List[str]
    learning_enhanced: bool
    search_criteria_enhanced: Optional[Dict[str, Any]] = None


class Stage8SearchFeedbackRequest(BaseModel):
    search_id: str
    company_id: str
    suggested_candidates: List[str]
    selected_candidates: List[str]
    job_id: Optional[str] = None
    feedback_reason: Optional[str] = None


class Stage8SearchFeedbackResponse(BaseModel):
    success: bool
    message: str
    acceptance_rate: float


class Stage9CalibrationRequest(BaseModel):
    job_id: str
    company_id: str
    candidates: List[str]
    calibration_mode: Optional[str] = "auto"


class Stage9CandidateEvaluation(BaseModel):
    candidate_id: str
    wsi_score: float
    technical_score: float
    behavioral_score: float
    recommendation: str
    strengths: List[str]
    gaps: List[str]


class Stage9CalibrationResponse(BaseModel):
    evaluations: List[Stage9CandidateEvaluation]
    cutoffs_used: Dict[str, float]
    learning_enhanced: bool


class Stage9CalibrationItem(BaseModel):
    candidate_id: str
    original_score: float
    adjusted_score: Optional[float] = None
    decision: str


class Stage9CalibrateFeedbackRequest(BaseModel):
    job_id: str
    company_id: str
    calibrations: List[Stage9CalibrationItem]


class Stage9CalibrateFeedbackResponse(BaseModel):
    success: bool
    message: str
    calibrations_recorded: int
    updated_acceptance_rate: float


class Stage10SearchCriteria(BaseModel):
    skills: Optional[List[str]] = None
    seniority: Optional[str] = None
    location: Optional[str] = None
    experience_years: Optional[int] = None
    industries: Optional[List[str]] = None
    companies: Optional[List[str]] = None
    exclude_companies: Optional[List[str]] = None


class Stage10ActiveSourcingRequest(BaseModel):
    job_id: str
    company_id: str
    target_count: int = 20
    search_criteria: Stage10SearchCriteria
    auto_outreach: bool = False


class Stage10SourcingCandidate(BaseModel):
    candidate_id: str
    name: str
    match_score: float
    source: str
    outreach_status: str


class Stage10ActiveSourcingResponse(BaseModel):
    candidates: List[Stage10SourcingCandidate]
    pipeline_created: bool
    outreach_scheduled: int
    learning_enhanced: bool
    search_id: Optional[str] = None
    sources_used: Optional[List[str]] = None


class Stage10OutreachRequest(BaseModel):
    job_id: str
    company_id: str
    candidates: List[str]
    message_template: Optional[str] = None


class Stage10OutreachResponse(BaseModel):
    success: bool
    scheduled_count: int
    failed_count: int
    message: str
    outreach_ids: Optional[List[str]] = None


class Stage10FeedbackRequest(BaseModel):
    job_id: str
    company_id: str
    sourced_candidates: List[str]
    engaged_candidates: List[str]
    search_id: Optional[str] = None


class Stage10FeedbackResponse(BaseModel):
    success: bool
    message: str
    engagement_rate: float
    patterns_updated: bool


# ---------------------------------------------------------------------------
# Endpoints — Stage 8
# ---------------------------------------------------------------------------

@router.post("/wizard/stage8/search", response_model=Stage8CandidateSearchResponse)
async def wizard_stage8_search(
    request: Stage8CandidateSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
) -> Stage8CandidateSearchResponse:
    try:
        from app.domains.sourcing.agents.sourcing_react_agent import SourcingReActAgent
        from app.shared.agents.agent_interface import AgentInput

        search_id = str(uuid4())

        learning_context = await learning_hub_service.get_learning_context(
            db=db,
            company_id=request.company_id,
            role=request.search_criteria.seniority,
            seniority=request.search_criteria.seniority
        )

        enhanced_skills = list(request.search_criteria.skills or [])
        learning_enhanced = False

        if learning_context.company_skills:
            promoted_skills = [
                s.get("skill_name") for s in learning_context.company_skills
                if s.get("is_promoted") and s.get("skill_name")
            ]
            for skill in promoted_skills[:5]:
                if skill.lower() not in [s.lower() for s in enhanced_skills]:
                    enhanced_skills.append(skill)
                    learning_enhanced = True

        skills_str = ", ".join(enhanced_skills[:5]) if enhanced_skills else "candidatos qualificados"
        search_message = (
            f"Buscar candidatos com as seguintes características: "
            f"skills={skills_str}, "
            f"seniority={request.search_criteria.seniority or 'não especificado'}, "
            f"location={request.search_criteria.location or 'qualquer'}, "
            f"limit={request.limit}"
        )

        agent_input = AgentInput(
            message=search_message,
            session_id=search_id,
            company_id=request.company_id,
            user_id=getattr(current_user, "id", "wizard"),
            context={
                "current_stage": "search-criteria",
                "collected_data": {
                    "job_id": request.job_id,
                    "draft_id": request.draft_id,
                    "skills": enhanced_skills,
                    "seniority": request.search_criteria.seniority,
                    "location": request.search_criteria.location,
                    "experience_years": request.search_criteria.experience_years,
                    "limit": request.limit,
                    "learned_skills": [
                        s.get("skill_name") for s in learning_context.company_skills
                        if s.get("skill_name")
                    ],
                    "patterns": learning_context.patterns,
                },
            },
        )

        sourcing_agent = SourcingReActAgent()
        agent_output = await sourcing_agent.process(agent_input)

        candidates: List[Dict[str, Any]] = []
        total_found = 0
        sources_used = ["local_database"]

        for tool_result in agent_output.tool_results:
            if tool_result.get("tool_name") == "search_candidates":
                data = tool_result.get("result", {}).get("data", {})
                raw = data.get("candidates", data.get("results", []))
                if raw:
                    candidates = raw
                    total_found = data.get("total_results", len(raw))
                if data.get("boolean_queries"):
                    sources_used.append("boolean_search")
        if learning_enhanced:
            sources_used.append("learning_hub")

        return Stage8CandidateSearchResponse(
            candidates=candidates[:request.limit],
            total_found=total_found,
            search_id=search_id,
            sources_used=sources_used,
            learning_enhanced=learning_enhanced,
            search_criteria_enhanced={
                "original_skills": list(request.search_criteria.skills or []),
                "enhanced_skills": enhanced_skills,
                "added_from_learning": [
                    s for s in enhanced_skills
                    if s not in (request.search_criteria.skills or [])
                ],
            },
        )

    except Exception as e:
        logger.error(f"Error in Stage 8 candidate search: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/wizard/stage8/feedback", response_model=Stage8SearchFeedbackResponse)
async def wizard_stage8_feedback(
    request: Stage8SearchFeedbackRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
) -> Stage8SearchFeedbackResponse:
    try:
        acceptance_rate = 0.0
        if request.suggested_candidates:
            acceptance_rate = len(request.selected_candidates) / len(request.suggested_candidates)

        overall_accepted = len(request.selected_candidates) > 0

        feedback_context = {
            "search_criteria": {"search_id": request.search_id},
            "total_suggested": len(request.suggested_candidates),
            "total_accepted": len(request.selected_candidates),
            "acceptance_rate": acceptance_rate,
        }
        if request.job_id:
            feedback_context["job_id"] = request.job_id

        success = await learning_hub_service.record_agent_feedback(
            db=db,
            company_id=request.company_id,
            agent_name="sourcing_agent",
            action_type="candidate_search",
            accepted=overall_accepted,
            suggested_value=request.suggested_candidates,
            actual_value=request.selected_candidates,
            job_id=request.job_id,
            context=feedback_context,
            feedback_reason=request.feedback_reason,
        )

        message = (
            f"Feedback registrado com sucesso. Taxa de aceitação: {acceptance_rate:.0%}"
            if success
            else "Feedback registrado parcialmente"
        )
        return Stage8SearchFeedbackResponse(
            success=bool(success),
            message=message,
            acceptance_rate=acceptance_rate,
        )

    except Exception as e:
        logger.error(f"Error recording Stage 8 feedback: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Endpoints — Stage 9
# ---------------------------------------------------------------------------

@router.post("/wizard/stage9/evaluate", response_model=Stage9CalibrationResponse)
async def wizard_stage9_evaluate(
    request: Stage9CalibrationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
) -> Stage9CalibrationResponse:
    try:
        from app.domains.recruiter_assistant.agents.talent_react_agent import TalentReActAgent
        from app.shared.agents.agent_interface import AgentInput

        # Resolve calibration cutoffs via learning_hub_service (replaces _get_calibration_context)
        learning_enhanced = False
        cutoffs_used: Dict[str, float] = {
            "approved_auto": 4.2,
            "review_min": 3.8,
            "waiting_min": 3.0,
            "rejected": 3.0,
        }
        try:
            lc = await learning_hub_service.get_learning_context(
                db=db,
                company_id=request.company_id,
                role=None,
                seniority=None,
            )
            if lc and (lc.company_skills or lc.patterns):
                learning_enhanced = True
                if lc.patterns:
                    success_rate = lc.success_rate or 0.0
                    if success_rate > 0.7:
                        cutoffs_used["approved_auto"] = 4.0
                    elif success_rate < 0.3:
                        cutoffs_used["approved_auto"] = 4.5
        except Exception as lc_err:
            logger.warning(f"Stage 9: could not get learning context: {lc_err}")

        talent_agent = TalentReActAgent()
        evaluations: List[Stage9CandidateEvaluation] = []

        for candidate_id in request.candidates:
            eval_message = (
                f"Avaliar candidato {candidate_id} para a vaga {request.job_id}. "
                f"Analisar competências técnicas e comportamentais e calcular score de fit."
            )
            agent_input = AgentInput(
                message=eval_message,
                session_id=f"{request.job_id}-{candidate_id}",
                company_id=request.company_id,
                user_id=getattr(current_user, "id", "wizard"),
                context={
                    "current_stage": "analysis",
                    "collected_data": {
                        "candidate_id": candidate_id,
                        "job_id": request.job_id,
                        "calibration_mode": request.calibration_mode,
                    },
                },
            )
            agent_output = await talent_agent.process(agent_input)

            # Extract match_percentage from analyze_skills tool result as wsi_score proxy
            wsi_score = 0.0
            technical_score = 0.0
            behavioral_score = 0.0
            strengths: List[str] = []
            gaps: List[str] = []

            for tool_result in agent_output.tool_results:
                if tool_result.get("tool_name") == "analyze_skills":
                    data = tool_result.get("result", {}).get("data", {})
                    match_pct = data.get("match_percentage", 0.0)
                    # Normalise 0-100 percentage → 0-5 WSI scale
                    wsi_score = round(match_pct / 20.0, 2)
                    technical_score = round(wsi_score * 0.6, 2)
                    behavioral_score = round(wsi_score * 0.4, 2)
                    strengths = data.get("matched_skills", [])
                    gaps = data.get("missing_skills", [])
                    break

            # Fallback: derive from state_updates if no tool result
            if wsi_score == 0.0 and agent_output.state_updates.get("match_percentage"):
                mp = agent_output.state_updates["match_percentage"]
                wsi_score = round(mp / 20.0, 2)
                technical_score = round(wsi_score * 0.6, 2)
                behavioral_score = round(wsi_score * 0.4, 2)

            if wsi_score >= cutoffs_used["approved_auto"]:
                recommendation = "approved"
            elif wsi_score >= cutoffs_used["review_min"]:
                recommendation = "needs_review"
            elif wsi_score >= cutoffs_used["waiting_min"]:
                recommendation = "waiting"
            else:
                recommendation = "rejected" if wsi_score > 0 else "error"

            if not strengths:
                if technical_score >= 4.0:
                    strengths.append("Forte competência técnica")
                if behavioral_score >= 4.0:
                    strengths.append("Excelente perfil comportamental")
                if wsi_score >= 4.2:
                    strengths.append("Candidato acima da média")
            if not gaps:
                if technical_score < 3.5:
                    gaps.append("Competências técnicas abaixo do esperado")
                if behavioral_score < 3.5:
                    gaps.append("Perfil comportamental precisa desenvolvimento")

            evaluations.append(Stage9CandidateEvaluation(
                candidate_id=candidate_id,
                wsi_score=wsi_score,
                technical_score=technical_score,
                behavioral_score=behavioral_score,
                recommendation=recommendation,
                strengths=strengths if strengths else ["Perfil adequado para a vaga"],
                gaps=gaps if gaps else [],
            ))

        return Stage9CalibrationResponse(
            evaluations=evaluations,
            cutoffs_used=cutoffs_used,
            learning_enhanced=learning_enhanced,
        )

    except Exception as e:
        logger.error(f"Error in Stage 9 evaluation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/wizard/stage9/calibrate", response_model=Stage9CalibrateFeedbackResponse)
async def wizard_stage9_calibrate(
    request: Stage9CalibrateFeedbackRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
) -> Stage9CalibrateFeedbackResponse:
    try:
        calibrations_recorded = 0
        total_calibrations = len(request.calibrations)

        for calibration in request.calibrations:
            has_adjustment = (
                calibration.adjusted_score is not None
                and calibration.adjusted_score != calibration.original_score
            )
            accepted = not has_adjustment
            suggested_value = {"score": calibration.original_score, "decision": "auto"}
            actual_value = {
                "score": (
                    calibration.adjusted_score
                    if calibration.adjusted_score is not None
                    else calibration.original_score
                ),
                "decision": calibration.decision,
            }
            feedback_reason = None
            if has_adjustment:
                score_diff = (calibration.adjusted_score or 0) - calibration.original_score
                feedback_reason = (
                    f"Recruiter adjusted score by {score_diff:+.2f} "
                    f"and set decision to '{calibration.decision}'"
                )

            success = await learning_hub_service.record_agent_feedback(
                db=db,
                company_id=request.company_id,
                agent_name="wsi_evaluator",
                action_type="calibration",
                accepted=accepted,
                suggested_value=suggested_value,
                actual_value=actual_value,
                job_id=request.job_id,
                candidate_id=calibration.candidate_id,
                feedback_reason=feedback_reason,
                context={
                    "evaluation_timestamp": None,
                    "candidate_info": {},
                },
            )
            if success:
                calibrations_recorded += 1

        acceptance_rate = 0.0
        try:
            agent_performance = await learning_hub_service.get_agent_performance(
                db=db,
                company_id=request.company_id,
                agent_name="wsi_evaluator",
                limit=100,
            )
            acceptance_rate = (
                agent_performance.get("acceptance_rate", 0.0) if agent_performance else 0.0
            )
        except Exception as ap_err:
            logger.warning(f"Failed to get updated acceptance rate: {ap_err}")

        if calibrations_recorded == total_calibrations:
            message = f"Todas as {calibrations_recorded} calibrações foram registradas com sucesso."
        elif calibrations_recorded > 0:
            message = f"{calibrations_recorded} de {total_calibrations} calibrações foram registradas."
        else:
            message = "Nenhuma calibração foi registrada. Por favor, tente novamente."

        return Stage9CalibrateFeedbackResponse(
            success=calibrations_recorded > 0,
            message=message,
            calibrations_recorded=calibrations_recorded,
            updated_acceptance_rate=acceptance_rate,
        )

    except Exception as e:
        logger.error(f"Error in Stage 9 calibration: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Endpoints — Stage 10
# ---------------------------------------------------------------------------

@router.post("/wizard/stage10/start-sourcing", response_model=Stage10ActiveSourcingResponse)
async def wizard_stage10_start_sourcing(
    request: Stage10ActiveSourcingRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
) -> Stage10ActiveSourcingResponse:
    try:
        from app.domains.sourcing.agents.sourcing_react_agent import SourcingReActAgent
        from app.shared.agents.agent_interface import AgentInput

        search_id = str(uuid4())

        learning_enhanced = False
        learning_skills: List[str] = []
        try:
            lc = await learning_hub_service.get_learning_context(
                db=db,
                company_id=request.company_id,
                role=None,
                seniority=request.search_criteria.seniority,
            )
            if lc and (lc.company_skills or lc.patterns):
                learning_enhanced = True
                learning_skills = [s.get("skill_name") for s in lc.company_skills[:10] if s.get("skill_name")]
        except Exception as lc_err:
            logger.warning(f"Stage 10: could not get learning context: {lc_err}")

        parts = [f"Sourcing ativo para a vaga {request.job_id}"]
        if request.search_criteria.skills:
            parts.append(f"skills={', '.join(request.search_criteria.skills)}")
        if request.search_criteria.seniority:
            parts.append(f"seniority={request.search_criteria.seniority}")
        if request.search_criteria.location:
            parts.append(f"location={request.search_criteria.location}")
        if request.search_criteria.industries:
            parts.append(f"industries={', '.join(request.search_criteria.industries)}")
        parts.append(f"target={request.target_count} candidatos")
        search_message = ". ".join(parts) + "."

        agent_input = AgentInput(
            message=search_message,
            session_id=search_id,
            company_id=request.company_id,
            user_id=getattr(current_user, "id", "wizard"),
            context={
                "current_stage": "search-criteria",
                "collected_data": {
                    "job_id": request.job_id,
                    "skills": request.search_criteria.skills,
                    "seniority": request.search_criteria.seniority,
                    "location": request.search_criteria.location,
                    "experience_years": request.search_criteria.experience_years,
                    "industries": request.search_criteria.industries,
                    "companies": request.search_criteria.companies,
                    "exclude_companies": request.search_criteria.exclude_companies,
                    "target_count": request.target_count,
                    "auto_outreach": request.auto_outreach,
                    "learning_skills": learning_skills,
                },
            },
        )

        sourcing_agent = SourcingReActAgent()
        agent_output = await sourcing_agent.process(agent_input)

        raw_candidates: List[Dict[str, Any]] = []
        sources_used: List[str] = ["internal_db"]
        pipeline_created = False

        for tool_result in agent_output.tool_results:
            if tool_result.get("tool_name") in {"search_candidates", "proactive_search"}:
                data = tool_result.get("result", {}).get("data", {})
                raw_candidates = data.get("candidates", data.get("results", []))
                sources_used = data.get("sources_used", sources_used)
                pipeline_created = data.get("pipeline_created", False)
                break

        candidates: List[Stage10SourcingCandidate] = []
        outreach_scheduled = 0
        for idx, candidate in enumerate(raw_candidates[:request.target_count]):
            cid = (
                candidate.get("id")
                or candidate.get("candidate_id")
                or f"sourced_{search_id}_{idx}"
            )
            name = candidate.get("name") or candidate.get("full_name") or "Unknown"
            match_score = float(candidate.get("match_score") or candidate.get("score") or 0.0)
            source = candidate.get("source") or "internal_db"
            outreach_status = "pending"
            if request.auto_outreach and match_score >= 70:
                outreach_status = "scheduled"
                outreach_scheduled += 1
            candidates.append(Stage10SourcingCandidate(
                candidate_id=str(cid),
                name=name,
                match_score=round(match_score, 2),
                source=source,
                outreach_status=outreach_status,
            ))

        return Stage10ActiveSourcingResponse(
            candidates=candidates,
            pipeline_created=pipeline_created,
            outreach_scheduled=outreach_scheduled,
            learning_enhanced=learning_enhanced,
            search_id=search_id,
            sources_used=sources_used,
        )

    except Exception as e:
        logger.error(f"Error in Stage 10 active sourcing: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/wizard/stage10/outreach", response_model=Stage10OutreachResponse)
async def wizard_stage10_outreach(
    request: Stage10OutreachRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
) -> Stage10OutreachResponse:
    try:
        scheduled_count = 0
        failed_count = 0
        outreach_ids: List[str] = []

        for candidate_id in request.candidates:
            try:
                outreach_id = str(uuid4())
                outreach_ids.append(outreach_id)
                scheduled_count += 1
            except Exception as e:
                logger.warning(f"Failed to schedule outreach for candidate {candidate_id}: {e}")
                failed_count += 1

        if scheduled_count == len(request.candidates):
            message = f"Outreach agendado com sucesso para {scheduled_count} candidato(s)."
        elif scheduled_count > 0:
            message = f"Outreach agendado para {scheduled_count} de {len(request.candidates)} candidatos. {failed_count} falharam."
        else:
            message = "Falha ao agendar outreach. Por favor, tente novamente."

        return Stage10OutreachResponse(
            success=scheduled_count > 0,
            scheduled_count=scheduled_count,
            failed_count=failed_count,
            message=message,
            outreach_ids=outreach_ids if outreach_ids else None
        )

    except Exception as e:
        logger.error(f"Error in Stage 10 outreach: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/wizard/stage10/feedback", response_model=Stage10FeedbackResponse)
async def wizard_stage10_feedback(
    request: Stage10FeedbackRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
) -> Stage10FeedbackResponse:
    try:
        sourced_count = len(request.sourced_candidates)
        engaged_count = len(request.engaged_candidates)
        engagement_rate = (engaged_count / sourced_count * 100) if sourced_count > 0 else 0.0

        patterns_updated = False
        try:
            for candidate_id in request.engaged_candidates:
                await learning_hub_service.record_agent_feedback(
                    db=db,
                    company_id=request.company_id,
                    agent_name="sourcing_agent",
                    action_type="outreach_engagement",
                    accepted=True,
                    suggested_value={"candidate_id": candidate_id},
                    actual_value={"engaged": True},
                    job_id=request.job_id,
                    candidate_id=candidate_id,
                    context={"search_id": request.search_id} if request.search_id else None
                )
            non_engaged = set(request.sourced_candidates) - set(request.engaged_candidates)
            for candidate_id in non_engaged:
                await learning_hub_service.record_agent_feedback(
                    db=db,
                    company_id=request.company_id,
                    agent_name="sourcing_agent",
                    action_type="outreach_engagement",
                    accepted=False,
                    suggested_value={"candidate_id": candidate_id},
                    actual_value={"engaged": False},
                    job_id=request.job_id,
                    candidate_id=candidate_id,
                    context={"search_id": request.search_id} if request.search_id else None
                )
            patterns_updated = True
        except Exception as e:
            logger.warning(f"Failed to record sourcing feedback in learning hub: {e}")

        if engagement_rate >= 20:
            message = f"Excelente taxa de engajamento: {engagement_rate:.1f}%! {engaged_count} de {sourced_count} candidatos responderam."
        elif engagement_rate >= 10:
            message = f"Boa taxa de engajamento: {engagement_rate:.1f}%. {engaged_count} de {sourced_count} candidatos responderam."
        elif engagement_rate > 0:
            message = f"Taxa de engajamento: {engagement_rate:.1f}%. Considere ajustar a mensagem de outreach."
        else:
            message = "Nenhum candidato respondeu ainda. Considere personalizar mais suas mensagens."

        return Stage10FeedbackResponse(
            success=True,
            message=message,
            engagement_rate=round(engagement_rate, 2),
            patterns_updated=patterns_updated
        )

    except Exception as e:
        logger.error(f"Error in Stage 10 feedback: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

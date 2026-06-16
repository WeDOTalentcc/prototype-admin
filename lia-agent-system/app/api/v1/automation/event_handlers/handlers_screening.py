"""
Screening event handlers.

Routes:
- POST /handle-trigger/screening-completed
"""
import uuid
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.analytics.services.activity_service import ActivityService, get_activity_service as get_activity_service_canonical
from app.shared.compliance.audit_service import AuditService, get_audit_service

from .._shared import (
    WSI_PASS_THRESHOLD,
    ScreeningCompletedRequest,
    ScreeningCompletedResponse,
    CommunicationService,
    get_communication_service,
    get_wsi_service,
    validate_multi_tenancy,
)
from app.shared.security.require_company_id import require_company_id

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Shared helper (used by screening only but also called from interview module)
# ---------------------------------------------------------------------------

async def _fetch_candidate_and_vacancy(db, candidate_id: str, vacancy_id: str):
    """Fetch candidate and vacancy from DB, raise 404 if not found.

    ADR-001 Repository Pattern: delegates to CandidateRepository +
    JobVacancyCRUDRepository instead of inline SQL. Endpoint helper
    (not a service) but kept canonical for consistency.
    """
    from app.domains.candidates.repositories.candidate_repository import (
        CandidateRepository,
    )
    from app.domains.job_management.repositories.job_vacancy_crud_repository import (
        JobVacancyCRUDRepository,
    )

    candidate_repo = CandidateRepository(db)
    try:
        candidate = await candidate_repo.get_by_id_str(candidate_id)
    except (ValueError, TypeError):
        candidate = None
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidato não encontrado")

    vacancy_repo = JobVacancyCRUDRepository(db)
    vacancy = await vacancy_repo.get_vacancy_by_id(vacancy_id)
    if not vacancy:
        raise HTTPException(status_code=404, detail="Vaga não encontrada")

    return candidate, vacancy


# ---------------------------------------------------------------------------
# Private helpers – screening
# ---------------------------------------------------------------------------

def _build_screening_response_analyses(responses: list) -> list:
    """Build ResponseAnalysis objects from structured response list."""
    from app.domains.cv_screening.services.wsi_service import ResponseAnalysis
    result = []
    for resp in responses:
        result.append(ResponseAnalysis(
            question_id=resp.get("question_id", str(uuid.uuid4())),
            competency=resp.get("competency", "general"),
            response_text=resp.get("response", ""),
            evidences=resp.get("evidences", []),
            red_flags=resp.get("red_flags", []),
            final_score=resp.get("score", 3.0),
            justification=resp.get("justification", "Análise automática")
        ))
    return result


def _normalize_weights(weights: dict, response_analyses: list) -> dict:
    """Compute and normalize competency weights.

    Returns an empty dict when response_analyses is empty (no division-by-zero).
    """
    if not response_analyses:
        return {}
    if not weights:
        equal_weight = 1.0 / len(response_analyses)
        weights = {a.competency: equal_weight for a in response_analyses}
    total = sum(weights.values())
    if total > 0:
        weights = {k: v / total for k, v in weights.items()}
    return weights


def _determine_screening_decision(overall_wsi: float):
    """Determine screening decision and next stage from WSI score."""
    passed = overall_wsi >= WSI_PASS_THRESHOLD
    recommendation = "passed" if passed else "failed"
    if overall_wsi >= WSI_PASS_THRESHOLD:
        decision, suggested_next_stage = "aprovado", "Entrevista Técnica"
    elif overall_wsi >= 3.0:
        decision, suggested_next_stage = "aguardando", "Entrevista Técnica"
    else:
        decision, suggested_next_stage = "nao_aprovado", None
    return passed, recommendation, decision, suggested_next_stage


async def _send_screening_communication(
    comm_svc, db, request, passed: bool, overall_wsi: float,
    candidate, vacancy, candidate_feedback
) -> bool:
    """Send screening result communication to candidate. Returns True if sent."""
    candidate_email = getattr(candidate, 'email', None)
    candidate_name = getattr(candidate, 'name', 'Candidato')
    candidate_phone = getattr(candidate, 'phone', None)
    company_name = getattr(vacancy, 'company_name', None) or request.company_id
    all_strengths = (
        candidate_feedback.technical_strengths + candidate_feedback.behavioral_strengths
    )
    try:
        comm_result = await comm_svc.send_screening_result(
            db=db, candidate_id=request.candidate_id, vacancy_id=request.vacancy_id,
            company_id=request.company_id, passed=passed, wsi_score=overall_wsi,
            strengths=all_strengths, development_areas=candidate_feedback.development_opportunities,
            candidate_name=candidate_name, candidate_email=candidate_email,
            candidate_phone=candidate_phone, job_title=vacancy.title, company_name=company_name
        )
        return comm_result.get("success", False)
    except Exception as e:
        logger.error(f"❌ [SCREENING_COMPLETED] Failed to send communication: {e}")
        return False


async def _create_screening_recruiter_notification(
    activity_svc, request, overall_wsi: float, wsi_result,
    recommendation: str, passed: bool, suggested_next_stage, candidate_name: str, vacancy
) -> bool:
    """Create recruiter notification for screening completion. Returns True if created."""
    try:
        await activity_svc.create_activity(
            activity_type="screening_wsi_completed",
            title=f"Triagem WSI Concluída - {candidate_name}",
            description=(
                f"Candidato {candidate_name} completou triagem por {request.screening_type}. "
                f"WSI: {overall_wsi:.2f}/5.0 ({wsi_result.classification}). "
                f"Recomendação: {recommendation.upper()}"
            ),
            actor_id="system", actor_name="LIA Automation", actor_type="system",
            target_id=request.candidate_id, target_type="candidate",
            extra_data={
                "vacancy_id": request.vacancy_id, "vacancy_title": vacancy.title,
                "company_id": request.company_id, "screening_type": request.screening_type,
                "wsi_score": overall_wsi, "wsi_classification": wsi_result.classification,
                "recommendation": recommendation, "passed": passed,
                "suggested_next_stage": suggested_next_stage
            },
            category="screening"
        )
        return True
    except Exception as e:
        logger.error(f"❌ [SCREENING_COMPLETED] Failed to create notification: {e}")
        return False


def _add_screening_execution_log(db, request, overall_wsi: float, wsi_result, recommendation: str, passed: bool) -> None:
    """Persist AutomationExecutionLog for screening WSI calculation."""
    try:
        from app.models.automation import AutomationExecutionLog
        execution_time = int((request.metadata or {}).get("duration_seconds", 0) * 1000)
        db.add(AutomationExecutionLog(
            company_id=request.company_id, trigger_event="screening_completed",
            trigger_data={
                "candidate_id": request.candidate_id, "vacancy_id": request.vacancy_id,
                "screening_type": request.screening_type, "has_transcript": bool(request.transcript),
                "responses_count": len(request.responses) if request.responses else 0
            },
            candidate_id=request.candidate_id, vacancy_id=request.vacancy_id,
            action_executed="wsi_calculation",
            action_result={
                "wsi_score": overall_wsi, "technical_wsi": wsi_result.technical_wsi,
                "behavioral_wsi": wsi_result.behavioral_wsi,
                "classification": wsi_result.classification,
                "recommendation": recommendation, "passed": passed
            },
            status="success", execution_time_ms=execution_time
        ))
    except Exception as e:
        logger.error(f"❌ [SCREENING_COMPLETED] Failed to create execution log: {e}")


async def _record_screening_decision(audit_svc, request, overall_wsi: float, wsi_result, recommendation: str, passed: bool, suggested_next_stage, weights: dict) -> None:
    """Call audit_svc.log_decision for screening WSI evaluation."""
    try:
        wsi_dimensions = list(weights.keys()) if weights else ["technical", "behavioral"]
        reasoning_list = [
            f"WSI Score: {overall_wsi:.2f}/5.0 ({wsi_result.classification})",
            f"Technical WSI: {wsi_result.technical_wsi:.2f}",
            f"Behavioral WSI: {wsi_result.behavioral_wsi:.2f}",
            f"Threshold: {WSI_PASS_THRESHOLD}",
            f"Screening Type: {request.screening_type}",
            f"Candidate passed screening - recommended for: {suggested_next_stage}" if passed else "Candidate did not meet minimum WSI threshold",
        ]
        await audit_svc.log_decision(
            company_id=request.company_id, agent_name="wsi_evaluator",
            decision_type="screening_evaluation", action="evaluate_screening",
            decision=recommendation, score=overall_wsi, confidence=0.85,
            reasoning=reasoning_list, criteria_used=wsi_dimensions,
            candidate_id=request.candidate_id, job_vacancy_id=request.vacancy_id,
            human_review_required=not passed
        )
    except Exception as e:
        logger.error(f"❌ [SCREENING_COMPLETED] Failed to create audit log: {e}")


async def _log_screening_audit(db, audit_svc, request, overall_wsi: float, wsi_result, recommendation: str, passed: bool, suggested_next_stage, weights: dict) -> None:
    """Log automation execution log and centralized audit for screening."""
    _add_screening_execution_log(db, request, overall_wsi, wsi_result, recommendation, passed)
    await _record_screening_decision(audit_svc, request, overall_wsi, wsi_result, recommendation, passed, suggested_next_stage, weights)

    # WT-2022 P0.C: LGPD Art. 20 + EU AI Act Art. 13 — log automated decision per
    # candidato. AITransparencyPanel le esta tabela e expoe ao recrutador/DPO/
    # candidato pra direito de revisao de decisao automatizada. fail-safe (returns
    # None se DB error) — log nunca bloqueia a decisao IA.
    try:
        from app.shared.services.automated_decision_logger import (
            log_automated_decision,
            PROTECTED_CRITERIA_PT,
        )
        await log_automated_decision(
            db=db,
            company_id=str(request.company_id),
            candidate_id=str(request.candidate_id),
            job_id=str(request.vacancy_id),
            decision_type="wsi_screening_score",
            ai_model_used="claude-opus-4-7",
            explanation_text=(
                f"WSI={overall_wsi:.2f} (classification={wsi_result.classification}); "
                f"technical_wsi={wsi_result.technical_wsi:.2f}, "
                f"behavioral_wsi={wsi_result.behavioral_wsi:.2f}; "
                f"recommendation={recommendation}; passed={passed}"
            ),
            criteria_used=["competencies_weighted_score", "technical_match", "behavioral_indicators", "evidence_concreteness"],
            criteria_ignored=PROTECTED_CRITERIA_PT,
            confidence_score=0.85,
            review_eligible=True,
            extra_metadata={"weights": weights, "suggested_next_stage": suggested_next_stage},
        )
    except ValueError:
        # ADR-LGPD-001 violation: protected criteria leaked — re-raise (fail-loud)
        raise
    except Exception as _adl_exc:
        logger.warning("[handlers_screening] log_automated_decision failed (fail-safe): %s", _adl_exc)


def _validate_screening_request(request) -> None:
    """Raise HTTPException if screening request payload is invalid."""
    if not request.candidate_id or not request.vacancy_id:
        raise HTTPException(status_code=400, detail="candidate_id e vacancy_id são obrigatórios")
    if not request.transcript and not request.responses:
        raise HTTPException(
            status_code=400,
            detail="É necessário fornecer 'transcript' ou 'responses' para calcular o WSI"
        )


def _build_wsi_prompt(transcript: str, vacancy_title: str) -> str:
    """Build the LLM prompt for WSI transcript analysis."""
    return f"""Analise esta transcrição de triagem e extraia as respostas do candidato para avaliação WSI.

Vaga: {vacancy_title}

Transcrição:
{transcript[:8000]}

Extraia cada pergunta/resposta relevante e avalie:
1. Competência avaliada
2. Qualidade da resposta (1-5)
3. Evidências concretas mencionadas
4. Red flags identificados
5. Justificativa da nota

Responda em JSON:
{{
  "responses": [
    {{
      "question_id": "q1",
      "competency": "Nome da competência",
      "response_text": "Resumo da resposta",
      "score": 4.0,
      "evidences": ["Evidência 1", "Evidência 2"],
      "red_flags": [],
      "justification": "Candidato demonstrou X com exemplo concreto Y"
    }}
  ]
}}"""


def _parse_wsi_llm_response(content: str, transcript: str, ResponseAnalysis) -> list:
    """Parse LLM JSON output into ResponseAnalysis objects; falls back on error."""
    import json
    try:
        if "```json" in content:
            start = content.find("```json") + 7
            content = content[content.find("```json") + 7:content.find("```", start)].strip()
        elif "```" in content:
            start = content.find("```") + 3
            content = content[start:content.find("```", start)].strip()
        return [
            ResponseAnalysis(
                question_id=r.get("question_id", str(uuid.uuid4())),
                competency=r.get("competency", "general"),
                response_text=r.get("response_text", ""),
                evidences=r.get("evidences", []),
                red_flags=r.get("red_flags", []),
                final_score=float(r.get("score", 3.0)),
                justification=r.get("justification", "Análise automática"),
            )
            for r in json.loads(content).get("responses", [])
        ]
    except Exception:
        return [ResponseAnalysis(
            question_id=str(uuid.uuid4()), competency="general",
            response_text=transcript[:500] if transcript else "",
            evidences=[], red_flags=["Falha na análise automática"],
            final_score=3.0, justification="Análise automática não completada - score padrão aplicado",
        )]


async def _analyze_transcript_for_wsi(transcript: str, vacancy_title: str, wsi_service) -> list:
    """Analyze a conversation transcript and extract structured ResponseAnalysis objects via LLM."""
    from app.domains.cv_screening.services.wsi_service import ResponseAnalysis
    from app.domains.ai.services.llm import llm_service
    try:
        content = await llm_service.safe_invoke(_build_wsi_prompt(transcript, vacancy_title), provider="claude")
        return _parse_wsi_llm_response(content, transcript, ResponseAnalysis)
    except Exception as e:
        logger.error(f"Failed to analyze transcript: {e}")
        return [ResponseAnalysis(
            question_id=str(uuid.uuid4()), competency="general",
            response_text=transcript[:500] if transcript else "",
            evidences=[], red_flags=["Falha na análise automática"],
            final_score=3.0, justification="Análise automática não completada - score padrão aplicado",
        )]


async def _calculate_wsi(request, vacancy, wsi_service) -> tuple:
    """Calculate WSI score and classification. Returns (wsi_result, response_analyses, weights)."""
    if request.responses:
        response_analyses = _build_screening_response_analyses(request.responses)
    else:
        response_analyses = await _analyze_transcript_for_wsi(
            transcript=request.transcript, vacancy_title=vacancy.title, wsi_service=wsi_service
        )
    weights = _normalize_weights(request.competency_weights or {}, response_analyses)
    wsi_result = wsi_service.calculate_wsi(
        candidate_id=request.candidate_id, job_vacancy_id=request.vacancy_id,
        responses=response_analyses, weights=weights
    )
    return wsi_result, response_analyses, weights


def _build_screening_response(request, wsi_result, response_analyses, overall_wsi: float, recommendation: str, passed: bool, communication_sent: bool, notification_created: bool, suggested_next_stage: str, candidate_feedback) -> dict:
    """Build the final response dict for screening_completed trigger."""
    return {
        "success": True,
        "trigger": "screening_completed",
        "wsi_score": round(overall_wsi, 2),
        "wsi_details": {
            "technical_wsi": round(wsi_result.technical_wsi, 2),
            "behavioral_wsi": round(wsi_result.behavioral_wsi, 2),
            "classification": wsi_result.classification,
            "percentile": wsi_result.percentile
        },
        "recommendation": recommendation,
        "passed": passed,
        "communication_sent": communication_sent,
        "notification_created": notification_created,
        "suggested_next_stage": suggested_next_stage,
        "confidence": 0.85,
        "candidate_feedback": {
            "decision": candidate_feedback.decision,
            "main_message": candidate_feedback.main_message,
            "technical_strengths": candidate_feedback.technical_strengths,
            "development_opportunities": candidate_feedback.development_opportunities,
            "next_steps": candidate_feedback.next_steps
        },
        "metadata": {
            "screening_type": request.screening_type,
            "responses_analyzed": len(response_analyses),
            "processed_at": datetime.utcnow().isoformat()
        }
    }


async def _score_and_decide(request, vacancy, wsi_service):
    """Run WSI calculation and decide outcome. Returns (wsi_result, analyses, weights, overall_wsi, passed, recommendation, decision, suggested_next_stage)."""
    wsi_result, response_analyses, weights = await _calculate_wsi(request, vacancy, wsi_service)
    overall_wsi = wsi_result.overall_wsi
    passed, recommendation, decision, suggested_next_stage = _determine_screening_decision(overall_wsi)
    logger.info(
        f"📊 [SCREENING_COMPLETED] WSI={overall_wsi:.2f}, "
        f"classification={wsi_result.classification}, recommendation={recommendation}"
    )
    return wsi_result, response_analyses, weights, overall_wsi, passed, recommendation, decision, suggested_next_stage


async def _persist_lia_opinion_with_ocean(
    *,
    db,
    request,
    wsi_result,
    overall_wsi: float,
    recommendation: str,
    candidate_feedback,
) -> None:
    """Phase 2.5 / P1-LiaRepo + P1-Clobber: upsert LiaOpinion(opinion_type='wsi')
    with OCEAN snapshot. Delegates to OpinionsRepository.upsert_ocean_opinion()
    which encapsulates:
    - ADR-001 compliance (no inline select in this handler)
    - P1-Clobber guard (full_interview source never downgraded to text_screening)

    Fail-soft: any DB error is logged and swallowed — screening dispatch
    must never break over a learning-loop write.
    """
    try:
        from app.repositories.opinions_repository import (
from app.shared.errors import LIAError
            OpinionsRepository,
        )

        ocean_traits = dict(getattr(wsi_result, "ocean_traits", {}) or {})
        summary = getattr(candidate_feedback, "main_message", None) or None

        repo = OpinionsRepository(db)
        opinion = await repo.upsert_ocean_opinion(
            candidate_id=request.candidate_id,
            vacancy_id=request.vacancy_id,
            company_id=str(request.company_id),
            ocean_traits=ocean_traits,
            overall_wsi=float(overall_wsi),
            recommendation=recommendation,
            summary=summary,
        )

        # Extend behavioral_analysis with per-trait WSI breakdown
        # (additional context beyond ocean_traits, preserved in blob)
        ba = dict(opinion.behavioral_analysis or {})
        ba["wsi_classification"] = wsi_result.classification
        ba["wsi_technical"] = wsi_result.technical_wsi
        ba["wsi_behavioral"] = wsi_result.behavioral_wsi
        ba["recommendation"] = recommendation
        opinion.behavioral_analysis = ba

        try:
            await db.commit()
        except Exception:
            await db.rollback()
            raise
        logger.info(
            "[SCREENING_COMPLETED] LiaOpinion upserted with ocean_traits=%s",
            sorted(ocean_traits.keys()),
        )
    except Exception as exc:
        logger.warning(
            "[SCREENING_COMPLETED] LiaOpinion persist failed (fail-soft): %s",
            str(exc)[:200],
        )


async def _process_screening_completed(request, db, audit_svc, activity_svc, comm_svc) -> dict:
    """Orchestrate screening_completed trigger: validate, score, notify, audit, respond."""
    logger.info(
        f"🎯 [SCREENING_COMPLETED] Processing: candidate={request.candidate_id}, "
        f"vacancy={request.vacancy_id}, type={request.screening_type}"
    )

    is_valid, error_message = await validate_multi_tenancy(
        db=db, candidate_id=request.candidate_id,
        vacancy_id=request.vacancy_id, company_id=request.company_id
    )
    if not is_valid:
        raise HTTPException(status_code=403, detail=error_message)

    _validate_screening_request(request)

    candidate, vacancy = await _fetch_candidate_and_vacancy(db, request.candidate_id, request.vacancy_id)
    wsi_service = get_wsi_service()
    wsi_result, response_analyses, weights, overall_wsi, passed, recommendation, decision, suggested_next_stage = \
        await _score_and_decide(request, vacancy, wsi_service)

    candidate_feedback = await wsi_service.generate_candidate_feedback(
        wsi_result=wsi_result, responses=response_analyses, decision=decision
    )
    communication_sent = await _send_screening_communication(
        comm_svc, db, request, passed, overall_wsi, candidate, vacancy, candidate_feedback
    )
    notification_created = await _create_screening_recruiter_notification(
        activity_svc, request, overall_wsi, wsi_result,
        recommendation, passed, suggested_next_stage, getattr(candidate, 'name', 'Candidato'), vacancy
    )
    await _log_screening_audit(
        db, audit_svc, request, overall_wsi, wsi_result, recommendation, passed, suggested_next_stage, weights
    )

    # Phase 2.5: persist LiaOpinion with behavioral_analysis['ocean_traits']
    # so _hook_conclusion_hired can later read the snapshot and call
    # BigFiveDepartmentService.record_hire (closes ADR-LGPD-001 data
    # source). Fail-soft: a missing opinion never breaks screening.
    await _persist_lia_opinion_with_ocean(
        db=db, request=request, wsi_result=wsi_result, overall_wsi=overall_wsi,
        recommendation=recommendation, candidate_feedback=candidate_feedback,
    )

    logger.info(f"✅ [SCREENING_COMPLETED] Done: wsi={overall_wsi:.2f}, recommendation={recommendation}")

    return _build_screening_response(
        request, wsi_result, response_analyses, overall_wsi, recommendation,
        passed, communication_sent, notification_created, suggested_next_stage, candidate_feedback
    )


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------

@router.post("/handle-trigger/screening-completed", response_model=ScreeningCompletedResponse)
async def handle_screening_completed(
    request: ScreeningCompletedRequest,
    db: AsyncSession = Depends(get_db),
    audit_svc: AuditService = Depends(get_audit_service),
    activity_svc: ActivityService = Depends(get_activity_service_canonical),
    comm_svc: CommunicationService = Depends(get_communication_service),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Handle screening_completed trigger: WSI calculation and candidate notification."""
    try:
        return await _process_screening_completed(request, db, audit_svc, activity_svc, comm_svc)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [SCREENING_COMPLETED] Error: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")

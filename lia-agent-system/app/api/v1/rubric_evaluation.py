"""
Rubric Evaluation API - Structured rubrics for CV vs Job evaluation.

Based on Schmidt & Hunter (1998) meta-analysis and BARS methodology.
"""
from datetime import datetime
from enum import Enum as PyEnum
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db, get_tenant_db
from app.domains.cv_screening.repositories.screening_repository import ScreeningRepository
from app.domains.cv_screening.services.rubric_evaluation_service import RubricEvaluationService, get_rubric_evaluation_service
from app.models.rubric import JobRequirement, RubricEvaluation
from app.schemas.rubric import (
    BatchEvaluateRequest,
    BatchEvaluateResponse,
    EvaluateCandidateRequest,
    JobRequirementCreate,
    JobRequirementResponse,
    RequirementPriorityEnum,
    RubricEvaluationResponse,
    RubricEvaluationResult,
)
from app.shared.services.consent_checker_service import ConsentCheckerService
from app.shared.compliance.audit_service import AuditService, get_audit_service
from app.shared.compliance.fairness_guard import FairnessGuard
from app.shared.pii_masking import get_masked_logger
from app.shared.security.require_company_id import require_company_id

logger = get_masked_logger(__name__)
fairness_guard = FairnessGuard()


def _normalize_priority(priority_value) -> RequirementPriorityEnum:
    """Normalize priority value to RequirementPriorityEnum, handling ORM enums and strings."""
    if priority_value is None:
        return RequirementPriorityEnum.IMPORTANT
    if isinstance(priority_value, RequirementPriorityEnum):
        return priority_value
    if isinstance(priority_value, PyEnum):
        priority_value = priority_value.value
    if isinstance(priority_value, str):
        try:
            return RequirementPriorityEnum(priority_value.lower())
        except ValueError:
            return RequirementPriorityEnum.IMPORTANT
    return RequirementPriorityEnum.IMPORTANT


async def get_screening_repo(db: AsyncSession = Depends(get_db)) -> ScreeningRepository:
    return ScreeningRepository(db)


router = APIRouter()


@router.post("/evaluate", response_model=RubricEvaluationResponse)
async def evaluate_candidate(
    request: EvaluateCandidateRequest,
    db: AsyncSession = Depends(get_tenant_db),
    audit_svc: AuditService = Depends(get_audit_service),
    rubric_svc: RubricEvaluationService = Depends(get_rubric_evaluation_service),
    repo: ScreeningRepository = Depends(get_screening_repo),
    company_id: str = Depends(require_company_id),
):
    # multi-tenancy: company_id vem do JWT via require_company_id (canonical)
    """
    Evaluate a single candidate against job requirements using structured rubrics.

    This endpoint uses the BARS (Behaviorally Anchored Rating Scale) methodology
    with Claude AI for semantic analysis of CV content.

    The evaluation:
    - Rates each requirement as EXCEEDS (100), MEETS (75), PARTIAL (40), or MISSING (0)
    - Applies priority multipliers: ESSENTIAL (3x), IMPORTANT (2x), NICE_TO_HAVE (1x)
    - Calculates final score using: Score = Σ(Points × Multiplier) / Σ(100 × Multiplier) × 100
    - Provides specific evidence from the CV for each evaluation
    """
    # LGPD: verificar consentimento antes de avaliação por IA
    consent_warnings: list = []
    candidate_id_for_consent = request.candidate_id
    if candidate_id_for_consent:
        consent_svc = ConsentCheckerService(db)
        consent_result = await consent_svc.check_candidate_consent(
            candidate_id=str(candidate_id_for_consent),
            company_id=company_id,
            purpose="ai_scoring",
        )
        if not consent_result.allowed:
            raise HTTPException(
                status_code=451,
                detail={
                    "error": "Consentimento LGPD revogado",
                    "message": "O candidato revogou o consentimento para avaliação por IA.",
                    "candidate_id": str(candidate_id_for_consent),
                    "consent_type": consent_result.consent_type,
                }
            )
        if consent_result.soft_warning:
            consent_warnings.append(
                f"LGPD: consentimento para 'ai_scoring' não encontrado para candidato "
                f"{candidate_id_for_consent} — avaliação realizada sob soft enforcement."
            )

    candidate_data = request.candidate_data
    if not candidate_data:
        candidate = await repo.get_candidate_by_id(request.candidate_id)
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")

        candidate_data = {
            "id": str(candidate.id),
            "name": candidate.name,
            "email": candidate.email,
            "current_title": candidate.current_title,
            "current_company": candidate.current_company,
            "years_of_experience": candidate.years_of_experience,
            "seniority_level": candidate.seniority_level,
            "technical_skills": candidate.technical_skills or [],
            "soft_skills": candidate.soft_skills or [],
            "certifications": candidate.certifications or [],
            "languages": candidate.languages or {},
            "location_city": candidate.location_city,
            "location_state": candidate.location_state,
            "location_country": candidate.location_country,
            "is_remote": candidate.is_remote,
            "work_history": candidate.work_history or [],
            "education": candidate.education or [],
            "resume_text": candidate.resume_text,
            "self_introduction": candidate.self_introduction,
        }

    requirements = request.job_requirements
    if not requirements:
        db_requirements = await repo.get_requirements_by_vacancy(request.job_vacancy_id)
        if not db_requirements:
            raise HTTPException(
                status_code=404,
                detail="No requirements found for this job vacancy. Add requirements first."
            )

        requirements = [
            JobRequirementCreate(
                requirement=req.requirement,
                description=req.description,
                priority=_normalize_priority(req.priority),
                category=req.category,
            )
            for req in db_requirements
        ]

    evaluation_result = await rubric_svc.evaluate_candidate(
        candidate_data=candidate_data,
        requirements=requirements,
    )

    # LGPD: propagar consent_warnings ao result (soft enforcement)
    if consent_warnings:
        evaluation_result = evaluation_result.model_copy(
            update={"consent_warnings": consent_warnings}
        )

    # B3: FairnessGuard — verificar reasoning gerado pelo LLM antes de persistir e retornar
    guard_result = fairness_guard.check(evaluation_result.reasoning)
    if guard_result.is_blocked:
        logger.warning(
            "FairnessGuard bloqueou reasoning de avaliação: candidate=%s category=%s terms=%s",
            request.candidate_id, guard_result.category, guard_result.blocked_terms,
        )
        evaluation_result = evaluation_result.model_copy(
            update={"reasoning": "[Avaliação sob revisão — conteúdo sinalizado pelo FairnessGuard para análise de possível viés discriminatório.]"}
        )

    db_evaluation = None
    if request.save_result:
        new_evaluation = RubricEvaluation(
            candidate_id=request.candidate_id,
            job_vacancy_id=request.job_vacancy_id,
            score=evaluation_result.score,
            evaluations=[e.model_dump() for e in evaluation_result.evaluations],
            strengths=evaluation_result.strengths,
            concerns=evaluation_result.concerns,
            reasoning=evaluation_result.reasoning,
            evaluated_by="system",
            model_version="claude-sonnet-4-6",
        )
        db_evaluation = await repo.create_evaluation(new_evaluation)

    try:
        _evals = evaluation_result.evaluations or []
        dimension_summary = [f"{e.requirement}: {e.score}/5" for e in _evals[:5]]
        _n_dimensions = len(_evals)
        await audit_svc.log_decision(
            company_id=company_id,
            agent_name="rubric_evaluation",
            decision_type="score_candidate",
            action="evaluate_candidate",
            decision="scored",
            reasoning=[
                "Rubric evaluation completed via BARS methodology",
                f"Overall score: {evaluation_result.score}/5",
                f"Dimensions evaluated: {_n_dimensions}",
                "Model: claude-sonnet-4-6",
                f"Fairness guard: {'blocked' if (guard_result and guard_result.is_blocked) else 'passed'}",
            ] + dimension_summary[:3],
            criteria_used=[r.requirement for r in (requirements or [])[:10]],
            candidate_id=str(request.candidate_id) if request.candidate_id else None,
            job_vacancy_id=str(request.job_vacancy_id) if request.job_vacancy_id else None,
            score=evaluation_result.score,
            confidence=0.85,
            human_review_required=guard_result.is_blocked if guard_result else False,
        )
    except Exception as audit_err:
        logger.warning(f"Audit log failed for rubric_evaluation: {audit_err}")

    return RubricEvaluationResponse(
        id=db_evaluation.id if db_evaluation else None,
        candidate_id=request.candidate_id,
        job_vacancy_id=request.job_vacancy_id,
        result=evaluation_result,
        evaluated_at=db_evaluation.evaluated_at if db_evaluation else datetime.utcnow(),
        model_version="claude-sonnet-4-6",
    )


@router.post("/batch-evaluate", response_model=BatchEvaluateResponse)
async def batch_evaluate_candidates(
    request: BatchEvaluateRequest,
    db: AsyncSession = Depends(get_tenant_db),
    rubric_svc: RubricEvaluationService = Depends(get_rubric_evaluation_service),
    repo: ScreeningRepository = Depends(get_screening_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Evaluate multiple candidates against the same job requirements.

    This is useful for ranking candidates for a specific job vacancy.
    Results are sorted by score in descending order.
    """
    requirements = request.job_requirements
    if not requirements:
        db_requirements = await repo.get_requirements_by_vacancy(request.job_vacancy_id)
        if not db_requirements:
            raise HTTPException(
                status_code=404,
                detail="No requirements found for this job vacancy"
            )

        requirements = [
            JobRequirementCreate(
                requirement=req.requirement,
                description=req.description,
                priority=_normalize_priority(req.priority),
                category=req.category,
            )
            for req in db_requirements
        ]

    candidates = await repo.get_candidates_by_ids(request.candidate_ids)
    candidate_map = {str(c.id): c for c in candidates}

    candidates_data = []
    errors = []

    for cid in request.candidate_ids:
        candidate = candidate_map.get(str(cid))
        if candidate:
            candidates_data.append({
                "id": str(candidate.id),
                "name": candidate.name,
                "email": candidate.email,
                "current_title": candidate.current_title,
                "current_company": candidate.current_company,
                "years_of_experience": candidate.years_of_experience,
                "seniority_level": candidate.seniority_level,
                "technical_skills": candidate.technical_skills or [],
                "soft_skills": candidate.soft_skills or [],
                "certifications": candidate.certifications or [],
                "languages": candidate.languages or {},
                "location_city": candidate.location_city,
                "location_state": candidate.location_state,
                "location_country": candidate.location_country,
                "is_remote": candidate.is_remote,
                "work_history": candidate.work_history or [],
                "education": candidate.education or [],
                "resume_text": candidate.resume_text,
                "self_introduction": candidate.self_introduction,
            })
        else:
            errors.append({"candidate_id": str(cid), "error": "Candidate not found"})

    batch_results = await rubric_svc.batch_evaluate(
        candidates=candidates_data,
        requirements=requirements,
        sort_by_score=True,
    )

    responses = []
    for candidate_data, eval_result in batch_results:
        candidate_id = UUID(candidate_data["id"])

        # B3: FairnessGuard — verificar reasoning de cada candidato antes de persistir e retornar
        guard_result = fairness_guard.check(eval_result.reasoning)
        if guard_result.is_blocked:
            logger.warning(
                "FairnessGuard bloqueou reasoning em batch: candidate=%s category=%s terms=%s",
                candidate_id, guard_result.category, guard_result.blocked_terms,
            )
            eval_result = eval_result.model_copy(
                update={"reasoning": "[Avaliação sob revisão — conteúdo sinalizado pelo FairnessGuard para análise de possível viés discriminatório.]"}
            )

        db_evaluation = None
        if request.save_results:
            new_eval = RubricEvaluation(
                candidate_id=candidate_id,
                job_vacancy_id=request.job_vacancy_id,
                score=eval_result.score,
                evaluations=[e.model_dump() for e in eval_result.evaluations],
                strengths=eval_result.strengths,
                concerns=eval_result.concerns,
                reasoning=eval_result.reasoning,
                evaluated_by="system",
                model_version="claude-sonnet-4-6",
            )
            await repo.add_evaluation(new_eval)
            db_evaluation = new_eval

        responses.append(RubricEvaluationResponse(
            id=db_evaluation.id if db_evaluation else None,
            candidate_id=candidate_id,
            job_vacancy_id=request.job_vacancy_id,
            result=eval_result,
            evaluated_at=datetime.utcnow(),
            model_version="claude-sonnet-4-6",
        ))

    if request.save_results:
        await repo.flush()

    return BatchEvaluateResponse(
        job_vacancy_id=request.job_vacancy_id,
        total_candidates=len(request.candidate_ids),
        evaluated=len(responses),
        failed=len(errors),
        results=responses,
        errors=errors,
    )


@router.get("/{job_id}/requirements", response_model=list[JobRequirementResponse])
async def get_job_requirements(
    job_id: UUID,
    repo: ScreeningRepository = Depends(get_screening_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Get all requirements for a specific job vacancy.
    """
    job = await repo.get_job_vacancy_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job vacancy not found")

    requirements = await repo.get_requirements_by_vacancy(job_id)
    return requirements


@router.post("/{job_id}/requirements", response_model=JobRequirementResponse)
async def add_job_requirement(
    job_id: UUID,
    requirement: JobRequirementCreate,
    repo: ScreeningRepository = Depends(get_screening_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Add a requirement to a job vacancy for rubric evaluation.
    """
    job = await repo.get_job_vacancy_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job vacancy not found")

    db_requirement = JobRequirement(
        job_vacancy_id=job_id,
        requirement=requirement.requirement,
        description=requirement.description,
        priority=requirement.priority.value,
        category=requirement.category,
    )
    return await repo.create_requirement(db_requirement)


@router.delete("/{job_id}/requirements/{requirement_id}", response_model=None)
async def delete_job_requirement(
    job_id: UUID,
    requirement_id: UUID,
    repo: ScreeningRepository = Depends(get_screening_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Delete a requirement from a job vacancy.
    """
    requirement = await repo.get_requirement_by_id(requirement_id, job_id)
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")

    await repo.delete_requirement(requirement)
    return {"message": "Requirement deleted successfully"}


@router.get("/{job_id}/evaluations", response_model=list[RubricEvaluationResponse])
async def get_job_evaluations(
    job_id: UUID,
    min_score: float | None = None,
    repo: ScreeningRepository = Depends(get_screening_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Get all rubric evaluations for a specific job vacancy.
    Optionally filter by minimum score.
    """
    evaluations = await repo.get_evaluations_by_vacancy(job_id, min_score=min_score)

    responses = []
    for ev in evaluations:
        responses.append(RubricEvaluationResponse(
            id=ev.id,
            candidate_id=ev.candidate_id,
            job_vacancy_id=ev.job_vacancy_id,
            result=RubricEvaluationResult(
                score=ev.score,
                total_weighted_points=0,
                max_possible_points=0,
                evaluations=ev.evaluations,
                strengths=ev.strengths,
                concerns=ev.concerns,
                reasoning=ev.reasoning or "",
                recommendation="",
            ),
            evaluated_at=ev.evaluated_at,
            model_version=ev.model_version,
        ))

    return responses


@router.get("/{job_id}/candidates/{candidate_id}/breakdown", response_model=None)
async def get_score_breakdown(
    job_id: UUID,
    candidate_id: UUID,
    repo: ScreeningRepository = Depends(get_screening_repo),
    db=None,
company_id: str = Depends(require_company_id)) -> dict:
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    # Support db kwarg for backwards compatibility (tests inject db directly)
    if db is not None and not hasattr(repo, 'get_latest_evaluation'):
        from app.domains.cv_screening.repositories.screening_repository import ScreeningRepository as _SR
        repo = _SR(db)
    """
    Retorna detalhamento completo do score de um candidato em uma vaga (E1).

    Endpoint para o ScoreBreakdownBadge no kanban — lazy-load ao abrir o Popover.
    Inclui score geral, avaliações por critério, pontos fortes, pontos de atenção.

    Returns 404 se não houver avaliação para o par candidato+vaga.
    """
    evaluation = await repo.get_latest_evaluation(candidate_id, job_id)

    if evaluation is None:
        raise HTTPException(
            status_code=404,
            detail="Avaliação não encontrada para este candidato nesta vaga",
        )

    return {
        "candidate_id": str(candidate_id),
        "job_vacancy_id": str(job_id),
        "score": evaluation.score,
        "evaluated_at": evaluation.evaluated_at.isoformat() if evaluation.evaluated_at else None,
        "model_version": evaluation.model_version,
        "strengths": evaluation.strengths or [],
        "concerns": evaluation.concerns or [],
        "reasoning": evaluation.reasoning or "",
        "recommendation": getattr(evaluation, "recommendation", ""),
        "evaluations": evaluation.evaluations or [],
        "auto_excluded": getattr(evaluation, "auto_excluded", False),
    }


@router.post("/evaluate/legacy", response_model=None)
async def evaluate_candidate_legacy(
    request: EvaluateCandidateRequest,
    db: AsyncSession = Depends(get_db),
    rubric_svc: RubricEvaluationService = Depends(get_rubric_evaluation_service),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Evaluate candidate and return result in legacy LIA Score format.

    This endpoint is for backward compatibility during the transition
    from the old LIA Score system to the new Rubric Evaluation system.
    """
    response = await evaluate_candidate(request, db, rubric_svc=rubric_svc)

    legacy_result = rubric_svc.to_legacy_format(response.result)

    return legacy_result.model_dump()

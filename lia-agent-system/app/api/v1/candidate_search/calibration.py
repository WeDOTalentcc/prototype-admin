"""
Calibration workflows, vacancy goal-check, and candidate management routes.
"""
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

# F11 Phase 1 fix (2026-05-24): get_tenant_db for RLS-protected writes
from app.core.database import get_tenant_db

from ._shared import (
    CandidateSearchResultDTO,
    JobRequirement,
    JobRequirementCreate,
    _normalize_priority,
    get_db,
    logger,
    RubricEvaluationService,
    get_rubric_evaluation_service,
    rubric_evaluation_service,
)
from app.domains.cv_screening.repositories.screening_repository import ScreeningRepository
from app.shared.types import WeDoBaseModel

router = APIRouter()


async def get_screening_repo(db: AsyncSession = Depends(get_db)) -> ScreeningRepository:
    return ScreeningRepository(db)


class CalibrationFeedbackRequest(WeDoBaseModel):
    """Request para feedback de calibração."""
    candidate_id: str = Field(..., description="ID do candidato")
    feedback: str = Field(..., pattern="^(like|dislike|skip)$", description="Tipo: 'like' ou 'dislike'")
    vacancy_id: str | None = Field(None, description="ID da vaga (opcional)")
    session_id: str | None = Field(None, description="ID da sessão de calibração")
    reason: str | None = Field(None, description="Motivo do feedback")
    candidate_snapshot: dict[str, Any] | None = Field(None, description="Dados do candidato")


class CalibrationFeedbackResponse(BaseModel):
    """Response do feedback de calibração."""
    status: str
    total_feedbacks: int
    likes_count: int
    dislikes_count: int
    calibration_complete: bool
    confidence_level: float
    learned_patterns: dict[str, Any]
    message: str
    feedback_id: str
    sourcing_blocked: bool = True
    ready_to_source: bool = False
    feedbacks_remaining: int = 0
    min_feedbacks_required: int = 5


class CalibrationStartRequest(WeDoBaseModel):
    """Request para iniciar sessão de calibração."""
    vacancy_id: str | None = Field(None, description="ID da vaga")
    search_criteria: dict[str, Any] | None = Field(None, description="Critérios de busca")
    sample_size: int = Field(5, ge=3, le=10, description="Quantidade de candidatos para avaliar")


class CalibrationStartResponse(BaseModel):
    """Response do início da calibração."""
    session_id: str
    vacancy_id: str | None
    status: str
    candidates: list[CandidateSearchResultDTO]
    message: str


class CalibrationStatusResponse(BaseModel):
    """Response do status da calibração."""
    session_id: str
    vacancy_id: str | None
    status: str
    total_shown: int
    likes_count: int
    dislikes_count: int
    calibration_complete: bool
    confidence_level: float
    learned_patterns: dict[str, Any] | None
    message: str
    created_at: str | None
    completed_at: str | None
    sourcing_blocked: bool = True
    ready_to_source: bool = False
    feedbacks_remaining: int = 0
    min_feedbacks_required: int = 5


class VacancyGoalRequest(WeDoBaseModel):
    """Request para verificar meta da vaga."""
    vacancy_id: str = Field(..., description="ID da vaga")
    current_count: int = Field(..., ge=0, description="Contagem atual de candidatos")
    target_min: int = Field(50, ge=1, description="Meta mínima")
    target_max: int = Field(70, ge=1, description="Meta máxima")


class VacancyGoalResponse(BaseModel):
    """Response da verificação de meta."""
    status: str
    vacancy_id: str
    current_count: int
    target_range: list[int]
    deficit: int
    surplus: int
    progress_percentage: int
    recommendation: str
    message: str
    suggested_actions: list[dict[str, Any]]


from app.domains.candidates.services.candidate_goal_service import candidate_goal_service as _recruiter_agent
from app.shared.security.require_company_id import require_company_id


@router.post("/calibration/feedback", response_model=CalibrationFeedbackResponse)
async def submit_calibration_feedback(
    request: CalibrationFeedbackRequest,
    db: AsyncSession = Depends(get_tenant_db),
    repo: ScreeningRepository = Depends(get_screening_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Recebe feedback de calibração do recrutador.

    O recrutador avalia candidatos com like/dislike para calibrar o perfil ideal.
    Após 5 feedbacks, o sistema:
    1. Analisa padrões dos feedbacks
    2. Salva critérios aprendidos
    3. Confirma status e desbloqueia sourcing automático
    """
    from datetime import datetime
    import uuid

    from app.models.calibration import CalibrationFeedback, CalibrationSession

    try:
        session = None
        if request.session_id:
            session = await repo.get_calibration_session_by_id(request.session_id)

        if not session and request.vacancy_id:
            session = await repo.get_latest_blocked_session_for_vacancy(request.vacancy_id)

        if not session:
            session = CalibrationSession(
                id=str(uuid.uuid4()),
                vacancy_id=request.vacancy_id,
                status="awaiting_feedback",
                sourcing_blocked=True,
                min_feedbacks_required=5
            )
            await repo.create_calibration_session(session)

        feedback_entry = CalibrationFeedback(
            session_id=session.id,
            candidate_id=request.candidate_id,
            feedback_type=request.feedback,
            reason=request.reason,
            candidate_snapshot=request.candidate_snapshot
        )
        await repo.create_calibration_feedback(feedback_entry)

        if request.feedback.lower() == "like":
            session.likes_count = (session.likes_count or 0) + 1
        elif request.feedback.lower() == "dislike":
            session.dislikes_count = (session.dislikes_count or 0) + 1
        # skip: nao conta como like nem dislike, mas conta em total_shown
        session.total_shown = (session.total_shown or 0) + 1

        min_feedbacks = session.min_feedbacks_required or 5
        feedbacks_remaining = max(0, min_feedbacks - session.total_shown)
        calibration_complete = session.total_shown >= min_feedbacks

        if calibration_complete and session.sourcing_blocked:
            all_feedbacks = await repo.get_feedbacks_by_session(session.id)

            feedbacks_for_analysis = [
                {
                    "feedback": f.feedback_type,
                    "candidate_snapshot": f.candidate_snapshot or {}
                } for f in all_feedbacks
            ]

            analysis = await _recruiter_agent.analyze_calibration_patterns_for_session(
                session_id=session.id,
                feedbacks=feedbacks_for_analysis
            )

            session.learned_criteria = analysis.get("patterns", {})
            session.status = "confirmed"
            session.sourcing_blocked = False
            session.confirmation_message = analysis.get("confirmation_message", "")
            session.completed_at = datetime.now()

            confidence_level = analysis.get("confidence", 0.9)
            message = analysis.get("confirmation_message", "Calibração completa! Sourcing automático liberado.")
        else:
            if session.total_shown >= 3:
                session.status = "learning"
                message = f"Entendendo seu perfil... Faltam {feedbacks_remaining} avaliação(ões)."
            else:
                session.status = "awaiting_feedback"
                message = f"Coletando preferências... Avalie mais {feedbacks_remaining} candidato(s)."
            confidence_level = min(0.9, 0.3 + (session.total_shown * 0.12))

        return CalibrationFeedbackResponse(
            status=session.status,
            total_feedbacks=session.total_shown,
            likes_count=session.likes_count,
            dislikes_count=session.dislikes_count,
            calibration_complete=calibration_complete,
            confidence_level=round(confidence_level, 2),
            learned_patterns=session.learned_criteria or {},
            message=message,
            feedback_id=feedback_entry.id if hasattr(feedback_entry, 'id') else str(uuid.uuid4()),
            sourcing_blocked=session.sourcing_blocked,
            ready_to_source=not session.sourcing_blocked,
            feedbacks_remaining=feedbacks_remaining,
            min_feedbacks_required=min_feedbacks
        )

    except HTTPException:
        raise
    except Exception as e:
        await repo.rollback()
        logger.error(f"Calibration feedback failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/calibration/start", response_model=CalibrationStartResponse)
async def start_calibration_session(
    request: CalibrationStartRequest,
    db: AsyncSession = Depends(get_tenant_db),
    repo: ScreeningRepository = Depends(get_screening_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Inicia uma sessão de calibração.

    Retorna uma amostra de candidatos para o recrutador avaliar com like/dislike.
    Os feedbacks são usados para calibrar o perfil ideal para a busca.
    Bloqueia sourcing automático até a calibração ser completada (5 feedbacks).
    """
    import uuid

    from app.models.calibration import CalibrationSession

    try:
        session_id = str(uuid.uuid4())
        sample_size = request.sample_size or 5

        new_session = CalibrationSession(
            id=session_id,
            vacancy_id=request.vacancy_id,
            search_criteria=request.search_criteria,
            status="awaiting_feedback",
            min_feedbacks_required=sample_size,
            sourcing_blocked=True,
            total_shown=0,
            likes_count=0,
            dislikes_count=0
        )
        await repo.create_calibration_session(new_session)

        candidates_orm = await repo.get_random_candidates(sample_size)

        candidates = []
        for c in candidates_orm:
            candidates.append(CandidateSearchResultDTO(
                id=str(c.id),
                name=c.name or "Candidato",
                first_name=c.name.split()[0] if c.name else None,
                headline=c.headline,
                current_title=c.current_title,
                current_company=c.current_company,
                location=f"{c.location_city or ''}, {c.location_state or ''}".strip(", "),
                total_experience_years=float(c.years_of_experience) if c.years_of_experience else None,
                skills=c.technical_skills[:10] if c.technical_skills else [],
                score=c.lia_score,
                linkedin_url=c.linkedin_url,
                has_email=bool(c.email),
                has_phone=bool(c.phone),
                source="local"
            ))

        if not candidates:
            return CalibrationStartResponse(
                session_id=session_id,
                vacancy_id=request.vacancy_id,
                status="no_candidates",
                candidates=[],
                message="Não há candidatos disponíveis para calibração. Importe candidatos primeiro."
            )

        return CalibrationStartResponse(
            session_id=session_id,
            vacancy_id=request.vacancy_id,
            status="awaiting_feedback",
            candidates=candidates,
            message=f"Sessão de calibração iniciada com {len(candidates)} candidatos. Avalie cada um com like ou dislike para liberar o sourcing automático."
        )

    except HTTPException:
        raise
    except Exception as e:
        await repo.rollback()
        logger.error(f"Start calibration failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/calibration/{session_id}/status", response_model=CalibrationStatusResponse)
async def get_calibration_status(
    session_id: str,
    repo: ScreeningRepository = Depends(get_screening_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Retorna o status da sessão de calibração.

    Mostra progresso, feedbacks recebidos, padrões aprendidos e estado de bloqueio de sourcing.
    """
    try:
        session = await repo.get_calibration_session_by_id(session_id)

        if not session:
            return CalibrationStatusResponse(
                session_id=session_id,
                vacancy_id=None,
                status="not_found",
                total_shown=0,
                likes_count=0,
                dislikes_count=0,
                calibration_complete=False,
                confidence_level=0.0,
                learned_patterns=None,
                message="Sessão de calibração não encontrada.",
                created_at=None,
                completed_at=None,
                sourcing_blocked=True,
                ready_to_source=False,
                feedbacks_remaining=5,
                min_feedbacks_required=5
            )

        min_feedbacks = session.min_feedbacks_required or 5
        total_shown = session.total_shown or 0
        likes_count = session.likes_count or 0
        dislikes_count = session.dislikes_count or 0
        feedbacks_remaining = max(0, min_feedbacks - total_shown)

        calibration_complete = not session.sourcing_blocked
        confidence_level = min(0.9, 0.3 + (total_shown * 0.12))

        if calibration_complete:
            message = session.confirmation_message or "Calibração completa! Sourcing automático liberado."
        elif total_shown >= 3:
            message = f"Calibração em andamento. Faltam {feedbacks_remaining} avaliação(ões)."
        else:
            message = f"Coletando preferências. Avalie mais {feedbacks_remaining} candidato(s)."

        return CalibrationStatusResponse(
            session_id=session_id,
            vacancy_id=session.vacancy_id,
            status=session.status or "awaiting_feedback",
            total_shown=total_shown,
            likes_count=likes_count,
            dislikes_count=dislikes_count,
            calibration_complete=calibration_complete,
            confidence_level=round(confidence_level, 2),
            learned_patterns=session.learned_criteria if calibration_complete else None,
            message=message,
            created_at=session.created_at.isoformat() if session.created_at else None,
            completed_at=session.completed_at.isoformat() if session.completed_at else None,
            sourcing_blocked=session.sourcing_blocked,
            ready_to_source=not session.sourcing_blocked,
            feedbacks_remaining=feedbacks_remaining,
            min_feedbacks_required=min_feedbacks
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get calibration status failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/vacancy/goal-check", response_model=VacancyGoalResponse)
async def check_vacancy_candidate_goal(
    request: VacancyGoalRequest,
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Verifica se a vaga atingiu a meta de candidatos.

    Retorna status (abaixo, na meta, acima), recomendações e ações sugeridas.
    """
    try:
        result = await _recruiter_agent.check_vacancy_candidate_goal(
            vacancy_id=request.vacancy_id,
            current_count=request.current_count,
            target_min=request.target_min,
            target_max=request.target_max
        )

        return VacancyGoalResponse(
            status=result.get("status", "unknown"),
            vacancy_id=result.get("vacancy_id", request.vacancy_id),
            current_count=result.get("current_count", request.current_count),
            target_range=result.get("target_range", [request.target_min, request.target_max]),
            deficit=result.get("deficit", 0),
            surplus=result.get("surplus", 0),
            progress_percentage=result.get("progress_percentage", 0),
            recommendation=result.get("recommendation", ""),
            message=result.get("message", ""),
            suggested_actions=result.get("suggested_actions", [])
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Vacancy goal check failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


class AddCandidatesToVacancyRequest(WeDoBaseModel):
    """Request para adicionar candidatos a uma vaga."""
    candidate_ids: list[str] = Field(..., min_length=1, description="Lista de IDs de candidatos para adicionar")
    source: str = Field("local", description="Fonte dos candidatos: 'local' ou 'pearch'")
    added_by: str | None = Field(None, description="ID do usuário que adicionou")


class AddCandidatesToVacancyResponse(BaseModel):
    """Response da adição de candidatos a uma vaga."""
    vacancy_id: str
    added_count: int
    total_count: int
    skipped_count: int
    skipped_ids: list[str] = Field(default_factory=list)
    at_capacity: bool = Field(False, description="Indica se a vaga atingiu capacidade máxima (70)")
    goal_check: VacancyGoalResponse
    message: str


@router.post("/vacancy/{vacancy_id}/add-candidates", response_model=AddCandidatesToVacancyResponse)
async def add_candidates_to_vacancy(
    vacancy_id: str,
    request: AddCandidatesToVacancyRequest,
    db: AsyncSession = Depends(get_tenant_db),
    rubric_svc: RubricEvaluationService = Depends(get_rubric_evaluation_service),
    repo: ScreeningRepository = Depends(get_screening_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Adiciona candidatos a uma vaga e verifica meta automaticamente.

    Workflow:
    1. Verifica se calibração foi completada (BLOQUEIO se sourcing_blocked=True)
    2. Conta candidatos atuais na vaga
    3. Adiciona novos candidatos (até limite de 70)
    4. Chama check_vacancy_candidate_goal
    5. Retorna status e recomendações

    A meta de candidatos por vaga é de 50-70 candidatos.
    O sistema não permite adicionar além de 70 candidatos.
    """
    import uuid

    from app.models.candidate import VacancyCandidate

    try:
        vacancy = await repo.get_job_vacancy_by_id(vacancy_id)
        vacancy_company_id = vacancy.company_id if vacancy else None

        calibration_session = await repo.get_latest_session_for_vacancy(vacancy_id)

        if calibration_session and calibration_session.sourcing_blocked:
            feedbacks_remaining = max(
                0,
                (calibration_session.min_feedbacks_required or 5) - (calibration_session.total_shown or 0)
            )
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "calibration_required",
                    "message": "Complete a calibração antes de adicionar candidatos automaticamente.",
                    "feedbacks_remaining": feedbacks_remaining,
                    "session_id": calibration_session.id,
                    "current_feedbacks": calibration_session.total_shown or 0,
                    "min_feedbacks_required": calibration_session.min_feedbacks_required or 5
                }
            )

        target_min = 50
        target_max = 70

        current_count = await repo.count_vacancy_candidates(uuid.UUID(vacancy_id))

        max_to_add = max(0, target_max - current_count)
        candidates_to_add = request.candidate_ids[:max_to_add]
        skipped_ids = request.candidate_ids[max_to_add:]

        added_count = 0
        for candidate_id in candidates_to_add:
            try:
                existing = await repo.get_vacancy_candidate(
                    uuid.UUID(vacancy_id), uuid.UUID(candidate_id)
                )
                if existing is None:
                    from app.shared.services.stage_id_resolver import resolve_recruitment_stage_id
                    initial_stage_id = await resolve_recruitment_stage_id(
                        db, str(vacancy_company_id), "sourcing"
                    )
                    new_vc = VacancyCandidate(
                        vacancy_id=uuid.UUID(vacancy_id),
                        candidate_id=uuid.UUID(candidate_id),
                        company_id=vacancy_company_id,
                        source=request.source,
                        added_by=request.added_by,
                        status="sourced",
                        stage="sourcing",
                        recruitment_stage_id=initial_stage_id
                    )
                    await repo.create_vacancy_candidate(new_vc)
                    added_count += 1
                else:
                    skipped_ids.append(candidate_id)
            except ValueError:
                skipped_ids.append(candidate_id)

        # G-11: flush explicito para que erros de integridade do bulk add
        # aflorem AQUI (virando 500 honesto) em vez de falhar no commit final
        # do get_tenant_db apos a resposta ja ter sido enviada (falso 200).
        if added_count > 0:
            await db.flush()

        if added_count > 0 and vacancy:
            try:
                job_requirements = await repo.get_requirements_by_vacancy(uuid.UUID(vacancy_id))

                if job_requirements:
                    requirements_list = [
                        JobRequirementCreate(
                            requirement=req.requirement,
                            description=req.description,
                            priority=_normalize_priority(req.priority),
                            category=req.category
                        )
                        for req in job_requirements
                    ]

                    for cand_id in candidates_to_add:
                        try:
                            candidate = await repo.get_candidate_by_id(uuid.UUID(cand_id))

                            if candidate:
                                candidate_data = {
                                    "name": candidate.name,
                                    "current_title": candidate.current_title,
                                    "current_company": candidate.current_company,
                                    "years_of_experience": candidate.years_of_experience,
                                    "seniority_level": candidate.seniority_level,
                                    "technical_skills": candidate.technical_skills or [],
                                    "soft_skills": getattr(candidate, 'soft_skills', []) or [],
                                    "certifications": getattr(candidate, 'certifications', []) or [],
                                    "languages": getattr(candidate, 'languages', {}) or {},
                                    "location_city": candidate.location_city,
                                    "location_state": candidate.location_state,
                                    "education": getattr(candidate, 'education', []) or [],
                                    "work_history": getattr(candidate, 'work_history', []) or [],
                                    "resume_text": getattr(candidate, 'resume_text', None),
                                }

                                await rubric_svc.evaluate_and_create_activity(
                                    candidate_id=cand_id,
                                    candidate_name=candidate.name or "Candidato",
                                    candidate_data=candidate_data,
                                    job_id=vacancy_id,
                                    job_title=vacancy.title or "Vaga",
                                    job_code=getattr(vacancy, 'code', None) or getattr(vacancy, 'job_code', None),
                                    requirements=requirements_list,
                                    company_id=vacancy_company_id,
                                    created_by=request.added_by,
                                )
                        except Exception as eval_err:
                            logger.warning(f"Rubric evaluation failed for candidate {cand_id}: {eval_err}")

            except Exception as rubric_err:
                logger.warning(f"Rubric evaluation setup failed: {rubric_err}")

        new_total = current_count + added_count
        at_capacity = new_total >= target_max

        goal_result = await _recruiter_agent.check_vacancy_candidate_goal(
            vacancy_id=vacancy_id,
            current_count=new_total,
            target_min=target_min,
            target_max=target_max
        )

        goal_check = VacancyGoalResponse(
            status=goal_result.get("status", "unknown"),
            vacancy_id=vacancy_id,
            current_count=goal_result.get("current_count", new_total),
            target_range=goal_result.get("target_range", [target_min, target_max]),
            deficit=goal_result.get("deficit", 0),
            surplus=goal_result.get("surplus", 0),
            progress_percentage=goal_result.get("progress_percentage", 0),
            recommendation=goal_result.get("recommendation", ""),
            message=goal_result.get("message", ""),
            suggested_actions=goal_result.get("suggested_actions", [])
        )

        if at_capacity:
            message = f"Vaga atingiu capacidade máxima! {added_count} candidato(s) adicionado(s). Total: {new_total}/{target_max}."
        elif added_count == 0:
            message = "Nenhum candidato novo adicionado. Candidatos já existem na vaga ou IDs inválidos."
        elif goal_result.get("status") == "on_target":
            message = f"{added_count} candidato(s) adicionado(s). Meta atingida! Total: {new_total}."
        else:
            deficit = goal_result.get("deficit", 0)
            message = f"{added_count} candidato(s) adicionado(s). Total: {new_total}. Faltam {deficit} para meta mínima."

        return AddCandidatesToVacancyResponse(
            vacancy_id=vacancy_id,
            added_count=added_count,
            total_count=new_total,
            skipped_count=len(skipped_ids),
            skipped_ids=skipped_ids[:10],
            at_capacity=at_capacity,
            goal_check=goal_check,
            message=message
        )

    except HTTPException:
        raise
    except Exception as e:
        await repo.rollback()
        logger.error(f"Add candidates to vacancy failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/vacancy/{vacancy_id}/candidates/count", response_model=None)
async def get_vacancy_candidates_count(
    vacancy_id: str,
    repo: ScreeningRepository = Depends(get_screening_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Retorna a contagem de candidatos em uma vaga e o status da meta.
    """
    import uuid

    try:
        current_count = await repo.count_vacancy_candidates(uuid.UUID(vacancy_id))

        goal_result = await _recruiter_agent.check_vacancy_candidate_goal(
            vacancy_id=vacancy_id,
            current_count=current_count,
            target_min=50,
            target_max=70
        )

        return {
            "vacancy_id": vacancy_id,
            "current_count": current_count,
            "target_min": 50,
            "target_max": 70,
            "status": goal_result.get("status", "unknown"),
            "progress_percentage": goal_result.get("progress_percentage", 0),
            "recommendation": goal_result.get("recommendation", ""),
            "message": goal_result.get("message", "")
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get vacancy candidates count failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

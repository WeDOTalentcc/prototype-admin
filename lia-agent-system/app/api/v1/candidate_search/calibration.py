"""
Calibration workflows, vacancy goal-check, and candidate management routes.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, File, UploadFile, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from ._shared import (
    logger, get_db, get_current_user_or_demo, get_user_company_id, assert_resource_ownership,
    User, ImportUser, cv_parser_service, search_analytics_service,
    extract_tags_from_search_spec, build_archetype_from_search,
    ArchetypeFromSearchCreate, ArchetypeFromSearchResponse, ArchetypeResponse,
    rubric_evaluation_service, JobRequirement, JobRequirementCreate, RequirementPriorityEnum,
    pearch_service, HybridSearchRequest, PearchSearchRequest, SearchType,
    _normalize_priority, _normalize_name, _generate_fingerprint,
    _get_job_requirements, _get_match_label, _build_candidate_data_from_dto,
    _evaluate_candidates_with_rubrics, _recruiter_agent,
    ExperienceDTO, EducationDTO, LanguageDTO, CandidateSearchResultDTO, SearchResponseDTO,
    SearchRequestDTO, ImportCandidateExperienceDTO, ImportCandidateDTO,
    ImportCandidatesRequest, IdMapping, ImportCandidatesResponse,
    CreditEstimateDTO, EvaluateForJobRequest, EvaluateForJobResult, EvaluateForJobResponse,
)

router = APIRouter()

class CalibrationFeedbackRequest(BaseModel):
    """Request para feedback de calibração."""
    candidate_id: str = Field(..., description="ID do candidato")
    feedback: str = Field(..., pattern="^(like|dislike)$", description="Tipo: 'like' ou 'dislike'")
    vacancy_id: Optional[str] = Field(None, description="ID da vaga (opcional)")
    session_id: Optional[str] = Field(None, description="ID da sessão de calibração")
    reason: Optional[str] = Field(None, description="Motivo do feedback")
    candidate_snapshot: Optional[Dict[str, Any]] = Field(None, description="Dados do candidato")


class CalibrationFeedbackResponse(BaseModel):
    """Response do feedback de calibração."""
    status: str
    total_feedbacks: int
    likes_count: int
    dislikes_count: int
    calibration_complete: bool
    confidence_level: float
    learned_patterns: Dict[str, Any]
    message: str
    feedback_id: str
    sourcing_blocked: bool = True
    ready_to_source: bool = False
    feedbacks_remaining: int = 0
    min_feedbacks_required: int = 5


class CalibrationStartRequest(BaseModel):
    """Request para iniciar sessão de calibração."""
    vacancy_id: Optional[str] = Field(None, description="ID da vaga")
    search_criteria: Optional[Dict[str, Any]] = Field(None, description="Critérios de busca")
    sample_size: int = Field(5, ge=3, le=10, description="Quantidade de candidatos para avaliar")


class CalibrationStartResponse(BaseModel):
    """Response do início da calibração."""
    session_id: str
    vacancy_id: Optional[str]
    status: str
    candidates: List[CandidateSearchResultDTO]
    message: str


class CalibrationStatusResponse(BaseModel):
    """Response do status da calibração."""
    session_id: str
    vacancy_id: Optional[str]
    status: str
    total_shown: int
    likes_count: int
    dislikes_count: int
    calibration_complete: bool
    confidence_level: float
    learned_patterns: Optional[Dict[str, Any]]
    message: str
    created_at: Optional[str]
    completed_at: Optional[str]
    sourcing_blocked: bool = True
    ready_to_source: bool = False
    feedbacks_remaining: int = 0
    min_feedbacks_required: int = 5


class VacancyGoalRequest(BaseModel):
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
    target_range: List[int]
    deficit: int
    surplus: int
    progress_percentage: int
    recommendation: str
    message: str
    suggested_actions: List[Dict[str, Any]]




@router.post("/calibration/feedback", response_model=CalibrationFeedbackResponse)
async def submit_calibration_feedback(
    request: CalibrationFeedbackRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Recebe feedback de calibração do recrutador.
    
    O recrutador avalia candidatos com like/dislike para calibrar o perfil ideal.
    Após 5 feedbacks, o sistema:
    1. Analisa padrões dos feedbacks
    2. Salva critérios aprendidos
    3. Confirma status e desbloqueia sourcing automático
    """
    from datetime import datetime
    from sqlalchemy import select
    from app.models.calibration import CalibrationSession, CalibrationFeedback
    
    try:
        session = None
        if request.session_id:
            stmt = select(CalibrationSession).where(CalibrationSession.id == request.session_id)
            result = await db.execute(stmt)
            session = result.scalar_one_or_none()
        
        if not session and request.vacancy_id:
            stmt = select(CalibrationSession).where(
                CalibrationSession.vacancy_id == request.vacancy_id,
                CalibrationSession.sourcing_blocked == True
            ).order_by(CalibrationSession.created_at.desc())
            result = await db.execute(stmt)
            session = result.scalars().first()
        
        if not session:
            import uuid
            session = CalibrationSession(
                id=str(uuid.uuid4()),
                vacancy_id=request.vacancy_id,
                status="awaiting_feedback",
                sourcing_blocked=True,
                min_feedbacks_required=5
            )
            db.add(session)
            await db.flush()
        
        feedback_entry = CalibrationFeedback(
            session_id=session.id,
            candidate_id=request.candidate_id,
            feedback_type=request.feedback,
            reason=request.reason,
            candidate_snapshot=request.candidate_snapshot
        )
        db.add(feedback_entry)
        
        if request.feedback.lower() == "like":
            session.likes_count = (session.likes_count or 0) + 1
        else:
            session.dislikes_count = (session.dislikes_count or 0) + 1
        session.total_shown = (session.total_shown or 0) + 1
        
        min_feedbacks = session.min_feedbacks_required or 5
        feedbacks_remaining = max(0, min_feedbacks - session.total_shown)
        calibration_complete = session.total_shown >= min_feedbacks
        
        if calibration_complete and session.sourcing_blocked:
            stmt = select(CalibrationFeedback).where(
                CalibrationFeedback.session_id == session.id
            )
            result = await db.execute(stmt)
            all_feedbacks = result.scalars().all()
            
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
        
        await db.commit()
        
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
    
    except Exception as e:
        await db.rollback()
        logger.error(f"Calibration feedback failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Calibration feedback failed: {str(e)}")


@router.post("/calibration/start", response_model=CalibrationStartResponse)
async def start_calibration_session(
    request: CalibrationStartRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Inicia uma sessão de calibração.
    
    Retorna uma amostra de candidatos para o recrutador avaliar com like/dislike.
    Os feedbacks são usados para calibrar o perfil ideal para a busca.
    Bloqueia sourcing automático até a calibração ser completada (5 feedbacks).
    """
    import uuid
    from sqlalchemy import select, func
    from app.models.candidate import Candidate
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
        db.add(new_session)
        
        query = select(Candidate).order_by(func.random()).limit(sample_size)
        result = await db.execute(query)
        candidates_orm = result.scalars().all()
        
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
        
        await db.commit()
        
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
    
    except Exception as e:
        await db.rollback()
        logger.error(f"Start calibration failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Start calibration failed: {str(e)}")


@router.get("/calibration/{session_id}/status", response_model=CalibrationStatusResponse)
async def get_calibration_status(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Retorna o status da sessão de calibração.
    
    Mostra progresso, feedbacks recebidos, padrões aprendidos e estado de bloqueio de sourcing.
    """
    from sqlalchemy import select
    from app.models.calibration import CalibrationSession
    
    try:
        stmt = select(CalibrationSession).where(CalibrationSession.id == session_id)
        result = await db.execute(stmt)
        session = result.scalar_one_or_none()
        
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
    
    except Exception as e:
        logger.error(f"Get calibration status failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Get calibration status failed: {str(e)}")


@router.post("/vacancy/goal-check", response_model=VacancyGoalResponse)
async def check_vacancy_candidate_goal(
    request: VacancyGoalRequest,
    db: AsyncSession = Depends(get_db)
):
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
    
    except Exception as e:
        logger.error(f"Vacancy goal check failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Vacancy goal check failed: {str(e)}")


class AddCandidatesToVacancyRequest(BaseModel):
    """Request para adicionar candidatos a uma vaga."""
    candidate_ids: List[str] = Field(..., min_length=1, description="Lista de IDs de candidatos para adicionar")
    source: str = Field("local", description="Fonte dos candidatos: 'local' ou 'pearch'")
    added_by: Optional[str] = Field(None, description="ID do usuário que adicionou")


class AddCandidatesToVacancyResponse(BaseModel):
    """Response da adição de candidatos a uma vaga."""
    vacancy_id: str
    added_count: int
    total_count: int
    skipped_count: int
    skipped_ids: List[str] = Field(default_factory=list)
    at_capacity: bool = Field(False, description="Indica se a vaga atingiu capacidade máxima (70)")
    goal_check: VacancyGoalResponse
    message: str


@router.post("/vacancy/{vacancy_id}/add-candidates", response_model=AddCandidatesToVacancyResponse)
async def add_candidates_to_vacancy(
    vacancy_id: str,
    request: AddCandidatesToVacancyRequest,
    db: AsyncSession = Depends(get_db)
):
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
    from sqlalchemy import select, func
    from app.models.candidate import VacancyCandidate
    from app.models.calibration import CalibrationSession
    from app.models.job_vacancy import JobVacancy
    import uuid
    
    try:
        vacancy_result = await db.execute(
            select(JobVacancy).where(JobVacancy.id == vacancy_id)
        )
        vacancy = vacancy_result.scalar_one_or_none()
        vacancy_company_id = vacancy.company_id if vacancy else "default"
        
        calibration_stmt = select(CalibrationSession).where(
            CalibrationSession.vacancy_id == vacancy_id,
        ).order_by(CalibrationSession.created_at.desc())
        calibration_result = await db.execute(calibration_stmt)
        calibration_session = calibration_result.scalars().first()
        
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
        
        count_result = await db.execute(
            select(func.count(VacancyCandidate.id)).where(
                VacancyCandidate.vacancy_id == uuid.UUID(vacancy_id)
            )
        )
        current_count = count_result.scalar() or 0
        
        max_to_add = max(0, target_max - current_count)
        candidates_to_add = request.candidate_ids[:max_to_add]
        skipped_ids = request.candidate_ids[max_to_add:]
        
        added_count = 0
        for candidate_id in candidates_to_add:
            try:
                existing = await db.execute(
                    select(VacancyCandidate).where(
                        VacancyCandidate.vacancy_id == uuid.UUID(vacancy_id),
                        VacancyCandidate.candidate_id == uuid.UUID(candidate_id)
                    )
                )
                if existing.scalar_one_or_none() is None:
                    new_vc = VacancyCandidate(
                        vacancy_id=uuid.UUID(vacancy_id),
                        candidate_id=uuid.UUID(candidate_id),
                        company_id=vacancy_company_id or "default",
                        source=request.source,
                        added_by=request.added_by,
                        status="sourced",
                        stage="initial"
                    )
                    db.add(new_vc)
                    added_count += 1
                else:
                    skipped_ids.append(candidate_id)
            except ValueError:
                skipped_ids.append(candidate_id)
        
        await db.commit()
        
        if added_count > 0 and vacancy:
            try:
                from app.models.candidate import Candidate
                
                reqs_result = await db.execute(
                    select(JobRequirement).where(JobRequirement.job_vacancy_id == uuid.UUID(vacancy_id))
                )
                job_requirements = reqs_result.scalars().all()
                
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
                            cand_result = await db.execute(
                                select(Candidate).where(Candidate.id == uuid.UUID(cand_id))
                            )
                            candidate = cand_result.scalar_one_or_none()
                            
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
                                
                                await rubric_evaluation_service.evaluate_and_create_activity(
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
    
    except Exception as e:
        await db.rollback()
        logger.error(f"Add candidates to vacancy failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Add candidates to vacancy failed: {str(e)}")


@router.get("/vacancy/{vacancy_id}/candidates/count")
async def get_vacancy_candidates_count(
    vacancy_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Retorna a contagem de candidatos em uma vaga e o status da meta.
    """
    from sqlalchemy import select, func
    from app.models.candidate import VacancyCandidate
    import uuid
    
    try:
        count_result = await db.execute(
            select(func.count(VacancyCandidate.id)).where(
                VacancyCandidate.vacancy_id == uuid.UUID(vacancy_id)
            )
        )
        current_count = count_result.scalar() or 0
        
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
    
    except Exception as e:
        logger.error(f"Get vacancy candidates count failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Get vacancy candidates count failed: {str(e)}")

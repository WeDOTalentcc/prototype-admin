"""
Applications API - Endpoints for candidate applications to job vacancies.

This module handles:
1. Candidate application submission
2. Automatic adherence score calculation
3. Automatic feedback for low adherence candidates
4. CV resubmission handling
"""
from uuid import UUID
import logging
import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.cv_screening.services.cv_parser import cv_parser_service
from app.domains.cv_screening.services.rubric_evaluation_service import rubric_evaluation_service
from app.models.candidate import Candidate, VacancyCandidate
from app.models.candidate_feedback import CandidateFeedback
from app.models.job_vacancy import JobVacancy
from app.models.rubric import JobRequirement
from app.schemas.rubric import JobRequirementCreate, RequirementPriorityEnum
from app.services.candidate_feedback_service import candidate_feedback_service
from app.services.lia_score_service import LIAScoreService
from app.services.notification_service import NotificationType, notification_service

logger = logging.getLogger(__name__)


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
router = APIRouter(prefix="/applications", tags=["applications"])

lia_score_service = LIAScoreService()


class CandidateApplicationRequest(BaseModel):
    """Request para inscrição de candidato em uma vaga."""
    name: str = Field(..., description="Nome completo do candidato")
    email: EmailStr = Field(..., description="Email do candidato")
    phone: str | None = Field(None, description="Telefone do candidato")
    linkedin_url: str | None = Field(None, description="URL do LinkedIn")
    current_title: str | None = Field(None, description="Cargo atual")
    current_company: str | None = Field(None, description="Empresa atual")
    years_of_experience: int | None = Field(None, description="Anos de experiência")
    technical_skills: list[str] = Field(default_factory=list, description="Habilidades técnicas")
    location: str | None = Field(None, description="Localização")
    salary_expectation: float | None = Field(None, description="Pretensão salarial")
    cover_letter: str | None = Field(None, description="Carta de apresentação")


class ApplicationResponseDTO(BaseModel):
    """Response da inscrição."""
    status: str
    candidate_id: str
    vacancy_id: str
    adherence_score: float
    feedback_sent: bool = False
    feedback_channels: list[str] = Field(default_factory=list)
    resubmit_url: str | None = None
    message: str
    next_step: str | None = None


class ResubmitResponseDTO(BaseModel):
    """Response do reenvio de CV."""
    status: str
    candidate_id: str
    vacancy_id: str
    new_adherence_score: float
    previous_adherence_score: float
    improvement: float
    message: str
    qualified: bool


class FeedbackAnalyticsDTO(BaseModel):
    """Analytics de feedback."""
    period_days: int
    total_feedbacks_sent: int
    channels: dict[str, int]
    engagement: dict[str, Any]
    scores: dict[str, Any]


@router.post("/apply/{vacancy_id}", response_model=ApplicationResponseDTO)
async def apply_to_vacancy(
    vacancy_id: str,
    application: CandidateApplicationRequest,
    cv_file: UploadFile | None = File(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Processa inscrição de candidato em uma vaga.
    
    Workflow:
    1. Criar/atualizar candidato no banco
    2. Calcular score de aderência usando LIA Score Service
    3. Se aderência < 50%: enviar feedback automático
    4. Se aderência >= 50%: adicionar ao pipeline de seleção
    
    Returns:
        ApplicationResponseDTO com status da inscrição e próximos passos
    """
    try:
        result = await db.execute(
            select(JobVacancy).where(JobVacancy.id == vacancy_id)
        )
        vacancy = result.scalar_one_or_none()
        
        if not vacancy:
            raise HTTPException(status_code=404, detail=f"Vaga {vacancy_id} não encontrada")
        
        if vacancy.status not in ["open", "active", "published"]:
            raise HTTPException(status_code=400, detail="Esta vaga não está aberta para candidaturas")
        
        candidate_data = application.model_dump()
        
        if cv_file:
            try:
                cv_content = await cv_file.read()
                parsed_cv = await cv_parser_service.parse_cv(
                    file_content=cv_content,
                    filename=cv_file.filename
                )
                
                if parsed_cv.get("skills"):
                    candidate_data["technical_skills"] = list(set(
                        candidate_data.get("technical_skills", []) + parsed_cv.get("skills", [])
                    ))
                if parsed_cv.get("experience_years") and not candidate_data.get("years_of_experience"):
                    candidate_data["years_of_experience"] = parsed_cv.get("experience_years")
                if parsed_cv.get("current_title") and not candidate_data.get("current_title"):
                    candidate_data["current_title"] = parsed_cv.get("current_title")
                    
            except Exception as e:
                logger.warning(f"Failed to parse CV: {e}")
        
        result = await db.execute(
            select(Candidate).where(Candidate.email == application.email)
        )
        existing_candidate = result.scalar_one_or_none()
        
        if existing_candidate:
            candidate = existing_candidate
            for key, value in candidate_data.items():
                if value is not None and hasattr(candidate, key):
                    setattr(candidate, key, value)
            candidate.updated_at = datetime.utcnow()
        else:
            candidate = Candidate(
                id=uuid.uuid4(),
                name=candidate_data["name"],
                email=candidate_data["email"],
                phone=candidate_data.get("phone"),
                linkedin_url=candidate_data.get("linkedin_url"),
                current_title=candidate_data.get("current_title"),
                current_company=candidate_data.get("current_company"),
                years_of_experience=candidate_data.get("years_of_experience"),
                technical_skills=candidate_data.get("technical_skills", []),
                location_city=candidate_data.get("location"),
                desired_salary_min=candidate_data.get("salary_expectation"),
                source="application",
                status="new"
            )
            db.add(candidate)
        
        await db.flush()
        
        vacancy_requirements = {
            "query": vacancy.title or "",
            "skills": vacancy.required_skills or [],
            "experience_years": vacancy.min_experience_years,
            "seniority": vacancy.seniority_level,
            "location": vacancy.location_city
        }
        
        candidate_profile = {
            "skills": candidate_data.get("technical_skills", []),
            "experience_years": candidate_data.get("years_of_experience"),
            "current_title": candidate_data.get("current_title"),
            "location": candidate_data.get("location"),
            "seniority": None
        }
        
        score_result = lia_score_service.calculate_score(
            candidate=candidate_profile,
            search_criteria=vacancy_requirements
        )
        
        adherence_score = score_result.score
        matched_skills = score_result.matched_skills
        missing_skills = score_result.missing_skills
        
        candidate.lia_score = adherence_score
        candidate.skills_match_percentage = score_result.breakdown.skills_match
        candidate.lia_insights = score_result.to_dict()
        
        if adherence_score < candidate_feedback_service.ADHERENCE_THRESHOLD:
            feedback_result = await candidate_feedback_service.check_and_send_feedback(
                candidate_id=str(candidate.id),
                vacancy_id=vacancy_id,
                adherence_score=adherence_score,
                candidate_email=candidate_data["email"],
                candidate_phone=candidate_data.get("phone"),
                candidate_name=candidate_data["name"],
                vacancy_title=vacancy.title,
                company_name=vacancy.company_name or "Nossa Empresa",
                missing_skills=missing_skills,
                matched_skills=matched_skills,
                db=db
            )
            
            await db.commit()
            
            return ApplicationResponseDTO(
                status="low_adherence",
                candidate_id=str(candidate.id),
                vacancy_id=vacancy_id,
                adherence_score=adherence_score,
                feedback_sent=feedback_result["feedback_sent"],
                feedback_channels=feedback_result.get("channels_used", []),
                resubmit_url=feedback_result.get("resubmit_url"),
                message="Obrigado pela candidatura! Enviamos um feedback com sugestões para aumentar suas chances.",
                next_step="improve_profile"
            )
        
        existing_assignment = await db.execute(
            select(VacancyCandidate).where(
                VacancyCandidate.vacancy_id == uuid.UUID(vacancy_id),
                VacancyCandidate.candidate_id == candidate.id
            )
        )
        if not existing_assignment.scalar_one_or_none():
            import secrets as _secrets
            screening_token = _secrets.token_urlsafe(32)

            is_saturated = False
            try:
                from sqlalchemy import and_, func, not_

                from app.models.company import CompanyProfile
                company_id = vacancy.company_id
                if not company_id:
                    logger.warning(f"Vacancy {vacancy_id} has no company_id set")
                threshold_web = 20
                if company_id:
                    cp_result = await db.execute(
                        select(CompanyProfile).where(CompanyProfile.id == company_id)
                    )
                    cp = cp_result.scalar_one_or_none()
                    if cp and cp.additional_data:
                        sat_cfg = cp.additional_data.get("saturation_settings", {})
                        threshold_web = sat_cfg.get("threshold_web", 20)

                governance = vacancy.governance_rules or {} if hasattr(vacancy, "governance_rules") else {}
                threshold_web = governance.get("threshold_web", threshold_web)

                EXCLUDED = ("rejected", "declined", "withdrawn")
                active_filter = and_(
                    VacancyCandidate.vacancy_id == uuid.UUID(vacancy_id),
                    not_(VacancyCandidate.status.in_(EXCLUDED)),
                    VacancyCandidate.origin.in_(("web", "whatsapp")) if hasattr(VacancyCandidate, "origin") else True,
                )
                cnt = await db.execute(select(func.count(VacancyCandidate.id)).where(active_filter))
                organic_count = cnt.scalar() or 0
                is_saturated = organic_count >= threshold_web
            except Exception as sat_err:
                logger.warning(f"Saturation check in applications failed, allowing application: {sat_err}")
                is_saturated = False

            candidate_status = "awaiting_screening" if is_saturated else "applied"

            if not vacancy.company_id:
                raise HTTPException(status_code=400, detail="Vacancy has no company_id. Cannot process application without tenant.")
            vacancy_candidate = VacancyCandidate(
                id=uuid.uuid4(),
                vacancy_id=uuid.UUID(vacancy_id),
                candidate_id=candidate.id,
                company_id=vacancy.company_id,
                source="application",
                lia_score=adherence_score,
                match_percentage=score_result.breakdown.skills_match,
                status=candidate_status,
                stage="pending_gate1",
                additional_data={
                    "screening_invite_token": screening_token,
                    "applied_at": datetime.utcnow().isoformat(),
                    "is_saturated_at_apply": is_saturated,
                },
            )
            db.add(vacancy_candidate)
        
        await notification_service.create_notification(
            user_id="default_user",
            title="✅ Nova candidatura qualificada",
            message=f"{candidate_data['name']} aplicou para {vacancy.title} com aderência de {adherence_score:.0f}%",
            notification_type=NotificationType.SUCCESS,
            category="new_application",
            related_job_id=vacancy_id,
            related_candidate_id=str(candidate.id),
            action_url=f"/candidates/{candidate.id}",
            action_label="Ver Candidato",
            db=db
        )
        
        await db.commit()
        
        try:
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
                
                application_candidate_data = {
                    "name": candidate_data.get("name"),
                    "current_title": candidate_data.get("current_title"),
                    "current_company": candidate_data.get("current_company"),
                    "years_of_experience": candidate_data.get("years_of_experience"),
                    "technical_skills": candidate_data.get("technical_skills", []),
                    "location_city": candidate_data.get("location"),
                }
                
                await rubric_evaluation_service.evaluate_and_create_activity(
                    candidate_id=str(candidate.id),
                    candidate_name=candidate_data.get("name", "Candidato"),
                    candidate_data=application_candidate_data,
                    job_id=vacancy_id,
                    job_title=vacancy.title or "Vaga",
                    job_code=getattr(vacancy, 'code', None) or getattr(vacancy, 'job_code', None),
                    requirements=requirements_list,
                    company_id=vacancy.company_id,
                    created_by="application",
                )
        except Exception as rubric_err:
            logger.warning(f"Rubric evaluation failed for application: {rubric_err}")
        
        # O convite de triagem Gate 1 é disparado posteriormente pelo sistema de
        # saturação (saturation.py) quando houver capacidade disponível — não aqui.
        return ApplicationResponseDTO(
            status="accepted",
            candidate_id=str(candidate.id),
            vacancy_id=vacancy_id,
            adherence_score=adherence_score,
            feedback_sent=False,
            message="Candidatura recebida com sucesso! Você avançará para a próxima etapa do processo.",
            next_step="pending_gate1",
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing application: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao processar candidatura: {str(e)}")


@router.post("/resubmit/{vacancy_id}", response_model=ResubmitResponseDTO)
async def resubmit_cv(
    vacancy_id: str,
    candidate_id: str = Query(..., description="ID do candidato"),
    token: str = Query(..., description="Token de reenvio"),
    cv_file: UploadFile = File(..., description="Currículo atualizado"),
    db: AsyncSession = Depends(get_db)
):
    """
    Processa reenvio de CV após feedback de baixa aderência.
    
    Workflow:
    1. Validar token de reenvio
    2. Atualizar perfil do candidato com novos dados do CV
    3. Recalcular score de aderência
    4. Registrar melhoria no feedback original
    5. Se novo score >= 50%: adicionar ao pipeline
    """
    try:
        result = await db.execute(
            select(CandidateFeedback).where(
                CandidateFeedback.candidate_id == candidate_id,
                CandidateFeedback.vacancy_id == vacancy_id,
                CandidateFeedback.resubmit_token == token
            )
        )
        feedback = result.scalar_one_or_none()
        
        if not feedback:
            raise HTTPException(status_code=404, detail="Token de reenvio inválido ou expirado")
        
        result = await db.execute(
            select(Candidate).where(Candidate.id == uuid.UUID(candidate_id))
        )
        candidate = result.scalar_one_or_none()
        
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidato não encontrado")
        
        result = await db.execute(
            select(JobVacancy).where(JobVacancy.id == vacancy_id)
        )
        vacancy = result.scalar_one_or_none()
        
        if not vacancy:
            raise HTTPException(status_code=404, detail="Vaga não encontrada")
        
        cv_content = await cv_file.read()
        parsed_cv = await cv_parser_service.parse_cv(
            file_content=cv_content,
            filename=cv_file.filename
        )
        
        if parsed_cv.get("skills"):
            candidate.technical_skills = list(set(
                (candidate.technical_skills or []) + parsed_cv.get("skills", [])
            ))
        if parsed_cv.get("experience_years"):
            candidate.years_of_experience = parsed_cv.get("experience_years")
        if parsed_cv.get("current_title"):
            candidate.current_title = parsed_cv.get("current_title")
        
        candidate.updated_at = datetime.utcnow()
        
        vacancy_requirements = {
            "query": vacancy.title or "",
            "skills": vacancy.required_skills or [],
            "experience_years": vacancy.min_experience_years,
            "seniority": vacancy.seniority_level,
            "location": vacancy.location_city
        }
        
        candidate_profile = {
            "skills": candidate.technical_skills or [],
            "experience_years": candidate.years_of_experience,
            "current_title": candidate.current_title,
            "location": candidate.location_city,
            "seniority": candidate.seniority_level
        }
        
        score_result = lia_score_service.calculate_score(
            candidate=candidate_profile,
            search_criteria=vacancy_requirements
        )
        
        new_adherence_score = score_result.score
        previous_score = feedback.adherence_score or 0
        improvement = new_adherence_score - previous_score
        
        candidate.lia_score = new_adherence_score
        candidate.skills_match_percentage = score_result.breakdown.skills_match
        candidate.lia_insights = score_result.to_dict()
        
        await candidate_feedback_service.mark_resubmit_completed(
            feedback_id=feedback.id,
            new_adherence_score=new_adherence_score,
            db=db
        )
        
        qualified = new_adherence_score >= candidate_feedback_service.ADHERENCE_THRESHOLD
        
        if qualified:
            existing_assignment = await db.execute(
                select(VacancyCandidate).where(
                    VacancyCandidate.vacancy_id == uuid.UUID(vacancy_id),
                    VacancyCandidate.candidate_id == candidate.id
                )
            )
            if not existing_assignment.scalar_one_or_none():
                if not vacancy.company_id:
                    raise HTTPException(status_code=400, detail="Vacancy has no company_id. Cannot process resubmission without tenant.")
                vacancy_candidate = VacancyCandidate(
                    id=uuid.uuid4(),
                    vacancy_id=uuid.UUID(vacancy_id),
                    candidate_id=candidate.id,
                    company_id=vacancy.company_id,
                    source="resubmission",
                    lia_score=new_adherence_score,
                    match_percentage=score_result.breakdown.skills_match,
                    status="applied",
                    stage="initial"
                )
                db.add(vacancy_candidate)
            
            await notification_service.create_notification(
                user_id="default_user",
                title="🎯 Candidato melhorou perfil e qualificou!",
                message=f"{candidate.name} reenviou CV e agora tem aderência de {new_adherence_score:.0f}% "
                        f"(+{improvement:.0f}% de melhoria)",
                notification_type=NotificationType.SUCCESS,
                category="resubmission_qualified",
                related_job_id=vacancy_id,
                related_candidate_id=candidate_id,
                action_url=f"/candidates/{candidate_id}",
                action_label="Ver Candidato",
                db=db
            )
            
            message = f"Parabéns! Sua nova aderência é {new_adherence_score:.0f}%. Você avançará para a próxima etapa!"
        else:
            message = f"Obrigado pelo reenvio! Sua aderência melhorou para {new_adherence_score:.0f}%, mas ainda está abaixo do mínimo necessário."
        
        await db.commit()
        
        return ResubmitResponseDTO(
            status="resubmitted",
            candidate_id=candidate_id,
            vacancy_id=vacancy_id,
            new_adherence_score=new_adherence_score,
            previous_adherence_score=previous_score,
            improvement=improvement,
            message=message,
            qualified=qualified
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing CV resubmission: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao processar reenvio: {str(e)}")


@router.get("/feedback/{vacancy_id}/analytics", response_model=FeedbackAnalyticsDTO)
async def get_feedback_analytics(
    vacancy_id: str,
    days: int = Query(30, ge=1, le=365, description="Período em dias"),
    db: AsyncSession = Depends(get_db)
):
    """
    Retorna analytics sobre feedbacks enviados para uma vaga.
    
    Métricas incluídas:
    - Total de feedbacks enviados
    - Taxa de cliques no reenvio
    - Taxa de conclusão de reenvio
    - Melhoria média de score
    """
    try:
        analytics = await candidate_feedback_service.get_feedback_analytics(
            vacancy_id=vacancy_id,
            days=days,
            db=db
        )
        
        return FeedbackAnalyticsDTO(**analytics)
        
    except Exception as e:
        logger.error(f"Error getting feedback analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao obter analytics: {str(e)}")


@router.post("/feedback/{feedback_id}/track-click")
async def track_resubmit_click(
    feedback_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Registra clique no link de reenvio de CV."""
    try:
        success = await candidate_feedback_service.mark_resubmit_clicked(
            feedback_id=feedback_id,
            db=db
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Feedback não encontrado")
        
        return {"status": "tracked", "feedback_id": feedback_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error tracking click: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao registrar clique: {str(e)}")

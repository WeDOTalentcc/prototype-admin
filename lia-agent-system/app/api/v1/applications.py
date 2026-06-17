"""
Applications API - Endpoints for candidate applications to job vacancies.

This module handles:
1. Candidate application submission
2. Automatic adherence score calculation
3. Automatic feedback for low adherence candidates
4. CV resubmission handling
"""
import logging
import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel, EmailStr, Field

from app.domains.recruitment.dependencies import get_application_repo
from app.domains.recruitment.repositories.application_repository import ApplicationRepository
from app.domains.cv_screening.services.cv_parser import CVParserService, cv_parser_service, get_cv_parser_service
from app.domains.cv_screening.services.rubric_evaluation_service import RubricEvaluationService, rubric_evaluation_service, get_rubric_evaluation_service
from app.schemas.rubric import JobRequirementCreate, RequirementPriorityEnum
from app.domains.candidates.services.candidate_feedback_service import candidate_feedback_service
from app.domains.cv_screening.services.lia_score_service import lia_score_service
from app.services.notification_service import NotificationType, notification_service
from app.shared.security.require_company_id import require_company_id
from app.shared.errors import LIAError
from app.shared.types import WeDoBaseModel
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN

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



class CandidateApplicationRequest(WeDoBaseModel):
    """Request para inscricao de candidato em uma vaga."""
    name: str = Field(..., description="Nome completo do candidato")
    email: EmailStr = Field(..., description="Email do candidato")
    phone: str | None = Field(None, description="Telefone do candidato")
    linkedin_url: str | None = Field(None, description="URL do LinkedIn")
    current_title: str | None = Field(None, description="Cargo atual")
    current_company: str | None = Field(None, description="Empresa atual")
    years_of_experience: int | None = Field(None, description="Anos de experiencia")
    technical_skills: list[str] = Field(default_factory=list, description="Habilidades tecnicas")
    location: str | None = Field(None, description="Localizacao")
    salary_expectation: float | None = Field(None, description="Pretensao salarial")
    cover_letter: str | None = Field(None, description="Carta de apresentacao")


class ApplicationResponseDTO(BaseModel):
    """Response da inscricao."""
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
    vacancy_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    application: CandidateApplicationRequest,
    cv_file: UploadFile | None = File(None),
    repo: ApplicationRepository = Depends(get_application_repo),
    cv_parser_svc: CVParserService = Depends(get_cv_parser_service),
    rubric_svc: RubricEvaluationService = Depends(get_rubric_evaluation_service),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Processa inscricao de candidato em uma vaga.

    Workflow:
    1. Criar/atualizar candidato no banco
    2. Calcular score de aderencia usando LIA Score Service
    3. Se aderencia < 50%: enviar feedback automatico
    4. Se aderencia >= 50%: adicionar ao pipeline de selecao

    Returns:
        ApplicationResponseDTO com status da inscricao e proximos passos
    """
    try:
        vacancy = await repo.get_vacancy_by_id(vacancy_id)

        if not vacancy:
            raise HTTPException(status_code=404, detail=f"Vaga {vacancy_id} nao encontrada")

        if vacancy.status not in ["open", "active", "published"]:
            raise HTTPException(status_code=400, detail="Esta vaga nao esta aberta para candidaturas")

        candidate_data = application.model_dump()

        if cv_file:
            try:
                cv_content = await cv_file.read()
                parsed_cv = await cv_parser_svc.parse_cv(
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

        existing_candidate = await repo.get_candidate_by_email(application.email)

        if existing_candidate:
            candidate = await repo.update_candidate_from_data(existing_candidate, candidate_data)
        else:
            candidate = await repo.create_candidate(candidate_data)

        await repo.flush()

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

        # WT-2022 P0.C: LGPD Art. 20 audit trail para decisao automatizada de score apply-time
        try:
            from app.shared.services.automated_decision_logger import (
                PROTECTED_CRITERIA_PT,
                log_automated_decision,
            )
            await log_automated_decision(
                db=repo.db,
                company_id=company_id,
                candidate_id=str(candidate.id) if candidate.id else None,
                job_id=str(vacancy_id),
                decision_type="apply_lia_score",
                ai_model_used="lia_score_service_deterministic",
                explanation_text=(
                    f"Apply-time LIA score={adherence_score:.2f} (skills_match="
                    f"{score_result.breakdown.skills_match:.2f}). "
                    f"Matched skills={len(matched_skills)}; missing={len(missing_skills)}."
                ),
                criteria_used=["skills_match", "experience_years", "current_title", "location"],
                criteria_ignored=PROTECTED_CRITERIA_PT,
                confidence_score=float(adherence_score) / 100.0 if adherence_score else None,
                review_eligible=True,
            )
        except Exception as _audit_exc:  # fail-safe: log gap nao bloqueia apply
            logger.warning("WT-2022 P0.C: apply lia_score audit log failed: %s", _audit_exc)

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
                db=repo.db
            )

            return ApplicationResponseDTO(
                status="low_adherence",
                candidate_id=str(candidate.id),
                vacancy_id=vacancy_id,
                adherence_score=adherence_score,
                feedback_sent=feedback_result["feedback_sent"],
                feedback_channels=feedback_result.get("channels_used", []),
                resubmit_url=feedback_result.get("resubmit_url"),
                message="Obrigado pela candidatura! Enviamos um feedback com sugestoes para aumentar suas chances.",
                next_step="improve_profile"
            )

        existing_vc = await repo.get_vacancy_candidate(vacancy_id, candidate.id)
        if not existing_vc:
            import secrets as _secrets
            screening_token = _secrets.token_urlsafe(32)

            is_saturated = False
            try:
                company_id = vacancy.company_id
                if not company_id:
                    logger.warning(f"Vacancy {vacancy_id} has no company_id set")
                threshold_web = await repo.get_company_threshold(company_id, default_threshold=20)

                governance = vacancy.governance_rules or {} if hasattr(vacancy, "governance_rules") else {}
                threshold_web = governance.get("threshold_web", threshold_web)

                organic_count = await repo.count_organic_candidates(
                    vacancy_id, excluded_statuses=("rejected", "declined", "withdrawn")
                )
                is_saturated = organic_count >= threshold_web
            except Exception as sat_err:
                logger.warning(f"Saturation check in applications failed, allowing application: {sat_err}")
                is_saturated = False

            candidate_status = "awaiting_screening" if is_saturated else "applied"

            if not vacancy.company_id:
                raise HTTPException(status_code=400, detail="Vacancy has no company_id. Cannot process application without tenant.")
            await repo.create_vacancy_candidate(
                vacancy_id=vacancy_id,
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

            # Agent Studio Fase 2.5 — Onda C1.3: emite candidate_applied no
            # platform.events para o motor event-driven (deployments on_apply).
            # REGRA 4: fail-soft mas LOUD — falha de publish NAO quebra o apply
            # do candidato, mas e logada com exc_info (nunca silenciada).
            # Multi-tenancy: company_id vem de vacancy.company_id (contexto do
            # tenant), NUNCA do payload do request.
            try:
                from lia_events.schemas import CandidateAppliedEvent
                from app.shared.messaging.events_outbox_service import get_events_outbox_service
                from lia_config.database import AsyncSessionLocal
                _evt = CandidateAppliedEvent(
                    company_id=str(vacancy.company_id),
                    payload={
                        "candidate_id": str(candidate.id),
                        "vacancy_id": str(vacancy_id),
                    },
                    source_api="lia-agent-system",
                )
                async with AsyncSessionLocal() as _evt_db:
                    await get_events_outbox_service().publish_via_outbox(_evt, _evt_db)
                    await _evt_db.commit()
            except Exception as _evt_err:  # noqa: BLE001  # REGRA-4-EXEMPT: event dispatch é best-effort, apply prossegue
                logger.error(
                    "[C1.3] publish candidate_applied outbox failed (apply prossegue): %s",
                    type(_evt_err).__name__,
                    exc_info=True,
                )

        _cand_name = candidate_data["name"]
        _vac_title = vacancy.title
        await notification_service.create_notification(
            user_id="default_user",
            title="Nova candidatura qualificada",
            message=f"{_cand_name} aplicou para {_vac_title} com aderencia de {adherence_score:.0f}%",
            notification_type=NotificationType.SUCCESS,
            category="new_application",
            related_job_id=vacancy_id,
            related_candidate_id=str(candidate.id),
            action_url=f"/candidates/{candidate.id}",
            action_label="Ver Candidato",
            db=repo.db
        )

        try:
            job_requirements = await repo.get_job_requirements(vacancy_id)

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

                await rubric_svc.evaluate_and_create_activity(
                    candidate_id=str(candidate.id),
                    candidate_name=candidate_data.get("name", "Candidato"),
                    candidate_data=application_candidate_data,
                    job_id=vacancy_id,
                    job_title=vacancy.title or "Vaga",
                    job_code=getattr(vacancy, "code", None) or getattr(vacancy, "job_code", None),
                    requirements=requirements_list,
                    company_id=vacancy.company_id,
                    created_by="application",
                )
        except Exception as rubric_err:
            logger.warning(f"Rubric evaluation failed for application: {rubric_err}")

        return ApplicationResponseDTO(
            status="accepted",
            candidate_id=str(candidate.id),
            vacancy_id=vacancy_id,
            adherence_score=adherence_score,
            feedback_sent=False,
            message="Candidatura recebida com sucesso! Voce avancara para a proxima etapa do processo.",
            next_step="pending_gate1",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing application: {e}")
        await repo.rollback()
        raise LIAError(message="Erro interno do servidor")


@router.post("/resubmit/{vacancy_id}", response_model=ResubmitResponseDTO)
async def resubmit_cv(
    vacancy_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    candidate_id: str = Query(..., description="ID do candidato"),
    token: str = Query(..., description="Token de reenvio"),
    cv_file: UploadFile = File(..., description="Curriculo atualizado"),
    repo: ApplicationRepository = Depends(get_application_repo)
,
    cv_parser_svc: CVParserService = Depends(get_cv_parser_service),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Processa reenvio de CV apos feedback de baixa aderencia.

    Workflow:
    1. Validar token de reenvio
    2. Atualizar perfil do candidato com novos dados do CV
    3. Recalcular score de aderencia
    4. Registrar melhoria no feedback original
    5. Se novo score >= 50%: adicionar ao pipeline
    """
    try:
        feedback = await repo.get_feedback_by_token(candidate_id, vacancy_id, token)

        if not feedback:
            raise HTTPException(status_code=404, detail="Token de reenvio invalido ou expirado")

        candidate = await repo.get_candidate_by_id(candidate_id)

        if not candidate:
            raise HTTPException(status_code=404, detail="Candidato nao encontrado")

        vacancy = await repo.get_vacancy_by_id(vacancy_id)

        if not vacancy:
            raise HTTPException(status_code=404, detail="Vaga nao encontrada")

        cv_content = await cv_file.read()
        parsed_cv = await cv_parser_svc.parse_cv(
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

        # WT-2022 P0.C: LGPD Art. 20 audit trail para decisao automatizada de score em resubmit
        try:
            from app.shared.services.automated_decision_logger import (
                PROTECTED_CRITERIA_PT,
                log_automated_decision,
            )
            await log_automated_decision(
                db=repo.db,
                company_id=company_id,
                candidate_id=str(candidate.id) if candidate.id else None,
                job_id=str(vacancy_id),
                decision_type="resubmit_lia_score",
                ai_model_used="lia_score_service_deterministic",
                explanation_text=(
                    f"Resubmit LIA score={new_adherence_score:.2f} (anterior="
                    f"{previous_score:.2f}, melhoria={improvement:+.2f}, skills_match="
                    f"{score_result.breakdown.skills_match:.2f})."
                ),
                criteria_used=["skills_match", "experience_years", "current_title", "location", "seniority"],
                criteria_ignored=PROTECTED_CRITERIA_PT,
                confidence_score=float(new_adherence_score) / 100.0 if new_adherence_score else None,
                review_eligible=True,
            )
        except Exception as _audit_exc:  # fail-safe
            logger.warning("WT-2022 P0.C: resubmit lia_score audit log failed: %s", _audit_exc)

        await candidate_feedback_service.mark_resubmit_completed(
            feedback_id=feedback.id,
            new_adherence_score=new_adherence_score,
            db=repo.db
        )

        qualified = new_adherence_score >= candidate_feedback_service.ADHERENCE_THRESHOLD

        if qualified:
            existing_vc = await repo.get_vacancy_candidate(vacancy_id, candidate.id)
            if not existing_vc:
                if not vacancy.company_id:
                    raise HTTPException(status_code=400, detail="Vacancy has no company_id. Cannot process resubmission without tenant.")
                await repo.create_vacancy_candidate(
                    vacancy_id=vacancy_id,
                    candidate_id=candidate.id,
                    company_id=vacancy.company_id,
                    source="resubmission",
                    lia_score=new_adherence_score,
                    match_percentage=score_result.breakdown.skills_match,
                    status="applied",
                    stage="initial",
                )

            _cand_name_resub = candidate.name
            await notification_service.create_notification(
                user_id="default_user",
                title="Candidato melhorou perfil e qualificou!",
                message=f"{_cand_name_resub} reenviou CV e agora tem aderencia de {new_adherence_score:.0f}% (+{improvement:.0f}% de melhoria)",
                notification_type=NotificationType.SUCCESS,
                category="resubmission_qualified",
                related_job_id=vacancy_id,
                related_candidate_id=candidate_id,
                action_url=f"/candidates/{candidate_id}",
                action_label="Ver Candidato",
                db=repo.db
            )

            message = f"Parabens! Sua nova aderencia e {new_adherence_score:.0f}%. Voce avancara para a proxima etapa!"
        else:
            message = f"Obrigado pelo reenvio! Sua aderencia melhorou para {new_adherence_score:.0f}%, mas ainda esta abaixo do minimo necessario."

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
        await repo.rollback()
        raise LIAError(message="Erro interno do servidor")


@router.get("/feedback/{vacancy_id}/analytics", response_model=FeedbackAnalyticsDTO)
async def get_feedback_analytics(
    vacancy_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    days: int = Query(30, ge=1, le=365, description="Periodo em dias"),
    repo: ApplicationRepository = Depends(get_application_repo), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Retorna analytics sobre feedbacks enviados para uma vaga.

    Metricas incluidas:
    - Total de feedbacks enviados
    - Taxa de cliques no reenvio
    - Taxa de conclusao de reenvio
    - Melhoria media de score
    """
    try:
        analytics = await candidate_feedback_service.get_feedback_analytics(
            vacancy_id=vacancy_id,
            days=days,
            db=repo.db
        )

        return FeedbackAnalyticsDTO(**analytics)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting feedback analytics: {e}")
        raise LIAError(message="Erro interno do servidor")


@router.post("/feedback/{feedback_id}/track-click", response_model=None)
async def track_resubmit_click(
    feedback_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    repo: ApplicationRepository = Depends(get_application_repo), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Registra clique no link de reenvio de CV."""
    try:
        success = await candidate_feedback_service.mark_resubmit_clicked(
            feedback_id=feedback_id,
            db=repo.db
        )

        if not success:
            raise HTTPException(status_code=404, detail="Feedback nao encontrado")

        return {"status": "tracked", "feedback_id": feedback_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error tracking click: {e}")
        raise LIAError(message="Erro interno do servidor")



async def _require_auth_401():
    """FastAPI dependency: raises HTTP 401 if not authenticated.

    Backward-compat: used as a dependency_override target in tests.
    In production the dependency override is replaced with the real
    get_current_active_user so that all endpoints inherit the same auth
    chain without explicitly importing from app.auth.dependencies.
    """
    raise HTTPException(status_code=401, detail="Not authenticated")

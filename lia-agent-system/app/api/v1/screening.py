import logging
import uuid as uuid_mod

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_active_user, get_user_company_id
from app.auth.models import User
from app.core.config import settings
from app.core.database import get_db
from app.domains.cv_screening.dependencies import get_screening_repo, WSIService, get_wsi_service
from app.domains.cv_screening.repositories.screening_repository import ScreeningRepository
from app.models.screening import ScreeningTask
from app.schemas.screening import (
    RegenerateQuestionsRequest,
    ScreeningQuestion,
    ScreeningQuestionRequest,
    ScreeningQuestionResponse,
)
from app.shared.security.require_company_id import require_company_id
from app.shared.errors import LIAError, LIAInternalError
from app.shared.services.automated_decision_logger import (
    PROTECTED_CRITERIA_PT,
    log_automated_decision,
)
from app.shared.types import WeDoBaseModel
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/screening", tags=["screening"])


class AutoScreeningRequest(WeDoBaseModel):
    candidate_id: str
    job_id: str
    source: str
    resume_text: str | None = None
    resume_url: str | None = None


def _wsi_questions_to_screening_response(wsi_questions, request) -> ScreeningQuestionResponse:
    """Convert WSIQuestion list from canonical generator to ScreeningQuestionResponse."""
    from app.domains.cv_screening.constants.wsi_constants import (
        BLOOM_LEVEL_LABELS,
        DREYFUS_STAGE_LABELS,
        SENIORITY_TO_BLOOM,
        SENIORITY_TO_DREYFUS,
    )
    all_questions = []
    behavioral_questions = []
    technical_questions = []
    cultural_questions = []

    for idx, wq in enumerate(wsi_questions):
        # F6.O5: cultural_questions sempre vazio. Root cause upstream:
        #   - WSIQuestion (services/wsi_service/models.py:138) NAO tem field competency_type
        #   - question_generator.py:242 funde Competency(type=cultural) no bucket behavioral antes
        #     de gerar WSIQuestion, perdendo a origem cultural
        #   - generate_from_simple_inputs (service.py:204) nao aceita parametro cultural
        # Fix correto exige mudanca upstream: adicionar competency_type ao WSIQuestion e
        # propagar pelo question_generator. Veja tambem F6.O3 (behavioral=[] hardcoded
        # em screening.py:117 abaixo, que reforca o mesmo gap).
        # Defesa em profundidade: SE WSIQuestion futuramente expor competency_type ou
        # competency_obj.type, categorizar como cultural (prioridade sobre behavioral).
        _comp_type = getattr(wq, "competency_type", None)
        if _comp_type is None:
            _comp_obj = getattr(wq, "competency_obj", None)
            if _comp_obj is not None:
                _comp_type = getattr(_comp_obj, "type", None)
        is_cultural = _comp_type == "cultural"
        is_behavioral = (wq.framework == "BigFive" or wq.question_type == "situational") and not is_cultural
        category = "cultural" if is_cultural else ("behavioral" if is_behavioral else "technical")
        bloom_level = wq.scoring_criteria.get("bloom_level", 3) if isinstance(wq.scoring_criteria, dict) else 3
        if not isinstance(bloom_level, int):
            try:
                bloom_level = int(bloom_level)
            except (ValueError, TypeError):
                bloom_level = 3
        dreyfus_stage = SENIORITY_TO_DREYFUS.get(request.seniority or "pleno", 3)
        bloom_info = BLOOM_LEVEL_LABELS.get(bloom_level, BLOOM_LEVEL_LABELS.get(3, {}))
        dreyfus_info = DREYFUS_STAGE_LABELS.get(dreyfus_stage, DREYFUS_STAGE_LABELS.get(3, {}))

        sq = ScreeningQuestion(
            id=wq.id,
            text=wq.question_text,
            category=category,
            trait=wq.scoring_criteria.get("ocean_trait") if isinstance(wq.scoring_criteria, dict) else None,
            skill=wq.competency if category == "technical" else None,
            bloom_level=bloom_level,
            bloom_label=bloom_info if isinstance(bloom_info, str) else "Aplicar",
            dreyfus_stage=dreyfus_stage,
            dreyfus_label=dreyfus_info if isinstance(dreyfus_info, str) else "Competente",
            framework=wq.framework,
            weight=wq.weight,
            expected_signals=wq.expected_signals,
            scoring_criteria=wq.scoring_criteria if isinstance(wq.scoring_criteria, dict) else {},
            is_selected=True,
            question_type="open",
            order=idx,
        )
        all_questions.append(sq)
        if category == "cultural":
            cultural_questions.append(sq)
        elif category == "behavioral":
            behavioral_questions.append(sq)
        else:
            technical_questions.append(sq)

    seniority = request.seniority or "pleno"
    return ScreeningQuestionResponse(
        questions=all_questions,
        behavioral_questions=behavioral_questions,
        technical_questions=technical_questions,
        cultural_questions=cultural_questions,
        total_count=len(all_questions),
        metadata={
            "seniority": seniority,
            "dreyfus_stage": SENIORITY_TO_DREYFUS.get(seniority, 3),
            "bloom_levels": SENIORITY_TO_BLOOM.get(seniority, [3, 4]),
            "skills_count": len(request.skills) if request.skills else 0,
            "title": request.title,
            "department": request.department,
            "generator": "wsi_service_canonical_f6",
        }
    )


@router.post("/questions", response_model=ScreeningQuestionResponse)
async def generate_screening_questions(
    request: ScreeningQuestionRequest,
    current_user: User = Depends(get_current_active_user),
    wsi_svc: WSIService = Depends(get_wsi_service),
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)) -> ScreeningQuestionResponse:
    try:
        company_id = get_user_company_id(current_user)
        logger.info(f"Generating screening questions for: {request.title} ({request.seniority}) - company: {company_id}, user: {current_user.id}")

        mode = "full" if request.question_count > 10 else "compact"
        wsi_questions = await wsi_svc.generate_from_simple_inputs(
            skills=request.skills or [],
            behavioral=request.behavioral_competencies or [],
            seniority=request.seniority or "pleno",
            job_description=request.job_description,
            mode=mode,
            max_questions=request.question_count,
        )

        response = _wsi_questions_to_screening_response(wsi_questions, request)

        # F6.O2 fix (audit 2026-05-20): contrato API expõe cap quando count solicitado
        # > total_count devolvido (le=15 no schema mas distribuição canonical max=12).
        # Sem isso, frontend acredita que recebeu N perguntas quando recebeu menos.
        if request.question_count and response.total_count < request.question_count:
            if not hasattr(response, "metadata") or response.metadata is None:
                response.metadata = {}
            response.metadata["cap_applied"] = True
            response.metadata["requested_count"] = request.question_count
            response.metadata["returned_count"] = response.total_count

        logger.info(f"Generated {response.total_count} questions: "
                   f"{len(response.behavioral_questions)} behavioral, "
                   f"{len(response.technical_questions)} technical, "
                   f"{len(response.cultural_questions)} cultural")

        # WT-2022 P0.C wave 2 / LGPD Art. 20 + EU AI Act Art. 13 — audit trail.
        # Cobre /screening/questions (handler high-level, distinto de /wsi/generate-questions
        # que cobre o pipeline interno). Ambos ficam logados — board de transparência
        # mostra a decisao IA independente do endpoint usado pelo cliente.
        try:
            seniority = request.seniority or "pleno"
            await log_automated_decision(
                db=db,
                company_id=company_id,
                decision_type="wsi_simple_inputs",
                ai_model_used=getattr(settings, "LLM_PRIMARY_MODEL", "claude-sonnet-4-6"),
                explanation_text=(
                    f'Gerou {response.total_count} pergunta(s) de triagem para a vaga '
                    f'"{request.title}" (senioridade={seniority}, mode={mode}) via '
                    "pipeline canonical wsi_service.generate_from_simple_inputs (CBI + Bloom + "
                    "Dreyfus + BigFive). Skills tecnicos: "
                    f'{request.skills or []}. Competencias comportamentais: '
                    f'{request.behavioral_competencies or []}.'
                ),
                criteria_used=[
                    *[f"skill:{s}" for s in (request.skills or [])],
                    *[f"behavioral:{b}" for b in (request.behavioral_competencies or [])],
                    f"seniority:{seniority}",
                    f"mode:{mode}",
                ],
                criteria_ignored=list(PROTECTED_CRITERIA_PT),
                confidence_score=None,
                review_eligible=True,
                extra_metadata={
                    "endpoint": "/screening/questions",
                    "title": request.title,
                    "department": request.department,
                    "questions_count": response.total_count,
                    "behavioral_count": len(response.behavioral_questions),
                    "technical_count": len(response.technical_questions),
                    "cultural_count": len(response.cultural_questions),
                    "requested_count": request.question_count,
                    "mode": mode,
                    "seniority": seniority,
                    "prompt_template_version": "wsi_F6_pipeline_v2",
                    "llm_model": getattr(settings, "LLM_PRIMARY_MODEL", "claude-sonnet-4-6"),
                },
            )
        except ValueError:
            # Compliance gate raised — protected criteria leaked.
            # Re-raise fail-loud per CLAUDE.md REGRA #2 (LGPD).
            raise
        except Exception as audit_err:
            # Audit gap — log e segue (decisao IA nao deve ser bloqueada).
            logger.error(
                "WT-2022 P0.C wave 2: log_automated_decision falhou em /screening/questions "
                "(LGPD Art. 20 audit gap, title=%s, company=%s): %s",
                request.title, company_id, audit_err, exc_info=True,
            )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating screening questions: {e}")
        raise LIAInternalError("Internal server error")


@router.post("/questions/regenerate", response_model=list[ScreeningQuestion])
async def regenerate_questions(
    request: RegenerateQuestionsRequest,
    current_user: User = Depends(get_current_active_user),
    wsi_svc: WSIService = Depends(get_wsi_service),
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)) -> list[ScreeningQuestion]:
    try:
        company_id = get_user_company_id(current_user)
        logger.info(f"Regenerating questions for: {request.context.title} - company: {company_id}, user: {current_user.id}")

        wsi_questions = await wsi_svc.generate_from_simple_inputs(
            skills=request.context.skills or [],
            behavioral=[],
            seniority=request.context.seniority or "pleno",
            job_description=request.context.job_description,
            mode="compact",
        )

        response = _wsi_questions_to_screening_response(wsi_questions, request.context)

        if request.category:
            filtered = [q for q in response.questions if q.category == request.category]
            if request.exclude_ids:
                filtered = [q for q in filtered if q.id not in request.exclude_ids]
            logger.info(f"Regenerated {len(filtered)} {request.category} questions")
            final_questions = filtered
        else:
            logger.info(f"Regenerated all {len(response.questions)} questions")
            final_questions = response.questions

        # WT-2022 P0.C wave 2 / LGPD Art. 20 + EU AI Act Art. 13.
        # Regenerate gera questions novas via IA — cada chamada produz decisao
        # automatizada e precisa de audit trail equivalente ao generate.
        try:
            seniority = request.context.seniority or "pleno"
            await log_automated_decision(
                db=db,
                company_id=company_id,
                decision_type="wsi_simple_inputs",
                ai_model_used=getattr(settings, "LLM_PRIMARY_MODEL", "claude-sonnet-4-6"),
                explanation_text=(
                    f'Regenerou {len(final_questions)} pergunta(s) de triagem para a vaga '
                    f'"{request.context.title}" (senioridade={seniority}, mode=compact, '
                    f'category_filter={request.category}) via wsi_service.generate_from_simple_inputs. '
                    f'Skills tecnicos: {request.context.skills or []}.'
                ),
                criteria_used=[
                    *[f"skill:{s}" for s in (request.context.skills or [])],
                    f"seniority:{seniority}",
                    "mode:compact",
                    *([f"category:{request.category}"] if request.category else []),
                ],
                criteria_ignored=list(PROTECTED_CRITERIA_PT),
                confidence_score=None,
                review_eligible=True,
                extra_metadata={
                    "endpoint": "/screening/questions/regenerate",
                    "title": request.context.title,
                    "questions_count": len(final_questions),
                    "category_filter": request.category,
                    "exclude_ids_count": len(request.exclude_ids or []),
                    "mode": "compact",
                    "seniority": seniority,
                    "operation": "regenerate",
                    "prompt_template_version": "wsi_F6_pipeline_v2",
                    "llm_model": getattr(settings, "LLM_PRIMARY_MODEL", "claude-sonnet-4-6"),
                },
            )
        except ValueError:
            raise
        except Exception as audit_err:
            logger.error(
                "WT-2022 P0.C wave 2: log_automated_decision falhou em /screening/questions/regenerate "
                "(LGPD Art. 20 audit gap, title=%s, company=%s): %s",
                request.context.title, company_id, audit_err, exc_info=True,
            )

        return final_questions

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error regenerating questions: {e}")
        raise LIAInternalError("Internal server error")


@router.get("/frameworks", response_model=None)
async def get_screening_frameworks(
    current_user: User = Depends(get_current_active_user), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    from app.api.v1.wsi._shared import BLOOM_LEVELS as BLOOM_RICH
    from app.api.v1.wsi._shared import DREYFUS_LEVELS as DREYFUS_RICH
    from app.domains.cv_screening.constants.wsi_constants import (
        BLOOM_LEVEL_LABELS,
        DREYFUS_STAGE_LABELS,
        SENIORITY_TO_BLOOM,
        SENIORITY_TO_DREYFUS,
    )

    return {
        "bloom_levels": {
            k: {"label": BLOOM_LEVEL_LABELS[k], "description": BLOOM_RICH[k]["description"]}
            for k in BLOOM_LEVEL_LABELS
        },
        "dreyfus_stages": {
            k: {"label": DREYFUS_STAGE_LABELS[k], "description": DREYFUS_RICH[k]["description"]}
            for k in DREYFUS_STAGE_LABELS
        },
        "big_five_traits": {
            "openness": {"label": "Abertura", "description": "Criatividade, curiosidade, inovacao"},
            "conscientiousness": {"label": "Conscienciosidade", "description": "Organizacao, responsabilidade, disciplina"},
            "extraversion": {"label": "Extraversao", "description": "Sociabilidade, energia, assertividade"},
            "agreeableness": {"label": "Amabilidade", "description": "Cooperacao, empatia, harmonia"},
            "stability": {"label": "Estabilidade", "description": "Calma, resiliencia, equilibrio emocional"}
        },
        "seniority_mapping": {
            k: {"dreyfus": SENIORITY_TO_DREYFUS[k], "bloom_range": SENIORITY_TO_BLOOM[k]}
            for k in SENIORITY_TO_DREYFUS
        }
    }


@router.post("/auto-trigger", status_code=202, response_model=None)
async def auto_trigger_screening(
    request: AutoScreeningRequest,
    current_user: User = Depends(get_current_active_user),
    repo: ScreeningRepository = Depends(get_screening_repo),
    company_id: str = Depends(require_company_id),
):
    # multi-tenancy: company_id from JWT via require_company_id (canonical)
    # current_user ensures the caller is authenticated and active
    _ = get_user_company_id(current_user)  # defense-in-depth: validate user has company
    if request.source != "website":
        raise HTTPException(
            status_code=400,
            detail="Auto-screening only processes applications with source 'website'"
        )

    try:
        task = ScreeningTask(
            candidate_id=request.candidate_id,
            job_id=request.job_id,
            company_id=company_id,
            status="pending",
            source=request.source,
            resume_text=request.resume_text,
            resume_url=request.resume_url,
        )
        task = await repo.create_task(task)

        logger.info(
            f"Auto-screening task created: {task.id} for candidate={request.candidate_id} "
            f"job={request.job_id} company={company_id}"
        )

        return JSONResponse(
            status_code=202,
            content={"task_id": str(task.id), "status": "pending"},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create auto-screening task: {e}")
        await repo.rollback()
        raise LIAError(message="Failed to create screening task")


@router.get("/tasks/{job_id}", response_model=None)
async def list_screening_tasks(
    job_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    repo: ScreeningRepository = Depends(get_screening_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    try:
        tasks = await repo.list_tasks_by_job(job_id)
        return {"job_id": job_id, "tasks": [t.to_dict() for t in tasks], "total": len(tasks)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list screening tasks for job {job_id}: {e}")
        raise LIAError(message="Failed to list screening tasks")


@router.post("/tasks/{task_id}/execute", response_model=None)
async def execute_screening_task(
    task_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    repo: ScreeningRepository = Depends(get_screening_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    try:
        task_uuid = uuid_mod.UUID(task_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid task_id format")

    try:
        task = await repo.get_task_by_id(task_uuid)

        if not task:
            raise HTTPException(status_code=404, detail="Screening task not found")

        if task.status not in ("pending", "failed"):
            raise HTTPException(
                status_code=409,
                detail=f"Task cannot be executed in current status: {task.status}"
            )

        task = await repo.update_task_status(task, "processing")

        logger.info(f"Screening task {task_id} status updated to processing")

        return task.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to execute screening task {task_id}: {e}")
        await repo.rollback()
        raise LIAError(message="Failed to execute screening task")

reorder_collection_before_item(router)

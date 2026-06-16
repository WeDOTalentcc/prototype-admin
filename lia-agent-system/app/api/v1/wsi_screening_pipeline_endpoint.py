"""
WSI Screening Pipeline API - Unified endpoint for complete WSI screening question generation.

Orchestrates all WSI blocks:
- Block 1.5: Company default screening questions
- Block 2: WSI Eligibility (deduplicated)
- Block 3: Technical Assessment (Bloom/Dreyfus)
- Block 4: Behavioral/Situational (Big Five/CBI)
"""
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import (
    get_current_user_or_demo,
    get_user_company_id,
)
from app.auth.models import User
from app.core.config import settings
from app.core.database import get_db
from app.domains.cv_screening.services.wsi_screening_pipeline import wsi_screening_pipeline
from app.schemas.screening import (
    WSIScreeningPipelineRequest,
    WSIScreeningPipelineResponse,
)
from app.shared.security.require_company_id import require_company_id
from app.shared.errors import LIAError
from app.shared.services.automated_decision_logger import (
    PROTECTED_CRITERIA_PT,
    log_automated_decision,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/wsi", tags=["WSI Screening Pipeline"])


@router.post("/screening-pipeline", response_model=WSIScreeningPipelineResponse)
# TODO(phase2): extract to repository — WSI screening pipeline DB calls
async def generate_screening_pipeline(
    request: WSIScreeningPipelineRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)):
    """
    Generate unified WSI screening questions across all blocks.
    
    Fetches company questions from database and generates WSI questions
    using scientific frameworks (Big Five, Bloom, Dreyfus, CBI).
    """
    try:
        company_id = get_user_company_id(current_user)

        # Onda 2C.1 (audit 2026-06-06): a VAGA é a fonte da verdade da ação afirmativa.
        # Resolve is_affirmative/critério do banco server-side (não confia na flag do FE),
        # garantindo que marcar a vaga como afirmativa auto-habilita a pergunta de autodeclaração.
        if request.job_id:
            from app.models.job_vacancy import JobVacancy
            from app.domains.cv_screening.services.wsi_screening_pipeline import (
                criterion_to_affirmative_type,
            )
            job_row = (await db.execute(
                select(JobVacancy).where(  # ADR-001-EXEMPT: endpoint layer, leitura pontual p/ resolver ação afirmativa server-side
                    JobVacancy.id == request.job_id,
                    JobVacancy.company_id == company_id,
                )
            )).scalar_one_or_none()
            if job_row is not None and getattr(job_row, "is_affirmative", False):
                request.is_affirmative = True
                request.affirmative_type = criterion_to_affirmative_type(
                    getattr(job_row, "affirmative_criteria_primary", None)
                )

        company_questions_raw = []
        if request.include_company_questions:
            try:
                from app.models.screening_question import CompanyScreeningQuestion

                stmt = select(CompanyScreeningQuestion).where(  # ADR-001-EXEMPT: endpoint vive no api/v1 layer (não service), select é inline proposital — CompanyScreeningQuestionRepository não existia quando endpoint foi criado. Migrar para repo em sprint futura.
                    CompanyScreeningQuestion.company_id == company_id,
                    CompanyScreeningQuestion.is_active,
                ).order_by(CompanyScreeningQuestion.order)

                result = await db.execute(stmt)
                rows = result.scalars().all()

                for row in rows:
                    company_questions_raw.append({
                        "id": str(row.id),
                        "question_text": row.question_text,
                        "question_type": row.question_type or "text",
                        "options": row.options,
                        "is_required": row.is_required,
                        "is_eliminatory": row.is_eliminatory,
                        "expected_answer": row.expected_answer,
                        "category": row.category,
                        "order": row.order or 0,
                        "is_active": row.is_active,
                    })

                logger.info(
                    f"Fetched {len(company_questions_raw)} company questions for company {company_id}"
                )
            except Exception as e:
                logger.warning(f"Could not fetch company questions: {e}")
                company_questions_raw = []

        response = await wsi_screening_pipeline.build_pipeline(
            request=request,
            company_questions_raw=company_questions_raw,
        )

        logger.info(
            f"WSI Pipeline generated {response.total_count} questions "
            f"for '{request.job_title}' ({request.seniority}) - "
            f"company: {company_id}, user: {current_user.email}, "
            f"distribution: {response.block_distribution}, "
            f"is_affirmative: {request.is_affirmative}, "
            f"affirmative_type: {request.affirmative_type}"
        )

        # WT-2022 P0.C wave 2 / LGPD Art. 20 + EU AI Act Art. 13.
        # /api/v1/wsi/screening-pipeline e o entry-point unificado que invoca
        # _build_technical_block + _build_behavioral_block + Block 1.5 + Block 2.
        # Logamos UMA decisao agregada por chamada do pipeline — block-by-block
        # nao tem company_id em scope (sao helpers privados sem dep injection),
        # entao audit no endpoint cobre o fluxo completo per Art. 20.
        try:
            seniority = request.seniority or "pleno"
            await log_automated_decision(
                db=db,
                company_id=company_id,
                decision_type="wsi_screening_pipeline_iteration",
                ai_model_used=getattr(settings, "LLM_PRIMARY_MODEL", "claude-sonnet-4-6"),
                explanation_text=(
                    f'Pipeline WSI unificada gerou {response.total_count} pergunta(s) para "{request.job_title}" '
                    f'(senioridade={seniority}, format={request.format}). '
                    f'Distribuicao por bloco: {response.block_distribution}. '
                    f'Skills tecnicos: {request.technical_skills}. Comportamentais: {request.behavioral_competencies}. '
                    f'Affirmative_action={request.is_affirmative} (type={request.affirmative_type}). '
                    f'Frameworks ativos: Big Five (Block 4), Bloom/Dreyfus (Block 3), CBI (Block 4), eligibility (Block 2).'
                ),
                criteria_used=[
                    *[f"skill:{s}" for s in request.technical_skills],
                    *[f"behavioral:{b}" for b in request.behavioral_competencies],
                    f"seniority:{seniority}",
                    f"format:{request.format}",
                    f"department:{request.department or 'n/a'}",
                    *([f"affirmative:{request.affirmative_type}"] if request.is_affirmative else []),
                ],
                criteria_ignored=list(PROTECTED_CRITERIA_PT),
                confidence_score=None,
                review_eligible=True,
                extra_metadata={
                    "endpoint": "/api/v1/wsi/screening-pipeline",
                    "job_title": request.job_title,
                    "department": request.department,
                    "questions_count": response.total_count,
                    "block_distribution": response.block_distribution,
                    "company_questions_count": len(company_questions_raw),
                    "include_company_questions": request.include_company_questions,
                    "format": request.format,
                    "seniority": seniority,
                    "question_count_target": request.question_count,
                    "is_affirmative": request.is_affirmative,
                    "affirmative_type": request.affirmative_type,
                    "frameworks_used": ["BigFive", "Bloom", "Dreyfus", "CBI"],
                    "prompt_template_version": "wsi_F6_pipeline_v2",
                    "llm_model": getattr(settings, "LLM_PRIMARY_MODEL", "claude-sonnet-4-6"),
                },
            )
        except ValueError:
            raise
        except Exception as audit_err:
            logger.error(
                "WT-2022 P0.C wave 2: log_automated_decision falhou em /api/v1/wsi/screening-pipeline "
                "(LGPD Art. 20 audit gap, job_title=%s, company=%s): %s",
                request.job_title, company_id, audit_err, exc_info=True,
            )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in WSI screening pipeline: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")

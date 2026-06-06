"""
WSI package — question generation, suggestion, save, and version routes.

Routes:
  POST /generate-questions
  POST /suggest-question
  POST /questions/save
  GET  /question-sets/{job_id}/active
  GET  /question-sets/{job_id}/versions
  GET  /question-sets/{job_id}/version/{version}
  GET  /question-sets/{job_id}/consistency
"""
import json
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db, get_tenant_db
from app.domains.voice.repositories.wsi_repository import WsiRepository
from app.domains.cv_screening.dependencies import WSIService, get_wsi_service
from app.domains.cv_screening.services.screening_question_set_service import (
    ScreeningQuestionSetService,
    get_screening_question_set_service,
)

from ._shared import (
    BLOOM_LEVELS,
    GenerateQuestionsRequest,
    GenerateQuestionsResponse,
    SaveQuestionsRequest,
    SuggestQuestionRequest,
    WSIQuestionOutput,
    _run_anthropic_sync,
    get_anthropic_client,
    parse_json_response,
)
from app.shared.security.require_company_id import require_company_id
from app.shared.services.automated_decision_logger import (
    log_automated_decision,
    PROTECTED_CRITERIA_PT,
)
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

_FRAMEWORK_BLOOM_MAP = {
    "CBI": 4,
    "Bloom": 3,
    "Dreyfus": 2,
    "BigFive": 3,
}

_FRAMEWORK_CATEGORY_MAP = {
    "CBI": "technical",
    "Bloom": "technical",
    "Dreyfus": "technical",
    "BigFive": "behavioral",
}


@router.post("/generate-questions", response_model=GenerateQuestionsResponse)
async def generate_questions(
    request: GenerateQuestionsRequest,
    db: AsyncSession = Depends(get_tenant_db),
    sqs_svc: ScreeningQuestionSetService = Depends(get_screening_question_set_service),
    wsi_svc: WSIService = Depends(get_wsi_service),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Generate WSI screening questions using the canonical F6 pipeline
    (CBI + Bloom + Dreyfus + BigFive via WSIService).
    """
    session_id = f"wsi_text_{uuid.uuid4().hex[:12]}"

    job_title = request.job_title or "Professional"
    all_skills = request.skills or request.technical_skills or ["Problem Solving", "Communication"]
    behavioral = request.behavioral_competencies or []
    seniority = request.seniority_level or request.seniority or "pleno"
    description = request.description or ""
    requirements = request.requirements or request.responsibilities or []
    job_desc_parts = [description] if description else []
    if requirements:
        job_desc_parts.append("Responsabilidades: " + ", ".join(requirements))
    job_description = "\n".join(job_desc_parts) if job_desc_parts else None

    requested_count = request.max_questions or request.num_questions
    mode = "full" if requested_count > 10 else "compact"
    wsi_questions = await wsi_svc.generate_from_simple_inputs(
        skills=all_skills,
        behavioral=behavioral,
        seniority=seniority,
        job_description=job_description,
        mode=mode,
        max_questions=requested_count,
    )

    questions = []
    for idx, wq in enumerate(wsi_questions):
        question_id = f"q_{session_id}_{idx+1}"
        bloom_level = _FRAMEWORK_BLOOM_MAP.get(wq.framework, 3)
        category = _FRAMEWORK_CATEGORY_MAP.get(wq.framework, "technical")
        questions.append(WSIQuestionOutput(
            id=question_id,
            text=wq.question_text,
            bloom_level=bloom_level,
            bloom_level_name=BLOOM_LEVELS.get(bloom_level, BLOOM_LEVELS[3])["name"],
            skill_targeted=wq.competency,
            question_type=wq.question_type,
            block_id=3 if category == "technical" else 4,
            category=category,
            is_eliminatory=False
        ))

    try:
        active_qs = await sqs_svc.get_active_version(db, request.job_vacancy_id or "")
        qs_version = active_qs.version if active_qs else None
        qs_id = str(active_qs.id) if active_qs else None

        _repo = WsiRepository(db)
        await _repo.upsert_session(
            session_id=session_id,
            candidate_id="pending",
            job_vacancy_id=request.job_vacancy_id or "",
            screening_type="text",
            mode="compact",
            status="in_progress",
            question_set_version=qs_version,
            question_set_id=qs_id,
        )

        for idx, q in enumerate(questions):
            await _repo.upsert_question(
                question_id=q.id,
                session_id=session_id,
                competency=q.skill_targeted,
                framework=wsi_questions[idx].framework if idx < len(wsi_questions) else "CBI",
                question_type=q.question_type,
                question_text=q.text,
                weight=wsi_questions[idx].weight if idx < len(wsi_questions) else 1.0 / max(len(questions), 1),
                expected_signals=wsi_questions[idx].expected_signals if idx < len(wsi_questions) else [],
                scoring_criteria=dict(wsi_questions[idx].scoring_criteria) if idx < len(wsi_questions) else {},
                sequence_order=idx + 1,
            )
    except Exception as e:
        logger.warning(f"Failed to save to DB: {e}")

    # WT-2022 P0.C / LGPD Art. 20 + EU AI Act Art. 13 — audit trail de decisao automatizada IA.
    # ADR-LGPD-001 + CLAUDE.md REGRA #2: company_id vem do JWT (require_company_id), nunca do payload.
    try:
        await log_automated_decision(
            db=db,
            company_id=company_id,
            job_id=request.job_vacancy_id or None,
            decision_type="wsi_question_generation",
            ai_model_used=getattr(settings, "LLM_PRIMARY_MODEL", "claude-sonnet-4-6"),
            explanation_text=(
                f"Gerou {len(questions)} pergunta(s) de triagem WSI ({mode}) para a vaga "
                f'"{job_title}" (senioridade={seniority}) via pipeline canonical '
                "CBI + Bloom + Dreyfus + BigFive. Skills tecnicos avaliados: "
                f"{all_skills}. Competencias comportamentais: {behavioral}."
            ),
            criteria_used=[
                *[f"skill:{s}" for s in all_skills],
                *[f"behavioral:{b}" for b in behavioral],
                f"seniority:{seniority}",
                f"mode:{mode}",
            ],
            criteria_ignored=list(PROTECTED_CRITERIA_PT),
            confidence_score=None,  # WSI nao expoe confidence agregado; cada pergunta tem validation_flags
            review_eligible=True,
            extra_metadata={
                "session_id": session_id,
                "questions_count": len(questions),
                "mode": mode,
                "seniority": seniority,
                "prompt_template_version": "wsi_F6_pipeline_v2",
                "llm_model": getattr(settings, "LLM_PRIMARY_MODEL", "claude-sonnet-4-6"),
                "frameworks_used": sorted({wq.framework for wq in wsi_questions}),
            },
        )
    except ValueError:
        # Compliance gate raised — protected criteria leaked into criteria_used.
        # Re-raise fail-loud per CLAUDE.md REGRA #2 (LGPD): NUNCA mascarar essa violacao.
        raise
    except Exception as exc:
        # Outros erros: log e segue (audit trail gap, mas decisao IA nao deve ser bloqueada).
        logger.error(
            "WT-2022 P0.C: log_automated_decision falhou em /generate-questions "
            "(LGPD Art. 20 audit gap, session_id=%s): %s",
            session_id, exc, exc_info=True,
        )

    return GenerateQuestionsResponse(
        session_id=session_id,
        questions=questions,
        job_title=job_title
    )


@router.post("/suggest-question", response_model=None)
async def suggest_question(
    request: SuggestQuestionRequest,
    company_id: str = Depends(require_company_id),
    wsi_svc: WSIService = Depends(get_wsi_service),
):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Generate a single screening question from a recruiter prompt using LLM."""
    # Consolidação WSI Fase 2 (2026-05-31): delega ao canônico único
    # WSIService.suggest_single_question (mesmo método usado pelo HITL do
    # wizard conversacional). Single source of truth.
    return await wsi_svc.suggest_single_question(
        prompt=request.prompt,
        block_id=request.block_id,
        job_title=request.job_title,
        seniority=request.seniority,
        technical_skills=request.technical_skills,
        behavioral_competencies=request.behavioral_competencies,
    )


@router.post("/questions/save", response_model=None)
async def save_questions(
    request: SaveQuestionsRequest,
    db: AsyncSession = Depends(get_tenant_db),
    sqs_svc: ScreeningQuestionSetService = Depends(get_screening_question_set_service),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Save screening questions for a job vacancy."""
    # P0 (audit 2026-06-05): valida ownership do job_id contra o company_id do JWT
    # ANTES de qualquer escrita. job_screening_questions/screening_question_sets nao
    # tem RLS — este e o gate multi-tenant canonico (fail-closed no produtor).
    # FORA do try/except abaixo: senao o HTTPException 404 seria engolido pelo fallback.
    from app.domains.job_management.repositories.job_vacancy_crud_repository import (
        JobVacancyCrudRepository,
    )
    if not await JobVacancyCrudRepository(db).owned_by_company(request.job_id, company_id):
        raise HTTPException(status_code=404, detail="Vaga nao encontrada para esta empresa.")
    try:
        for q in request.questions:
            q_id = q.get("id", f"q_{uuid.uuid4().hex[:12]}")
            _repo = WsiRepository(db)
            await _repo.upsert_job_screening_question(
                question_id=q_id,
                job_id=request.job_id,
                question_text=q.get("text", q.get("question", "")),
                category=q.get("category", "general"),
                question_type=q.get("type", "open"),
                weight=q.get("weight", 0.75),
                skill_targeted=q.get("skill_targeted", ""),
                block_id=q.get("block_id"),
                source=request.source,
            )
        try:
            await sqs_svc.save_question_set(
                db=db,
                job_vacancy_id=request.job_id,
                questions=request.questions,
                source=request.source or "manual",
                block_distribution=None,
                metadata=None,
            )
            logger.info(f"Saved question set version for job {request.job_id}")
        except Exception as version_err:
            # Audit C9/#1 (2026-06-05): o set versionado NAO e opcional.
            # save_question_set faz o db.commit() de flat+set juntos; se falhar,
            # o flat fica uncommitted. Rollback descarta tudo e propaga a falha
            # em vez de mascarar com success:True (orfao flat sem set versionado).
            logger.error(f"Failed to save question set version (rolling back): {version_err}")
            await db.rollback()
            return {"success": False, "error": f"version_save_failed: {version_err}"}
        return {"success": True, "saved_count": len(request.questions)}
    except Exception as e:
        logger.error(f"Failed to save questions: {e}")
        try:
            await db.rollback()
            await db.execute(text("""
                CREATE TABLE IF NOT EXISTS job_screening_questions (
                    id VARCHAR(255) PRIMARY KEY,
                    job_vacancy_id VARCHAR(255) NOT NULL,
                    question_text TEXT NOT NULL,
                    category VARCHAR(100) DEFAULT 'general',
                    question_type VARCHAR(100) DEFAULT 'open',
                    weight FLOAT DEFAULT 0.75,
                    skill_targeted VARCHAR(255) DEFAULT '',
                    block_id INTEGER,
                    source VARCHAR(100) DEFAULT 'manual',
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """))
            for q in request.questions:
                q_id = q.get("id", f"q_{uuid.uuid4().hex[:12]}")
                # RLS-EXEMPT: job_screening_questions — transitive via job_vacancies
                await db.execute(text("""
                    INSERT INTO job_screening_questions (id, job_vacancy_id, question_text, category, question_type, weight, skill_targeted, block_id, source, is_active)
                    VALUES (:id, :job_id, :text, :category, :type, :weight, :skill_targeted, :block_id, :source, true)
                    ON CONFLICT (id) DO UPDATE SET
                        question_text = EXCLUDED.question_text,
                        category = EXCLUDED.category,
                        question_type = EXCLUDED.question_type
                """), {
                    "id": q_id,
                    "job_id": request.job_id,
                    "text": q.get("text", q.get("question", "")),
                    "category": q.get("category", "general"),
                    "type": q.get("type", "open"),
                    "weight": q.get("weight", 0.75),
                    "skill_targeted": q.get("skill_targeted", ""),
                    "block_id": q.get("block_id"),
                    "source": request.source
                })
            try:
                await sqs_svc.save_question_set(
                    db=db,
                    job_vacancy_id=request.job_id,
                    questions=request.questions,
                    source=request.source or "manual",
                    block_distribution=None,
                    metadata=None,
                )
                logger.info(f"Saved question set version for job {request.job_id}")
            except Exception as version_err:
                # Audit C9/#1 (2026-06-05): set versionado NAO e opcional (mesma
                # transacao do flat). Rollback + propaga a falha em vez de success:True.
                logger.error(f"Failed to save question set version (rolling back): {version_err}")
                await db.rollback()
                return {"success": False, "error": f"version_save_failed: {version_err}"}
            return {"success": True, "saved_count": len(request.questions)}
        except Exception as e2:
            logger.error(f"Failed even after table creation: {e2}")
            return {"success": False, "error": str(e2)}


@router.get("/question-sets/{job_id}/active", response_model=None)
async def get_active_question_set(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    sqs_svc: ScreeningQuestionSetService = Depends(get_screening_question_set_service),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    try:
        qs = await sqs_svc.get_active_version(db, job_id)
        if not qs:
            return {"success": False, "error": "No active question set found", "version": None}
        return {
            "success": True,
            "version": qs.version,
            "questions_count": qs.questions_count,
            "questions": qs.questions_snapshot,
            "source": qs.source,
            "difficulty_coefficient": qs.difficulty_coefficient,
            "block_distribution": qs.block_distribution,
            "created_at": qs.created_at.isoformat() if qs.created_at else None,
        }
    except Exception as e:
        logger.error(f"Failed to get active question set: {e}")
        return {"success": False, "error": str(e)}


@router.get("/question-sets/{job_id}/versions", response_model=None)
async def list_question_set_versions(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    sqs_svc: ScreeningQuestionSetService = Depends(get_screening_question_set_service),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    try:
        versions = await sqs_svc.list_versions(db, job_id)
        return {"success": True, "versions": versions, "total": len(versions)}
    except Exception as e:
        logger.error(f"Failed to list question set versions: {e}")
        return {"success": False, "error": str(e)}


@router.get("/question-sets/{job_id}/version/{version}", response_model=None)
async def get_question_set_by_version(
    job_id: str,
    version: int,
    db: AsyncSession = Depends(get_db),
    sqs_svc: ScreeningQuestionSetService = Depends(get_screening_question_set_service),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    try:
        qs = await sqs_svc.get_by_version(db, job_id, version)
        if not qs:
            return {"success": False, "error": f"Version {version} not found"}
        return {
            "success": True,
            "version": qs.version,
            "questions_count": qs.questions_count,
            "questions": qs.questions_snapshot,
            "source": qs.source,
            "is_active": qs.is_active,
            "difficulty_coefficient": qs.difficulty_coefficient,
            "block_distribution": qs.block_distribution,
            "created_at": qs.created_at.isoformat() if qs.created_at else None,
        }
    except Exception as e:
        logger.error(f"Failed to get question set version: {e}")
        return {"success": False, "error": str(e)}


@router.get("/question-sets/{job_id}/consistency", response_model=None)
async def check_question_set_consistency(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    sqs_svc: ScreeningQuestionSetService = Depends(get_screening_question_set_service),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    try:
        result = await sqs_svc.check_version_consistency(db, job_id)
        return {"success": True, **result}
    except Exception as e:
        logger.error(f"Failed to check consistency: {e}")
        return {"success": False, "error": str(e)}

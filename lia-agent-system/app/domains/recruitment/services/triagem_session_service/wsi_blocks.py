"""
WSI block loading, building, and mapping helpers.
"""
import logging
from typing import Any

from app.core.config import settings
from app.shared.runtime_context import RuntimeContext
from app.shared.services.automated_decision_logger import (
    PROTECTED_CRITERIA_PT,
    log_automated_decision,
)

from ._shared import WSI_BLOCKS_FALLBACK

logger = logging.getLogger(__name__)


def _resolve_screening_mode(screening_config: dict) -> str:
    """Resolve modo de triagem com backward compat para chave legada format.

    Wizard grava screening_mode; codigo legado usava format.
    Precedencia: screening_mode > format > default compact.
    """
    mode = screening_config.get("screening_mode") or screening_config.get("format")
    return mode if mode in ("full", "compact") else "compact"


def _resolve_screening_mode(screening_config: dict) -> str:
    """Resolve modo de triagem com backward compat para chave legada format.

    Wizard grava screening_mode; codigo legado usava format.
    Precedencia: screening_mode > format > default compact.
    """
    mode = screening_config.get("screening_mode") or screening_config.get("format")
    return mode if mode in ("full", "compact") else "compact"


def _map_question_type_to_category(question_type: str) -> str:
    mapping = {
        "autodeclaration": "technical",
        "situational": "behavioral",
        "contextual": "behavioral",
        "open": "technical",
    }
    return mapping.get(question_type, "behavioral")

def _build_wsi_blocks_from_question_set(questions_snapshot: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Build WSI blocks structure from a question set snapshot.
    Maps questions to canonical WSI blocks (0-5) based on block_id or category.
    Falls back to distributing by category if block_id is missing.
    """
    from app.domains.cv_screening.constants.wsi_constants import WSI_BLOCK_NAMES

    block_map: dict[int, list[str]] = {i: [] for i in range(6)}
    block_meta: dict[int, dict[str, str]] = {
        0: {"block_type": "behavioral", "competency": "initial_approach"},
        1: {"block_type": "behavioral", "competency": "motivation"},
        2: {"block_type": "behavioral", "competency": "cultural_fit"},
        3: {"block_type": "technical", "competency": "technical_skills"},
        4: {"block_type": "behavioral", "competency": "interpersonal_skills"},
        5: {"block_type": "behavioral", "competency": "self_assessment"},
    }

    for q in questions_snapshot:
        text = q.get("text", q.get("question", q.get("question_text", "")))
        if not text:
            continue

        block_id = q.get("block_id")
        if block_id is not None:
            try:
                bid = int(block_id)
                if 0 <= bid <= 5:
                    block_map[bid].append(text)
                    continue
            except (ValueError, TypeError):
                pass

        category = q.get("category", "").lower()
        if category == "technical":
            block_map[3].append(text)
        elif category in ("behavioral", "situational", "contextual"):
            block_map[4].append(text)
        elif category == "company":
            block_map[2].append(text)
        else:
            block_map[4].append(text)

    blocks = []
    for idx in range(6):
        questions_for_block = block_map[idx]
        if not questions_for_block and idx not in (0, 5):
            continue
        if not questions_for_block:
            for fb in WSI_BLOCKS_FALLBACK:
                if fb["index"] == idx:
                    questions_for_block = fb["questions"]
                    break

        meta = block_meta[idx]
        blocks.append({
            "index": idx,
            "name": WSI_BLOCK_NAMES.get(idx, f"Bloco {idx}"),
            "block_type": meta["block_type"],
            "competency": meta["competency"],
            "questions": questions_for_block,
        })

    if not blocks:
        logger.warning("[Triagem] Question set mapping produced empty blocks, using fallback")
        return WSI_BLOCKS_FALLBACK

    return blocks

async def _load_or_generate_blocks(
    db,
    job_id: str,
    job: Any | None = None,
) -> tuple[list[dict[str, Any]], str | None, str | None]:
    """
    Load WSI blocks for a job from:
    1. Active question set version (preferred)
    2. wsi_service.generate_screening_questions() (fallback)
    3. WSI_BLOCKS_FALLBACK hardcoded (emergency fallback)

    Returns:
        (blocks, wsi_question_set_id, wsi_question_set_version)
    """
    try:
        from app.domains.cv_screening.services.screening_question_set_service import (
            screening_question_set_service,
        )
        active_qs = await screening_question_set_service.get_active_version(db, job_id)
        if active_qs and active_qs.questions_snapshot:
            blocks = _build_wsi_blocks_from_question_set(active_qs.questions_snapshot)
            if blocks:
                n_questions = sum(len(b["questions"]) for b in blocks)
                logger.info(
                    f"[Triagem] Loaded question set v{active_qs.version} "
                    f"with {n_questions} questions for job {job_id}"
                )
                return blocks, str(active_qs.id), str(active_qs.version)
            logger.warning(f"[Triagem] Question set for job {job_id} produced empty blocks, trying wsi_service")
    except Exception as exc:
        logger.warning(f"[Triagem] Could not load question set for job {job_id}: {exc}")

    try:
        from app.domains.cv_screening.services.wsi_service import Competency, wsi_service
        competencies = []
        if job and getattr(job, "screening_config", None):
            skills = job.screening_config.get("skills") or {}
            for skill_name, skill_data in list(skills.items())[:10]:
                comp_type = skill_data.get("type", "technical") if isinstance(skill_data, dict) else "technical"
                competencies.append(Competency(
                    name=skill_name,
                    type=comp_type if comp_type in ("technical", "behavioral", "cultural") else "technical",
                    weight=0.5,
                    seniority_level=getattr(job, "seniority_level", "pleno") or "pleno",
                ))
        if not competencies:
            competencies = [
                Competency(name="Experiencia Relevante", type="technical", weight=0.5, seniority_level="pleno"),
                Competency(name="Comunicacao", type="behavioral", weight=0.5, seniority_level="pleno"),
            ]
        seniority = getattr(job, "seniority_level", "pleno") or "pleno" if job else "pleno"
        job_description = (job.description or "")[:1000] if job and job.description else ""
        sc = getattr(job, "screening_config", None) or {} if job else {}
        mode = _resolve_screening_mode(sc)
        generated_qs = await wsi_service.generate_screening_questions(
            competencies=competencies,
            mode=mode,
            job_description=job_description,
            seniority=seniority,
        )
        if generated_qs:
            snapshot = [
                {"text": q.question_text, "category": _map_question_type_to_category(q.question_type), "block_id": None, "weight": q.weight}
                for q in generated_qs
            ]
            blocks = _build_wsi_blocks_from_question_set(snapshot)
            if blocks:
                logger.info(f"[Triagem] Generated {len(generated_qs)} questions via wsi_service for job {job_id}")

                # WT-2022 P0.C wave 2 / LGPD Art. 20 + EU AI Act Art. 13.
                # Triagem session fallback — wsi_service inline gerou questions
                # via IA. company_id: prefer job.company_id (FK direto), fallback
                # RuntimeContext. silent_on_persist_error porque triagem precisa
                # continuar mesmo se audit falhar (degradacao graciosa).
                try:
                    company_id = (
                        getattr(job, "company_id", None)
                        or RuntimeContext.from_contextvars().company_id
                    )
                    if company_id:
                        await log_automated_decision(
                            db=db,
                            company_id=str(company_id),
                            job_id=job_id,
                            decision_type="wsi_triagem_session_fallback",
                            ai_model_used=getattr(settings, "LLM_PRIMARY_MODEL", "claude-sonnet-4-6"),
                            explanation_text=(
                                f'Triagem session: question set versionado ausente para job {job_id}; '
                                f'wsi_service.generate_screening_questions gerou {len(generated_qs)} '
                                f'pergunta(s) dinamicamente (mode={mode}, seniority={seniority}). '
                                f'Competencias: {[c.name for c in competencies]}.'
                            ),
                            criteria_used=[
                                *[f"competency:{c.name}" for c in competencies],
                                f"seniority:{seniority}",
                                f"mode:{mode}",
                                "fallback:triagem_dynamic",
                            ],
                            criteria_ignored=list(PROTECTED_CRITERIA_PT),
                            confidence_score=None,
                            review_eligible=True,
                            extra_metadata={
                                "endpoint": "triagem_session_service.wsi_blocks._load_or_generate_blocks",
                                "job_id": job_id,
                                "questions_count": len(generated_qs),
                                "competencies_count": len(competencies),
                                "mode": mode,
                                "seniority": seniority,
                                "fallback_dynamic": True,
                                "prompt_template_version": "wsi_F6_pipeline_v2",
                                "llm_model": getattr(settings, "LLM_PRIMARY_MODEL", "claude-sonnet-4-6"),
                            },
                            silent_on_persist_error=True,  # triagem session: nao bloquear
                        )
                    else:
                        logger.warning(
                            "WT-2022 P0.C wave 2: triagem wsi_blocks sem company_id "
                            "(job.company_id None, ContextVar vazio). LGPD audit gap job_id=%s",
                            job_id,
                        )
                except ValueError:
                    raise
                except Exception as audit_err:
                    logger.error(
                        "WT-2022 P0.C wave 2: log_automated_decision falhou em triagem wsi_blocks "
                        "(LGPD Art. 20 audit gap, job_id=%s): %s",
                        job_id, audit_err, exc_info=True,
                    )

                return blocks, None, None
    except Exception as exc:
        logger.warning(f"[Triagem] wsi_service question generation failed for job {job_id}: {exc}")

    logger.warning(f"[Triagem] Using hardcoded fallback blocks for job {job_id}")
    return WSI_BLOCKS_FALLBACK, None, None

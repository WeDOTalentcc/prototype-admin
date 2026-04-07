"""
WSI block loading, building, and mapping helpers.
"""
import logging
from typing import Any

from ._shared import WSI_BLOCKS_FALLBACK

logger = logging.getLogger(__name__)


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
                logger.info(
                    f"[Triagem] Loaded question set v{active_qs.version} "
                    f"with {sum(len(b[\questions\]) for b in blocks)} questions for job {job_id}"
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
        mode = sc.get("format", "compact")
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
                return blocks, None, None
    except Exception as exc:
        logger.warning(f"[Triagem] wsi_service question generation failed for job {job_id}: {exc}")

    logger.warning(f"[Triagem] Using hardcoded fallback blocks for job {job_id}")
    return WSI_BLOCKS_FALLBACK, None, None

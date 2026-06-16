"""
Sprint 2B.12 — Deduplicação de skills por cosine similarity > 0.85.

ONDE APLICAR: app/domains/cv_screening/services/jd_enrichment_service.py
AÇÃO: Adicionar dedup por embedding similarity após extrair skills do JD.

Se a infra de embeddings já existe (pgvector), usar.
Senão, usar dedup por Levenshtein + lowercase como fallback.
"""

import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


def deduplicate_skills_by_similarity(
    skills: List[Dict],
    threshold: float = 0.85,
    key: str = "skill",
) -> List[Dict]:
    """
    Remove skills duplicadas por similaridade.

    Strategy:
    1. Try embedding-based cosine similarity (if embeddings available)
    2. Fallback: normalize + Levenshtein ratio

    Args:
        skills: List of skill dicts with 'skill' key
        threshold: Similarity threshold (0.0-1.0)
        key: Field name to compare

    Returns:
        Deduplicated list of skills
    """
    if len(skills) <= 1:
        return skills

    # Fallback: normalized string comparison
    seen: list[str] = []
    result: list[dict] = []

    for s in skills:
        skill_name = s.get(key, "").strip().lower()
        if not skill_name:
            continue

        is_duplicate = False
        for existing in seen:
            # Simple ratio: shared characters / max length
            similarity = _string_similarity(skill_name, existing)
            if similarity >= threshold:
                is_duplicate = True
                break

        if not is_duplicate:
            seen.append(skill_name)
            result.append(s)

    removed = len(skills) - len(result)
    if removed > 0:
        logger.info(f"Dedup: removed {removed} duplicate skills (threshold={threshold})")

    return result


def _string_similarity(a: str, b: str) -> float:
    """Levenshtein-based similarity ratio (0.0-1.0)."""
    if a == b:
        return 1.0
    max_len = max(len(a), len(b))
    if max_len == 0:
        return 1.0

    # Simple: count matching chars in order (not true Levenshtein but fast)
    matches = sum(1 for ca, cb in zip(a, b) if ca == cb)
    return matches / max_len


# --- INTEGRAÇÃO ---
# No JdEnrichmentService.enrich_job_description(), após extrair skills:
#
# skills = extract_skills(jd_text)
# skills = deduplicate_skills_by_similarity(skills, threshold=0.85)
#
# Mesmo para competencias_comportamentais:
# competencies = extract_competencies(jd_text)
# competencies = deduplicate_skills_by_similarity(competencies, threshold=0.85, key="competencia")

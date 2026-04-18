"""
Scoring helpers for triagem session responses.

Escala canônica: WSI /10 (constants/wsi_scale.py — PR2 #497).
Cutoffs importados do canônico — nunca hardcoded:
- CUTOFF_APPROVED_AUTO (7.5) → aprovado
- CUTOFF_REVIEW_MIN (6.0) → aguardando revisão; abaixo → reprovado
Default fallback = SCALE_MEDIAN (6.0 mediano em /10).
"""
import logging
from typing import Any

from app.domains.cv_screening.constants.wsi_scale import (
    CUTOFF_APPROVED_AUTO,
    CUTOFF_REVIEW_MIN,
    SCALE_MAX,
    SCALE_MIN_VALID,
)

logger = logging.getLogger(__name__)

# Mediano em /10 (entre SCALE_MIN_VALID e SCALE_MAX) — usado como fallback
# quando o scorer determinístico falha (B0 #523: era 3.0 em /5).
SCALE_MEDIAN: float = (SCALE_MIN_VALID + SCALE_MAX) / 2.0  # = 6.0


def _score_response_deterministic(response_text: str, block_type: str, competency: str) -> dict[str, Any]:
    try:
        from app.domains.cv_screening.services.wsi_deterministic_scorer import (
            calculate_wsi_deterministic,
        )
        result = calculate_wsi_deterministic(
            response_text=response_text,
            competency_name=competency,
        )
        return {
            "score": result.final_score,  # já em /10 (escala canônica)
            "block_type": block_type,
            "bloom_level": result.bloom_level,
            "dreyfus_level": result.dreyfus_level,
            "evidences": result.evidences,
            "red_flags": result.red_flags,
            "justification": result.justification,
        }
    except Exception as exc:
        logger.warning(f"[Triagem] Deterministic scoring failed: {exc}")
        return {
            "score": SCALE_MEDIAN,
            "block_type": block_type,
            "bloom_level": 2,
            "dreyfus_level": 2,
            "evidences": [],
            "red_flags": [],
            "justification": "Scoring fallback applied",
        }


def _classify(final_score: float) -> str:
    """Classifica score canônico /10 nos 3 níveis WSI_CUTOFFS."""
    if final_score >= CUTOFF_APPROVED_AUTO:
        return "aprovado"
    if final_score >= CUTOFF_REVIEW_MIN:
        return "aguardando"
    return "reprovado"


def _calculate_final_score(response_scores: list[dict[str, Any]]) -> tuple[float, str]:
    if not response_scores:
        return SCALE_MEDIAN, "aguardando"

    technical_scores = []
    behavioral_scores = []

    for rs in response_scores:
        score = rs.get("score", SCALE_MEDIAN)
        block_type = rs.get("block_type", "behavioral")
        # F9-1 — trait_weight do ranking F3; padrao 1.0 = pesos uniformes
        trait_weight = float(rs.get("trait_weight", 1.0))
        if block_type == "technical":
            technical_scores.append(("", score, 1.0))
        else:
            behavioral_scores.append(("", score, trait_weight))

    try:
        from app.domains.cv_screening.services.wsi_deterministic_scorer import (
            calculate_final_wsi_score,
        )
        result = calculate_final_wsi_score(
            technical_scores=technical_scores or [("", SCALE_MEDIAN, 1.0)],
            behavioral_scores=behavioral_scores or [("", SCALE_MEDIAN, 1.0)],
        )
        # B0 #523 — final_score já em /10 (canônico). Nada de * 2.0.
        final_score = round(result["final_score"], 1)
        return final_score, _classify(final_score)
    except Exception as exc:
        logger.warning(f"[Triagem] Final score calculation failed: {exc}")
        if response_scores:
            avg = sum(rs.get("score", SCALE_MEDIAN) for rs in response_scores) / len(response_scores)
            final_score = round(avg, 1)  # B0 #523 — sem * 2.0; scores já em /10
        else:
            final_score = SCALE_MEDIAN
        return final_score, _classify(final_score)

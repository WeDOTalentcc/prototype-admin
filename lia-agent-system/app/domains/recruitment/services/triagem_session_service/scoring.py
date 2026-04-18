"""
Scoring helpers for triagem session responses.

Escala canônica: WSI /10 (constants/wsi_scale.py — PR2 #497).
Cutoffs aplicados: aprovado >= 7.5, aguardando >= 5.5 (alinhados a WSI_CUTOFFS).
Default fallback = 6.0 (mediano em /10).
"""
import logging
from typing import Any

logger = logging.getLogger(__name__)


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
            "score": 6.0,  # mediano em /10
            "block_type": block_type,
            "bloom_level": 2,
            "dreyfus_level": 2,
            "evidences": [],
            "red_flags": [],
            "justification": "Scoring fallback applied",
        }


def _calculate_final_score(response_scores: list[dict[str, Any]]) -> tuple[float, str]:
    if not response_scores:
        return 6.0, "aguardando"

    technical_scores = []
    behavioral_scores = []

    for rs in response_scores:
        score = rs.get("score", 6.0)
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
            technical_scores=technical_scores or [("", 6.0, 1.0)],
            behavioral_scores=behavioral_scores or [("", 6.0, 1.0)],
        )
        # B0 #523 — final_score já em /10 (canônico). Nada de * 2.0.
        final_score = round(result["final_score"], 1)

        if final_score >= 7.5:
            recommendation = "aprovado"
        elif final_score >= 5.5:
            recommendation = "aguardando"
        else:
            recommendation = "reprovado"

        return final_score, recommendation
    except Exception as exc:
        logger.warning(f"[Triagem] Final score calculation failed: {exc}")
        if response_scores:
            avg = sum(rs.get("score", 6.0) for rs in response_scores) / len(response_scores)
            final_score = round(avg, 1)  # B0 #523 — sem * 2.0; scores já em /10
        else:
            final_score = 6.0

        if final_score >= 7.5:
            recommendation = "aprovado"
        elif final_score >= 5.5:
            recommendation = "aguardando"
        else:
            recommendation = "reprovado"

        return final_score, recommendation

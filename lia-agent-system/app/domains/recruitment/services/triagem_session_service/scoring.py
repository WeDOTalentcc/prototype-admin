"""
Scoring helpers for triagem session responses.
"""
import logging
import statistics as _stats
from typing import Any

logger = logging.getLogger(__name__)

_DEFAULT_TECH_WEIGHT = 0.625  # pleno default
_DEFAULT_BEHAV_WEIGHT = 1.0 - _DEFAULT_TECH_WEIGHT

# Blocos administrativos do WSI_BLOCKS_FALLBACK que NÃO representam competências técnicas
# ou comportamentais e portanto NÃO devem entrar no cálculo de score.
# Bloco 0: perguntas de disponibilidade/salário (abordagem inicial).
# Bloco 5: perguntas de encerramento/planos futuros.
SCORING_SKIP_BLOCK_INDICES: frozenset[int] = frozenset({0, 5})

# Score neutro aplicado quando todos os blocos são admin (fallback de emergência extremo).
_NEUTRAL_SCORE_ADMIN_ONLY = 3.0  # × 2.0 = 6.0 → "aguardando"


def _score_response_deterministic(
    response_text: str,
    block_type: str,
    competency: str,
    question_framework: str = "CBI",
) -> dict[str, Any]:
    try:
        from app.domains.cv_screening.services.wsi_deterministic_scorer import (
            calculate_wsi_deterministic,
        )
        result = calculate_wsi_deterministic(
            response_text=response_text,
            competency_name=competency,
            question_framework=question_framework,
        )
        return {
            "score": result.final_score,
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
            "score": 3.0,
            "block_type": block_type,
            "bloom_level": 2,
            "dreyfus_level": 2,
            "evidences": [],
            "red_flags": [],
            "justification": "Scoring fallback applied",
        }


def calculate_session_final_score(
    technical_scores: list[float],
    behavioral_scores: list[float],
    seniority: str | None = None,
) -> dict[str, Any]:
    """
    Calcula o score final da sessao de triagem aplicando SENIORITY_WEIGHTS.

    Args:
        technical_scores:  Lista de scores numericos para blocos tecnicos.
        behavioral_scores: Lista de scores numericos para blocos comportamentais.
        seniority:         Nivel de senioridade da vaga (lookup em SENIORITY_WEIGHTS).

    Returns:
        Dict com final_score, technical_mean, behavioral_mean, tech_weight, behav_weight.
    """
    if not technical_scores and not behavioral_scores:
        return {
            "final_score": 0.0,
            "technical_mean": 0.0,
            "behavioral_mean": 0.0,
            "tech_weight": _DEFAULT_TECH_WEIGHT,
            "behav_weight": _DEFAULT_BEHAV_WEIGHT,
            "seniority_used": seniority,
        }

    t_mean = _stats.mean(technical_scores) if technical_scores else 0.0
    b_mean = _stats.mean(behavioral_scores) if behavioral_scores else 0.0

    tech_weight = _DEFAULT_TECH_WEIGHT
    if seniority:
        try:
            from app.domains.cv_screening.services.wsi_deterministic_scorer import (
                get_seniority_weights,
            )
            weights = get_seniority_weights(seniority)
            tech_weight = weights.get("technical", _DEFAULT_TECH_WEIGHT)
        except Exception as exc:
            logger.warning(f"[Triagem] Failed to resolve seniority weights for {seniority!r}: {exc}")

    behav_weight = 1.0 - tech_weight
    return {
        "final_score": round(t_mean * tech_weight + b_mean * behav_weight, 2),
        "technical_mean": round(t_mean, 2),
        "behavioral_mean": round(b_mean, 2),
        "tech_weight": tech_weight,
        "behav_weight": behav_weight,
        "seniority_used": seniority,
    }


def _calculate_final_score(
    response_scores: list[dict[str, Any]],
    seniority: str | None = None,
) -> tuple[float, str]:
    if not response_scores:
        return 3.0, "aguardando"

    technical_scores = []
    behavioral_scores = []

    for rs in response_scores:
        # Blocos 0 e 5 contêm perguntas administrativas (disponibilidade, salário,
        # encerramento) que não avaliam competências — excluir do cálculo de score.
        if rs.get("block_index") in SCORING_SKIP_BLOCK_INDICES:
            continue

        score = rs.get("score", 3.0)
        block_type = rs.get("block_type", "behavioral")
        # F9-1 - trait_weight do ranking F3; padrao 1.0 = pesos uniformes
        trait_weight = float(rs.get("trait_weight", 1.0))
        if block_type == "technical":
            technical_scores.append(("", score, 1.0))
        else:
            behavioral_scores.append(("", score, trait_weight))

    # Se após filtrar admin só restam listas vazias (fallback de emergência extremo),
    # usar score neutro "aguardando" em vez de reprovar candidato por perguntas admin.
    if not technical_scores and not behavioral_scores:
        logger.warning(
            "[Triagem] Todas as respostas são de blocos admin (0/5) — usando score neutro. "
            "Provável uso do WSI_BLOCKS_FALLBACK de emergência sem question set versionado."
        )
        return round(_NEUTRAL_SCORE_ADMIN_ONLY * 2.0, 1), "aguardando"

    try:
        from app.domains.cv_screening.services.wsi_deterministic_scorer import (
            calculate_final_wsi_score,
        )
        result = calculate_final_wsi_score(
            technical_scores=technical_scores or [("", 3.0, 1.0)],
            behavioral_scores=behavioral_scores or [("", 3.0, 1.0)],
            seniority=seniority,
        )
        final = result["final_score"]
        scaled = round(final * 2.0, 1)

        if scaled >= 7.5:
            recommendation = "aprovado"
        elif scaled >= 5.5:
            recommendation = "aguardando"
        else:
            recommendation = "reprovado"

        return scaled, recommendation
    except Exception as exc:
        logger.warning(f"[Triagem] Final score calculation failed: {exc}")
        if technical_scores or behavioral_scores:
            all_scores = [s for _, s, _ in technical_scores + behavioral_scores]
            avg = sum(all_scores) / len(all_scores)
            scaled = round(avg * 2.0, 1)
        else:
            scaled = 6.0

        if scaled >= 7.5:
            recommendation = "aprovado"
        elif scaled >= 5.5:
            recommendation = "aguardando"
        else:
            recommendation = "reprovado"

        return scaled, recommendation

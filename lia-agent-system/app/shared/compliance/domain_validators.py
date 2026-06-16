"""
Validadores domain-specific para o FactChecker.
Cada validador verifica claims específicos do seu domínio.

Registrados automaticamente quando o módulo do domínio é importado.
Parte do LIA-C06 — Domain-Specific Fact Validation.
"""
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


async def validate_cv_score_claim(
    claim_text: str, context_data: dict[str, Any]
) -> str | None:
    """
    Valida claims de score em cv_screening.
    Ex: LIA diz "score 85" mas real é 72 → retorna discrepância.

    Tolerância: 5 pontos para absorver arredondamentos legítimos.
    """
    score_pattern = re.compile(
        r"\b(\d{1,3})\s*(?:pontos?|score|%)\b", re.IGNORECASE
    )
    mentioned_scores = score_pattern.findall(claim_text)
    if not mentioned_scores:
        return None

    real_score = context_data.get("candidate_score") or context_data.get("score")
    if real_score is None:
        return None

    try:
        real_val = float(real_score)
    except (TypeError, ValueError):
        logger.debug("validate_cv_score_claim: could not parse real_score=%r", real_score)
        return None

    for score_str in mentioned_scores:
        try:
            mentioned = int(score_str)
        except ValueError:
            # T-04 Tipo D: regex may match non-int (e.g. trailing punctuation
            # captured by group); skip and let other matches in the loop
            # be evaluated. No data loss — fact-check is best-effort.
            continue
        if abs(mentioned - real_val) > 5:
            return (
                f"Score mencionado ({mentioned}) difere do score real "
                f"({real_score}) em mais de 5 pontos"
            )
    return None


async def validate_analytics_metric_claim(
    claim_text: str, context_data: dict[str, Any]
) -> str | None:
    """
    Valida claims de métricas em analytics.
    Ex: "tempo médio 15d" mas real é 23d → retorna discrepância.

    Tolerância: 3 dias para flutuação natural do período.
    """
    time_pattern = re.compile(
        r"\b(\d+)\s*(?:dias?|semanas?|meses?)\b", re.IGNORECASE
    )

    real_avg_days = context_data.get("avg_time_to_hire")
    if real_avg_days is not None:
        try:
            real_val = float(real_avg_days)
        except (TypeError, ValueError):
            logger.debug(
                "validate_analytics_metric_claim: could not parse avg_time_to_hire=%r",
                real_avg_days,
            )
            return None

        for days_str in time_pattern.findall(claim_text):
            try:
                mentioned = int(days_str)
            except ValueError:
                # T-04 Tipo D: regex may capture non-int fragments; skip
                # and let other matches in the loop be evaluated.
                continue
            if abs(mentioned - real_val) > 3:
                return (
                    f"Tempo mencionado ({mentioned}d) difere do tempo real "
                    f"({real_avg_days}d) em mais de 3 dias"
                )

    return None


async def validate_sourcing_count_claim(
    claim_text: str, context_data: dict[str, Any]
) -> str | None:
    """
    Valida claims de contagem em sourcing.
    Ex: "encontrei 150 candidatos" mas real é 23 → retorna discrepância.

    Só valida quando contagem real é pequena (< 100) para evitar falsos positivos
    em buscas amplas onde estimativas imprecisas são aceitáveis.
    """
    count_pattern = re.compile(
        r"\b(\d+)\s*(?:candidatos?|perfis?|profissionais?)\b", re.IGNORECASE
    )

    real_count = context_data.get("total_candidates") or context_data.get("search_count")
    if real_count is None:
        return None

    try:
        real_val = float(real_count)
    except (TypeError, ValueError):
        logger.debug(
            "validate_sourcing_count_claim: could not parse real_count=%r", real_count
        )
        return None

    # Só valida se contagem real for pequena (evitar falsos positivos em buscas amplas)
    if real_val >= 100:
        return None

    for count_str in count_pattern.findall(claim_text):
        try:
            mentioned = int(count_str)
        except ValueError:
            # T-04 Tipo D: regex may capture non-int fragments; skip
            # and let other matches in the loop be evaluated.
            continue
        if mentioned > real_val * 2:
            return (
                f"Contagem mencionada ({mentioned}) muito maior que resultado real "
                f"({real_count}) — excede o dobro"
            )
    return None


async def validate_evaluation_score_claim(
    claim_text: str, context_data: dict[str, Any]
) -> str | None:
    """
    Valida scores de avaliação em evaluation/interview domains.
    Delega à mesma lógica de cv_score_claim.
    """
    return await validate_cv_score_claim(claim_text, context_data)

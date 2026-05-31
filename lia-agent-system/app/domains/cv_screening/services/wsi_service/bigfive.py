"""Canonical Big Five (OCEAN) trait ranking — formula deterministica F3.

Consolidacao WSI Fase 2.4b (decisao Paulo 2026-05-31): portado de
``job_creation/services/wsi_question_generator.py`` para o canonico cv_screening
— single source of truth. Inclui a formula hibrida de ate 4 camadas
(LLM + O*NET prior + CompanyCulture + DeptHistory blend) que respeita
ADR-LGPD-001 (agregados departamentais anonimizados, gate MIN_DEPT_SAMPLES>=10
aplicado upstream em BigFiveDepartmentService).

cv_screening passa a ser dono do Big Five RICO. O fork job_creation.rank_traits
delega a este modulo (thin adapter) ate ser deletado na Fase 4. ``rank_traits``
e PURO/deterministico (sem LLM, sem DB) — facilmente testavel.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Os 5 traits OCEAN canonicos.
TRAITS = ("openness", "conscientiousness", "extraversion", "agreeableness", "stability")

# Pesos da formula F3 (identicos ao fork — zero mudanca de comportamento).
TRAIT_FORMULA_WEIGHTS = {"llm": 0.40, "prior": 0.35, "seniority_boost": 0.25}
TRAIT_FORMULA_WEIGHTS_4L = {"llm": 0.40, "onet": 0.20, "culture": 0.15, "dept": 0.25}
TRAIT_FORMULA_WEIGHTS_3L = {"llm": 0.40, "onet": 0.35, "culture": 0.25}

# O*NET prior profiles por arquetipo de cargo (simplificado).
ONET_PRIOR_PROFILES = {
    "engineering": {"openness": 0.7, "conscientiousness": 0.8, "extraversion": 0.4, "agreeableness": 0.5, "stability": 0.7},
    "product": {"openness": 0.8, "conscientiousness": 0.6, "extraversion": 0.7, "agreeableness": 0.6, "stability": 0.6},
    "design": {"openness": 0.9, "conscientiousness": 0.5, "extraversion": 0.5, "agreeableness": 0.6, "stability": 0.6},
    "sales": {"openness": 0.5, "conscientiousness": 0.6, "extraversion": 0.9, "agreeableness": 0.7, "stability": 0.5},
    "operations": {"openness": 0.4, "conscientiousness": 0.9, "extraversion": 0.5, "agreeableness": 0.6, "stability": 0.7},
    "default": {"openness": 0.5, "conscientiousness": 0.7, "extraversion": 0.5, "agreeableness": 0.6, "stability": 0.6},
}

# Seniority boosts para ranking de traits (F3).
SENIORITY_TRAIT_BOOSTS = {
    "junior": {"conscientiousness": 0.2, "agreeableness": 0.1},
    "pleno": {"conscientiousness": 0.1, "openness": 0.1},
    "senior": {"openness": 0.15, "stability": 0.1},
    "lead": {"extraversion": 0.2, "stability": 0.15},
    "diretor": {"extraversion": 0.2, "openness": 0.15, "stability": 0.1},
}


def get_blend_score(blend, trait: str) -> float:
    """Extrai score de blend para um trait de BigFiveBlend.

    Stability: alto = bom em ambas BigFiveBlend e CompanyCultureProfile (sem
    inversao, simplificado pos P0.5 Sprint B Phase 2). Fail-soft: 0.5 default.
    """
    if blend is None:
        return 0.5
    val = getattr(blend, f"{trait}_score", None)
    return val if val is not None else 0.5


def rank_traits(
    llm_scores: dict[str, float],
    seniority: str,
    role_archetype: str = "default",
    dept_blend=None,  # Optional[BigFiveBlend] — Sprint B Phase 2 Layer 4
) -> list[dict[str, Any]]:
    """F3 — ranking deterministico de traits (formula hibrida ate 4 camadas).

    4-layer (dept_blend.method == "dept_blend", >=10 samples, toggle ON):
      score = 0.40*LLM + 0.20*O*NET + (0.15+0.25)*DeptHistory
    3-layer (dept_blend.method == "company_culture"):
      score = 0.40*LLM + 0.35*O*NET + 0.25*CompanyCulture
    2-layer fallback (dept_blend None ou method == "llm_only"):
      score = 0.40*LLM + 0.35*O*NET + 0.25*SeniorityBoost

    Args:
        llm_scores: dict trait->[0.0,1.0] (output do extractor Big Five LLM).
        seniority: nivel da vaga (chave de SENIORITY_TRAIT_BOOSTS).
        role_archetype: chave de ONET_PRIOR_PROFILES.
        dept_blend: BigFiveBlend opcional (Layer 3/4 — ADR-LGPD-001 upstream).

    Returns:
        Lista de dicts ordenada desc por score, cada um com
        {trait, score, llm_score, prior_score, boost, blend_method, rank, weight}.
        ``weight`` normaliza scores para somar ~1.0. Superset do TraitRanking do FE.
    """
    onet_prior = ONET_PRIOR_PROFILES.get(role_archetype, ONET_PRIOR_PROFILES["default"])
    boosts = SENIORITY_TRAIT_BOOSTS.get(seniority, {})
    blend_method = "llm_only"
    if dept_blend is not None and hasattr(dept_blend, "method"):
        blend_method = dept_blend.method

    rankings: list[dict[str, Any]] = []
    for trait in TRAITS:
        llm_val = float(llm_scores.get(trait, 0.5))
        onet_val = onet_prior.get(trait, 0.5)
        boost_val = boosts.get(trait, 0.0)

        if blend_method == "dept_blend" and dept_blend is not None:
            blend_prior = get_blend_score(dept_blend, trait)
            score = (
                TRAIT_FORMULA_WEIGHTS_4L["llm"] * llm_val
                + TRAIT_FORMULA_WEIGHTS_4L["onet"] * onet_val
                + (TRAIT_FORMULA_WEIGHTS_4L["culture"] + TRAIT_FORMULA_WEIGHTS_4L["dept"]) * blend_prior
            )
        elif blend_method == "company_culture" and dept_blend is not None:
            culture_prior = get_blend_score(dept_blend, trait)
            score = (
                TRAIT_FORMULA_WEIGHTS_3L["llm"] * llm_val
                + TRAIT_FORMULA_WEIGHTS_3L["onet"] * onet_val
                + TRAIT_FORMULA_WEIGHTS_3L["culture"] * culture_prior
            )
        else:
            score = (
                TRAIT_FORMULA_WEIGHTS["llm"] * llm_val
                + TRAIT_FORMULA_WEIGHTS["prior"] * onet_val
                + TRAIT_FORMULA_WEIGHTS["seniority_boost"] * boost_val
            )

        rankings.append({
            "trait": trait,
            "score": round(score, 4),
            "llm_score": llm_val,
            "prior_score": onet_val,
            "boost": boost_val,
            "blend_method": blend_method,
        })

    rankings.sort(key=lambda x: x["score"], reverse=True)
    total_score = sum(r["score"] for r in rankings) or 1.0
    for i, r in enumerate(rankings):
        r["rank"] = i + 1
        r["weight"] = round(r["score"] / total_score, 4)

    logger.info(
        "[WSI:F3 canonical] Trait ranking (method=%s): %s",
        blend_method,
        " > ".join(f"{r['trait']}({r['score']:.3f})" for r in rankings),
    )
    return rankings

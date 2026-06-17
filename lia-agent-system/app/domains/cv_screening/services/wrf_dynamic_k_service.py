"""
WRF Dynamic K Service (WDT-014 + Fase 5 / A6)
Adjusts Weighted Rank Fusion K parameter based on job qualification level.
K controls result diversity: lower K = more precision, higher K = more recall.

Fase 5 enhancement: Quality-adaptive K that adjusts based on match score distribution.
If top scores cluster high → reduce K for precision. If scores spread low → increase K for recall.
"""
import logging
import os
import statistics
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_K_VALUES = {
    "alta": 25,
    "media": 45,
    "baixa": 70,
}

SCORE_WEIGHTS = {
    "alta": {"es": 0.6, "pgv": 0.4},
    "media": {"es": 0.5, "pgv": 0.5},
    "baixa": {"es": 0.4, "pgv": 0.6},
}

K_ADJUSTMENT_BOUNDS = {
    "min_k": 10,
    "max_k": 100,
    "high_quality_threshold": 0.75,
    "low_quality_threshold": 0.35,
    "k_reduction_factor": 0.7,
    "k_increase_factor": 1.4,
}


class WRFDynamicKService:
    def __init__(self):
        self.k_values = {
            "alta": int(os.environ.get("WRF_K_ALTA", DEFAULT_K_VALUES["alta"])),
            "media": int(os.environ.get("WRF_K_MEDIA", DEFAULT_K_VALUES["media"])),
            "baixa": int(os.environ.get("WRF_K_BAIXA", DEFAULT_K_VALUES["baixa"])),
        }
        self.weights = SCORE_WEIGHTS.copy()
        self.adaptive_enabled = os.environ.get("WRF_ADAPTIVE_K", "true").lower() == "true"

    def get_k(self, qualification_level: str | None = None) -> int:
        level = (qualification_level or "media").lower()
        return self.k_values.get(level, self.k_values["media"])

    def get_weights(self, qualification_level: str | None = None) -> dict[str, float]:
        level = (qualification_level or "media").lower()
        return self.weights.get(level, self.weights["media"])

    def compute_adaptive_k(
        self,
        base_k: int,
        es_scores: list[float],
        pgv_scores: list[float],
    ) -> dict[str, Any]:
        if not self.adaptive_enabled or len(es_scores) < 3:
            return {"k": base_k, "adjusted": False, "reason": "adaptive_disabled_or_insufficient_data"}

        all_scores = [s for s in (es_scores + pgv_scores) if s > 0]
        if not all_scores:
            return {"k": base_k, "adjusted": False, "reason": "no_valid_scores"}

        top_n = max(1, len(all_scores) // 4)
        sorted_scores = sorted(all_scores, reverse=True)
        top_avg = statistics.mean(sorted_scores[:top_n])

        bounds = K_ADJUSTMENT_BOUNDS
        adjusted_k = base_k
        reason = "no_adjustment"

        if top_avg >= bounds["high_quality_threshold"]:
            adjusted_k = max(
                bounds["min_k"],
                int(base_k * bounds["k_reduction_factor"]),
            )
            reason = f"high_quality_cluster(top_avg={top_avg:.3f})→precision"
        elif top_avg <= bounds["low_quality_threshold"]:
            adjusted_k = min(
                bounds["max_k"],
                int(base_k * bounds["k_increase_factor"]),
            )
            reason = f"low_quality_spread(top_avg={top_avg:.3f})→recall"

        score_spread = statistics.stdev(all_scores) if len(all_scores) > 1 else 0
        if score_spread < 0.05 and adjusted_k == base_k:
            adjusted_k = max(bounds["min_k"], base_k - 10)
            reason = f"tight_cluster(spread={score_spread:.4f})→precision"

        return {
            "k": adjusted_k,
            "base_k": base_k,
            "adjusted": adjusted_k != base_k,
            "reason": reason,
            "top_avg": round(top_avg, 4),
            "score_spread": round(score_spread, 4) if score_spread else 0,
        }

    def compute_wrf_score(self, es_rank: int, pgv_rank: int, qualification_level: str | None = None, k_override: int | None = None) -> float:
        k = k_override if k_override is not None else self.get_k(qualification_level)
        weights = self.get_weights(qualification_level)
        es_rrf = 1.0 / (k + es_rank)
        pgv_rrf = 1.0 / (k + pgv_rank)
        return weights["es"] * es_rrf + weights["pgv"] * pgv_rrf

    def rank_candidates(
        self,
        candidates: list[dict[str, Any]],
        qualification_level: str | None = None,
        es_scores: list[float] | None = None,
        pgv_scores: list[float] | None = None,
    ) -> list[dict[str, Any]]:
        base_k = self.get_k(qualification_level)
        weights = self.get_weights(qualification_level)

        adaptive_result = None
        k = base_k
        if es_scores is not None and pgv_scores is not None:
            adaptive_result = self.compute_adaptive_k(base_k, es_scores, pgv_scores)
            k = adaptive_result["k"]

        ranked = []
        for i, candidate in enumerate(candidates):
            es_rank = candidate.get("es_rank", i + 1)
            pgv_rank = candidate.get("pgv_rank", i + 1)
            wrf_score = self.compute_wrf_score(es_rank, pgv_rank, qualification_level, k_override=k)
            ranked.append({
                **candidate,
                "wrf_score": round(wrf_score, 6),
                "wrf_k_used": k,
                "wrf_weights": weights,
            })

        ranked.sort(key=lambda x: x["wrf_score"], reverse=True)

        for i, item in enumerate(ranked):
            item["wrf_rank"] = i + 1

        log_extra = ""
        if adaptive_result and adaptive_result["adjusted"]:
            log_extra = f", adaptive={adaptive_result['reason']}"
            for item in ranked:
                item["wrf_adaptive"] = adaptive_result

        logger.info(
            "WRF ranking: K=%d, weights=%s, level=%s, candidates=%d%s",
            k, weights, qualification_level, len(ranked), log_extra,
        )
        return ranked

    def get_config(self) -> dict[str, Any]:
        return {
            "k_values": self.k_values,
            "weights": self.weights,
            "defaults": DEFAULT_K_VALUES,
            "adaptive_enabled": self.adaptive_enabled,
            "adjustment_bounds": K_ADJUSTMENT_BOUNDS,
        }


wrf_dynamic_k_service = WRFDynamicKService()

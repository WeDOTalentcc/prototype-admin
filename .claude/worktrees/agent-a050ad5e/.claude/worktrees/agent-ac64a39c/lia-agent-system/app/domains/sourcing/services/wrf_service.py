"""
WRF Dynamic K Service (WDT-014)
Adjusts Weighted Rank Fusion K parameter based on job qualification level.
K controls result diversity: lower K = more precision, higher K = more recall.
"""
import logging
import os
from typing import Optional, Dict, Any, List

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


class WRFDynamicKService:
    def __init__(self):
        self.k_values = {
            "alta": int(os.environ.get("WRF_K_ALTA", DEFAULT_K_VALUES["alta"])),
            "media": int(os.environ.get("WRF_K_MEDIA", DEFAULT_K_VALUES["media"])),
            "baixa": int(os.environ.get("WRF_K_BAIXA", DEFAULT_K_VALUES["baixa"])),
        }
        self.weights = SCORE_WEIGHTS.copy()

    def get_k(self, qualification_level: Optional[str] = None) -> int:
        level = (qualification_level or "media").lower()
        return self.k_values.get(level, self.k_values["media"])

    def get_weights(self, qualification_level: Optional[str] = None) -> Dict[str, float]:
        level = (qualification_level or "media").lower()
        return self.weights.get(level, self.weights["media"])

    def compute_wrf_score(self, es_rank: int, pgv_rank: int, qualification_level: Optional[str] = None) -> float:
        k = self.get_k(qualification_level)
        weights = self.get_weights(qualification_level)
        es_rrf = 1.0 / (k + es_rank)
        pgv_rrf = 1.0 / (k + pgv_rank)
        return weights["es"] * es_rrf + weights["pgv"] * pgv_rrf

    def rank_candidates(self, candidates: List[Dict[str, Any]], qualification_level: Optional[str] = None) -> List[Dict[str, Any]]:
        k = self.get_k(qualification_level)
        weights = self.get_weights(qualification_level)
        
        ranked = []
        for i, candidate in enumerate(candidates):
            es_rank = candidate.get("es_rank", i + 1)
            pgv_rank = candidate.get("pgv_rank", i + 1)
            wrf_score = self.compute_wrf_score(es_rank, pgv_rank, qualification_level)
            ranked.append({
                **candidate,
                "wrf_score": round(wrf_score, 6),
                "wrf_k_used": k,
                "wrf_weights": weights,
            })
        
        ranked.sort(key=lambda x: x["wrf_score"], reverse=True)
        
        for i, item in enumerate(ranked):
            item["wrf_rank"] = i + 1
        
        logger.info(f"WRF ranking: K={k}, weights={weights}, level={qualification_level}, candidates={len(ranked)}")
        return ranked

    def get_config(self) -> Dict[str, Any]:
        return {
            "k_values": self.k_values,
            "weights": self.weights,
            "defaults": DEFAULT_K_VALUES,
        }


wrf_dynamic_k_service = WRFDynamicKService()

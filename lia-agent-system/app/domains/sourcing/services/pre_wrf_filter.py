"""
Pre-WRF Filter Orchestrator (WDT-015)
Orchestrates ES score drop analysis and PGVector gap analysis before WRF fusion.
Applies adaptive filtering based on job qualification level.
"""
import logging
from datetime import datetime
from typing import Any

from app.shared.services.es_score_drop_analyzer import es_score_drop_analyzer
from app.shared.services.pgv_gap_analyzer import pgv_gap_analyzer
from app.shared.services.wrf_dynamic_k_service import wrf_dynamic_k_service

logger = logging.getLogger(__name__)


class PreWRFFilterService:
    def orchestrate(self, es_candidates: list[dict[str, Any]], pgv_candidates: list[dict[str, Any]],
                    qualification_level: str | None = None) -> dict[str, Any]:
        level = (qualification_level or "media").lower()
        started_at = datetime.utcnow()

        es_result = es_score_drop_analyzer.analyze(es_candidates, level)
        pgv_result = pgv_gap_analyzer.analyze(pgv_candidates, level)

        es_filtered_ids = {c.get("id", c.get("candidate_id", "")) for c in es_result["filtered_candidates"]}
        pgv_filtered_ids = {c.get("id", c.get("candidate_id", "")) for c in pgv_result["filtered_candidates"]}

        survived_ids = es_filtered_ids | pgv_filtered_ids

        candidate_map = {}
        for c in es_candidates:
            cid = c.get("id", c.get("candidate_id", ""))
            if cid:
                candidate_map[cid] = {**c}
        
        for c in pgv_candidates:
            cid = c.get("id", c.get("candidate_id", ""))
            if cid and cid in candidate_map:
                candidate_map[cid]["pgv_distance"] = c.get("pgv_distance", c.get("distance"))
                candidate_map[cid]["pgv_rank"] = c.get("pgv_rank")
            elif cid:
                candidate_map[cid] = {**c}

        survivors = []
        for cid, data in candidate_map.items():
            if cid in survived_ids:
                survivors.append(data)

        for i, s in enumerate(survivors):
            if "es_rank" not in s:
                s["es_rank"] = i + 1
            if "pgv_rank" not in s:
                s["pgv_rank"] = i + 1

        wrf_ranked = wrf_dynamic_k_service.rank_candidates(survivors, level)
        
        k_used = wrf_dynamic_k_service.get_k(level)
        weights_used = wrf_dynamic_k_service.get_weights(level)

        elapsed = (datetime.utcnow() - started_at).total_seconds()

        pipeline_log = {
            "qualification_level": level,
            "input": {
                "es_candidates": len(es_candidates),
                "pgv_candidates": len(pgv_candidates),
                "unique_candidates": len(candidate_map),
            },
            "es_filter": {
                "output": es_result["total_output"],
                "cutoff_index": es_result["cutoff_index"],
                "threshold": es_result["threshold_used"],
                "top_score": es_result.get("top_score"),
            },
            "pgv_filter": {
                "output": pgv_result["total_output"],
                "gap_index": pgv_result["gap_index"],
                "multiplier": pgv_result["multiplier_used"],
            },
            "fusion": {
                "survived": len(survivors),
                "k_used": k_used,
                "weights": weights_used,
            },
            "output": {
                "final_candidates": len(wrf_ranked),
            },
            "elapsed_seconds": round(elapsed, 4),
        }

        logger.info(f"Pre-WRF pipeline: {len(es_candidates)} ES + {len(pgv_candidates)} PGV → "
                    f"{len(survivors)} survived → {len(wrf_ranked)} ranked (K={k_used}, level={level}, "
                    f"elapsed={elapsed:.3f}s)")

        return {
            "candidates": wrf_ranked,
            "pipeline_log": pipeline_log,
            "es_analysis": es_result["analysis"],
            "pgv_analysis": pgv_result["analysis"],
        }


pre_wrf_filter_service = PreWRFFilterService()

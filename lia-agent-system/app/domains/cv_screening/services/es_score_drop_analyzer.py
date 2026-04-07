"""
ES Score Drop Analyzer (WDT-011)
Analyzes Elasticsearch score decay patterns to identify natural cutoff points.
Uses adaptive thresholds based on job qualification level.
"""
import logging
import statistics
from typing import Any

logger = logging.getLogger(__name__)

DROP_THRESHOLDS = {
    "alta": 0.40,
    "media": 0.55,
    "baixa": 0.70,
}


class EsScoreDropAnalyzer:
    def __init__(self):
        self.thresholds = DROP_THRESHOLDS.copy()

    def analyze(self, candidates: list[dict[str, Any]], qualification_level: str | None = None) -> dict[str, Any]:
        if not candidates:
            return {
                "filtered_candidates": [],
                "removed_candidates": [],
                "cutoff_index": 0,
                "cutoff_score": 0,
                "top_score": 0,
                "threshold_used": 0,
                "qualification_level": qualification_level,
                "analysis": "No candidates to analyze",
            }

        level = (qualification_level or "media").lower()
        threshold = self.thresholds.get(level, self.thresholds["media"])

        sorted_candidates = sorted(candidates, key=lambda c: c.get("es_score", c.get("score", 0)), reverse=True)
        
        top_score = sorted_candidates[0].get("es_score", sorted_candidates[0].get("score", 100))
        if top_score <= 0:
            top_score = 100

        cutoff_score = top_score * (1 - threshold)
        cutoff_index = len(sorted_candidates)

        drops = []
        for i, candidate in enumerate(sorted_candidates):
            score = candidate.get("es_score", candidate.get("score", 0))
            drop_pct = ((top_score - score) / top_score) * 100 if top_score > 0 else 0
            candidate["es_drop_pct"] = round(drop_pct, 2)
            
            if score < cutoff_score and cutoff_index == len(sorted_candidates):
                cutoff_index = i
            
            if i > 0:
                prev_score = sorted_candidates[i - 1].get("es_score", sorted_candidates[i - 1].get("score", 0))
                inter_drop = ((prev_score - score) / prev_score) * 100 if prev_score > 0 else 0
                drops.append(inter_drop)

        steep_drop_index = None
        if len(drops) >= 3:
            mean_drop = statistics.mean(drops)
            std_drop = statistics.stdev(drops) if len(drops) > 1 else 0
            for i, drop in enumerate(drops):
                if drop > mean_drop + 2 * std_drop and i > 0:
                    steep_drop_index = i + 1
                    break

        if steep_drop_index and steep_drop_index < cutoff_index:
            cutoff_index = steep_drop_index

        filtered = sorted_candidates[:cutoff_index]
        removed = sorted_candidates[cutoff_index:]

        analysis = (
            f"Score drop analysis: top_score={top_score:.1f}, threshold={threshold*100:.0f}%, "
            f"cutoff_score={cutoff_score:.1f}, cutoff_index={cutoff_index}/{len(sorted_candidates)}, "
            f"steep_drop_at={steep_drop_index}, level={level}"
        )
        logger.info(analysis)

        return {
            "filtered_candidates": filtered,
            "removed_candidates": removed,
            "cutoff_index": cutoff_index,
            "cutoff_score": round(cutoff_score, 2),
            "top_score": round(top_score, 2),
            "threshold_used": threshold,
            "qualification_level": level,
            "steep_drop_index": steep_drop_index,
            "total_input": len(candidates),
            "total_output": len(filtered),
            "analysis": analysis,
        }


es_score_drop_analyzer = EsScoreDropAnalyzer()

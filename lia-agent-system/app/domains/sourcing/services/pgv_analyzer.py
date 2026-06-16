"""
PGVector Gap Analyzer (WDT-012)
Analyzes semantic embedding distance gaps to identify natural cluster boundaries.
Uses adaptive gap multipliers based on job qualification level.
"""
import logging
import statistics
from typing import Any

logger = logging.getLogger(__name__)

GAP_MULTIPLIERS = {
    "alta": 1.5,
    "media": 2.0,
    "baixa": 2.5,
}


class PgvGapAnalyzer:
    def __init__(self):
        self.multipliers = GAP_MULTIPLIERS.copy()

    def analyze(self, candidates: list[dict[str, Any]], qualification_level: str | None = None) -> dict[str, Any]:
        if not candidates:
            return {
                "filtered_candidates": [],
                "removed_candidates": [],
                "gap_index": 0,
                "gap_threshold": 0,
                "qualification_level": qualification_level,
                "analysis": "No candidates to analyze",
            }

        level = (qualification_level or "media").lower()
        multiplier = self.multipliers.get(level, self.multipliers["media"])

        sorted_candidates = sorted(candidates, key=lambda c: c.get("pgv_distance", c.get("distance", 1.0)))

        distances = [c.get("pgv_distance", c.get("distance", 1.0)) for c in sorted_candidates]

        gaps = []
        for i in range(1, len(distances)):
            gap = distances[i] - distances[i - 1]
            gaps.append(gap)

        gap_index = len(sorted_candidates)
        gap_threshold = 0

        if gaps:
            mean_gap = statistics.mean(gaps)
            std_gap = statistics.stdev(gaps) if len(gaps) > 1 else mean_gap * 0.5
            gap_threshold = mean_gap + multiplier * std_gap

            for i, gap in enumerate(gaps):
                if gap > gap_threshold:
                    gap_index = i + 1
                    break

        for i, candidate in enumerate(sorted_candidates):
            candidate["pgv_rank"] = i + 1
            if i > 0:
                candidate["pgv_gap_from_prev"] = round(distances[i] - distances[i - 1], 4)
            else:
                candidate["pgv_gap_from_prev"] = 0

        filtered = sorted_candidates[:gap_index]
        removed = sorted_candidates[gap_index:]

        analysis = (
            f"PGV gap analysis: multiplier={multiplier}x, gap_threshold={gap_threshold:.4f}, "
            f"gap_index={gap_index}/{len(sorted_candidates)}, level={level}"
        )
        logger.info(analysis)

        return {
            "filtered_candidates": filtered,
            "removed_candidates": removed,
            "gap_index": gap_index,
            "gap_threshold": round(gap_threshold, 4),
            "multiplier_used": multiplier,
            "qualification_level": level,
            "mean_gap": round(statistics.mean(gaps), 4) if gaps else 0,
            "std_gap": round(statistics.stdev(gaps), 4) if len(gaps) > 1 else 0,
            "total_input": len(candidates),
            "total_output": len(filtered),
            "analysis": analysis,
        }


pgv_gap_analyzer = PgvGapAnalyzer()

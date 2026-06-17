"""
WSI Observability Service - Read-Only Metrics for WSI Screening Performance.

CRITICAL: This service is READ-ONLY. It does NOT modify WSI weights, criteria,
or any configuration. The WSI methodology must NOT be altered automatically.

Provides observability into:
- Score vs outcome correlation
- Block-level accuracy analysis
- Score distribution statistics
- Threshold analysis for different cutoff points
"""
import logging
import math
import statistics
from typing import Any

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.candidate import VacancyCandidate
from lia_models.feedback_learning import JobOutcome, JobOutcomeType

logger = logging.getLogger(__name__)

MIN_SAMPLE_SIZE = 10
HIRED_STATUSES = {"hired", "contratado"}
REJECTED_STATUSES = {"rejected", "reprovado", "recusado"}

WSI_BLOCKS = [
    "technical",
    "behavioral",
    "cultural_fit",
    "eligibility",
    "experience",
    "education",
    "leadership",
]


def _point_biserial_correlation(scores: list[float], outcomes: list[int]) -> float | None:
    if len(scores) < MIN_SAMPLE_SIZE or len(set(outcomes)) < 2:
        return None

    n = len(scores)
    n1 = sum(outcomes)
    n0 = n - n1
    if n0 == 0 or n1 == 0:
        return None

    scores_1 = [s for s, o in zip(scores, outcomes) if o == 1]
    scores_0 = [s for s, o in zip(scores, outcomes) if o == 0]

    mean_1 = statistics.mean(scores_1)
    mean_0 = statistics.mean(scores_0)

    try:
        std_all = statistics.stdev(scores)
    except statistics.StatisticsError:
        return None

    if std_all == 0:
        return None

    r = ((mean_1 - mean_0) / std_all) * math.sqrt((n1 * n0) / (n * n))
    return max(-1.0, min(1.0, r))


def _classify_predictive_power(correlation: float | None) -> str:
    if correlation is None:
        return "insufficient_data"
    abs_corr = abs(correlation)
    if abs_corr >= 0.5:
        return "high"
    elif abs_corr >= 0.3:
        return "medium"
    return "low"


class WSIObservabilityService:
    """
    Read-only observability service for WSI screening metrics.

    All methods are purely analytical - they query data and compute statistics
    without modifying any WSI configuration, weights, or criteria.
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    async def _get_scored_candidates_with_outcomes(
        self, company_id: str, db: AsyncSession
    ) -> list[dict[str, Any]]:
        stmt = (
            select(
                VacancyCandidate.id,
                VacancyCandidate.vacancy_id,
                VacancyCandidate.candidate_id,
                VacancyCandidate.lia_score,
                VacancyCandidate.match_percentage,
                VacancyCandidate.status,
                VacancyCandidate.stage,
                VacancyCandidate.additional_data,
                JobOutcome.outcome,
                JobOutcome.job_id,
            )
            .outerjoin(
                JobOutcome,
                and_(
                    VacancyCandidate.vacancy_id == JobOutcome.job_id,
                    JobOutcome.company_id == company_id,
                ),
            )
            .where(
                and_(
                    VacancyCandidate.company_id == company_id,
                    VacancyCandidate.lia_score.isnot(None),
                )
            )
        )

        result = await db.execute(stmt)
        rows = result.all()

        records = []
        for row in rows:
            is_hired = row.status in HIRED_STATUSES or row.stage in HIRED_STATUSES
            job_filled = row.outcome == JobOutcomeType.FILLED if row.outcome else False

            additional = row.additional_data or {}
            block_scores = additional.get("block_scores", additional.get("wsi_blocks", {}))

            records.append({
                "id": str(row.id),
                "vacancy_id": str(row.vacancy_id),
                "candidate_id": str(row.candidate_id),
                "lia_score": float(row.lia_score) if row.lia_score is not None else None,
                "match_percentage": float(row.match_percentage) if row.match_percentage is not None else None,
                "status": row.status,
                "stage": row.stage,
                "is_hired": is_hired,
                "job_filled": job_filled,
                "block_scores": block_scores,
            })

        return records

    async def get_score_vs_outcome_correlation(
        self, company_id: str, db: AsyncSession
    ) -> dict[str, Any]:
        records = await self._get_scored_candidates_with_outcomes(company_id, db)

        scored_records = [r for r in records if r["lia_score"] is not None]

        if len(scored_records) < MIN_SAMPLE_SIZE:
            return {
                "insufficient_data": True,
                "sample_size": len(scored_records),
                "minimum_required": MIN_SAMPLE_SIZE,
                "message": f"Need at least {MIN_SAMPLE_SIZE} scored candidates for correlation analysis",
            }

        scores = [r["lia_score"] for r in scored_records]
        outcomes = [1 if r["is_hired"] else 0 for r in scored_records]

        correlation = _point_biserial_correlation(scores, outcomes)

        ranges = [
            ("0-20", 0, 20),
            ("20-40", 20, 40),
            ("40-60", 40, 60),
            ("60-80", 60, 80),
            ("80-100", 80, 100),
        ]

        score_ranges = []
        for label, low, high in ranges:
            in_range = [r for r in scored_records if low <= (r["lia_score"] or 0) < high + (1 if high == 100 else 0)]
            hired_in_range = [r for r in in_range if r["is_hired"]]
            if in_range:
                score_ranges.append({
                    "range": label,
                    "hired_rate": round(len(hired_in_range) / len(in_range), 4),
                    "sample_count": len(in_range),
                    "hired_count": len(hired_in_range),
                })

        return {
            "insufficient_data": False,
            "correlation_coefficient": round(correlation, 4) if correlation is not None else None,
            "predictive_power": _classify_predictive_power(correlation),
            "sample_size": len(scored_records),
            "hired_count": sum(outcomes),
            "not_hired_count": len(outcomes) - sum(outcomes),
            "score_ranges": score_ranges,
        }

    async def get_block_accuracy(
        self, company_id: str, db: AsyncSession
    ) -> dict[str, Any]:
        records = await self._get_scored_candidates_with_outcomes(company_id, db)

        records_with_blocks = [r for r in records if r.get("block_scores") and isinstance(r["block_scores"], dict)]

        if len(records_with_blocks) < MIN_SAMPLE_SIZE:
            return {
                "insufficient_data": True,
                "sample_size": len(records_with_blocks),
                "minimum_required": MIN_SAMPLE_SIZE,
                "message": f"Need at least {MIN_SAMPLE_SIZE} candidates with block-level scores",
                "blocks": [],
            }

        all_blocks = set()
        for r in records_with_blocks:
            all_blocks.update(r["block_scores"].keys())

        block_results = []
        for block_name in sorted(all_blocks):
            block_scores = []
            block_outcomes = []
            for r in records_with_blocks:
                score = r["block_scores"].get(block_name)
                if score is not None:
                    try:
                        block_scores.append(float(score))
                        block_outcomes.append(1 if r["is_hired"] else 0)
                    except (ValueError, TypeError):
                        continue

            if len(block_scores) < MIN_SAMPLE_SIZE:
                block_results.append({
                    "block_name": block_name,
                    "correlation": None,
                    "sample_size": len(block_scores),
                    "predictive_power": "insufficient_data",
                })
                continue

            correlation = _point_biserial_correlation(block_scores, block_outcomes)
            block_results.append({
                "block_name": block_name,
                "correlation": round(correlation, 4) if correlation is not None else None,
                "sample_size": len(block_scores),
                "predictive_power": _classify_predictive_power(correlation),
                "avg_score_hired": round(statistics.mean([s for s, o in zip(block_scores, block_outcomes) if o == 1]), 2) if any(o == 1 for o in block_outcomes) else None,
                "avg_score_not_hired": round(statistics.mean([s for s, o in zip(block_scores, block_outcomes) if o == 0]), 2) if any(o == 0 for o in block_outcomes) else None,
            })

        block_results.sort(key=lambda x: abs(x["correlation"] or 0), reverse=True)

        return {
            "insufficient_data": False,
            "sample_size": len(records_with_blocks),
            "blocks": block_results,
        }

    async def get_score_distribution(
        self, company_id: str, db: AsyncSession
    ) -> dict[str, Any]:
        records = await self._get_scored_candidates_with_outcomes(company_id, db)

        scored = [r for r in records if r["lia_score"] is not None]

        if len(scored) < 2:
            return {
                "insufficient_data": True,
                "total_evaluated": len(scored),
                "minimum_required": 2,
                "message": "Need at least 2 scored candidates for distribution analysis",
            }

        all_scores = [r["lia_score"] for r in scored]
        hired_scores = [r["lia_score"] for r in scored if r["is_hired"]]
        not_hired_scores = [r["lia_score"] for r in scored if not r["is_hired"]]

        sorted_scores = sorted(all_scores)
        n = len(sorted_scores)

        def percentile(data, p):
            k = (len(data) - 1) * (p / 100)
            f = math.floor(k)
            c = math.ceil(k)
            if f == c:
                return data[int(k)]
            return data[f] * (c - k) + data[c] * (k - f)

        try:
            std_dev = statistics.stdev(all_scores)
        except statistics.StatisticsError:
            std_dev = 0.0

        result = {
            "insufficient_data": False,
            "total_evaluated": n,
            "avg_score": round(statistics.mean(all_scores), 2),
            "median_score": round(statistics.median(all_scores), 2),
            "std_dev": round(std_dev, 2),
            "min_score": round(min(all_scores), 2),
            "max_score": round(max(all_scores), 2),
            "percentiles": {
                "p25": round(percentile(sorted_scores, 25), 2),
                "p50": round(percentile(sorted_scores, 50), 2),
                "p75": round(percentile(sorted_scores, 75), 2),
                "p90": round(percentile(sorted_scores, 90), 2),
            },
            "by_outcome": {},
        }

        if hired_scores:
            result["by_outcome"]["hired"] = {
                "avg": round(statistics.mean(hired_scores), 2),
                "median": round(statistics.median(hired_scores), 2),
                "count": len(hired_scores),
                "min": round(min(hired_scores), 2),
                "max": round(max(hired_scores), 2),
            }

        if not_hired_scores:
            result["by_outcome"]["not_hired"] = {
                "avg": round(statistics.mean(not_hired_scores), 2),
                "median": round(statistics.median(not_hired_scores), 2),
                "count": len(not_hired_scores),
                "min": round(min(not_hired_scores), 2),
                "max": round(max(not_hired_scores), 2),
            }

        return result

    async def get_threshold_analysis(
        self, company_id: str, db: AsyncSession
    ) -> dict[str, Any]:
        records = await self._get_scored_candidates_with_outcomes(company_id, db)

        scored = [r for r in records if r["lia_score"] is not None]

        if len(scored) < MIN_SAMPLE_SIZE:
            return {
                "insufficient_data": True,
                "sample_size": len(scored),
                "minimum_required": MIN_SAMPLE_SIZE,
                "message": f"Need at least {MIN_SAMPLE_SIZE} scored candidates for threshold analysis",
                "thresholds": [],
            }

        total_hired = sum(1 for r in scored if r["is_hired"])

        thresholds = [50, 60, 70, 80, 90]
        threshold_results = []

        for threshold in thresholds:
            above = [r for r in scored if (r["lia_score"] or 0) >= threshold]
            below = [r for r in scored if (r["lia_score"] or 0) < threshold]

            hired_above = sum(1 for r in above if r["is_hired"])
            hired_below = sum(1 for r in below if r["is_hired"])

            precision = (hired_above / len(above)) if above else 0
            recall = (hired_above / total_hired) if total_hired > 0 else 0

            f1 = 0
            if precision + recall > 0:
                f1 = 2 * (precision * recall) / (precision + recall)

            threshold_results.append({
                "threshold": threshold,
                "candidates_above": len(above),
                "candidates_below": len(below),
                "candidates_hired_above": hired_above,
                "candidates_hired_below": hired_below,
                "precision": round(precision, 4),
                "recall": round(recall, 4),
                "f1_score": round(f1, 4),
            })

        return {
            "insufficient_data": False,
            "sample_size": len(scored),
            "total_hired": total_hired,
            "thresholds": threshold_results,
        }

    async def get_observability_summary(
        self, company_id: str, db: AsyncSession
    ) -> dict[str, Any]:
        correlation_data = await self.get_score_vs_outcome_correlation(company_id, db)
        block_data = await self.get_block_accuracy(company_id, db)
        distribution_data = await self.get_score_distribution(company_id, db)
        threshold_data = await self.get_threshold_analysis(company_id, db)

        alerts = []

        corr_value = correlation_data.get("correlation_coefficient")
        if corr_value is not None and abs(corr_value) < 0.3:
            alerts.append({
                "type": "low_correlation",
                "severity": "warning",
                "message": (
                    f"WSI score correlation with hiring outcomes is low ({corr_value:.3f}). "
                    "This may indicate the scoring criteria need manual review by the team."
                ),
                "recommendation": "Review WSI block weights and criteria alignment with actual hiring decisions.",
            })

        if correlation_data.get("insufficient_data"):
            alerts.append({
                "type": "insufficient_data",
                "severity": "info",
                "message": (
                    f"Only {correlation_data.get('sample_size', 0)} scored candidates available. "
                    f"Need at least {MIN_SAMPLE_SIZE} for reliable analysis."
                ),
                "recommendation": "Continue using WSI screening to build sufficient data for analysis.",
            })

        if not distribution_data.get("insufficient_data"):
            by_outcome = distribution_data.get("by_outcome", {})
            hired_avg = by_outcome.get("hired", {}).get("avg")
            not_hired_avg = by_outcome.get("not_hired", {}).get("avg")
            if hired_avg is not None and not_hired_avg is not None:
                if hired_avg <= not_hired_avg:
                    alerts.append({
                        "type": "score_inversion",
                        "severity": "warning",
                        "message": (
                            f"Hired candidates average score ({hired_avg}) is not higher "
                            f"than non-hired ({not_hired_avg}). Scoring may not align with hiring decisions."
                        ),
                        "recommendation": "Review WSI evaluation criteria and block weights.",
                    })

        return {
            "company_id": company_id,
            "correlation": correlation_data,
            "block_accuracy": block_data,
            "distribution": distribution_data,
            "threshold_analysis": threshold_data,
            "alerts": alerts,
            "metadata": {
                "read_only": True,
                "note": "This report is purely observational. No WSI configuration has been modified.",
            },
        }


wsi_observability_service = WSIObservabilityService()

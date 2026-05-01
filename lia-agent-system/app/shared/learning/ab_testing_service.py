import hashlib
import logging
import math
import statistics
from datetime import datetime
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ab_testing import ABTestResult, PromptVariant

logger = logging.getLogger(__name__)


class ABTestingService:

    def _hash_assignment(self, test_name: str, session_id: str) -> int:
        combined = f"{test_name}:{session_id}"
        hash_val = hashlib.md5(combined.encode()).hexdigest()
        return int(hash_val, 16)

    async def get_variant(
        self,
        test_name: str,
        session_id: str,
        db: AsyncSession,
    ) -> dict[str, Any] | None:
        try:
            result = await db.execute(
                select(PromptVariant).where(
                    and_(
                        PromptVariant.test_name == test_name,
                        PromptVariant.is_active,
                    )
                ).order_by(PromptVariant.variant_name)
            )
            variants = result.scalars().all()

            if not variants:
                return None

            hash_val = self._hash_assignment(test_name, session_id)
            bucket = hash_val % 10000

            cumulative = 0.0
            selected = variants[0]

            for variant in variants:
                cumulative += variant.traffic_percentage
                threshold = cumulative * 100
                if bucket < threshold:
                    selected = variant
                    break

            return {
                "test_name": test_name,
                "variant_name": selected.variant_name,
                "prompt_template": selected.prompt_template,
                "variant_id": str(selected.id),
            }

        except Exception as e:
            logger.error(f"Error getting variant for test '{test_name}': {e}")
            return None

    async def record_metric(
        self,
        test_name: str,
        variant_name: str,
        session_id: str,
        company_id: str,
        metric_name: str,
        metric_value: float,
        db: AsyncSession,
        context: dict[str, Any] | None = None,
    ) -> ABTestResult | None:
        try:
            record = ABTestResult(
                test_name=test_name,
                variant_name=variant_name,
                session_id=session_id,
                company_id=company_id,
                metric_name=metric_name,
                metric_value=metric_value,
                context=context,
            )
            db.add(record)
            await db.flush()
            return record
        except Exception as e:
            logger.error(f"Error recording metric: {e}")
            return None

    def _compute_p_value(self, z: float) -> float:
        return 1.0 - 0.5 * (1.0 + math.erf(abs(z) / math.sqrt(2.0)))

    N_MIN_PER_VARIANT = 30

    async def get_test_results(
        self,
        test_name: str,
        db: AsyncSession,
    ) -> dict[str, Any]:
        try:
            result = await db.execute(
                select(ABTestResult).where(
                    ABTestResult.test_name == test_name,
                ).order_by(ABTestResult.created_at)
            )
            all_results = result.scalars().all()

            if not all_results:
                return {
                    "test_name": test_name,
                    "variants": {},
                    "statistical_significance": None,
                    "recommendation": "insufficient_data",
                    "winner": None,
                    "total_observations": 0,
                    "n_min": self.N_MIN_PER_VARIANT,
                }

            metrics_by_name: dict[str, dict[str, list[float]]] = {}

            for r in all_results:
                if r.metric_name not in metrics_by_name:
                    metrics_by_name[r.metric_name] = {}
                if r.variant_name not in metrics_by_name[r.metric_name]:
                    metrics_by_name[r.metric_name][r.variant_name] = []
                metrics_by_name[r.metric_name][r.variant_name].append(r.metric_value)

            variants_summary: dict[str, dict[str, Any]] = {}

            for r in all_results:
                if r.variant_name not in variants_summary:
                    variants_summary[r.variant_name] = {"metrics": {}}

            for metric_name, variant_values in metrics_by_name.items():
                for variant_name, values in variant_values.items():
                    n = len(values)
                    mean = statistics.mean(values) if values else 0
                    std_dev = statistics.stdev(values) if n > 1 else 0
                    se = std_dev / math.sqrt(n) if n > 0 else 0
                    ci_95 = (mean - 1.96 * se, mean + 1.96 * se) if n > 0 else (0, 0)

                    variants_summary[variant_name]["metrics"][metric_name] = {
                        "sample_size": n,
                        "mean": round(mean, 4),
                        "std_dev": round(std_dev, 4),
                        "confidence_interval_95": [round(ci_95[0], 4), round(ci_95[1], 4)],
                    }

            significance_results = {}
            winner = None

            for metric_name, variant_values in metrics_by_name.items():
                variant_names = sorted(variant_values.keys())
                if len(variant_names) < 2:
                    continue

                control_name = "control" if "control" in variant_names else variant_names[0]
                control_values = variant_values[control_name]

                for vname in variant_names:
                    if vname == control_name:
                        continue

                    variant_vals = variant_values[vname]
                    n_a = len(control_values)
                    n_b = len(variant_vals)

                    if n_a < 2 or n_b < 2:
                        continue

                    mean_a = statistics.mean(control_values)
                    mean_b = statistics.mean(variant_vals)
                    var_a = statistics.variance(control_values)
                    var_b = statistics.variance(variant_vals)

                    denominator = math.sqrt(var_a / n_a + var_b / n_b)
                    if denominator == 0:
                        continue

                    z_score = (mean_b - mean_a) / denominator
                    p_value = self._compute_p_value(z_score)

                    improvement_pct = ((mean_b - mean_a) / abs(mean_a) * 100) if mean_a != 0 else 0

                    below_n_min = n_a < self.N_MIN_PER_VARIANT or n_b < self.N_MIN_PER_VARIANT
                    is_significant = (
                        not below_n_min
                        and p_value < 0.05
                        and abs(improvement_pct) > 5
                    )

                    sig_key = f"{metric_name}:{control_name}_vs_{vname}"
                    significance_results[sig_key] = {
                        "control": control_name,
                        "variant": vname,
                        "metric": metric_name,
                        "n_control": n_a,
                        "n_variant": n_b,
                        "n_min": self.N_MIN_PER_VARIANT,
                        "below_n_min": below_n_min,
                        "z_score": round(z_score, 4),
                        "p_value": round(p_value, 6),
                        "improvement_pct": round(improvement_pct, 2),
                        "is_significant": is_significant,
                    }

                    if is_significant and improvement_pct > 5:
                        winner = {
                            "variant": vname,
                            "metric": metric_name,
                            "improvement_pct": round(improvement_pct, 2),
                            "p_value": round(p_value, 6),
                        }

            has_sufficient_data = all(
                not sig.get("below_n_min", True)
                for sig in significance_results.values()
            ) if significance_results else False

            if winner:
                recommendation = "winner"
            elif has_sufficient_data:
                recommendation = "no_significant_difference"
            else:
                recommendation = "insufficient_data"

            return {
                "test_name": test_name,
                "variants": variants_summary,
                "statistical_significance": significance_results,
                "recommendation": recommendation,
                "winner": winner,
                "total_observations": len(all_results),
                "n_min": self.N_MIN_PER_VARIANT,
            }

        except Exception as e:
            logger.error(f"Error getting test results: {e}")
            return {
                "test_name": test_name,
                "variants": {},
                "statistical_significance": None,
                "winner": None,
                "total_observations": 0,
                "error": str(e),
            }

    async def list_active_tests(
        self,
        db: AsyncSession,
    ) -> list[dict[str, Any]]:
        try:
            result = await db.execute(
                select(PromptVariant).where(
                    PromptVariant.is_active,
                ).order_by(PromptVariant.test_name, PromptVariant.variant_name)
            )
            variants = result.scalars().all()

            tests: dict[str, dict[str, Any]] = {}

            for v in variants:
                if v.test_name not in tests:
                    tests[v.test_name] = {
                        "test_name": v.test_name,
                        "variants": [],
                        "created_at": v.created_at.isoformat() if v.created_at else None,
                    }
                tests[v.test_name]["variants"].append({
                    "variant_name": v.variant_name,
                    "traffic_percentage": v.traffic_percentage,
                    "is_active": v.is_active,
                })

            return list(tests.values())

        except Exception as e:
            logger.error(f"Error listing active tests: {e}")
            return []

    async def create_test(
        self,
        test_name: str,
        variants: list[dict[str, Any]],
        db: AsyncSession,
    ) -> dict[str, Any]:
        try:
            existing = await db.execute(
                select(func.count(PromptVariant.id)).where(
                    and_(
                        PromptVariant.test_name == test_name,
                        PromptVariant.is_active,
                    )
                )
            )
            if (existing.scalar() or 0) > 0:
                return {
                    "error": f"Test '{test_name}' already exists with active variants",
                    "test_name": test_name,
                }

            created_variants = []

            for v in variants:
                variant = PromptVariant(
                    test_name=test_name,
                    variant_name=v.get("variant_name", "control"),
                    prompt_template=v.get("prompt_template", ""),
                    is_active=True,
                    traffic_percentage=v.get("traffic_percentage", 50.0),
                )
                db.add(variant)
                created_variants.append({
                    "variant_name": variant.variant_name,
                    "traffic_percentage": variant.traffic_percentage,
                })

            await db.flush()

            return {
                "test_name": test_name,
                "variants": created_variants,
                "created_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error creating test: {e}")
            return {"error": str(e), "test_name": test_name}


ab_testing_service = ABTestingService()


def get_ab_testing_service() -> "ABTestingService":
    return ab_testing_service

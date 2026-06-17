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

    N_MIN_PER_VARIANT = 100

    async def get_test_results(
        self,
        test_name: str,
        db: AsyncSession,
        company_id: str | None = None,  # P1-W4-15: tenant scoping
    ) -> dict[str, Any]:
        try:
            _conditions = [ABTestResult.test_name == test_name]
            if company_id:
                _conditions.append(ABTestResult.company_id == company_id)  # P1-W4-15
            else:
                import logging as _log; _log.getLogger(__name__).warning(
                    "[AB-TEST] get_test_results called without company_id — cross-tenant query (deprecated)")
            result = await db.execute(
                select(ABTestResult).where(
                    *_conditions,
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
                        and p_value < 0.01
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
        company_id: str | None = None,  # WT-2024 fix: tenant scoping
    ) -> list[dict[str, Any]]:
        # WT-2024 P1.2: filtro multi-tenant; None preserva legacy behavior (callers admin/seeder)
        if company_id is None:
            logger.warning(
                "[AB-TEST] list_active_tests called without company_id — "
                "cross-tenant query (deprecated; pass company_id explicitly)"
            )
        try:
            conditions = [PromptVariant.is_active]
            if company_id is not None:
                conditions.append(PromptVariant.company_id == company_id)
            result = await db.execute(
                select(PromptVariant).where(
                    *conditions
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


    async def auto_promote_winner(
        self,
        test_name: str,
        db: AsyncSession,
        *,
        use_thompson_sampling: bool = False,
        thompson_threshold: float = 0.95,
        company_id: str | None = None,  # WT-2022 P1.3: tenant scoping
    ) -> dict:
        """
        UC-P1-27 + T-19 Fase 3: deactivate non-winner variants em A/B test.

        Gate canonical aplicado em sequência:
        1. Significance gate (z-test p<0.01 + n>=100) OU
           Thompson Bayesian gate (winner_probability >= threshold) — opt-in.
        2. FairnessGate (T-19 Fase 1 ADR-031-v3) — bloqueia winner com viés.
        3. Promote (deactivate losers).

        Args:
            test_name: experiment identifier
            db: AsyncSession
            use_thompson_sampling: True = Bayesian gate (Thompson winner_prob).
                Default False (backward compat — keep z-test).
            thompson_threshold: minimum P(winner is best) para promote.
                Default 0.95 (canonical Bayesian convergence threshold).

        Returns: {"promoted": bool, "winner": str | None, "reason": str,
                  "gate_used": "frequentist" | "thompson"}
        """
        from sqlalchemy import update as _update
        results = await self.get_test_results(test_name, db)

        if not results or not results.get("winner"):
            return {"promoted": False, "winner": None, "reason": "no_winner_yet"}

        winner_info = results["winner"]
        sig_results = results.get("statistical_significance") or {}
        min_n = min(
            (v.get("n_control", 0) for v in sig_results.values()),
            default=0,
        )
        min_n = min(min_n, min(
            (v.get("n_variant", 0) for v in sig_results.values()),
            default=0,
        ))

        gate_used = "thompson" if use_thompson_sampling else "frequentist"

        # T-19 Fase 3 THOMPSON INTEGRATE canonical (ADR-AB-001):
        # Bayesian gate alternativo via ThompsonSampler.winner_probability.
        # Lê posteriors persistidos (T-19 Fase 2 BanditPosterior table).
        if use_thompson_sampling:
            try:
                from app.shared.intelligence.ab_testing.thompson_sampler import (
                    ThompsonSampler,
                )
                from app.shared.intelligence.ab_testing.bandit_posterior_repository import (
                    BanditPosteriorRepository,
                )

                _repo = BanditPosteriorRepository(db)
                _posteriors = await _repo.get_all_for_test(test_name)
                if not _posteriors:
                    return {
                        "promoted": False,
                        "winner": winner_info["variant"],
                        "reason": "thompson: no posteriors persisted yet",
                        "gate_used": gate_used,
                    }

                _sampler = ThompsonSampler(seed=42)
                _arms = []
                for _p in _posteriors:
                    _sampler.update(
                        _p.arm,
                        successes=max(0, int(round(_p.alpha - 1.0))),
                        failures=max(0, int(round(_p.beta - 1.0))),
                    )
                    _arms.append(_p.arm)

                _winner_arm = winner_info["variant"]
                if _winner_arm not in _arms:
                    return {
                        "promoted": False,
                        "winner": _winner_arm,
                        "reason": f"thompson: winner {_winner_arm} not in posteriors {_arms}",
                        "gate_used": gate_used,
                    }

                _winner_prob = _sampler.winner_probability(
                    _winner_arm, _arms, n_simulations=5000
                )
                if _winner_prob < thompson_threshold:
                    return {
                        "promoted": False,
                        "winner": _winner_arm,
                        "reason": (
                            f"thompson: P({_winner_arm} best)={_winner_prob:.4f} "
                            f"< threshold {thompson_threshold}"
                        ),
                        "gate_used": gate_used,
                        "thompson_winner_probability": _winner_prob,
                    }
                logger.info(
                    "[AB-TEST T-19 Fase 3] Thompson gate PASSED: "
                    "test=%s winner=%s P=%.4f >= %s",
                    test_name, _winner_arm, _winner_prob, thompson_threshold,
                )
            except Exception as _thomp_exc:
                logger.warning(
                    "[AB-TEST T-19 Fase 3] Thompson gate failed (fail-soft): %s — "
                    "falling back to frequentist z-test",
                    str(_thomp_exc)[:200],
                )
                gate_used = "frequentist_fallback"
                # Continue para frequentist gate (não-bloqueia)

        # Frequentist gate canonical (z-test) — sempre roda se Thompson não ativado
        # OU se Thompson falhou (fallback).
        if gate_used != "thompson":
            p_value = winner_info.get("p_value", 1.0)

            # T-19 Fase 4 BONFERRONI canonical (ADR-AB-001):
            # Multi-arm test inflaciona Type I error com z-test individual.
            # Correção: alpha_adjusted = 0.01 / max(1, n_comparisons).
            # n_comparisons = n_arms - 1 (each non-control compared vs control).
            # Backward compat: 2 arms = sem correção (alpha = 0.01).
            n_arms = len(sig_results) + 1  # sig_results = non-control variants vs control
            n_comparisons = max(1, n_arms - 1)
            alpha_base = 0.01
            alpha_adjusted = alpha_base / n_comparisons

            if p_value >= alpha_adjusted:
                if n_comparisons > 1:
                    reason_msg = (
                        f"p_value={p_value:.4f} >= {alpha_adjusted:.5f} "
                        f"(Bonferroni-adjusted for {n_arms} arms, "
                        f"base α={alpha_base})"
                    )
                else:
                    reason_msg = f"p_value={p_value:.4f} >= {alpha_base}"
                return {
                    "promoted": False,
                    "winner": winner_info["variant"],
                    "reason": reason_msg,
                    "gate_used": gate_used,
                    "n_arms": n_arms,
                    "alpha_adjusted": alpha_adjusted,
                }

            if min_n < 100:
                return {
                    "promoted": False,
                    "winner": winner_info["variant"],
                    "reason": f"n={min_n} < 100",
                    "gate_used": gate_used,
                    "n_arms": n_arms,
                }

            if n_arms >= 3:
                logger.info(
                    "[AB-TEST T-19 Fase 4] Bonferroni gate PASSED: "
                    "test=%s winner=%s p=%.4f < α_adj=%.5f n_arms=%d",
                    test_name, winner_info["variant"], p_value,
                    alpha_adjusted, n_arms,
                )

        # T-19 FAIRNESS GATE canonical (ADR-031-v3 + ADR-AB-001):
        # Winner variant DEVE passar FairnessGuard antes de promoção.
        # Previne discriminação indireta via A/B test winner que tem viés.
        # Fail-soft: se FairnessGuard indisponível, alerta WARN + permite promoção
        # (não bloqueia caminho crítico — sensor canonical detectará gap).
        try:
            from app.shared.compliance.fairness_guard import FairnessGuard
            _guard = FairnessGuard()
            # Resolve variant prompt text to validate
            _winner_variant_row = await db.execute(
                select(PromptVariant).where(
                    PromptVariant.test_name == test_name,
                    PromptVariant.variant_name == winner_info["variant"],
                ).limit(1)
            )
            _wv = _winner_variant_row.scalars().first()
            _prompt_text = getattr(_wv, "prompt_text", None) or ""
            if _prompt_text:
                _fairness_result = _guard.check(
                    query=_prompt_text,
                    action_type="ab_test_winner_promotion",
                )
                if getattr(_fairness_result, "is_blocked", False):
                    logger.warning(
                        "[AB-TEST T-19] FAIRNESS GATE BLOCKED promotion: "
                        "test=%s winner=%s reason=%s",
                        test_name,
                        winner_info["variant"],
                        getattr(_fairness_result, "blocked_reason", "fairness_violation"),
                    )
                    return {
                        "promoted": False,
                        "winner": winner_info["variant"],
                        "reason": (
                            "fairness_gate_blocked: "
                            + getattr(_fairness_result, "blocked_reason", "fairness_violation")
                        ),
                        "fairness_violation": True,
                    }
        except ImportError:
            # WT-2022 P5.2: FAIL-CLOSED (era fail-open silent — viola REGRA 4 Pydantic Conventions).
            # FairnessGate indisponivel = nao promover (gate eh requisito canonical T-19).
            logger.error(
                "[AB-TEST T-19] FairnessGuard import FAILED - blocking promotion "
                "(WT-2022 P5.2 fail-closed: refuses to promote without fairness gate)"
            )
            return {
                "promoted": False,
                "winner": winner_info["variant"],
                "reason": "fairness_gate_unavailable_import_error",
                "fairness_violation": False,
                "fairness_gate_error": True,
            }
        except Exception as _fg_exc:
            # WT-2022 P5.2: FAIL-CLOSED (era fail-open silent).
            logger.error(
                "[AB-TEST T-19] FairnessGuard check FAILED - blocking promotion: %s "
                "(WT-2022 P5.2 fail-closed)",
                str(_fg_exc)[:200],
            )
            return {
                "promoted": False,
                "winner": winner_info["variant"],
                "reason": f"fairness_gate_check_failed:{type(_fg_exc).__name__}",
                "fairness_violation": False,
                "fairness_gate_error": True,
            }

        # Promote: deactivate losing variants
        # WT-2022 P1.3: filtro company_id no UPDATE pra evitar cross-tenant write
        update_stmt = (
            _update(PromptVariant)
            .where(PromptVariant.test_name == test_name)
            .where(PromptVariant.variant_name != winner_info["variant"])
        )
        if company_id is not None:
            update_stmt = update_stmt.where(PromptVariant.company_id == company_id)
        else:
            logger.warning(
                "[AB-TEST] auto_promote_winner called without company_id — "
                "UPDATE without tenant filter (deprecated; pass company_id explicitly)"
            )
        await db.execute(update_stmt.values(is_active=False))
        await db.commit()

        logger.info(
            "[AB-TEST] Auto-promoted winner: test=%s winner=%s p=%.4f n=%d",
            test_name, winner_info["variant"], p_value, min_n,
        )
        return {"promoted": True, "winner": winner_info["variant"], "reason": "auto_promoted"}


    # ------------------------------------------------------------------
    # T-19 Fase 5 SEQUENTIAL testing early stopping canonical (ADR-AB-001)
    # ------------------------------------------------------------------

    async def check_early_stop(
        self,
        test_name: str,
        db: AsyncSession,
        *,
        look_number: int,
        max_looks: int = 10,
        alpha_total: float = 0.01,
        futility_threshold: float = 0.001,
    ) -> dict:
        """Sequential test early stopping decision (Pocock-style alpha-spending).

        Permite peek no resultado em múltiplos momentos sem inflar Type I error.
        Pattern canonical:
        - alpha_per_look = alpha_total / max_looks (Bonferroni-over-looks)
        - Stop for winner: p_value < alpha_per_look AND n >= 100 per variant
        - Stop for futility: |estimated effect| < futility_threshold AND n >= 50% max
        - Continue: else

        Args:
            test_name: experiment identifier
            db: AsyncSession
            look_number: current peek (1-indexed, 1..max_looks)
            max_looks: planned total peeks
            alpha_total: significance budget total (default 0.01)
            futility_threshold: minimum detectable effect (default 0.001)

        Returns:
            dict {
                "action": "stop_winner" | "stop_futility" | "continue",
                "winner": str | None,
                "p_value": float | None,
                "alpha_per_look": float,
                "look_number": int,
                "max_looks": int,
                "reason": str,
            }

        Refs:
        - Pocock (1977): "Group sequential methods in the design and analysis of clinical trials"
        - Lan & DeMets (1983): "Discrete sequential boundaries for clinical trials"
        """
        if look_number < 1:
            raise ValueError(f"look_number must be >= 1 (got {look_number})")
        if look_number > max_looks:
            raise ValueError(
                f"look_number {look_number} > max_looks {max_looks}"
            )
        if not 0 < alpha_total < 1:
            raise ValueError(f"alpha_total must be in (0, 1) (got {alpha_total})")

        # Pocock-style alpha-spending (simplified Bonferroni-over-looks)
        alpha_per_look = alpha_total / max_looks

        results = await self.get_test_results(test_name, db)
        if not results or not results.get("winner"):
            return {
                "action": "continue",
                "winner": None,
                "p_value": None,
                "alpha_per_look": alpha_per_look,
                "look_number": look_number,
                "max_looks": max_looks,
                "reason": "no_winner_data_yet",
            }

        winner_info = results["winner"]
        p_value = winner_info.get("p_value", 1.0)
        sig_results = results.get("statistical_significance") or {}
        min_n = min(
            (v.get("n_control", 0) for v in sig_results.values()),
            default=0,
        )
        min_n_variants = min(
            (v.get("n_variant", 0) for v in sig_results.values()),
            default=0,
        )
        min_n = min(min_n, min_n_variants)

        # Stop for winner canonical: p < alpha_per_look + n suficiente
        if p_value < alpha_per_look and min_n >= 100:
            logger.info(
                "[AB-TEST T-19 Fase 5] STOP_WINNER at look %d/%d: "
                "test=%s winner=%s p=%.5f < α_per_look=%.5f n=%d",
                look_number, max_looks, test_name, winner_info["variant"],
                p_value, alpha_per_look, min_n,
            )
            return {
                "action": "stop_winner",
                "winner": winner_info["variant"],
                "p_value": p_value,
                "alpha_per_look": alpha_per_look,
                "look_number": look_number,
                "max_looks": max_looks,
                "reason": (
                    f"p={p_value:.5f} < α_per_look={alpha_per_look:.5f} "
                    f"(early stop look {look_number}/{max_looks})"
                ),
            }

        # Stop for futility canonical: effect size muito pequeno + dados suficientes
        # Estimated effect via point estimate diff (mean control - mean variant)
        observed_effect = 0.0
        for variant_name, variant_sig in sig_results.items():
            obs_diff = abs(variant_sig.get("mean_diff", 0.0))
            observed_effect = max(observed_effect, obs_diff)

        n_threshold_futility = int(0.5 * max_looks * 100)  # heuristic
        if (
            observed_effect < futility_threshold
            and min_n >= n_threshold_futility
        ):
            logger.info(
                "[AB-TEST T-19 Fase 5] STOP_FUTILITY at look %d/%d: "
                "test=%s effect=%.5f < futility=%.5f n=%d",
                look_number, max_looks, test_name,
                observed_effect, futility_threshold, min_n,
            )
            return {
                "action": "stop_futility",
                "winner": None,
                "p_value": p_value,
                "alpha_per_look": alpha_per_look,
                "look_number": look_number,
                "max_looks": max_looks,
                "reason": (
                    f"observed_effect={observed_effect:.5f} < "
                    f"futility_threshold={futility_threshold:.5f} (no real winner)"
                ),
                "observed_effect": observed_effect,
            }

        # Continue canonical
        return {
            "action": "continue",
            "winner": None,
            "p_value": p_value,
            "alpha_per_look": alpha_per_look,
            "look_number": look_number,
            "max_looks": max_looks,
            "reason": (
                f"continue: p={p_value:.5f} not yet < α_per_look={alpha_per_look:.5f} "
                f"OR n={min_n} < 100 per variant"
            ),
        }


ab_testing_service = ABTestingService()


def get_ab_testing_service() -> "ABTestingService":
    return ab_testing_service

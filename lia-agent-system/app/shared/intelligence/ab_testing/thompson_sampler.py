"""T-19 Fase 1: Thompson sampling canonical para multi-arm bandit A/B testing.

Bayesian approach (vs frequentist p-value usado em auto_promote_winner):
- Cada variant tem prior Beta(alpha, beta) representando taxa de sucesso
- alpha = sucessos + 1, beta = falhas + 1 (Jeffreys prior 0.5/0.5 OK também)
- A cada round, sample da posterior de cada variant + pick max
- Variant explorando promissoras mais cedo (exploration/exploitation balance)

Vantagens vs z-test atual:
- Multi-arm (3+ variantes) sem inflação de Type I error
- Convergência rápida (não precisa esperar n=100 por variant)
- Naturalmente lida com unequal sample sizes

Refs:
- Thompson, W. R. (1933). On the likelihood that one unknown probability
  exceeds another in view of the evidence of two samples. Biometrika.
- Russo et al. (2018). A Tutorial on Thompson Sampling.
- ADR-AB-001 (este sprint T-19 Fase 1)
"""
from __future__ import annotations

import math
import random
from typing import Any


def _sample_beta(alpha: float, beta: float, rng: random.Random | None = None) -> float:
    """Sample from Beta(alpha, beta) via gamma ratio.

    Uses random module (not numpy) to avoid dependency.
    """
    if rng is None:
        rng = random.Random()
    # Sample X ~ Gamma(alpha, 1), Y ~ Gamma(beta, 1), return X/(X+Y)
    x = rng.gammavariate(alpha, 1.0)
    y = rng.gammavariate(beta, 1.0)
    return x / (x + y) if (x + y) > 0 else 0.5


class ThompsonSampler:
    """Multi-arm bandit canonical for A/B test variant selection.

    Usage:
        sampler = ThompsonSampler(seed=42)
        sampler.update("control", successes=45, failures=55)
        sampler.update("variant_b", successes=52, failures=48)
        next_arm = sampler.choose(["control", "variant_b"])
    """

    def __init__(self, seed: int | None = None):
        self._rng = random.Random(seed)
        # arm_name -> (alpha, beta) of beta posterior
        self._posteriors: dict[str, tuple[float, float]] = {}

    def update(self, arm: str, successes: int, failures: int) -> None:
        """Update posterior with observed sample counts.

        Uses uniform prior Beta(1, 1) → alpha = successes + 1, beta = failures + 1.
        """
        if successes < 0 or failures < 0:
            raise ValueError("successes and failures must be non-negative")
        alpha = float(successes + 1)
        beta = float(failures + 1)
        self._posteriors[arm] = (alpha, beta)

    def choose(self, arms: list[str]) -> str:
        """Sample posterior of each arm + return argmax (Thompson sampling step).

        Arms without prior observations get uniform prior Beta(1, 1).
        """
        if not arms:
            raise ValueError("arms list cannot be empty")

        best_arm = arms[0]
        best_sample = -1.0
        for arm in arms:
            alpha, beta = self._posteriors.get(arm, (1.0, 1.0))
            sample = _sample_beta(alpha, beta, self._rng)
            if sample > best_sample:
                best_sample = sample
                best_arm = arm
        return best_arm

    def get_posterior(self, arm: str) -> tuple[float, float] | None:
        """Return (alpha, beta) of posterior for inspection/audit."""
        return self._posteriors.get(arm)

    def expected_value(self, arm: str) -> float:
        """E[Beta(α, β)] = α / (α + β) — posterior mean (point estimate)."""
        alpha, beta = self._posteriors.get(arm, (1.0, 1.0))
        return alpha / (alpha + beta)

    def credible_interval(self, arm: str, confidence: float = 0.95) -> tuple[float, float]:
        """Approximate (1-α)% credible interval via Monte Carlo (1000 samples).

        For exact intervals use scipy.stats.beta.interval() (not available
        here without scipy dep).
        """
        if not 0 < confidence < 1:
            raise ValueError("confidence must be in (0, 1)")
        alpha, beta = self._posteriors.get(arm, (1.0, 1.0))
        samples = sorted(_sample_beta(alpha, beta, self._rng) for _ in range(1000))
        lo_pct = (1 - confidence) / 2
        hi_pct = 1 - lo_pct
        lo_idx = int(lo_pct * len(samples))
        hi_idx = int(hi_pct * len(samples))
        return (samples[lo_idx], samples[hi_idx])

    def winner_probability(
        self, arm: str, arms: list[str], n_simulations: int = 5000
    ) -> float:
        """Estimate P(arm is best) via Monte Carlo over posteriors.

        Returns:
            Probability in [0, 1] that arm has highest posterior in
            n_simulations rounds.
        """
        if arm not in arms:
            raise ValueError(f"arm '{arm}' not in arms list")
        wins = 0
        for _ in range(n_simulations):
            samples = {}
            for a in arms:
                alpha, beta = self._posteriors.get(a, (1.0, 1.0))
                samples[a] = _sample_beta(alpha, beta, self._rng)
            best = max(samples, key=samples.get)
            if best == arm:
                wins += 1
        return wins / n_simulations

    def to_dict(self) -> dict[str, Any]:
        """Serialize posteriors for audit log persistence."""
        return {
            arm: {"alpha": alpha, "beta": beta, "expected": alpha / (alpha + beta)}
            for arm, (alpha, beta) in self._posteriors.items()
        }

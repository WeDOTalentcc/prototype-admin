"""
A/B Testing for Prompts - Experiment framework for prompt optimization.

Enables controlled experiments across different prompt variants to measure
effectiveness and optimize LIA's responses.

Usage:
    from app.shared.ab_testing import PromptExperiment, get_experiment_manager
    
    manager = get_experiment_manager()
    experiment = manager.create_experiment(
        name="jd_generation_v2",
        variants={"control": prompt_v1, "treatment": prompt_v2},
        traffic_split={"control": 0.5, "treatment": 0.5},
    )
    
    selected = manager.get_variant("jd_generation_v2", user_id="user-123")
    # ... use selected.prompt ...
    
    manager.record_outcome("jd_generation_v2", user_id="user-123", 
                           metrics={"satisfaction": 4.5, "edit_count": 2})
"""
import hashlib
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class PromptVariant:
    variant_id: str
    prompt: str
    weight: float = 0.5
    impressions: int = 0
    outcomes: list[dict[str, Any]] = field(default_factory=list)

    @property
    def avg_satisfaction(self) -> float:
        if not self.outcomes:
            return 0.0
        scores = [o.get("satisfaction", 0) for o in self.outcomes if "satisfaction" in o]
        return sum(scores) / len(scores) if scores else 0.0


@dataclass
class PromptExperiment:
    name: str
    variants: dict[str, PromptVariant]
    traffic_split: dict[str, float]
    is_active: bool = True
    created_at: float = field(default_factory=time.time)
    description: str = ""


class ExperimentManager:
    _instance: Optional['ExperimentManager'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._experiments: dict[str, PromptExperiment] = {}
        return cls._instance

    def create_experiment(
        self,
        name: str,
        variants: dict[str, str],
        traffic_split: dict[str, float] | None = None,
        description: str = "",
    ) -> PromptExperiment:
        if not traffic_split:
            equal_weight = 1.0 / len(variants)
            traffic_split = {k: equal_weight for k in variants}

        total_weight = sum(traffic_split.values())
        if abs(total_weight - 1.0) > 0.01:
            logger.warning(f"Traffic split for '{name}' doesn't sum to 1.0 ({total_weight}), normalizing")
            traffic_split = {k: v / total_weight for k, v in traffic_split.items()}

        prompt_variants = {
            variant_id: PromptVariant(
                variant_id=variant_id,
                prompt=prompt,
                weight=traffic_split.get(variant_id, 0.5),
            )
            for variant_id, prompt in variants.items()
        }

        experiment = PromptExperiment(
            name=name,
            variants=prompt_variants,
            traffic_split=traffic_split,
            description=description,
        )

        self._experiments[name] = experiment
        logger.info(f"[A/B] Created experiment '{name}' with {len(variants)} variants")
        return experiment

    def get_variant(self, experiment_name: str, user_id: str) -> PromptVariant | None:
        experiment = self._experiments.get(experiment_name)
        if not experiment or not experiment.is_active:
            return None

        hash_input = f"{experiment_name}:{user_id}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16) % 1000
        bucket = hash_value / 1000.0

        cumulative = 0.0
        for variant_id, weight in experiment.traffic_split.items():
            cumulative += weight
            if bucket < cumulative:
                variant = experiment.variants[variant_id]
                variant.impressions += 1
                logger.debug(
                    f"[A/B] '{experiment_name}' assigned user '{user_id}' → '{variant_id}' "
                    f"(bucket={bucket:.3f})"
                )
                return variant

        first_variant = list(experiment.variants.values())[0]
        first_variant.impressions += 1
        return first_variant

    def record_outcome(
        self,
        experiment_name: str,
        user_id: str,
        metrics: dict[str, Any],
    ) -> None:
        experiment = self._experiments.get(experiment_name)
        if not experiment:
            return

        variant = self.get_variant(experiment_name, user_id)
        if variant:
            variant.outcomes.append({
                "user_id": user_id,
                "timestamp": time.time(),
                **metrics,
            })

    def get_experiment_results(self, experiment_name: str) -> dict[str, Any] | None:
        experiment = self._experiments.get(experiment_name)
        if not experiment:
            return None

        results = {}
        for variant_id, variant in experiment.variants.items():
            results[variant_id] = {
                "impressions": variant.impressions,
                "outcomes_count": len(variant.outcomes),
                "avg_satisfaction": round(variant.avg_satisfaction, 3),
                "weight": variant.weight,
            }

        return {
            "experiment": experiment_name,
            "is_active": experiment.is_active,
            "created_at": datetime.fromtimestamp(experiment.created_at).isoformat(),
            "variants": results,
        }

    def create_experiment_from_yaml(
        self,
        name: str,
        variant_versions: dict[str, str],
        domain: str,
        traffic_split: dict[str, float] | None = None,
        description: str = "",
    ) -> PromptExperiment | None:
        """Create an experiment using YAML-versioned prompts from PromptVersionRegistry.

        Args:
            name: Experiment name (e.g. "cv_screening_prompt_v2_vs_v3")
            variant_versions: Mapping of variant_id → prompt version string
                e.g. {"control": "2.0", "treatment": "2.1"}
            domain: The domain name in PromptVersionRegistry (e.g. "cv_screening")
            traffic_split: Optional weight distribution per variant
            description: Human-readable experiment description
        """
        from app.domains.ai.services.prompt_version_registry import prompt_version_registry

        variants: dict[str, str] = {}
        for variant_id, version in variant_versions.items():
            entry = prompt_version_registry.get(domain, version=version)
            if entry and entry.get("template"):
                variants[variant_id] = entry["template"]
            else:
                logger.warning(
                    "[A/B] YAML prompt not found: domain=%s version=%s — skipping variant %s",
                    domain, version, variant_id,
                )

        if len(variants) < 2:
            logger.warning(
                "[A/B] Not enough YAML variants for experiment '%s' (found %d, need ≥2)",
                name, len(variants),
            )
            return None

        return self.create_experiment(
            name=name,
            variants=variants,
            traffic_split=traffic_split,
            description=description or f"YAML-versioned experiment for {domain}",
        )

    def deactivate_experiment(self, experiment_name: str) -> None:
        experiment = self._experiments.get(experiment_name)
        if experiment:
            experiment.is_active = False
            logger.info(f"[A/B] Deactivated experiment '{experiment_name}'")

    def list_experiments(self) -> list[dict[str, Any]]:
        return [
            {
                "name": e.name,
                "is_active": e.is_active,
                "variants": list(e.variants.keys()),
                "description": e.description,
            }
            for e in self._experiments.values()
        ]


def get_experiment_manager() -> ExperimentManager:
    return ExperimentManager()

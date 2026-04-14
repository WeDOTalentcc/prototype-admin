"""
Model Registry - Version control and management for ML models.

Persistent storage in PostgreSQL with in-memory cache + TTL.
Item: PX08-075 (Sprint 11, item 11.5)

Provides functionality to:
- Register and version models (persisted in DB)
- Load appropriate model versions (cached in-memory)
- Track model performance
- A/B test different models
- Tenant isolation via company_id
"""
import hashlib
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Cache TTL: 5 minutes
_CACHE_TTL_SECONDS = 300


@dataclass
class ModelMetadata:
    """Metadata for a registered model."""
    model_id: str
    model_name: str
    version: str
    created_at: datetime
    created_by: str
    description: str
    metrics: dict[str, float]
    parameters: dict[str, Any]
    is_active: bool = True
    is_default: bool = False
    model_path: str | None = None
    features: list[str] | None = None
    training_samples: int | None = None
    company_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id,
            "model_name": self.model_name,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
            "description": self.description,
            "metrics": self.metrics,
            "parameters": self.parameters,
            "is_active": self.is_active,
            "is_default": self.is_default,
            "model_path": self.model_path,
            "features": self.features,
            "training_samples": self.training_samples,
            "company_id": self.company_id,
        }


@dataclass
class ModelPerformance:
    """Performance tracking for a model."""
    model_id: str
    predictions_count: int = 0
    correct_predictions: int = 0
    total_error: float = 0.0
    last_evaluated: datetime | None = None

    @property
    def accuracy(self) -> float:
        if self.predictions_count == 0:
            return 0.0
        return self.correct_predictions / self.predictions_count

    @property
    def mean_error(self) -> float:
        if self.predictions_count == 0:
            return 0.0
        return self.total_error / self.predictions_count


class ModelRegistry:
    """
    Registry for managing ML model versions.

    Persistent in PostgreSQL with in-memory cache.
    Sync methods operate on cache (backwards compatible).
    Async methods read/write DB.
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._models: dict[str, ModelMetadata] = {}
        self._performance: dict[str, ModelPerformance] = {}
        self._default_models: dict[str, str] = {}
        self._cache_loaded_at: float = 0.0
        self._db_loaded: bool = False
        self._pending_writes: list[str] = []  # model_ids to flush
        self._pending_perf_updates: list[str] = []  # model_ids with perf changes

        self._register_builtin_models()

    def _is_cache_stale(self) -> bool:
        if not self._db_loaded:
            return True
        return (time.monotonic() - self._cache_loaded_at) > _CACHE_TTL_SECONDS

    # ── Async DB operations ──────────────────────────────────────────

    async def load_from_db(self, db: AsyncSession) -> None:
        """Load all models from DB into cache."""
        from lia_models.ml_model_registry import MLModelRegistryRecord

        try:
            result = await db.execute(
                select(MLModelRegistryRecord).where(
                    MLModelRegistryRecord.status != "deleted"
                )
            )
            records = result.scalars().all()

            if records:
                self._models.clear()
                self._performance.clear()
                self._default_models.clear()

                for r in records:
                    meta = ModelMetadata(
                        model_id=r.model_id,
                        model_name=r.name,
                        version=r.version,
                        created_at=r.created_at,
                        created_by=r.created_by,
                        description=r.description or "",
                        metrics=r.metrics or {},
                        parameters=r.parameters or {},
                        is_active=(r.status == "active"),
                        is_default=r.is_default,
                        model_path=r.model_path,
                        features=r.features,
                        training_samples=r.training_samples,
                        company_id=r.company_id,
                    )
                    self._models[r.model_id] = meta

                    self._performance[r.model_id] = ModelPerformance(
                        model_id=r.model_id,
                        predictions_count=r.predictions_count,
                        correct_predictions=r.correct_predictions,
                        total_error=r.total_error,
                        last_evaluated=r.last_evaluated,
                    )

                    if r.is_default:
                        self._default_models[r.name] = r.model_id

                self.logger.info(
                    "Loaded %d models from DB into cache", len(records)
                )
            else:
                # DB empty — seed built-in models
                self._register_builtin_models()
                await self._seed_builtins_to_db(db)

            self._db_loaded = True
            self._cache_loaded_at = time.monotonic()
            self._pending_writes.clear()
            self._pending_perf_updates.clear()

        except Exception as exc:
            self.logger.warning("Failed to load from DB, using in-memory: %s", exc)

    async def _seed_builtins_to_db(self, db: AsyncSession) -> None:
        """Write built-in models to DB (first run)."""
        from lia_models.ml_model_registry import MLModelRegistryRecord
        import uuid

        for model_id, meta in self._models.items():
            record = MLModelRegistryRecord(
                id=uuid.uuid4(),
                model_id=meta.model_id,
                name=meta.model_name,
                version=meta.version,
                status="active" if meta.is_active else "inactive",
                description=meta.description,
                created_by=meta.created_by,
                is_default=meta.is_default,
                metrics=meta.metrics,
                parameters=meta.parameters,
                features=meta.features,
                company_id=meta.company_id,
            )
            db.add(record)

        await db.commit()
        self.logger.info("Seeded %d built-in models to DB", len(self._models))

    async def persist_model(self, db: AsyncSession, model_id: str) -> None:
        """Write a single model (metadata + performance) to DB."""
        from lia_models.ml_model_registry import MLModelRegistryRecord
        import uuid

        meta = self._models.get(model_id)
        if not meta:
            return

        perf = self._performance.get(model_id)

        # Upsert: check if exists
        result = await db.execute(
            select(MLModelRegistryRecord).where(
                MLModelRegistryRecord.model_id == model_id
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.name = meta.model_name
            existing.version = meta.version
            existing.status = "active" if meta.is_active else "inactive"
            existing.description = meta.description
            existing.is_default = meta.is_default
            existing.metrics = meta.metrics
            existing.parameters = meta.parameters
            existing.model_path = meta.model_path
            existing.features = meta.features
            existing.training_samples = meta.training_samples
            existing.company_id = meta.company_id
            existing.updated_at = datetime.utcnow()
            if perf:
                existing.predictions_count = perf.predictions_count
                existing.correct_predictions = perf.correct_predictions
                existing.total_error = perf.total_error
                existing.last_evaluated = perf.last_evaluated
        else:
            record = MLModelRegistryRecord(
                id=uuid.uuid4(),
                model_id=meta.model_id,
                name=meta.model_name,
                version=meta.version,
                status="active" if meta.is_active else "inactive",
                description=meta.description,
                model_path=meta.model_path,
                created_by=meta.created_by,
                is_default=meta.is_default,
                metrics=meta.metrics,
                parameters=meta.parameters,
                features=meta.features,
                training_samples=meta.training_samples,
                company_id=meta.company_id,
                predictions_count=perf.predictions_count if perf else 0,
                correct_predictions=perf.correct_predictions if perf else 0,
                total_error=perf.total_error if perf else 0.0,
                last_evaluated=perf.last_evaluated if perf else None,
            )
            db.add(record)

        await db.commit()

    async def flush_pending(self, db: AsyncSession) -> None:
        """Persist all pending writes and performance updates to DB."""
        to_write = set(self._pending_writes + self._pending_perf_updates)
        if not to_write:
            return

        for model_id in to_write:
            await self.persist_model(db, model_id)

        self._pending_writes.clear()
        self._pending_perf_updates.clear()
        self.logger.info("Flushed %d models to DB", len(to_write))

    async def ensure_loaded(self, db: AsyncSession) -> None:
        """Ensure cache is populated from DB. Call from API endpoints."""
        if self._is_cache_stale():
            await self.load_from_db(db)

    # ── Sync methods (operate on cache — backwards compatible) ───────

    def _register_builtin_models(self):
        """Register built-in rule-based models."""
        self.register_model(
            model_name="time_to_fill_predictor",
            version="1.0.0",
            description="Rule-based time to fill predictor using historical averages and feature multipliers",
            metrics={"baseline_mae": 15.0},
            parameters={"type": "rule_based", "features": 20},
            created_by="system",
            set_as_default=True
        )

        self.register_model(
            model_name="salary_predictor",
            version="1.0.0",
            description="Rule-based salary predictor using role/seniority matrices",
            metrics={"baseline_mape": 0.15},
            parameters={"type": "rule_based", "features": 15},
            created_by="system",
            set_as_default=True
        )

        self.register_model(
            model_name="skill_success_predictor",
            version="1.0.0",
            description="Confirmation-based skill success predictor",
            metrics={"baseline_auc": 0.65},
            parameters={"type": "frequency_based", "threshold": 3},
            created_by="system",
            set_as_default=True
        )

    def register_model(
        self,
        model_name: str,
        version: str,
        description: str,
        metrics: dict[str, float],
        parameters: dict[str, Any],
        created_by: str = "system",
        set_as_default: bool = False,
        model_path: str | None = None,
        features: list[str] | None = None,
        training_samples: int | None = None,
        company_id: str | None = None,
    ) -> ModelMetadata:
        """Register a new model version (cache + queued for DB)."""
        model_id = self._generate_model_id(model_name, version)

        metadata = ModelMetadata(
            model_id=model_id,
            model_name=model_name,
            version=version,
            created_at=datetime.utcnow(),
            created_by=created_by,
            description=description,
            metrics=metrics,
            parameters=parameters,
            is_active=True,
            is_default=set_as_default,
            model_path=model_path,
            features=features,
            training_samples=training_samples,
            company_id=company_id,
        )

        self._models[model_id] = metadata
        self._performance[model_id] = ModelPerformance(model_id=model_id)

        if set_as_default:
            # Unset previous default
            old_default_id = self._default_models.get(model_name)
            if old_default_id and old_default_id in self._models:
                self._models[old_default_id].is_default = False
                self._pending_writes.append(old_default_id)

            self._default_models[model_name] = model_id
            self.logger.info("Registered and set as default: %s v%s", model_name, version)
        else:
            self.logger.info("Registered model: %s v%s", model_name, version)

        self._pending_writes.append(model_id)
        return metadata

    def get_model(self, model_id: str) -> ModelMetadata | None:
        """Get model metadata by ID (from cache)."""
        return self._models.get(model_id)

    def get_default_model(self, model_name: str) -> ModelMetadata | None:
        """Get the default model for a given model type (from cache)."""
        model_id = self._default_models.get(model_name)
        if model_id:
            return self._models.get(model_id)
        return None

    def list_models(
        self,
        model_name: str | None = None,
        active_only: bool = True,
        company_id: str | None = None,
    ) -> list[ModelMetadata]:
        """List registered models (from cache)."""
        models = list(self._models.values())

        if model_name:
            models = [m for m in models if m.model_name == model_name]

        if active_only:
            models = [m for m in models if m.is_active]

        if company_id:
            models = [m for m in models if m.company_id == company_id or m.company_id is None]

        return sorted(models, key=lambda m: m.created_at, reverse=True)

    def record_prediction(
        self,
        model_id: str,
        predicted_value: float,
        actual_value: float | None = None
    ):
        """Record a prediction for performance tracking (cache + queued for DB)."""
        if model_id not in self._performance:
            self._performance[model_id] = ModelPerformance(model_id=model_id)

        perf = self._performance[model_id]
        perf.predictions_count += 1

        if actual_value is not None:
            error = abs(predicted_value - actual_value)
            perf.total_error += error

            tolerance = actual_value * 0.2
            if error <= tolerance:
                perf.correct_predictions += 1

            perf.last_evaluated = datetime.utcnow()

        self._pending_perf_updates.append(model_id)

    def get_performance(self, model_id: str) -> ModelPerformance | None:
        """Get performance metrics for a model (from cache)."""
        return self._performance.get(model_id)

    def compare_models(
        self,
        model_ids: list[str]
    ) -> dict[str, dict[str, Any]]:
        """Compare performance of multiple models."""
        comparison = {}

        for model_id in model_ids:
            model = self._models.get(model_id)
            perf = self._performance.get(model_id)

            if model and perf:
                comparison[model_id] = {
                    "model_name": model.model_name,
                    "version": model.version,
                    "predictions_count": perf.predictions_count,
                    "accuracy": perf.accuracy,
                    "mean_error": perf.mean_error,
                    "is_default": model.is_default,
                    "created_at": model.created_at.isoformat(),
                }

        return comparison

    def set_default(self, model_id: str) -> bool:
        """Set a model as the default for its type."""
        model = self._models.get(model_id)
        if not model:
            return False

        for mid, meta in self._models.items():
            if meta.model_name == model.model_name:
                was_default = meta.is_default
                meta.is_default = (mid == model_id)
                if was_default != meta.is_default:
                    self._pending_writes.append(mid)

        self._default_models[model.model_name] = model_id
        self.logger.info("Set default model: %s -> %s", model.model_name, model.version)
        return True

    def deactivate_model(self, model_id: str) -> bool:
        """Deactivate a model version."""
        model = self._models.get(model_id)
        if model:
            model.is_active = False

            if model.is_default:
                model.is_default = False
                if model.model_name in self._default_models:
                    del self._default_models[model.model_name]

            self._pending_writes.append(model_id)
            self.logger.info("Deactivated model: %s", model_id)
            return True
        return False

    def _generate_model_id(self, model_name: str, version: str) -> str:
        """Generate unique model ID."""
        timestamp = datetime.utcnow().isoformat()
        content = f"{model_name}:{version}:{timestamp}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def export_registry(self) -> dict[str, Any]:
        """Export registry state."""
        return {
            "models": {mid: m.to_dict() for mid, m in self._models.items()},
            "defaults": self._default_models,
            "performance": {
                mid: {
                    "predictions_count": p.predictions_count,
                    "correct_predictions": p.correct_predictions,
                    "total_error": p.total_error,
                    "last_evaluated": p.last_evaluated.isoformat() if p.last_evaluated else None,
                }
                for mid, p in self._performance.items()
            },
            "db_loaded": self._db_loaded,
            "exported_at": datetime.utcnow().isoformat(),
        }


_registry_instance: ModelRegistry | None = None


def get_model_registry() -> ModelRegistry:
    """Get singleton instance of ModelRegistry."""
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = ModelRegistry()
    return _registry_instance

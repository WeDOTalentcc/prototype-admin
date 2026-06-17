"""
Time-to-Fill Predictor — ML model with heuristic fallback.

Loads a trained model (XGBoost or similar) if available.
Falls back to heuristic (avg by seniority) when model unavailable.

Usage:
    predictor = TTFPredictor()
    result = predictor.predict({
        "seniority_level": "sênior",
        "work_model": "remoto",
        "urgency_level": 3,
    })
    # result: {"predicted_days": 42, "confidence": 0.75, "source": "ml_model"}
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_MODEL_DIR = Path(__file__).parent / "models"
_MODEL_PATH = _MODEL_DIR / "ttf_model.joblib"
_FEATURE_ENCODER_PATH = _MODEL_DIR / "ttf_encoder.joblib"

# Heuristic defaults (Brazilian market) — used when model unavailable
_SENIORITY_DEFAULTS = {
    "estagiário": 20, "estagiario": 20,
    "júnior": 25, "junior": 25,
    "pleno": 35,
    "sênior": 45, "senior": 45,
    "especialista": 50,
    "lead": 55,
    "gerente": 60,
    "diretor": 90,
    "vp": 120, "c-level": 120,
}

# Feature encoding for seniority (ordinal)
_SENIORITY_ORDINAL = {
    "estagiário": 0, "estagiario": 0,
    "júnior": 1, "junior": 1,
    "pleno": 2,
    "sênior": 3, "senior": 3,
    "especialista": 4,
    "lead": 5,
    "gerente": 6,
    "diretor": 7,
    "vp": 8, "c-level": 8,
}

_WORK_MODEL_MAP = {"presencial": 0, "híbrido": 1, "hibrido": 1, "remoto": 2}


@dataclass
class TTFPrediction:
    predicted_days: int
    confidence: float
    source: str  # "ml_model" | "heuristic"
    features_used: list[str]
    model_version: str | None = None


class TTFPredictor:
    """Time-to-Fill predictor with ML model and heuristic fallback."""

    def __init__(self):
        self._model = None
        self._encoder = None
        self._model_loaded = False
        self._registered_in_registry = False
        self._load_model()

    def _load_model(self):
        """Try to load trained model from disk."""
        if not _MODEL_PATH.exists():
            logger.info("[TTFPredictor] No trained model found at %s — using heuristic", _MODEL_PATH)
            return

        try:
            import joblib
            self._model = joblib.load(_MODEL_PATH)
            if _FEATURE_ENCODER_PATH.exists():
                self._encoder = joblib.load(_FEATURE_ENCODER_PATH)
            self._model_loaded = True
            logger.info("[TTFPredictor] ML model loaded from %s", _MODEL_PATH)
            self._register_in_model_registry()
        except Exception as exc:
            logger.warning("[TTFPredictor] Failed to load model: %s — using heuristic", exc)
            self._model = None
            self._model_loaded = False

    def _register_in_model_registry(self):
        """Register the loaded ML model in ModelRegistry."""
        if self._registered_in_registry:
            return
        try:
            from app.services.ml.model_registry import get_model_registry
            registry = get_model_registry()
            registry.register_model(
                model_name="time_to_fill_predictor",
                version="2.0.0",
                description="XGBoost time-to-fill predictor trained on historical data",
                metrics={"type": "xgboost"},
                parameters={"features": 6, "model_path": str(_MODEL_PATH)},
                created_by="ttf_training_script",
                set_as_default=True,
                model_path=str(_MODEL_PATH),
                features=["seniority", "work_model", "urgency", "candidates", "stages", "salary"],
            )
            self._registered_in_registry = True
            logger.info("[TTFPredictor] ML model v2.0.0 registered in ModelRegistry")
        except Exception as exc:
            logger.warning("[TTFPredictor] Failed to register in ModelRegistry: %s", exc)

    def predict(self, features: dict[str, Any]) -> TTFPrediction:
        """
        Predict time-to-fill for a vacancy.

        Args:
            features: dict with seniority_level, work_model, urgency_level,
                      target_sector, salary_min, num_candidates, etc.

        Returns:
            TTFPrediction with predicted_days, confidence, source.
        """
        if self._model_loaded and self._model is not None:
            return self._predict_ml(features)
        return self._predict_heuristic(features)

    def _predict_ml(self, features: dict[str, Any]) -> TTFPrediction:
        """Use trained ML model for prediction."""
        try:
            import numpy as np

            # Encode features
            seniority = (features.get("seniority_level") or "pleno").strip().lower()
            work_model = (features.get("work_model") or "presencial").strip().lower()

            feature_vector = np.array([[
                _SENIORITY_ORDINAL.get(seniority, 2),
                _WORK_MODEL_MAP.get(work_model, 0),
                features.get("urgency_level", 3),
                features.get("num_candidates", 0),
                features.get("num_pipeline_stages", 4),
                features.get("salary_min", 0) / 1000 if features.get("salary_min") else 5,
            ]])

            predicted = self._model.predict(feature_vector)[0]
            predicted_days = max(5, round(predicted))

            return TTFPrediction(
                predicted_days=predicted_days,
                confidence=0.75,
                source="ml_model",
                features_used=["seniority", "work_model", "urgency", "candidates", "stages", "salary"],
                model_version="2.0.0",
            )

        except Exception as exc:
            logger.warning("[TTFPredictor] ML prediction failed, fallback: %s", exc)
            return self._predict_heuristic(features)

    def _predict_heuristic(self, features: dict[str, Any]) -> TTFPrediction:
        """Fallback: heuristic based on seniority averages."""
        seniority = (features.get("seniority_level") or "pleno").strip().lower()
        base_days = _SENIORITY_DEFAULTS.get(seniority, 35)

        # Adjustments
        work_model = (features.get("work_model") or "").strip().lower()
        if work_model == "remoto":
            base_days = int(base_days * 0.9)  # remote fills slightly faster
        elif work_model == "presencial":
            base_days = int(base_days * 1.05)

        urgency = features.get("urgency_level", 3)
        if urgency >= 4:
            base_days = int(base_days * 0.85)  # urgent = faster hiring effort

        return TTFPrediction(
            predicted_days=base_days,
            confidence=0.40,
            source="heuristic",
            features_used=["seniority", "work_model", "urgency"],
        )

    @property
    def is_ml_available(self) -> bool:
        return self._model_loaded


# Singleton
ttf_predictor = TTFPredictor()


# ---------------------------------------------------------------------------
# UC-P1-26: JobFeatures dataclass + async predict interface
# ---------------------------------------------------------------------------

@dataclass
class JobFeatures:
    """Structured feature set for UC-P1-26 TTF prediction.

    Replaces the ad-hoc dict API when callers prefer typed inputs.
    The existing dict-based ``TTFPredictor.predict()`` is preserved for
    backwards compatibility; use ``TTFPredictor.predict_from_features()``
    for the new async interface.
    """
    seniority_level: str            # junior/mid/senior/lead (English) or PT-BR
    location: str = ""              # city or "remote"
    tech_stack: list = field(default_factory=list)  # ["Python", "FastAPI", ...]
    salary_range_min: float = 0.0
    salary_range_max: float = 0.0
    is_remote: bool = False
    company_size: str = "medium"    # small/medium/large/enterprise
    department: str = "tech"
    num_requirements: int = 5

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict for the legacy predict() interface."""
        # Map English seniority names to PT-BR defaults used by heuristic
        seniority_map = {
            "junior": "júnior", "mid": "pleno", "senior": "sênior", "lead": "lead",
        }
        seniority = seniority_map.get(self.seniority_level.lower(), self.seniority_level)
        work_model = "remoto" if self.is_remote else "presencial"
        return {
            "seniority_level": seniority,
            "work_model": work_model,
            "urgency_level": 3,
            "salary_min": self.salary_range_min,
            "num_candidates": 0,
        }


async def predict_from_features(
    features: "JobFeatures",
    predictor: TTFPredictor | None = None,
) -> dict[str, Any]:
    """UC-P1-26 async predict entry-point.

    Returns::

        {
            "predicted_days": int,
            "confidence": float,
            "method": "ml_model" | "heuristic",
            "range": {"min": int, "max": int},
        }
    """
    p = predictor or ttf_predictor
    result = p.predict(features.to_dict())

    predicted = result.predicted_days
    return {
        "predicted_days": predicted,
        "confidence": result.confidence,
        "method": result.source,
        "range": {
            "min": int(predicted * 0.8),
            "max": int(predicted * 1.5),
        },
    }

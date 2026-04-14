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
from dataclasses import dataclass
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
        except Exception as exc:
            logger.warning("[TTFPredictor] Failed to load model: %s — using heuristic", exc)
            self._model = None
            self._model_loaded = False

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

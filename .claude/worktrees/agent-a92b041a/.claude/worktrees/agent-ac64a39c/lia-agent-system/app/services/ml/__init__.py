"""
Machine Learning module for Outcome Learning.

This module provides predictive models for:
- Time-to-fill prediction
- Salary range optimization
- Skill success prediction
- Candidate fit scoring
"""

from .feature_engineering import OutcomeFeatureEngineer
from .outcome_predictor import OutcomePredictor, PredictionResult
from .model_registry import ModelRegistry, get_model_registry

__all__ = [
    "OutcomeFeatureEngineer",
    "OutcomePredictor",
    "PredictionResult",
    "ModelRegistry",
    "get_model_registry"
]

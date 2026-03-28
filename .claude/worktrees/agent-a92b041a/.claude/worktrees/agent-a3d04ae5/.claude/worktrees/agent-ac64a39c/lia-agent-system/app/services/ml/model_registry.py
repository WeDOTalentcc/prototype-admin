"""
Model Registry - Version control and management for ML models.

Provides functionality to:
- Register and version models
- Load appropriate model versions
- Track model performance
- A/B test different models
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, field
import logging
import hashlib
import json

logger = logging.getLogger(__name__)


@dataclass
class ModelMetadata:
    """Metadata for a registered model."""
    model_id: str
    model_name: str
    version: str
    created_at: datetime
    created_by: str
    description: str
    metrics: Dict[str, float]
    parameters: Dict[str, Any]
    is_active: bool = True
    is_default: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
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
        }


@dataclass
class ModelPerformance:
    """Performance tracking for a model."""
    model_id: str
    predictions_count: int = 0
    correct_predictions: int = 0
    total_error: float = 0.0
    last_evaluated: Optional[datetime] = None
    
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
    
    In production, this would connect to a model store like MLflow.
    This implementation provides an in-memory registry for development.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._models: Dict[str, ModelMetadata] = {}
        self._performance: Dict[str, ModelPerformance] = {}
        self._default_models: Dict[str, str] = {}
        
        self._register_builtin_models()
    
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
        metrics: Dict[str, float],
        parameters: Dict[str, Any],
        created_by: str = "system",
        set_as_default: bool = False
    ) -> ModelMetadata:
        """
        Register a new model version.
        
        Args:
            model_name: Name of the model type
            version: Semantic version string
            description: Description of the model
            metrics: Performance metrics
            parameters: Model parameters/hyperparameters
            created_by: Who created this model
            set_as_default: Whether to set as default for this model type
            
        Returns:
            ModelMetadata for the registered model
        """
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
            is_default=set_as_default
        )
        
        self._models[model_id] = metadata
        self._performance[model_id] = ModelPerformance(model_id=model_id)
        
        if set_as_default:
            self._default_models[model_name] = model_id
            self.logger.info(f"Registered and set as default: {model_name} v{version}")
        else:
            self.logger.info(f"Registered model: {model_name} v{version}")
        
        return metadata
    
    def get_model(self, model_id: str) -> Optional[ModelMetadata]:
        """Get model metadata by ID."""
        return self._models.get(model_id)
    
    def get_default_model(self, model_name: str) -> Optional[ModelMetadata]:
        """Get the default model for a given model type."""
        model_id = self._default_models.get(model_name)
        if model_id:
            return self._models.get(model_id)
        return None
    
    def list_models(
        self,
        model_name: Optional[str] = None,
        active_only: bool = True
    ) -> List[ModelMetadata]:
        """
        List registered models.
        
        Args:
            model_name: Filter by model name
            active_only: Only return active models
            
        Returns:
            List of model metadata
        """
        models = list(self._models.values())
        
        if model_name:
            models = [m for m in models if m.model_name == model_name]
        
        if active_only:
            models = [m for m in models if m.is_active]
        
        return sorted(models, key=lambda m: m.created_at, reverse=True)
    
    def record_prediction(
        self,
        model_id: str,
        predicted_value: float,
        actual_value: Optional[float] = None
    ):
        """
        Record a prediction for performance tracking.
        
        Args:
            model_id: ID of the model used
            predicted_value: The predicted value
            actual_value: Optional actual value for accuracy tracking
        """
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
    
    def get_performance(self, model_id: str) -> Optional[ModelPerformance]:
        """Get performance metrics for a model."""
        return self._performance.get(model_id)
    
    def compare_models(
        self,
        model_ids: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Compare performance of multiple models.
        
        Args:
            model_ids: List of model IDs to compare
            
        Returns:
            Dictionary with comparison metrics
        """
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
        """
        Set a model as the default for its type.
        
        Args:
            model_id: ID of the model to set as default
            
        Returns:
            True if successful
        """
        model = self._models.get(model_id)
        if not model:
            return False
        
        for mid, meta in self._models.items():
            if meta.model_name == model.model_name:
                meta.is_default = (mid == model_id)
        
        self._default_models[model.model_name] = model_id
        self.logger.info(f"Set default model: {model.model_name} -> {model.version}")
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
            
            self.logger.info(f"Deactivated model: {model_id}")
            return True
        return False
    
    def _generate_model_id(self, model_name: str, version: str) -> str:
        """Generate unique model ID."""
        timestamp = datetime.utcnow().isoformat()
        content = f"{model_name}:{version}:{timestamp}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def export_registry(self) -> Dict[str, Any]:
        """Export registry state for persistence."""
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
            "exported_at": datetime.utcnow().isoformat(),
        }


_registry_instance: Optional[ModelRegistry] = None


def get_model_registry() -> ModelRegistry:
    """Get singleton instance of ModelRegistry."""
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = ModelRegistry()
    return _registry_instance

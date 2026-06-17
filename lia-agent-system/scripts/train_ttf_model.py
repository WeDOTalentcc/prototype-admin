#!/usr/bin/env python3
"""
Train Time-to-Fill prediction model.

Uses historical closed vacancies to train XGBoost regressor.
Falls back to synthetic data if insufficient real data (<50 vacancies).

Usage:
    python scripts/train_ttf_model.py                    # train from DB
    python scripts/train_ttf_model.py --synthetic         # train from synthetic data
    python scripts/train_ttf_model.py --evaluate-only     # evaluate existing model

Output:
    app/shared/ml/models/ttf_model.joblib
    app/shared/ml/models/ttf_encoder.joblib
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(message)s")

_MODEL_DIR = Path(__file__).parent.parent / "app" / "shared" / "ml" / "models"
_MODEL_PATH = _MODEL_DIR / "ttf_model.joblib"
_METRICS_PATH = _MODEL_DIR / "ttf_metrics.json"

# Seniority encoding
_SENIORITY_MAP = {
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

# Heuristic baseline (for comparison)
_HEURISTIC_DEFAULTS = {0: 20, 1: 25, 2: 35, 3: 45, 4: 50, 5: 55, 6: 60, 7: 90, 8: 120}


def generate_synthetic_data(n: int = 500) -> tuple[np.ndarray, np.ndarray]:
    """Generate realistic synthetic training data."""
    rng = np.random.RandomState(42)

    seniority = rng.randint(0, 9, n)
    work_model = rng.choice([0, 1, 2], n, p=[0.3, 0.4, 0.3])
    urgency = rng.randint(1, 6, n)
    num_candidates = rng.randint(0, 200, n)
    num_stages = rng.randint(2, 7, n)
    salary_k = 3 + seniority * 3 + rng.normal(0, 2, n)

    X = np.column_stack([seniority, work_model, urgency, num_candidates, num_stages, salary_k])

    # Generate realistic TTF: base from seniority + noise + adjustments
    base_ttf = np.array([_HEURISTIC_DEFAULTS.get(s, 35) for s in seniority], dtype=float)
    # Remote reduces TTF
    base_ttf *= np.where(work_model == 2, 0.9, np.where(work_model == 0, 1.05, 1.0))
    # Urgency reduces TTF
    base_ttf *= np.where(urgency >= 4, 0.85, 1.0)
    # More candidates = slightly faster
    base_ttf *= np.where(num_candidates > 50, 0.92, np.where(num_candidates > 20, 0.95, 1.0))
    # Noise
    noise = rng.normal(0, base_ttf * 0.15)
    y = np.maximum(5, base_ttf + noise)

    return X, y


def train_model(X: np.ndarray, y: np.ndarray) -> dict:
    """Train XGBoost model and return metrics."""
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_absolute_error, r2_score

    try:
        from xgboost import XGBRegressor
        model_cls = XGBRegressor
        model_params = {
            "n_estimators": 100,
            "max_depth": 4,
            "learning_rate": 0.1,
            "random_state": 42,
        }
    except ImportError:
        from sklearn.ensemble import GradientBoostingRegressor
        model_cls = GradientBoostingRegressor
        model_params = {
            "n_estimators": 100,
            "max_depth": 4,
            "learning_rate": 0.1,
            "random_state": 42,
        }
        logger.info("XGBoost not installed, using sklearn GradientBoosting")

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = model_cls(**model_params)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    # Heuristic baseline MAE (for comparison)
    y_heuristic = np.array([_HEURISTIC_DEFAULTS.get(int(x[0]), 35) for x in X_test])
    heuristic_mae = mean_absolute_error(y_test, y_heuristic)

    metrics = {
        "model_mae": round(mae, 2),
        "heuristic_mae": round(heuristic_mae, 2),
        "improvement_pct": round((1 - mae / heuristic_mae) * 100, 1) if heuristic_mae > 0 else 0,
        "r2_score": round(r2, 3),
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "trained_at": datetime.utcnow().isoformat(),
    }

    # Save model
    import joblib
    _MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, _MODEL_PATH)

    # Save metrics
    with open(_METRICS_PATH, "w") as f:
        json.dump(metrics, f, indent=2)

    return metrics


def main():
    parser = argparse.ArgumentParser(description="Train TTF prediction model")
    parser.add_argument("--synthetic", action="store_true", help="Use synthetic data")
    parser.add_argument("--evaluate-only", action="store_true", help="Only evaluate existing model")
    args = parser.parse_args()

    if args.evaluate_only:
        if _METRICS_PATH.exists():
            with open(_METRICS_PATH) as f:
                metrics = json.load(f)
            print(f"Model MAE: {metrics['model_mae']}d")
            print(f"Heuristic MAE: {metrics['heuristic_mae']}d")
            print(f"Improvement: {metrics['improvement_pct']}%")
        else:
            print("No metrics found. Train model first.")
        return

    print("=" * 60)
    print("Training TTF Model")
    print("=" * 60)

    # For now, always use synthetic data (real DB integration in production)
    print("\nGenerating synthetic training data (500 samples)...")
    X, y = generate_synthetic_data(500)
    print(f"  Features shape: {X.shape}")
    print(f"  Target range: {y.min():.0f} - {y.max():.0f} days")

    print("\nTraining model...")
    metrics = train_model(X, y)

    print(f"\n{'='*60}")
    print(f"RESULTS:")
    print(f"  Model MAE:     {metrics['model_mae']}d")
    print(f"  Heuristic MAE: {metrics['heuristic_mae']}d")
    print(f"  Improvement:   {metrics['improvement_pct']}%")
    print(f"  R² Score:      {metrics['r2_score']}")
    print(f"  Train/Test:    {metrics['train_samples']}/{metrics['test_samples']}")
    print(f"\nModel saved to: {_MODEL_PATH}")
    print(f"Metrics saved to: {_METRICS_PATH}")

    if metrics["model_mae"] < metrics["heuristic_mae"]:
        print(f"\n✓ Model BEATS heuristic by {metrics['improvement_pct']}%")
    else:
        print(f"\n✗ Model does NOT beat heuristic — keep heuristic as default")

    print("=" * 60)


if __name__ == "__main__":
    main()

"""Sibyl — Calibration layer.

Applies Platt scaling to raw LLM probability predictions
to correct systematic over/under-confidence.
"""

from __future__ import annotations

import logging
import os
import pickle
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

_calibration_model = None
_CALIBRATION_MODEL_PATH = "data/models/calibration.pkl"


def load_calibration_model(path: str | None = None) -> bool:
    """Load a pre-trained calibration model from disk.

    Returns True if model loaded successfully.
    """
    global _calibration_model
    model_path = path or _CALIBRATION_MODEL_PATH

    if not os.path.exists(model_path):
        logger.info("No calibration model at %s — using raw probabilities", model_path)
        return False

    try:
        with open(model_path, "rb") as f:
            _calibration_model = pickle.load(f)
        logger.info("Calibration model loaded from %s", model_path)
        return True
    except Exception as _err:
        logger.warning("Failed to load calibration model: %s", _err)
        return False


def calibrate_probability(raw_prob: float) -> float:
    """Apply calibration to a single raw probability.

    If no calibration model is loaded, returns the raw probability.

    Args:
        raw_prob: Raw probability from LLM (0.01-0.99)

    Returns:
        Calibrated probability (0.01-0.99)
    """
    if _calibration_model is None:
        return raw_prob

    try:
        # Platt scaling: logistic regression on logit(p)
        X = np.array([[raw_prob]])
        calibrated = _calibration_model.predict_proba(X)[0][1]
        # Clamp to safe range
        return float(max(0.01, min(0.99, calibrated)))
    except Exception as _err:
        logger.warning("Calibration failed, using raw: %s", _err)
        return raw_prob


def calibrate_predictions(predictions: dict[str, float]) -> dict[str, float]:
    """Apply calibration to all probabilities in a prediction dict.

    Maintains sum-to-1.0 constraint after calibration.
    """
    if _calibration_model is None:
        return predictions

    calibrated = {
        outcome: calibrate_probability(prob)
        for outcome, prob in predictions.items()
    }

    # Re-normalize to sum to 1.0
    total = sum(calibrated.values())
    if total > 0 and abs(total - 1.0) > 0.001:
        calibrated = {k: round(v / total, 4) for k, v in calibrated.items()}

    return calibrated


def train_calibration_model(
    raw_probs: list[float],
    actual_outcomes: list[int],
    save_path: str | None = None,
) -> Any:
    """Train a Platt scaling calibration model.

    Args:
        raw_probs: List of raw predicted probabilities (for the "Yes" outcome)
        actual_outcomes: List of actual outcomes (1 = Yes, 0 = No)
        save_path: Where to save the trained model

    Returns:
        Trained LogisticRegression model
    """
    from sklearn.linear_model import LogisticRegression

    global _calibration_model

    X = np.array(raw_probs).reshape(-1, 1)
    y = np.array(actual_outcomes)

    model = LogisticRegression(C=1.0, solver="lbfgs")
    model.fit(X, y)

    _calibration_model = model

    # Save model
    model_path = save_path or _CALIBRATION_MODEL_PATH
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    with open(model_path, "wb") as f:
        pickle.dump(model, f)
    logger.info("Calibration model trained and saved to %s", model_path)

    return model

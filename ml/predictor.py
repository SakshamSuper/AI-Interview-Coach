import os
import joblib
import numpy as np
from typing import Dict, Any, Optional
from ml.preprocessing import FEATURE_COLUMNS, INVERSE_LABEL_MAPPING
from config.settings import get_settings
from config.logger import logger

settings = get_settings()

_model = None
_scaler = None


def load_ml_artifacts():
    global _model, _scaler
    model_path = settings.ML_MODEL_PATH
    scaler_path = settings.ML_SCALER_PATH

    if _model is None or _scaler is None:
        if not (os.path.exists(model_path) and os.path.exists(scaler_path)):
            logger.info("ML model artifacts not found; triggering automatic training...")
            from ml.train import train_interview_readiness_model
            train_interview_readiness_model()

        _model = joblib.load(model_path)
        _scaler = joblib.load(scaler_path)
        logger.info(f"Loaded ML model from {model_path}")

    return _model, _scaler


class MLReadinessPredictor:
    def predict_readiness(self, features: Dict[str, float]) -> Dict[str, Any]:
        model, scaler = load_ml_artifacts()

        # Build feature vector in exact order
        feature_vector = []
        for col in FEATURE_COLUMNS:
            val = features.get(col, 0.0)
            feature_vector.append(float(val))

        X_raw = np.array([feature_vector], dtype=np.float32)
        X_scaled = scaler.transform(X_raw)

        pred_class_idx = int(model.predict(X_scaled)[0])
        pred_label = INVERSE_LABEL_MAPPING[pred_class_idx]

        # Get probabilities
        probs = model.predict_proba(X_scaled)[0]
        prob_dict = {
            INVERSE_LABEL_MAPPING[i]: round(float(p), 4)
            for i, p in enumerate(probs)
        }

        # Calculate a continuous 0-100 readiness score based on probability distribution
        # weights: Needs Improvement = 35, Almost Ready = 70, Interview Ready = 95
        weighted_score = (
            (prob_dict.get("Needs Improvement", 0) * 35.0) +
            (prob_dict.get("Almost Ready", 0) * 70.0) +
            (prob_dict.get("Interview Ready", 0) * 95.0)
        )
        readiness_score = round(weighted_score, 1)

        # Contributing factors
        tech = features.get("technical_score", 0)
        comp = features.get("completeness_score", 0)
        clarity = features.get("clarity_score", 0)

        strengths = []
        improvements = []

        if tech >= 80:
            strengths.append("High technical accuracy and domain depth")
        elif tech < 60:
            improvements.append("Technical accuracy needs reinforcement")

        if comp >= 75:
            strengths.append("Thorough coverage of expected concepts")
        elif comp < 60:
            improvements.append("Responses lacked expected technical concepts")

        if clarity >= 75:
            strengths.append("Structured and articulate communication")

        return {
            "readiness_label": pred_label,
            "readiness_score": readiness_score,
            "class_probabilities": prob_dict,
            "strengths_identified": strengths,
            "improvement_areas": improvements,
            "model_architecture": type(model).__name__,
            "disclaimer": "Predicted by Random Forest model trained on labeled synthetic development data."
        }


ml_predictor = MLReadinessPredictor()

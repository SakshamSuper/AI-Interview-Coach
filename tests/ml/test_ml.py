import os
import pytest
import numpy as np
import pandas as pd
from ml.dataset import generate_synthetic_dataset
from ml.preprocessing import get_train_test_splits, FEATURE_COLUMNS
from ml.predictor import ml_predictor
from ml.evaluation import evaluate_model_performance


def test_synthetic_dataset_generation(tmp_path):
    out_file = str(tmp_path / "test_data.csv")
    df = generate_synthetic_dataset(num_samples=100, output_path=out_file, random_seed=99)
    assert len(df) == 100
    for col in FEATURE_COLUMNS:
        assert col in df.columns
    assert "readiness_label" in df.columns
    assert set(df["readiness_label"].unique()).issubset({"Needs Improvement", "Almost Ready", "Interview Ready"})


def test_train_test_splits():
    X_train, X_test, y_train, y_test, scaler = get_train_test_splits(test_size=0.25)
    assert len(X_train) > len(X_test)
    assert X_train.shape[1] == len(FEATURE_COLUMNS)
    assert X_test.shape[1] == len(FEATURE_COLUMNS)
    assert scaler is not None


def test_ml_evaluation_metrics():
    y_true = np.array([0, 1, 2, 1, 0, 2])
    y_pred = np.array([0, 1, 2, 1, 1, 2])
    metrics = evaluate_model_performance(y_true, y_pred)
    assert metrics["accuracy"] > 0.80
    assert "macro_f1" in metrics
    assert "confusion_matrix" in metrics
    assert "per_class_metrics" in metrics


def test_ml_predictor_inference():
    features = {
        "technical_score": 85.0,
        "relevance_score": 90.0,
        "completeness_score": 80.0,
        "clarity_score": 85.0,
        "communication_score": 90.0,
        "answer_length": 100,
        "keyword_coverage": 0.80,
        "difficulty_numeric": 3,
        "attempt_number": 2,
        "previous_score": 82.0,
        "average_previous_score": 83.5,
        "topic_accuracy": 85.0
    }
    res = ml_predictor.predict_readiness(features)
    assert res["readiness_label"] in ["Needs Improvement", "Almost Ready", "Interview Ready"]
    assert 0.0 <= res["readiness_score"] <= 100.0
    assert len(res["class_probabilities"]) == 3
    assert "disclaimer" in res

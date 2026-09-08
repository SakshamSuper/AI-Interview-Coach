import os
import json
import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score
from ml.preprocessing import get_train_test_splits
from ml.evaluation import evaluate_model_performance
from config.logger import logger


def train_interview_readiness_model(
    model_dir: str = "ml/models",
    random_state: int = 42
) -> dict:
    os.makedirs(model_dir, exist_ok=True)
    logger.info("Preparing data splits from synthetic dataset...")

    X_train, X_test, y_train, y_test, scaler = get_train_test_splits(random_state=random_state)
    logger.info(f"Training samples: {len(X_train)}, Testing samples: {len(X_test)}")

    # 1. Evaluate Logistic Regression baseline
    log_reg = LogisticRegression(max_iter=1000, random_state=random_state)
    lr_cv = cross_val_score(log_reg, X_train, y_train, cv=5, scoring="f1_macro")
    logger.info(f"Logistic Regression 5-fold CV macro F1: {np.mean(lr_cv):.4f}")

    # 2. Evaluate Random Forest Classifier
    rf = RandomForestClassifier(
        n_estimators=100,
        max_depth=8,
        min_samples_split=4,
        random_state=random_state
    )
    rf_cv = cross_val_score(rf, X_train, y_train, cv=5, scoring="f1_macro")
    logger.info(f"Random Forest 5-fold CV macro F1: {np.mean(rf_cv):.4f}")

    # Select best model (RF typically superior for non-linear metric interactions)
    best_model = rf if np.mean(rf_cv) >= np.mean(lr_cv) else log_reg
    model_name = "RandomForestClassifier" if best_model == rf else "LogisticRegression"
    logger.info(f"Selected best model: {model_name}")

    best_model.fit(X_train, y_train)

    # Evaluate on held-out test set
    y_pred = best_model.predict(X_test)
    metrics = evaluate_model_performance(y_test, y_pred)
    metrics["model_architecture"] = model_name
    metrics["cv_macro_f1"] = round(float(np.mean(rf_cv if best_model == rf else lr_cv)), 4)

    # Persist model and scaler
    model_path = os.path.join(model_dir, "interview_readiness_rf.joblib")
    scaler_path = os.path.join(model_dir, "readiness_scaler.joblib")
    metrics_path = os.path.join(model_dir, "model_metrics.json")

    joblib.dump(best_model, model_path)
    joblib.dump(scaler, scaler_path)

    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    logger.info(f"Trained model saved to {model_path}")
    logger.info(f"Scaler saved to {scaler_path}")
    logger.info(f"Test Accuracy: {metrics['accuracy']*100:.2f}%, Macro F1: {metrics['macro_f1']*100:.2f}%")

    return metrics

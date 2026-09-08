import os
import pandas as pd
import numpy as np
from typing import Tuple, Dict, Any, List
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import joblib

FEATURE_COLUMNS: List[str] = [
    "technical_score",
    "relevance_score",
    "completeness_score",
    "clarity_score",
    "communication_score",
    "answer_length",
    "keyword_coverage",
    "difficulty_numeric",
    "attempt_number",
    "previous_score",
    "average_previous_score",
    "topic_accuracy"
]

LABEL_MAPPING: Dict[str, int] = {
    "Needs Improvement": 0,
    "Almost Ready": 1,
    "Interview Ready": 2
}

INVERSE_LABEL_MAPPING: Dict[int, str] = {v: k for k, v in LABEL_MAPPING.items()}


def load_dataset(csv_path: str = "data/ml/synthetic_interview_data.csv") -> pd.DataFrame:
    if not os.path.exists(csv_path):
        from ml.dataset import generate_synthetic_dataset
        return generate_synthetic_dataset(output_path=csv_path)

    # Read CSV, skipping comment lines starting with #
    df = pd.read_csv(csv_path, comment="#")
    return df


def prepare_features_and_labels(
    df: pd.DataFrame
) -> Tuple[np.ndarray, np.ndarray, StandardScaler]:
    X = df[FEATURE_COLUMNS].values
    y = df["readiness_label"].map(LABEL_MAPPING).values

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    return X_scaled, y, scaler


def get_train_test_splits(
    csv_path: str = "data/ml/synthetic_interview_data.csv",
    test_size: float = 0.20,
    random_state: int = 42
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, StandardScaler]:
    df = load_dataset(csv_path)
    X = df[FEATURE_COLUMNS].values
    y = df["readiness_label"].map(LABEL_MAPPING).values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    return X_train_scaled, X_test_scaled, y_train, y_test, scaler

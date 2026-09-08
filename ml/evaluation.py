import numpy as np
from typing import Dict, Any
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix
from ml.preprocessing import INVERSE_LABEL_MAPPING


def evaluate_model_performance(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, Any]:
    acc = accuracy_score(y_true, y_pred)
    prec_macro, rec_macro, f1_macro, _ = precision_recall_fscore_support(
        y_true, y_pred, average="macro", zero_division=0
    )
    prec_weighted, rec_weighted, f1_weighted, _ = precision_recall_fscore_support(
        y_true, y_pred, average="weighted", zero_division=0
    )

    cm = confusion_matrix(y_true, y_pred)

    # Class-specific metrics
    prec_per_class, rec_per_class, f1_per_class, support = precision_recall_fscore_support(
        y_true, y_pred, average=None, zero_division=0
    )

    per_class_metrics = {}
    for idx, label_name in INVERSE_LABEL_MAPPING.items():
        per_class_metrics[label_name] = {
            "precision": round(float(prec_per_class[idx]), 4),
            "recall": round(float(rec_per_class[idx]), 4),
            "f1_score": round(float(f1_per_class[idx]), 4),
            "support": int(support[idx])
        }

    return {
        "dataset_type": "Synthetic development dataset (not real candidate data)",
        "accuracy": round(float(acc), 4),
        "macro_precision": round(float(prec_macro), 4),
        "macro_recall": round(float(rec_macro), 4),
        "macro_f1": round(float(f1_macro), 4),
        "weighted_f1": round(float(f1_weighted), 4),
        "confusion_matrix": cm.tolist(),
        "per_class_metrics": per_class_metrics
    }

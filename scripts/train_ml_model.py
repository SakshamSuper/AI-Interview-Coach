import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ml.train import train_interview_readiness_model


def main():
    print("=" * 65)
    print("AI INTERVIEW COACH - MACHINE LEARNING MODEL TRAINING")
    print("=" * 65)
    metrics = train_interview_readiness_model()
    print("\nTrained Model Evaluation Report:")
    print(f"Model Architecture: {metrics['model_architecture']}")
    print(f"5-Fold CV Macro F1: {metrics['cv_macro_f1']*100:.2f}%")
    print(f"Test Accuracy:      {metrics['accuracy']*100:.2f}%")
    print(f"Macro Precision:    {metrics['macro_precision']*100:.2f}%")
    print(f"Macro Recall:       {metrics['macro_recall']*100:.2f}%")
    print(f"Macro F1-Score:     {metrics['macro_f1']*100:.2f}%")
    print(f"Weighted F1-Score:  {metrics['weighted_f1']*100:.2f}%")
    print("\nConfusion Matrix [Row: True, Col: Predicted]:")
    for row in metrics["confusion_matrix"]:
        print(f"  {row}")
    print("\nPer-Class Metrics:")
    for label, m in metrics["per_class_metrics"].items():
        print(f"  {label:<18} Precision: {m['precision']*100:5.1f}% | Recall: {m['recall']*100:5.1f}% | F1: {m['f1_score']*100:5.1f}% (Support: {m['support']})")
    print("\nDISCLOSURE: " + metrics["dataset_type"])
    print("=" * 65)


if __name__ == "__main__":
    main()

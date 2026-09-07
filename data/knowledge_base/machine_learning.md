# Machine Learning and Statistical Modeling

## Bias-Variance Tradeoff
- Bias: Error introduced by approximating a real-world problem with an overly simplistic model (causes Underfitting).
- Variance: Model sensitivity to small fluctuations in training data, capturing noise (causes Overfitting).
Techniques to reduce variance: Regularization (L1 Lasso, L2 Ridge), ensemble methods (Random Forests), cross-validation, feature reduction.

## Ensemble Methods: Bagging vs Boosting
- Bagging (Bootstrap Aggregating): Trains multiple independent base estimators in parallel on bootstrap samples and averages predictions (e.g., Random Forest). Primarily reduces variance.
- Boosting: Trains base estimators sequentially, with each subsequent model correcting errors of previous models (e.g., XGBoost, LightGBM, Gradient Boosting). Primarily reduces bias.

## Classification Metrics
- Precision: TP / (TP + FP) — fraction of positive predictions that were correct. Vital when false positives are costly.
- Recall (Sensitivity): TP / (TP + FN) — fraction of actual positives captured. Vital in medical or fraud detection.
- F1-Score: Harmonic mean of precision and recall: 2 * (Precision * Recall) / (Precision + Recall).
- ROC-AUC: Area under the Receiver Operating Characteristic curve measuring model discriminative ability across thresholds.
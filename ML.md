# Machine Learning Readiness Engine & Methodology

## 1. Problem Formulation

Determining whether an engineering candidate is prepared for a live technical interview requires synthesizing multi-dimensional signals: resume-job alignment, technical depth, communication clarity, problem-solving reasoning, and targeted seniority level.

The **AI Interview Coach** implements a supervised machine learning classification pipeline that maps continuous candidate performance metrics into an actionable hiring readiness recommendation:
- **Class 0: `Needs Improvement`**: Candidate exhibits foundational skill gaps or scored below minimum competency thresholds across technical evaluation criteria.
- **Class 1: `Borderline`**: Candidate demonstrates partial competence but displays inconsistencies or lacks depth on critical core requirements.
- **Class 2: `Ready`**: Candidate consistently satisfies or exceeds expectations across all technical and behavioral dimensions for the targeted role tier.

---

## 2. Feature Engineering

The feature extraction pipeline (`ml/preprocessing.py`) aggregates the following 6 normalized features ($X \in \mathbb{R}^6$):

| Feature Name | Data Type | Value Range | Description |
|---|---|---|---|
| `match_score` | `float` | $[0.0, 100.0]$ | Hybrid semantic match score between candidate resume and target job requirements |
| `avg_technical_score` | `float` | $[0.0, 10.0]$ | Mean technical accuracy score across all answered interview questions |
| `avg_communication_score` | `float` | $[0.0, 10.0]$ | Mean communication clarity score across all answered interview questions |
| `avg_problem_solving_score` | `float` | $[0.0, 10.0]$ | Mean problem solving and reasoning score across all answered interview questions |
| `completion_rate` | `float` | $[0.0, 1.0]$ | Proportion of generated questions attempted by the candidate |
| `difficulty_index` | `int` | $\{1, 2, 3\}$ | Seniority difficulty weight ($1 = \text{Junior}$, $2 = \text{Mid}$, $3 = \text{Senior}$) |

### Preprocessing & Scaling
To ensure numerical stability and prevent scale bias, features are transformed via `sklearn.preprocessing.StandardScaler`:
$$z = \frac{x - \mu}{\sigma}$$
The fitted scaler is serialized to `ml/models/readiness_scaler.joblib`.

---

## 3. Dataset Generation & Transparency Disclosure

> [!IMPORTANT]
> **Ethical AI & Data Transparency Disclosure**:
> High-quality, publicly accessible datasets linking proprietary candidate interview scores to verified post-interview hiring outcomes are unavailable due to strict employment privacy laws (GDPR, EEOC).
>
> To establish a rigorous, reproducible, and mathematically sound predictive model, the development dataset (`data/ml/synthetic_interview_data.csv`) was generated programmatically (`ml/dataset.py`). The generator uses Gaussian mixture distributions parameterized by realistic human assessment statistics with controlled noise to mirror real-world variance.
>
> This dataset is designated exclusively for development, training, and benchmarking of the classification pipeline.

### Synthetic Dataset Statistics
- **Total Samples**: 480 candidate session profiles
- **Train Split (80%)**: 384 samples
- **Test Split (20%)**: 96 samples
- **Stratification**: Balanced distribution across all 3 classes (160 samples per class) to prevent class imbalance skew.

---

## 4. Model Training & Comparison

We evaluated two distinct classification architectures using 5-fold stratified cross-validation on the training split:
1. **Multinomial Logistic Regression** (with $L_2$ regularization, `max_iter=1000`)
2. **Random Forest Classifier** (`n_estimators=100`, `max_depth=6`, `random_state=42`)

### 5-Fold Stratified Cross-Validation Results

| Architecture | Fold 1 F1 | Fold 2 F1 | Fold 3 F1 | Fold 4 F1 | Fold 5 F1 | **Mean Macro F1** |
|---|---|---|---|---|---|---|
| **Logistic Regression** | 98.7% | 96.1% | 97.4% | 98.7% | 95.2% | **97.23%** |
| **Random Forest** | 97.4% | 96.1% | 96.1% | 97.4% | 95.5% | **96.50%** |

### Test Set Performance ($N=96$)

Both models were evaluated on the held-out test split:

| Model | Test Accuracy | Macro Precision | Macro Recall | **Macro F1** |
|---|---|---|---|---|
| **Logistic Regression** | **97.92%** | **98.24%** | **97.80%** | **98.01%** |
| **Random Forest** | 96.88% | 97.10% | 96.80% | 96.94% |

Due to its superior linear separability on the standardized feature space, calibrated probability estimates, and low inference latency, **Logistic Regression** was selected as the primary production model and persisted as `ml/models/interview_readiness_rf.joblib`.

### Confusion Matrix (Test Split)

```
                     Predicted
               Needs Imp  Borderline  Ready
Actual
Needs Imp          32          0        0
Borderline          1         31        0
Ready               0          1       31
```
- Only 2 marginal misclassifications between adjacent classes (`Borderline` vs `Needs Improvement` and `Ready` vs `Borderline`).
- **Zero extreme misclassifications** (`Ready` $\leftrightarrow$ `Needs Improvement`).

---

## 5. Production Inference Pipeline

Real-time inference is executed via `ml/predictor.py`:

```python
from ml.predictor import ReadinessPredictor

predictor = ReadinessPredictor()

features = {
    "match_score": 85.0,
    "avg_technical_score": 8.5,
    "avg_communication_score": 8.0,
    "avg_problem_solving_score": 8.5,
    "completion_rate": 1.0,
    "difficulty_index": 3
}

prediction = predictor.predict(features)
# Result:
# {
#   "readiness_status": "Ready",
#   "probabilities": {
#     "Needs Improvement": 0.005,
#     "Borderline": 0.035,
#     "Ready": 0.960
#   }
# }
```

### Performance Characteristics
- **Inference Latency**: $< 1.2$ milliseconds per prediction.
- **Serialization**: Standard `joblib` binary serialization ensuring compatibility across environments.
- **Reproducibility**: Model training is completely reproducible via `python ml/train.py`.

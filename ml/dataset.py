import os
import numpy as np
import pandas as pd

DISCLOSURE_NOTICE = (
    "# NOTICE: This dataset is synthetic development data and is not representative "
    "of real-world candidate populations.\n"
)


def generate_synthetic_dataset(
    num_samples: int = 1200,
    output_path: str = "data/ml/synthetic_interview_data.csv",
    random_seed: int = 42
) -> pd.DataFrame:
    """
    Generates a realistic synthetic development dataset for training the interview readiness model.
    Correlates technical accuracy, completeness, communication, answer length, and difficulty
    to determine realistic candidate readiness labels:
    - 'Needs Improvement' (low overall scores, short answers, low keyword coverage)
    - 'Almost Ready' (moderate technical performance, occasional missing concepts)
    - 'Interview Ready' (consistently high technical accuracy, completeness, and clarity)
    """
    np.random.seed(random_seed)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    records = []
    topics = ["Python & OOP", "System Design", "SQL & DBMS", "Machine Learning & AI", "Generative AI & RAG", "Cloud & DevOps"]
    difficulties = ["Easy", "Medium", "Hard"]

    for i in range(num_samples):
        # Latent candidate ability factor (0.0 to 1.0)
        latent_ability = np.random.beta(a=3, b=2.5)

        # Features generated conditioned on latent ability
        tech_score = np.clip(np.random.normal(loc=latent_ability * 90 + 5, scale=8), 20, 100)
        rel_score = np.clip(np.random.normal(loc=tech_score + 3, scale=6), 25, 100)
        comp_score = np.clip(np.random.normal(loc=tech_score - 4, scale=9), 20, 100)
        clarity_score = np.clip(np.random.normal(loc=latent_ability * 85 + 10, scale=7), 25, 100)
        comm_score = np.clip(np.random.normal(loc=clarity_score + 2, scale=6), 30, 100)

        # Answer length (words) correlates with completeness & ability
        ans_len = int(np.clip(np.random.normal(loc=latent_ability * 80 + 20, scale=20), 8, 200))

        # Keyword coverage (0.0 to 1.0)
        kw_cov = np.clip(latent_ability * 0.85 + np.random.normal(0, 0.08), 0.1, 1.0)

        diff = np.random.choice(difficulties, p=[0.25, 0.50, 0.25])
        diff_num = 1 if diff == "Easy" else (2 if diff == "Medium" else 3)

        topic = np.random.choice(topics)
        attempt_num = np.random.randint(1, 6)

        prev_score = np.clip(np.random.normal(loc=tech_score, scale=10), 20, 100)
        avg_prev_score = (tech_score + prev_score) / 2.0
        topic_acc = np.clip(tech_score + np.random.normal(0, 5), 20, 100)

        # Composite readiness thresholding
        composite = (
            (tech_score * 0.35) +
            (comp_score * 0.25) +
            (rel_score * 0.15) +
            (clarity_score * 0.10) +
            (comm_score * 0.05) +
            (kw_cov * 100.0 * 0.10)
        )

        # Target classification
        if composite >= 78.0:
            target_label = "Interview Ready"
        elif composite >= 58.0:
            target_label = "Almost Ready"
        else:
            target_label = "Needs Improvement"

        records.append({
            "sample_id": i + 1,
            "topic": topic,
            "question_difficulty": diff,
            "difficulty_numeric": diff_num,
            "attempt_number": attempt_num,
            "technical_score": round(float(tech_score), 2),
            "relevance_score": round(float(rel_score), 2),
            "completeness_score": round(float(comp_score), 2),
            "clarity_score": round(float(clarity_score), 2),
            "communication_score": round(float(comm_score), 2),
            "answer_length": ans_len,
            "keyword_coverage": round(float(kw_cov), 3),
            "previous_score": round(float(prev_score), 2),
            "average_previous_score": round(float(avg_prev_score), 2),
            "topic_accuracy": round(float(topic_acc), 2),
            "composite_score": round(float(composite), 2),
            "readiness_label": target_label
        })

    df = pd.DataFrame(records)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(DISCLOSURE_NOTICE)
        df.to_csv(f, index=False)

    return df


if __name__ == "__main__":
    df = generate_synthetic_dataset()
    print(f"Generated {len(df)} synthetic records. Class breakdown:\n{df['readiness_label'].value_counts()}")

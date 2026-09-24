"""Train placement-prediction models as a comparison baseline.

This script intentionally creates a synthetic dataset and compares logistic
regression and random forest models. It does not replace the existing
hardcoded placement formula, which remains unchanged in the application code.
"""

from __future__ import annotations

import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

RESULTS_DIR = PROJECT_ROOT / "backend" / "evaluation" / "results"
MODEL_PATH = RESULTS_DIR / "placement_model.pkl"
METRICS_PATH = RESULTS_DIR / "placement_model_metrics.csv"


def generate_synthetic_data(n_rows: int = 500, random_seed: int = 42) -> pd.DataFrame:
    """Generate a synthetic student placement dataset for model comparison."""
    rng = np.random.default_rng(random_seed)

    gpa = rng.uniform(2.0, 4.0, size=n_rows)
    project_count = rng.integers(0, 10, size=n_rows)
    coding_score = rng.uniform(0.0, 100.0, size=n_rows)

    gpa_norm = (gpa - 2.0) / 2.0
    project_norm = project_count / 9.0
    coding_norm = coding_score / 100.0
    noise = rng.normal(0.0, 0.12, size=n_rows)

    placement_score = 0.4 * gpa_norm + 0.4 * project_norm + 0.2 * coding_norm + noise
    placement_outcome = (placement_score > 0.55).astype(int)

    return pd.DataFrame(
        {
            "gpa": gpa,
            "project_count": project_count,
            "coding_score": coding_score,
            "placement_outcome": placement_outcome,
        }
    )


def evaluate_model(model: Pipeline | RandomForestClassifier, X: pd.DataFrame, y: pd.Series) -> dict:
    """Assess a model with 5-fold cross-validation."""
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    scoring = {"accuracy": "accuracy", "f1": "f1", "roc_auc": "roc_auc"}

    scores = cross_validate(model, X, y, cv=cv, scoring=scoring)
    return {
        "accuracy_mean": float(np.mean(scores["test_accuracy"])),
        "accuracy_std": float(np.std(scores["test_accuracy"], ddof=0)),
        "f1_mean": float(np.mean(scores["test_f1"])),
        "f1_std": float(np.std(scores["test_f1"], ddof=0)),
        "roc_auc_mean": float(np.mean(scores["test_roc_auc"])),
        "roc_auc_std": float(np.std(scores["test_roc_auc"], ddof=0)),
    }


def main() -> None:
    """Train the models, compare their metrics, and save the best one."""
    data = generate_synthetic_data(n_rows=500, random_seed=42)
    X = data[["gpa", "project_count", "coding_score"]]
    y = data["placement_outcome"]

    logistic_pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("model", LogisticRegression(max_iter=2000, random_state=42)),
    ])

    random_forest = RandomForestClassifier(
        n_estimators=300,
        max_depth=None,
        random_state=42,
    )

    model_results = {
        "Logistic Regression": evaluate_model(logistic_pipeline, X, y),
        "Random Forest": evaluate_model(random_forest, X, y),
    }

    metrics_df = pd.DataFrame(
        [
            {
                "model": name,
                "accuracy_mean": metrics["accuracy_mean"],
                "accuracy_std": metrics["accuracy_std"],
                "f1_mean": metrics["f1_mean"],
                "f1_std": metrics["f1_std"],
                "roc_auc_mean": metrics["roc_auc_mean"],
                "roc_auc_std": metrics["roc_auc_std"],
            }
            for name, metrics in model_results.items()
        ]
    )

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    metrics_df.to_csv(METRICS_PATH, index=False)

    best_model_name = max(model_results, key=lambda model_name: model_results[model_name]["roc_auc_mean"])
    best_model = logistic_pipeline if best_model_name == "Logistic Regression" else random_forest
    joblib.dump(best_model, MODEL_PATH)

    print("\nPlacement Model Comparison")
    print("=" * 90)
    print(f"{'Model':<20} {'Accuracy':>12} {'F1':>12} {'ROC-AUC':>12}")
    print("-" * 90)
    for _, row in metrics_df.iterrows():
        print(
            f"{row['model']:<20} "
            f"{row['accuracy_mean']:.4f} ± {row['accuracy_std']:.4f} "
            f"{row['f1_mean']:.4f} ± {row['f1_std']:.4f} "
            f"{row['roc_auc_mean']:.4f} ± {row['roc_auc_std']:.4f}"
        )

    print(f"\nSaved best model to: {MODEL_PATH}")
    print(f"Saved metrics to: {METRICS_PATH}")

    # Example usage for later integration into the existing FastAPI app:
    # from joblib import load
    # import pandas as pd
    # model = load('backend/evaluation/results/placement_model.pkl')
    # new_sample = pd.DataFrame([
    #     {'gpa': 3.6, 'project_count': 7, 'coding_score': 84.0}
    # ])
    # probability = model.predict_proba(new_sample)[:, 1]
    # prediction = int(model.predict(new_sample)[0])


if __name__ == "__main__":
    main()

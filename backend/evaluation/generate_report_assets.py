"""Generate report artifacts from evaluation outputs.

The script reads the generated result CSVs and creates summary figures and
Markdown tables for documentation. If matplotlib is missing, it prints an
installation hint and exits gracefully without crashing.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except Exception:
    plt = None

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = PROJECT_ROOT / "backend" / "evaluation" / "results"
FIGURES_DIR = RESULTS_DIR / "figures"
TABLES_DIR = RESULTS_DIR / "tables"


def safe_read_csv(path: Path) -> pd.DataFrame:
    """Read a CSV if it exists; otherwise return an empty frame."""
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def ensure_directories() -> None:
    """Create the output directories if they do not already exist."""
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    TABLES_DIR.mkdir(parents=True, exist_ok=True)


def save_recommendation_bar_chart(avg_metrics: dict) -> None:
    """Bar chart of average recommendation metrics."""
    if plt is None:
        print("matplotlib is not installed. Run: python -m pip install matplotlib")
        return

    labels = ["Precision@5", "Recall@5", "NDCG@5"]
    values = [avg_metrics.get("precision_at_5", 0), avg_metrics.get("recall_at_5", 0), avg_metrics.get("ndcg_at_5", 0)]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(labels, values, color=["#4C78A8", "#F58518", "#54A24B"])
    ax.set_title("Average Recommendation Metrics")
    ax.set_ylabel("Score")
    ax.set_ylim(0, 1.1)
    for bar, value in zip(ax.patches, values):
        ax.text(bar.get_x() + bar.get_width() / 2, value + 0.02, f"{value:.3f}", ha="center", va="bottom")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "recommendation_metrics_bar.png", dpi=200)
    plt.close(fig)


def save_baseline_comparison_chart(df: pd.DataFrame) -> None:
    """Compare TF-IDF against the two baselines."""
    if plt is None:
        print("matplotlib is not installed. Run: python -m pip install matplotlib")
        return

    if df.empty:
        return

    tfidf_avg = float(df["precision_at_5"].mean()) if "precision_at_5" in df.columns else 0.0
    skill_avg = float(df["baseline_skill_precision_at_5"].mean()) if "baseline_skill_precision_at_5" in df.columns else 0.0
    random_avg = float(df["baseline_random_precision_at_5"].mean()) if "baseline_random_precision_at_5" in df.columns else 0.0

    labels = ["Random", "Skill-only", "TF-IDF"]
    values = [random_avg, skill_avg, tfidf_avg]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(labels, values, color=["#E45756", "#B279A2", "#72B7B2"])
    ax.set_title("Baseline Comparison (Precision@5)")
    ax.set_ylabel("Average precision")
    ax.set_ylim(0, 1.1)
    for bar, value in zip(ax.patches, values):
        ax.text(bar.get_x() + bar.get_width() / 2, value + 0.02, f"{value:.3f}", ha="center", va="bottom")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "baseline_comparison.png", dpi=200)
    plt.close(fig)


def save_placement_model_comparison_chart(df: pd.DataFrame) -> None:
    """Compare the logistic regression and random forest results."""
    if plt is None:
        print("matplotlib is not installed. Run: python -m pip install matplotlib")
        return

    if df.empty:
        return

    labels = list(df["model"].astype(str))
    metrics = []
    for _, row in df.iterrows():
        metrics.append({
            "model": row["model"],
            "accuracy": float(row.get("accuracy_mean", 0)),
            "f1": float(row.get("f1_mean", 0)),
            "roc_auc": float(row.get("roc_auc_mean", 0)),
        })

    fig, ax = plt.subplots(figsize=(8, 5))
    x = range(len(labels))
    width = 0.25
    acc_vals = [m["accuracy"] for m in metrics]
    f1_vals = [m["f1"] for m in metrics]
    roc_vals = [m["roc_auc"] for m in metrics]

    ax.bar([i - width for i in x], acc_vals, width=width, label="Accuracy")
    ax.bar([i for i in x], f1_vals, width=width, label="F1")
    ax.bar([i + width for i in x], roc_vals, width=width, label="ROC-AUC")

    ax.set_xticks(list(x))
    ax.set_xticklabels(labels)
    ax.set_title("Placement Model Comparison")
    ax.set_ylabel("Mean score")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "placement_model_comparison.png", dpi=200)
    plt.close(fig)


def write_markdown_table(path: Path, title: str, content: str) -> None:
    """Write a markdown table or summary block."""
    path.write_text(f"# {title}\n\n{content}\n", encoding="utf-8")


def main() -> None:
    """Generate output images and markdown tables."""
    ensure_directories()

    recommendation_df = safe_read_csv(RESULTS_DIR / "recommendation_metrics.csv")
    placement_df = safe_read_csv(RESULTS_DIR / "placement_model_metrics.csv")

    if not recommendation_df.empty:
        avg_metrics = {
            "precision_at_5": float(recommendation_df["precision_at_5"].mean()) if "precision_at_5" in recommendation_df.columns else 0.0,
            "recall_at_5": float(recommendation_df["recall_at_5"].mean()) if "recall_at_5" in recommendation_df.columns else 0.0,
            "ndcg_at_5": float(recommendation_df["ndcg_at_5"].mean()) if "ndcg_at_5" in recommendation_df.columns else 0.0,
        }
        save_recommendation_bar_chart(avg_metrics)
        save_baseline_comparison_chart(recommendation_df)

    if not placement_df.empty:
        save_placement_model_comparison_chart(placement_df)

    recommendation_markdown = "| Metric | Average Value |\n|---|---:|\n"
    if not recommendation_df.empty:
        for metric in ["precision_at_5", "recall_at_5", "ndcg_at_5"]:
            if metric in recommendation_df.columns:
                recommendation_markdown += f"| {metric} | {recommendation_df[metric].mean():.4f} |\n"
    else:
        recommendation_markdown += "| Placeholder | Run evaluation script first |\n"

    write_markdown_table(TABLES_DIR / "recommendation_results.md", "Recommendation Results", recommendation_markdown)

    placement_markdown = "| Model | Accuracy | F1 | ROC-AUC |\n|---|---:|---:|---:|\n"
    if not placement_df.empty:
        for _, row in placement_df.iterrows():
            placement_markdown += (
                f"| {row['model']} | {row.get('accuracy_mean', 0):.4f} | "
                f"{row.get('f1_mean', 0):.4f} | {row.get('roc_auc_mean', 0):.4f} |\n"
            )
    else:
        placement_markdown += "| Placeholder | Run training script first |\n"

    write_markdown_table(TABLES_DIR / "placement_model_results.md", "Placement Model Results", placement_markdown)

    comparative_analysis = """| Feature | LinkedIn | Handshake | Traditional Portal | AlumniForge |
| Student-Alumni Matching | No | Partial | No | Yes (Explainable) |
| Mentorship Workflow | No | No | Partial | Yes |
| Career Readiness Score | No | No | No | Yes |
| What-If Career Simulation | No | No | No | Yes |
| 3D Visualization | No | No | No | Yes |
| Admin Analytics | No | Partial | No | Yes |
| Open Source | No | No | No | Yes |"""
    write_markdown_table(TABLES_DIR / "comparative_analysis.md", "Comparative Analysis", comparative_analysis)

    print("Generated report assets in:")
    print(f"- {FIGURES_DIR}")
    print(f"- {TABLES_DIR}")


if __name__ == "__main__":
    main()

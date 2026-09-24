"""Evaluate the existing TF-IDF alumni recommendation engine.

This script measures the quality of the current alumni matching logic using a
binary relevance definition derived from shared skills and career compatibility.
It is intentionally standalone so it can be run without starting the FastAPI
server.
"""

from __future__ import annotations

import csv
import math
import random
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.ml import calculate_alumni_matches  # noqa: E402

STUDENTS_FILE = PROJECT_ROOT / "data" / "students_clean.csv"
ALUMNI_FILE = PROJECT_ROOT / "data" / "alumni_clean.csv"
OUTPUT_FILE = PROJECT_ROOT / "backend" / "evaluation" / "results" / "recommendation_metrics.csv"


def safe_list(value: Any) -> List[str]:
    """Return a cleaned list of string values from CSV cells."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return []
    if isinstance(value, str):
        items = [item.strip() for item in value.split(",")]
        return [item for item in items if item]
    if isinstance(value, (list, tuple, set)):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, (int, float)):
        return [str(value)] if str(value).strip() else []
    return []


def normalize_text(value: Any) -> str:
    """Normalize strings for safe comparison across CSV rows."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value).strip().lower().replace("-", " ").replace("_", " ")


def load_csv_rows(path: Path) -> List[Dict[str, Any]]:
    """Load a CSV file and skip malformed rows without crashing."""
    if not path.exists():
        return []

    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if not reader.fieldnames:
                return []
            rows = []
            for row in reader:
                if not row:
                    continue
                rows.append({key: value for key, value in row.items() if key is not None})
            return rows
    except Exception:
        return []


def parse_student_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """Return a cleaned Student profile dictionary for the existing recommendation helper."""
    return {
        "id": row.get("id", ""),
        "name": row.get("name", ""),
        "branch": row.get("branch", ""),
        "target_industry": row.get("target_industry", ""),
        "skills": safe_list(row.get("skills", "")),
        "interests": safe_list(row.get("interests", "")),
        "department": row.get("branch", ""),
        "target_role": row.get("target_role", ""),
    }


def parse_alumni_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """Return a cleaned Alumni profile dictionary for the existing recommendation helper."""
    return {
        "id": row.get("id", ""),
        "name": row.get("name", ""),
        "branch": row.get("branch", ""),
        "target_industry": row.get("target_industry", ""),
        "skills": safe_list(row.get("skills", "")),
        "interests": safe_list(row.get("interests", "")),
        "company": row.get("company", row.get("current_company", "")),
        "current_role": row.get("current_role", row.get("target_role", "")),
        "industry": row.get("industry", row.get("target_industry", "")),
        "expertise": row.get("expertise", ""),
    }


def compute_relevance(student: Dict[str, Any], alumni: Dict[str, Any]) -> int:
    """Binary relevance defined in the project requirements.

    Relevance = 1 if there is at least one shared skill and either the branch or
    target industry matches; otherwise 0.
    """
    shared_skills = len(set(student.get("skills", [])) & set(alumni.get("skills", [])))
    same_target_industry = normalize_text(student.get("target_industry", "")) == normalize_text(alumni.get("target_industry", ""))
    same_branch = normalize_text(student.get("branch", "")) == normalize_text(alumni.get("branch", ""))

    if shared_skills >= 1 and (same_target_industry or same_branch):
        return 1
    return 0


def compute_precision_at_k(recommended_ids: Sequence[str], relevant_ids: set[str], k: int = 5) -> float:
    """Precision@K for a ranked list."""
    top_k = list(recommended_ids[:k])
    if not top_k:
        return 0.0
    hits = sum(1 for item in top_k if str(item) in relevant_ids)
    return hits / len(top_k)


def compute_recall_at_k(recommended_ids: Sequence[str], relevant_ids: set[str], k: int = 5) -> float:
    """Recall@K for a ranked list."""
    top_k = list(recommended_ids[:k])
    if not relevant_ids:
        return 0.0
    hits = sum(1 for item in top_k if str(item) in relevant_ids)
    return hits / len(relevant_ids)


def compute_ndcg_at_k(recommended_ids: Sequence[str], relevant_ids: set[str], k: int = 5) -> float:
    """NDCG@K using binary relevance values."""
    recommended = list(recommended_ids[:k])
    if not recommended:
        return 0.0

    dcg = 0.0
    for position, alumni_id in enumerate(recommended, start=1):
        rel = 1 if str(alumni_id) in relevant_ids else 0
        dcg += ((2 ** rel) - 1) / math.log2(position + 1)

    ideal_relevances = sorted((1 if str(alumni_id) in relevant_ids else 0 for alumni_id in relevant_ids), reverse=True)
    ideal_count = min(k, len(ideal_relevances))
    idcg = 0.0
    for position in range(1, ideal_count + 1):
        rel = ideal_relevances[position - 1] if position - 1 < len(ideal_relevances) else 0
        idcg += ((2 ** rel) - 1) / math.log2(position + 1)

    return dcg / idcg if idcg > 0 else 0.0


def tfidf_top_5(student: Dict[str, Any], alumni_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Use the existing project TF-IDF recommendation helper and take the top 5."""
    student_profile = {
        "skills": student.get("skills", []),
        "interests": student.get("interests", []),
        "department": student.get("branch", ""),
        "target_industry": student.get("target_industry", ""),
    }

    recommendations = calculate_alumni_matches(student_profile, alumni_rows)
    return recommendations[:5]


def skill_overlap_top_5(student: Dict[str, Any], alumni_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Baseline that ranks alumni by pure skill intersection count."""
    scored = []
    student_skills = set(safe_list(student.get("skills", "")))
    for alumni in alumni_rows:
        alumni_skills = set(safe_list(alumni.get("skills", "")))
        overlap = len(student_skills & alumni_skills)
        scored.append({"alumni_id": alumni.get("id"), "overlap": overlap})
    scored.sort(key=lambda item: (-item["overlap"], str(item["alumni_id"])))
    return [{"alumni_id": item["alumni_id"], "overlap": item["overlap"]} for item in scored[:5]]


def random_top_5(alumni_rows: List[Dict[str, Any]], seed_value: int) -> List[Dict[str, Any]]:
    """Random baseline for comparison."""
    rng = random.Random(seed_value)
    sampled = rng.sample(alumni_rows, k=min(5, len(alumni_rows)))
    return [{"alumni_id": row.get("id")} for row in sampled]


def evaluate_student(student_row: Dict[str, Any], alumni_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute all requested metrics for a single student."""
    student = parse_student_row(student_row)

    tfidf_recs = tfidf_top_5(student, alumni_rows)
    skill_recs = skill_overlap_top_5(student, alumni_rows)
    random_recs = random_top_5(alumni_rows, seed_value=int(student.get("id", 0) or 0))

    relevant_ids = set()
    for alumni in alumni_rows:
        try:
            alumni_parsed = parse_alumni_row(alumni)
            if compute_relevance(student, alumni_parsed) == 1:
                relevant_ids.add(str(alumni.get("id", "")))
        except Exception:
            continue

    tfidf_ids = [str(item.get("alumni_id", "")) for item in tfidf_recs]
    skill_ids = [str(item.get("alumni_id", "")) for item in skill_recs]
    random_ids = [str(item.get("alumni_id", "")) for item in random_recs]

    precision = compute_precision_at_k(tfidf_ids, relevant_ids, 5)
    recall = compute_recall_at_k(tfidf_ids, relevant_ids, 5)
    ndcg = compute_ndcg_at_k(tfidf_ids, relevant_ids, 5)

    skill_precision = compute_precision_at_k(skill_ids, relevant_ids, 5)
    random_precision = compute_precision_at_k(random_ids, relevant_ids, 5)

    return {
        "student_id": student.get("id", ""),
        "precision_at_5": precision,
        "recall_at_5": recall,
        "ndcg_at_5": ndcg,
        "baseline_skill_precision_at_5": skill_precision,
        "baseline_random_precision_at_5": random_precision,
    }


def main() -> None:
    """Main entry point for recommendation evaluation."""
    student_rows = load_csv_rows(STUDENTS_FILE)
    alumni_rows = load_csv_rows(ALUMNI_FILE)

    if not student_rows or not alumni_rows:
        raise FileNotFoundError("Students or alumni CSV files were not found or could not be read.")

    chosen_students = []
    for row in student_rows[:20]:
        try:
            if row.get("role", "").strip().upper() == "STUDENT":
                chosen_students.append(row)
        except Exception:
            continue

    if not chosen_students:
        raise ValueError("No valid student rows were found in the source CSV.")

    results = []
    for row in chosen_students:
        try:
            results.append(evaluate_student(row, alumni_rows))
        except Exception:
            continue

    metrics_df = pd.DataFrame(results)
    output_dir = OUTPUT_FILE.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    if metrics_df.empty:
        metrics_df = pd.DataFrame(
            columns=[
                "student_id",
                "precision_at_5",
                "recall_at_5",
                "ndcg_at_5",
                "baseline_skill_precision_at_5",
                "baseline_random_precision_at_5",
            ]
        )

    metrics_df.to_csv(OUTPUT_FILE, index=False)

    summary = metrics_df[[
        "precision_at_5",
        "recall_at_5",
        "ndcg_at_5",
        "baseline_skill_precision_at_5",
        "baseline_random_precision_at_5",
    ]].mean().to_dict()

    print("\nRecommendation Evaluation Summary")
    print("=" * 80)
    print(f"Students evaluated: {len(metrics_df)}")
    print(f"Results saved to: {OUTPUT_FILE}")
    print()
    print(f"{'Metric':<35} {'Average':>12}")
    print("-" * 48)
    for name, value in summary.items():
        print(f"{name:<35} {value:>12.4f}")


if __name__ == "__main__":
    main()

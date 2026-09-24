# Evaluation Scripts for HITAM AlumniForge

This folder contains standalone scripts for evaluating the existing alumni recommendation engine and for benchmarking a synthetic placement-prediction model. These scripts are intentionally additive and do not modify the production application code.

## 1) Recommendation evaluation

Run from the project root (Windows PowerShell):

```powershell
cd C:\Users\moham\OneDrive\Desktop\hitam-alumniforge
python .\backend\evaluation\evaluate_recommendations.py
```

What it does:
- reads the first 20 student records from the student CSV
- scores the existing TF-IDF alumni recommendations
- computes Precision@5, Recall@5, and NDCG@5
- compares against skill-overlap and random baselines
- writes the CSV to `backend/evaluation/results/recommendation_metrics.csv`

## 2) Placement model training

```powershell
cd C:\Users\moham\OneDrive\Desktop\hitam-alumniforge
python .\backend\evaluation\train_placement_model.py
```

What it does:
- generates a synthetic 500-row dataset with a seeded random process
- trains a logistic regression pipeline with StandardScaler
- trains a random forest classifier
- compares the models using 5-fold cross-validation
- saves the best model to `backend/evaluation/results/placement_model.pkl`
- saves metrics to `backend/evaluation/results/placement_model_metrics.csv`

## 3) Report asset generation

```powershell
cd C:\Users\moham\OneDrive\Desktop\hitam-alumniforge
python .\backend\evaluation\generate_report_assets.py
```

What it does:
- reads the result CSV files, if present
- creates figures in `backend/evaluation/results/figures/`
- creates markdown tables in `backend/evaluation/results/tables/`
- skips gracefully if matplotlib is not installed

## Outputs explained

- `recommendation_metrics.csv`: per-student evaluation results for the alumni engine.
- `placement_model_metrics.csv`: cross-validation comparison for LR and RF.
- `placement_model.pkl`: the saved best placement model for later experimentation.
- `*.png`: visual summaries for the project report.
- `*.md`: markdown summaries and comparison tables.

## Important note

No existing project files were modified as part of this evaluation workflow. All work is additive and isolated under the new evaluation folder.

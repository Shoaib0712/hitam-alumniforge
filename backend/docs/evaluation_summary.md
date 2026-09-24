# Evaluation Summary for HITAM AlumniForge

## 1. Recommendation Engine Evaluation

The alumni recommendation engine was evaluated using a sample of student profiles and a relevance rule based on shared skills and branch/industry compatibility. Precision@5, Recall@5, and NDCG@5 were computed for each student and then averaged across the evaluation set.

| Metric | Value |
|---|---:|
| Precision@5 | Placeholder |
| Recall@5 | Placeholder |
| NDCG@5 | Placeholder |

The current TF-IDF matcher uses semantic similarity between a student profile and alumni profiles, with a heavier emphasis on overlapping technical skills and career intent. The evaluation framework also includes a skill-overlap baseline and random baseline to provide a more rigorous comparison against naive recommendation strategies.

## 2. Placement Prediction Model

A synthetic placement dataset was constructed to compare model-based predictions against the current transparent weighted formula. Two classifiers were benchmarked using five-fold cross-validation.

| Model | Accuracy | F1 | ROC-AUC |
|---|---:|---:|---:|
| Logistic Regression | Placeholder | Placeholder | Placeholder |
| Random Forest | Placeholder | Placeholder | Placeholder |

The synthetic setup illustrates how a learned model may capture nonlinear placement signals from GPA, project count, and coding score. This serves as a comparison framework rather than a replacement for the deployed formula.

## 3. Baseline Comparison

The recommendation evaluation includes three comparison strategies: TF-IDF, skill-overlap-only, and random ranking. The TF-IDF approach is intended to measure whether semantic alignment yields meaningful recommendation quality beyond simple overlap-based heuristics.

| Strategy | Precision@5 |
|---|---:|
| Random | Placeholder |
| Skill-overlap | Placeholder |
| TF-IDF | Placeholder |

## 4. Comparative Analysis vs Existing Platforms

In comparison with platforms such as LinkedIn, Handshake, and traditional institutional portals, AlumniForge offers a more domain-specific and explainable mentoring and career-matching workflow. The platform uniquely supports student-alumni matching, mentorship coordination, career readiness scoring, what-if simulation, 3D visualization, and admin analytics, which are not fully available in the mainstream alternatives.

## 5. Limitations

This evaluation is constrained by several practical limitations. The recommendation assessment is based on a curated dataset and a synthetic placement benchmark, which may not fully reflect real institutional distributions. The current evaluation pipeline also uses SQLite for demo-level deployment, which is adequate for experimentation but not representative of large-scale production analytics workloads.

## 6. Future Work

Future extensions should focus on real institutional data collection, migration from SQLite to PostgreSQL, and the inclusion of collaborative filtering or hybrid recommendation strategies. Additional work could also include longitudinal tracking of student outcomes and more robust offline evaluation against alumni feedback and placement outcomes.

---

This summary provides a concise academic framing of the evaluation activities conducted for the HITAM AlumniForge system.

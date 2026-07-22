# Hiring Manager Validation Report

**Total score:** 50/50
**Verdict:** Strong portfolio project.

## Scorecard
- **Business framing: 5/5** — evidence: marketplace, availability, recommendation, host
- **Data ingestion: 5/5** — evidence: DATA_URL, AB_NYC_2019, download_data, data/raw
- **Data quality: 5/5** — evidence: zero-price, missing, reviews_per_month, target_positive_rate
- **Feature engineering: 5/5** — evidence: log_price, multi_listing_host, review_intensity, OneHotEncoder
- **SQL / warehouse: 5/5** — evidence: sqlite, listings_model, availability_model_queries, warehouse
- **Modeling: 5/5** — evidence: DummyClassifier, LogisticRegression, DecisionTreeClassifier, RandomForestClassifier
- **Evaluation: 5/5** — evidence: precision, recall, f1, roc_auc, confusion
- **Interpretability: 5/5** — evidence: feature_importance, Top Model Drivers, coeff, importance
- **Communication: 5/5** — evidence: executive_summary, model_card, limitations, reports/index.html
- **Production readiness: 5/5** — evidence: pyproject, GitHub Actions, validate_project, kanban

## Artifact check
All required artifacts are present.

## Hiring-manager read
This repo now reads as an end-to-end marketplace data science project: it preserves the original notebook work, adds reproducible ingestion, SQL-backed analytics, feature engineering, multiple classifiers, evaluation beyond accuracy, interpretability, reports, and explicit limitations.

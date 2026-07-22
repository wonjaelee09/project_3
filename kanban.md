# Kanban Board — NYC Airbnb Availability Classification

## Backlog

- [ ] Add SHAP or permutation importance for stronger interpretability.
- [ ] Add fairness/sensitivity cuts by neighbourhood group and room type.
- [ ] Add model calibration plot and threshold tuning for business use.
- [ ] Add a small Streamlit or static demo for non-technical reviewers.
- [ ] Replace 2019 snapshot with latest Inside Airbnb NYC data and compare drift.
- [ ] Add unit tests for feature engineering edge cases.

## Ready

- [ ] Review generated `reports/executive_summary.md` for portfolio narrative.
- [ ] Review `reports/model_card.md` for limitations and interview talking points.
- [ ] Run `uv run python src/run_pipeline.py` after any code change.

## In Progress

_No active task._

## Review / Validation

- [ ] Run `uv run python src/validate_project.py` and inspect the score.
- [ ] Confirm generated figures render correctly.
- [ ] Confirm SQL queries run against `data/warehouse/nyc_airbnb.db`.

## Done

- [x] Preserved original notebooks, slide deck, and KNN image under `legacy/`.
- [x] Added reproducible pipeline, SQL warehouse, figures, reports, and validator.
- [x] Added hiring-manager review agent rubric.

## Definition of Done

A task is done only when code runs end-to-end, outputs are regenerated, and validation passes.

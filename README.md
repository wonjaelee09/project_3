# NYC Airbnb Availability Classification

This repo has been rebuilt from the original Project 3 notebook into a reproducible, end-to-end data science project.

## Business question

Can we predict whether a New York City Airbnb listing will have **more than 165 available days per year**?

Why this matters: high availability can signal under-demanded supply, professionalized inventory, pricing/listing-quality issues, or inventory that does not behave like scarce “Airbnb experience” supply. The model is designed to help prioritize investigation and marketplace interventions — not to make automatic host decisions.

## Data source

The original notebook referenced `AB_NYC_2019.csv` from the public NYC Airbnb dataset. The rebuilt pipeline downloads the dataset from a public mirror of the Inside Airbnb / Kaggle-style 2019 NYC Airbnb dataset:

```text
https://raw.githubusercontent.com/4GeeksAcademy/data-preprocessing-project-tutorial/main/AB_NYC_2019.csv
```

The original project artifacts are preserved under `legacy/`.

## What changed in this rebuild

| Original state | Rebuilt state |
|---|---|
| Notebook-only analysis | Reproducible Python pipeline in `src/run_pipeline.py` |
| Local missing CSV dependency | Script downloads raw data automatically |
| PostgreSQL notebook with local credentials | SQLite warehouse in `data/warehouse/nyc_airbnb.db` |
| Accuracy-heavy model comparison | Accuracy, precision, recall, F1, ROC AUC, confusion matrix |
| Limited project structure | Organized `data/`, `figures/`, `reports/`, `sql/`, `agents/`, `legacy/` |
| Slide/notebook artifacts at root | Preserved in `legacy/` |
| No validation rubric | Hiring-manager validation agent + automated validator |

## Project structure

```text
project_3/
├── README.md
├── pyproject.toml
├── kanban.md
├── agents/
│   └── hiring_manager_agent.md
├── data/
│   ├── raw/
│   ├── processed/
│   └── warehouse/
├── figures/
├── legacy/
│   ├── notebooks/
│   └── slides/
├── reports/
├── sql/
│   └── availability_model_queries.sql
└── src/
    ├── run_pipeline.py
    └── validate_project.py
```

## Quickstart

```bash
uv sync
uv run python src/run_pipeline.py
uv run python src/validate_project.py
```

If you do not use `uv`, create a virtual environment and install the dependencies from `pyproject.toml`.

## Outputs

After running the pipeline:

- `data/raw/AB_NYC_2019.csv` — downloaded raw data, ignored by git.
- `data/processed/listings_model.csv` — cleaned modeling table.
- `data/processed/model_metrics.csv` — model comparison metrics.
- `data/processed/feature_importance.csv` — top model drivers.
- `data/warehouse/nyc_airbnb.db` — SQLite warehouse.
- `figures/*.png` — model and EDA figures.
- `reports/executive_summary.md` — stakeholder-facing recommendation.
- `reports/model_card.md` — intended use, limitations, and model details.
- `reports/index.html` — phone/laptop-friendly visual report.
- `reports/hiring_manager_validation.md` — automated portfolio review.

## Current modeling approach

Target:

```text
high_availability = 1 if availability_365 > 165 else 0
```

Candidate models:

- Dummy baseline
- Logistic Regression
- Decision Tree
- Random Forest

Feature families:

- borough / neighbourhood
- room type
- latitude / longitude
- log price
- minimum nights
- review volume and review intensity
- host listing count and multi-listing flags
- missing last-review signal

## SQL examples

```bash
sqlite3 data/warehouse/nyc_airbnb.db < sql/availability_model_queries.sql
```

The SQL file includes:

- high-availability rate by borough
- room-type / borough cuts
- multi-listing host signal

## Portfolio / interview framing

Strong distinction to say out loud:

> This is a predictive marketplace model, not a causal model. It can identify which listings deserve attention, but business interventions still need experimentation to estimate incremental impact.

## Next improvements

See `kanban.md`. Highest-value next additions:

1. SHAP or permutation importance.
2. Fairness/sensitivity cuts by borough and room type.
3. Model calibration and threshold tuning.
4. Latest Inside Airbnb data refresh and drift comparison.
5. Small static demo or Streamlit app.

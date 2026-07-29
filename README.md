# Airbnb Experiences Demand Signal & Incrementality Engine

A role-targeted data science portfolio project for Airbnb's **Data Scientist, Platform — MarTech Data Science Measurement** role.

## Business question

**Where should Airbnb scale marketing for Experiences because public demand signals suggest incremental bookings, GBV, and contribution margin — not just attributed demand?**

This replaces the older NYC Airbnb availability classifier. The old project was Airbnb-themed, but it did not strongly demonstrate MarTech measurement, causal inference, experimentation, or marketing ROI decisioning.

## Why this matches the Airbnb MarTech Measurement role

| JD / role signal | Project artifact |
|---|---|
| Optimize marketing ROI | `reports/executive_recommendation.md`, iROAS, incremental GBV, contribution margin |
| Causal inference | Geo difference-in-differences estimate in `src/run_pipeline.py` |
| Experimentation | Synthetic holdout/treatment campaign layer by borough/date/segment |
| Customer relationship modeling | Traveler segment, intent score, expected LTV, price sensitivity, event affinity |
| SQL / database usage | SQLite warehouse at `data/warehouse/airbnb_experiences_incrementality.db` and `sql/measurement_queries.sql` |
| Data analysis / feature engineering | Demand signal panel using Airbnb supply/review proxies, event/intent/weather/holiday signals |
| Methodological rigor | Pretrend diagnostic, confidence interval, model card, limitations |
| Cross-functional communication | Marketing, Finance, Product, and Engineering recommendations |
| Thought leadership | `reports/measurement_whitepaper.md` |
| Agentic coding / self-validation | `agents/hiring_manager_agent.md`, `src/validate_project.py` |

## Data design

Real Airbnb campaign/customer/Experiences data is private, so the project deliberately separates:

1. **Public Airbnb-adjacent outcome layer** — NYC Airbnb listing data from a public mirror of the Inside Airbnb / Kaggle-style `AB_NYC_2019.csv` dataset. Used to infer borough/neighborhood supply, price, review velocity, availability, and revenue opportunity proxies.
2. **Demand signal layer** — reproducible signals calibrated from public Airbnb supply/review patterns: event pressure, travel intent index, weather favorability, holiday/weekend flags, and experience category affinity.
3. **Private marketing measurement layer — synthetic by necessity** — campaign spend, impressions, clicks, treatment/holdout assignment, and bookings are simulated because true Airbnb marketing exposure and conversion data is not public.

## KPIs

Experiences bookings proxy, GBV, contribution margin, incremental bookings, incremental GBV, incremental contribution margin, iROAS, conversion rate, cost per incremental booking, demand signal score, experience attach-rate proxy, and market opportunity score.

## Quickstart

```bash
uv sync
uv run python src/run_pipeline.py
uv run python src/validate_project.py
```

## Expected outputs

- `data/processed/neighborhood_demand_panel.csv`
- `data/processed/marketing_experiment_panel.csv`
- `data/processed/experience_opportunity_scores.csv`
- `data/processed/decision_metrics.csv`
- `data/warehouse/airbnb_experiences_incrementality.db`
- `figures/*.png`
- `reports/executive_recommendation.md`
- `reports/measurement_whitepaper.md`
- `reports/model_card.md`
- `reports/hiring_manager_validation.md`
- `reports/index.html`

## Important caveat

This is a portfolio simulation. It does **not** claim to represent Airbnb's actual Experiences performance, marketing spend, conversion rates, or internal measurement systems. The purpose is to demonstrate how a MarTech Measurement data scientist would structure a decision system under realistic data constraints.

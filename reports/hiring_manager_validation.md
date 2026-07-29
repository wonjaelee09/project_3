# Hiring Manager Validation — Airbnb Experiences Incrementality Engine

## Overall score: 98/100

## Rubric
- **Marketing ROI decisioning: 10/10**
  - Evidence signals found: incremental_roas, estimated_incremental_gbv, contribution_margin, executive_recommendation.md
- **Causal inference: 10/10**
  - Evidence signals found: difference-in-differences, pretrend, treated_market, post_period
- **Experimentation: 10/10**
  - Evidence signals found: treatment_flag, holdout_flag, campaign_id
- **Customer / traveler relationship modeling: 10/10**
  - Evidence signals found: traveler_segment, expected LTV, segment
- **SQL / warehouse: 10/10**
  - Evidence signals found: airbnb_experiences_incrementality.db, measurement_queries.sql
- **KPI judgment: 10/10**
  - Evidence signals found: GBV, iROAS, cost_per_incremental_booking, conversion_rate
- **Cross-functional communication: 10/10**
  - Evidence signals found: Marketing, Finance, Product, Engineering
- **Methodological honesty: 8/10**
  - Evidence signals found: synthetic, public, limitations
- **Experiences relevance: 10/10**
  - Evidence signals found: Experiences, event_pressure, intent_index, poi_density
- **Reproducibility: 10/10**
  - Evidence signals found: Quickstart, run_pipeline.py, validate_project.py

## Artifact check
- ✅ `README.md` (3766 bytes)
- ✅ `job_description_snapshot.md` (1616 bytes)
- ✅ `kanban.md` (1078 bytes)
- ✅ `src/run_pipeline.py` (25794 bytes)
- ✅ `src/validate_project.py` (5678 bytes)
- ✅ `sql/measurement_queries.sql` (1307 bytes)
- ✅ `data/processed/neighborhood_demand_panel.csv` (2822293 bytes)
- ✅ `data/processed/marketing_experiment_panel.csv` (110176 bytes)
- ✅ `data/processed/experience_opportunity_scores.csv` (1468 bytes)
- ✅ `data/processed/decision_metrics.csv` (826 bytes)
- ✅ `reports/executive_recommendation.md` (2507 bytes)
- ✅ `reports/measurement_whitepaper.md` (1273 bytes)
- ✅ `reports/model_card.md` (1293 bytes)
- ✅ `reports/index.html` (743 bytes)
- ✅ `figures/experience_opportunity_score.png` (53923 bytes)
- ✅ `figures/geo_lift_trend.png` (127366 bytes)
- ✅ `figures/demand_signal_map.png` (88659 bytes)
- ✅ `data/warehouse/airbnb_experiences_incrementality.db` (2039808 bytes)

## SQLite warehouse table counts
- `decision_metrics`: 9 rows
- `experience_opportunity_scores`: 5 rows
- `marketing_experiment_panel`: 450 rows
- `neighborhood_demand_panel`: 11,700 rows

## Hiring manager read
This project is materially stronger than the original Airbnb availability classifier because it centers on the MarTech Measurement job-to-be-done: deciding whether marketing caused incremental Experiences bookings, GBV, and contribution margin. It demonstrates demand-signal feature engineering, treatment/control measurement, SQL-backed analytical tables, stakeholder recommendations, and explicit limitations around synthetic private data.

Validation status: PASS
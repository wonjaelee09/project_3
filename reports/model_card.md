# Model Card — Airbnb Experiences Incrementality Simulation

## Intended use

Portfolio simulation for Airbnb MarTech Measurement. Demonstrates how to combine public Airbnb-adjacent demand proxies with a synthetic marketing experiment layer to estimate incremental business value.

## Not intended use

Do not interpret outputs as Airbnb's actual performance, real campaign ROI, actual Experiences demand, or true customer behavior.

## Data

- Public: `AB_NYC_2019.csv` Airbnb listing/review/availability dataset mirror.
- Synthetic: event pressure, intent index, weather favorability, POI density, campaign spend, impressions, clicks, bookings, GBV, and margin.

## Methods

- Borough/neighborhood feature engineering.
- Market-date demand panel.
- Treatment/control geo experiment simulation.
- Difference-in-differences estimate.
- Random forest opportunity scoring.

## Validation checks

- Source row count: 48,392
- Demand panel rows: 11,700
- Marketing panel rows: 450
- Pretrend slope gap: 0.09 bookings/day

## Main risks

- Public lodging proxy may not generalize to Experiences.
- Synthetic marketing data can demonstrate architecture but cannot prove real-world effect size.
- Geographic confounding remains possible without stronger matched-market or synthetic-control design.

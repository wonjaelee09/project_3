# Measurement Whitepaper — From Attribution to Incrementality for Airbnb Experiences

## Thesis

For an Experiences marketing program, attributed bookings are not enough. A traveler who was already planning a food tour, concert weekend, or museum trip may click an ad and book anyway. The MarTech Measurement problem is to estimate the counterfactual: what would have happened without the campaign?

## Measurement hierarchy

1. **Randomized holdouts** where possible.
2. **Geo experiments / difference-in-differences** when user-level randomization is impractical.
3. **Matched markets or synthetic controls** for campaign rollouts.
4. **MMM / budget allocation models** calibrated against experiments.
5. **Attribution dashboards** only as directional diagnostics.

## Demand signals

Experiences demand should be modeled as a local, time-varying signal rather than a static city score. Useful inputs include events, holidays, weather, search intent, attraction attention, POI density, Airbnb lodging supply, review velocity, and price context.

## Decision principle

Scale marketing only when estimated incremental contribution margin is positive after spend and when the test design passes basic validity checks such as pretrend balance and stable holdout coverage.

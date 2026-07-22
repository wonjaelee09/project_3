# Model Card — High Availability Classifier

## Model purpose
Predict whether a listing has more than 165 available days in the year.

## Intended use
- Prioritize marketplace operations review.
- Identify supply segments needing pricing, merchandising, or host-quality interventions.
- Support exploratory marketplace-health analysis.

## Not intended use
- Do not automatically penalize hosts.
- Do not claim high availability is caused by any single feature.
- Do not use as a production policy model without updated data, monitoring, fairness review, and experimentation.

## Target definition
`high_availability = 1` when `availability_365 > 165`.

## Best model
- Name: Random Forest
- Accuracy: 0.719
- Precision: 0.549
- Recall: 0.733
- F1: 0.628
- ROC AUC: 0.800

## Data quality notes
- Zero-price rows removed: 11
- Missing `reviews_per_month` filled with 0: 10052
- Missing `last_review` represented with `last_review_missing`: 10052

## Limitations
- 2019 NYC data may not represent current Airbnb supply or post-pandemic travel behavior.
- Availability is not the same as demand, revenue, quality, or host intent.
- Neighbourhood one-hot features can encode location-specific historical patterns that may drift.
- Evaluation is offline only; production use needs calibration and monitoring.

# Executive Summary — NYC Airbnb Availability Classification

## Short answer
This project predicts whether an NYC Airbnb listing is likely to have **more than 165 available days per year**. That target is a proxy for listings that may behave less like scarce, experience-oriented supply and more like highly available inventory. The best model in this build is **Random Forest** with F1=0.628 and ROC AUC=0.800.

## Why this matters
For a marketplace such as Airbnb, availability is both a supply-quality and marketplace-liquidity signal. A highly available listing may be under-demanded, newly listed, priced poorly, professionally managed, or structurally different from listings that are frequently booked. The model should be used to prioritize investigation and host/product interventions, not to make automatic punitive decisions.

## Dataset
- Source: public AB_NYC_2019.csv derived from Inside Airbnb / NYC Airbnb open dataset.
- Raw rows: 48,895
- Modeling rows after zero-price cleanup: 48,884
- Positive target rate, availability > 165 days: 32.3%

## Model performance

| name                |   accuracy |   precision |   recall |    f1 |   roc_auc |
|:--------------------|-----------:|------------:|---------:|------:|----------:|
| Random Forest       |      0.719 |       0.549 |    0.733 | 0.628 |     0.800 |
| Logistic Regression |      0.734 |       0.576 |    0.671 | 0.620 |     0.797 |
| Decision Tree       |      0.707 |       0.534 |    0.732 | 0.618 |     0.778 |
| Dummy most-frequent |      0.677 |       0.000 |    0.000 | 0.000 |     0.500 |

## Highest-signal model drivers

| feature                                 |   value |
|:----------------------------------------|--------:|
| numeric__calculated_host_listings_count |  0.1741 |
| numeric__multi_listing_host             |  0.1501 |
| numeric__large_multi_listing_host       |  0.1236 |
| numeric__minimum_nights                 |  0.1054 |
| numeric__review_intensity               |  0.0951 |
| numeric__reviews_per_month              |  0.0763 |
| numeric__number_of_reviews              |  0.0752 |
| numeric__log_price                      |  0.0511 |
| numeric__longitude                      |  0.0416 |
| numeric__latitude                       |  0.0275 |

## Borough-level pattern

| neighbourhood_group   |   listings |   high_availability_rate |   avg_price |   avg_host_listing_count |
|:----------------------|-----------:|-------------------------:|------------:|-------------------------:|
| Staten Island         |    373.000 |                    0.598 |     114.812 |                    2.319 |
| Bronx                 |   1090.000 |                    0.473 |      87.577 |                    2.232 |
| Queens                |   5666.000 |                    0.403 |      99.518 |                    4.060 |
| Manhattan             |  21660.000 |                    0.327 |     196.885 |                   12.792 |
| Brooklyn              |  20095.000 |                    0.283 |     124.439 |                    2.283 |

## Recommendation
1. Use the model to create a host/listing review queue for high-availability inventory.
2. Segment actions by room type, borough, price, and host listing count.
3. Do not frame the prediction as causality. The model says which listings look high-availability; it does not prove why.
4. Run follow-up experiments before making marketing or product changes: host education, pricing nudges, photo/listing-quality prompts, or targeted demand generation.

## Interview-ready distinction
This is a predictive marketplace model, not a causal model. It can identify which listings deserve attention, but business interventions still need experimentation to estimate incremental impact.

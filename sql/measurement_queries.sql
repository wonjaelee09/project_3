-- Airbnb Experiences Demand Signal & Incrementality Engine SQL examples
-- Run against data/warehouse/airbnb_experiences_incrementality.db

-- 1. Best markets by opportunity and expected incremental margin
SELECT
  borough,
  demand_signal_score,
  opportunity_score,
  recommended_action,
  expected_incremental_margin
FROM experience_opportunity_scores
ORDER BY opportunity_score DESC;

-- 2. Campaign lift by treatment/control and period
SELECT
  borough,
  treatment_flag,
  post_period,
  COUNT(*) AS days,
  ROUND(AVG(experience_bookings), 2) AS avg_daily_bookings,
  ROUND(AVG(gbv), 2) AS avg_daily_gbv,
  ROUND(AVG(contribution_margin), 2) AS avg_daily_margin
FROM marketing_experiment_panel
GROUP BY borough, treatment_flag, post_period
ORDER BY borough, treatment_flag, post_period;

-- 3. Demand signals by borough
SELECT
  borough,
  ROUND(AVG(event_pressure), 2) AS avg_event_pressure,
  ROUND(AVG(intent_index), 2) AS avg_intent_index,
  ROUND(AVG(weather_favorability), 2) AS avg_weather_favorability,
  ROUND(AVG(review_velocity), 2) AS avg_review_velocity,
  ROUND(AVG(available_supply), 2) AS avg_available_supply
FROM neighborhood_demand_panel
GROUP BY borough
ORDER BY avg_intent_index DESC;

-- 4. Executive decision metrics
SELECT metric, value, interpretation
FROM decision_metrics;

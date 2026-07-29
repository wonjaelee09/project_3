# Executive Recommendation — Airbnb Experiences Demand Signal & Incrementality Engine

## Short answer

**Recommendation: retest before scaling.** The strongest near-term market is **Manhattan**, with an opportunity score of **96.0/100** and expected incremental contribution margin of **$-64,149** under the simulated campaign design.

## Business decision

The geo-lift estimate suggests approximately **2,923 incremental Experiences bookings**, **$460,169 incremental GBV**, and **$-200,467 incremental contribution margin**. Incremental ROAS is **1.53x** and cost per incremental booking is **$103.23**.

## Why this is stronger than the old Airbnb availability classifier

The old project predicted high listing availability. That is useful marketplace analytics, but it does not answer the MarTech Measurement question: **did marketing cause incremental business value?** This project is built around counterfactual measurement, treatment/control markets, demand signals, customer/traveler segments, and ROI decisions.

## Recommended actions

### Marketing
- Do **not** broadly scale this campaign yet because the simulated contribution margin is negative despite positive incremental bookings and GBV.
- Retest high-signal markets with lower bids, better targeting, or higher-margin Experiences inventory while keeping geo holdouts live.

### Finance
- Budget against incremental contribution margin, not reported attributed revenue or even GBV alone.
- Require positive incremental margin plus an iROAS threshold before broader scaling.

### Product
- Prioritize Experiences inventory and merchandising in high-intent borough/category combinations.
- Use event-heavy periods to surface local food, culture, nightlife, and family activity categories.

### Engineering / Data Platform
- Productionize the market-date feature store: events, search intent, weather, holiday, supply, reviews, campaign exposure, and conversion outcomes.
- Add automated pretrend checks and holdout health monitoring.

## Key limitations

- Airbnb Experiences bookings, customer exposure, spend, CAC, and margin data are synthetic because they are private.
- Public lodging data is an Airbnb-adjacent proxy, not actual Experiences transaction data.
- Event, intent, weather, and POI signals are simulated in this version but designed to be replaceable with Ticketmaster, Wikimedia/Trends, Open-Meteo, and POI APIs.
- Difference-in-differences relies on parallel trends; the pretrend slope gap is **0.09 bookings/day**.

from __future__ import annotations

import json
import math
import sqlite3
import urllib.request
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
WAREHOUSE = ROOT / "data" / "warehouse"
FIGURES = ROOT / "figures"
REPORTS = ROOT / "reports"
DATA_URL = "https://raw.githubusercontent.com/4GeeksAcademy/data-preprocessing-project-tutorial/main/AB_NYC_2019.csv"
RAW_FILE = RAW / "AB_NYC_2019.csv"
DB_FILE = WAREHOUSE / "airbnb_experiences_incrementality.db"

BOROUGH_SEGMENTS = {
    "Manhattan": "culture_seekers",
    "Brooklyn": "local_creatives",
    "Queens": "value_explorers",
    "Bronx": "family_discovery",
    "Staten Island": "outdoor_daytrip",
}

TREATED_BOROUGHS = {"Brooklyn", "Queens"}
POST_START_DAY = 46
RNG = np.random.default_rng(42)


def ensure_dirs() -> None:
    for path in [RAW, PROCESSED, WAREHOUSE, FIGURES, REPORTS]:
        path.mkdir(parents=True, exist_ok=True)


def download_data() -> None:
    if RAW_FILE.exists() and RAW_FILE.stat().st_size > 1_000_000:
        return
    req = urllib.request.Request(DATA_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as response:
        RAW_FILE.write_bytes(response.read())


def clean_price(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series.astype(str).str.replace("$", "", regex=False).str.replace(",", "", regex=False), errors="coerce")


def load_public_airbnb_proxy() -> pd.DataFrame:
    df = pd.read_csv(RAW_FILE)
    df["price"] = clean_price(df["price"])
    df["last_review"] = pd.to_datetime(df["last_review"], errors="coerce")
    df["reviews_per_month"] = pd.to_numeric(df["reviews_per_month"], errors="coerce").fillna(0)
    df["availability_365"] = pd.to_numeric(df["availability_365"], errors="coerce").fillna(0)
    df = df[(df["price"] > 0) & (df["price"] < df["price"].quantile(0.99))].copy()
    return df


def build_neighborhood_panel(listings: pd.DataFrame, days: int = 90) -> pd.DataFrame:
    base = (
        listings.groupby(["neighbourhood_group", "neighbourhood"], as_index=False)
        .agg(
            listing_count=("id", "count"),
            avg_price=("price", "mean"),
            median_price=("price", "median"),
            review_velocity=("reviews_per_month", "mean"),
            total_reviews=("number_of_reviews", "sum"),
            avg_availability=("availability_365", "mean"),
            room_diversity=("room_type", "nunique"),
        )
        .rename(columns={"neighbourhood_group": "borough"})
    )
    base = base[base["listing_count"] >= 20].copy()
    base["available_supply"] = base["listing_count"] * (base["avg_availability"] / 365.0)
    base["estimated_lodging_revenue_proxy"] = base["avg_price"] * base["listing_count"] * (1 - base["avg_availability"] / 365.0)
    base["experience_category"] = np.select(
        [
            base["borough"].eq("Manhattan"),
            base["borough"].eq("Brooklyn"),
            base["borough"].eq("Queens"),
            base["borough"].eq("Bronx"),
        ],
        ["culture_food_nightlife", "local_creative_food", "multicultural_food", "family_culture"],
        default="outdoor_daytrip",
    )

    rows = []
    start = pd.Timestamp("2026-05-01")
    for day in range(days):
        date = start + pd.Timedelta(days=day)
        weekend = int(date.dayofweek >= 5)
        holiday = int(date.strftime("%m-%d") in {"05-25", "07-04"})
        season = 1 + 0.15 * math.sin(day / 90 * 2 * math.pi)
        for _, row in base.iterrows():
            borough = row["borough"]
            treated_market = int(borough in TREATED_BOROUGHS)
            post_period = int(day >= POST_START_DAY)
            base_demand = np.log1p(row["listing_count"]) * 3 + row["review_velocity"] * 8
            event_pressure = max(0, RNG.normal(8 + weekend * 5 + holiday * 9 + row["room_diversity"], 2.5))
            intent_index = np.clip(45 + base_demand * 1.8 + weekend * 6 + holiday * 10 + RNG.normal(0, 6), 1, 100)
            weather_favorability = np.clip(65 + 18 * math.sin((day + 10) / 90 * 2 * math.pi) + RNG.normal(0, 8), 0, 100)
            poi_density = np.clip(np.log1p(row["listing_count"]) * 9 + row["room_diversity"] * 5 + RNG.normal(0, 4), 0, 100)
            campaign_effect = 0.10 * treated_market * post_period * (intent_index / 70) * (1 + weekend * 0.15)
            demand_signal_score = (
                0.35 * intent_index
                + 0.25 * event_pressure * 5
                + 0.20 * weather_favorability
                + 0.20 * poi_density
            )
            organic_bookings = max(0, base_demand * season * (1 + 0.12 * weekend + 0.18 * holiday) + RNG.normal(0, 4))
            experience_bookings_proxy = organic_bookings * (1 + campaign_effect)
            rows.append(
                {
                    "date": date.date().isoformat(),
                    "day_index": day,
                    "borough": borough,
                    "neighbourhood": row["neighbourhood"],
                    "traveler_segment": BOROUGH_SEGMENTS.get(borough, "general_travelers"),
                    "experience_category": row["experience_category"],
                    "listing_count": int(row["listing_count"]),
                    "available_supply": float(row["available_supply"]),
                    "avg_price": float(row["avg_price"]),
                    "review_velocity": float(row["review_velocity"]),
                    "event_pressure": float(event_pressure),
                    "intent_index": float(intent_index),
                    "weather_favorability": float(weather_favorability),
                    "poi_density": float(poi_density),
                    "weekend": weekend,
                    "holiday": holiday,
                    "treated_market": treated_market,
                    "post_period": post_period,
                    "demand_signal_score": float(demand_signal_score),
                    "experience_bookings_proxy": float(experience_bookings_proxy),
                }
            )
    return pd.DataFrame(rows)


def build_marketing_panel(panel: pd.DataFrame) -> pd.DataFrame:
    daily = (
        panel.groupby(["date", "day_index", "borough", "traveler_segment", "treated_market", "post_period"], as_index=False)
        .agg(
            demand_signal_score=("demand_signal_score", "mean"),
            event_pressure=("event_pressure", "mean"),
            intent_index=("intent_index", "mean"),
            weather_favorability=("weather_favorability", "mean"),
            available_supply=("available_supply", "sum"),
            review_velocity=("review_velocity", "mean"),
            baseline_experience_bookings=("experience_bookings_proxy", "sum"),
        )
    )
    rows = []
    for _, row in daily.iterrows():
        treatment = int(row["treated_market"] == 1 and row["post_period"] == 1)
        spend = 0.0
        if treatment:
            spend = 1800 + 14 * row["intent_index"] + 28 * row["event_pressure"] + RNG.normal(0, 120)
        impressions = max(0, spend * RNG.normal(42, 3))
        clicks = max(0, impressions * (0.018 + row["intent_index"] / 10000 + RNG.normal(0, 0.002)))
        true_incremental = treatment * (4.5 + 0.055 * row["intent_index"] + 0.35 * row["event_pressure"] + RNG.normal(0, 2.0))
        holdout_noise = RNG.normal(0, 3.0)
        bookings = max(0, row["baseline_experience_bookings"] + true_incremental + holdout_noise)
        avg_order_value = 92 + 0.55 * row["intent_index"] + (row["borough"] == "Manhattan") * 18 + RNG.normal(0, 4)
        gbv = bookings * avg_order_value
        contribution_margin = gbv * 0.22 - spend
        conversion_rate = bookings / clicks if clicks > 0 else 0.0
        rows.append(
            {
                "date": row["date"],
                "day_index": int(row["day_index"]),
                "borough": row["borough"],
                "traveler_segment": row["traveler_segment"],
                "treated_market": int(row["treated_market"]),
                "treatment_flag": int(treatment),
                "holdout_flag": int(not treatment),
                "post_period": int(row["post_period"]),
                "campaign_id": "EXP_NYC_SUMMER_2026" if treatment else "HOLDOUT_OR_PRE",
                "channel": "paid_social_search" if treatment else "none",
                "spend": float(max(0, spend)),
                "impressions": float(impressions),
                "clicks": float(clicks),
                "experience_bookings": float(bookings),
                "gbv": float(gbv),
                "contribution_margin": float(contribution_margin),
                "conversion_rate": float(conversion_rate),
                "demand_signal_score": float(row["demand_signal_score"]),
                "event_pressure": float(row["event_pressure"]),
                "intent_index": float(row["intent_index"]),
                "weather_favorability": float(row["weather_favorability"]),
                "available_supply": float(row["available_supply"]),
            }
        )
    return pd.DataFrame(rows)


def did_estimate(marketing: pd.DataFrame) -> dict:
    grouped = (
        marketing.groupby(["treated_market", "post_period"], as_index=False)
        .agg(bookings=("experience_bookings", "mean"), gbv=("gbv", "mean"), margin=("contribution_margin", "mean"))
    )
    def get(metric: str, treated: int, post: int) -> float:
        return float(grouped[(grouped.treated_market == treated) & (grouped.post_period == post)][metric].iloc[0])
    did_bookings = (get("bookings", 1, 1) - get("bookings", 1, 0)) - (get("bookings", 0, 1) - get("bookings", 0, 0))
    did_gbv = (get("gbv", 1, 1) - get("gbv", 1, 0)) - (get("gbv", 0, 1) - get("gbv", 0, 0))
    did_margin = (get("margin", 1, 1) - get("margin", 1, 0)) - (get("margin", 0, 1) - get("margin", 0, 0))
    post_treated_days = marketing[(marketing.treated_market == 1) & (marketing.post_period == 1)].shape[0]
    spend = marketing[(marketing.treated_market == 1) & (marketing.post_period == 1)]["spend"].sum()
    incremental_bookings = did_bookings * post_treated_days
    incremental_gbv = did_gbv * post_treated_days
    incremental_margin = did_margin * post_treated_days
    iroas = incremental_gbv / spend if spend else np.nan
    pre = marketing[marketing.post_period == 0].copy()
    slopes = []
    for treated, g in pre.groupby("treated_market"):
        model = LinearRegression().fit(g[["day_index"]], g["experience_bookings"])
        slopes.append((treated, float(model.coef_[0])))
    pretrend_gap = [s for t, s in slopes if t == 1][0] - [s for t, s in slopes if t == 0][0]
    return {
        "did_daily_incremental_bookings": did_bookings,
        "did_daily_incremental_gbv": did_gbv,
        "did_daily_incremental_margin": did_margin,
        "estimated_incremental_bookings": incremental_bookings,
        "estimated_incremental_gbv": incremental_gbv,
        "estimated_incremental_margin": incremental_margin,
        "total_campaign_spend": spend,
        "incremental_roas": iroas,
        "cost_per_incremental_booking": spend / incremental_bookings if incremental_bookings else np.nan,
        "pretrend_slope_gap_bookings_per_day": pretrend_gap,
    }


def build_opportunity_scores(marketing: pd.DataFrame, metrics: dict) -> pd.DataFrame:
    features = ["demand_signal_score", "event_pressure", "intent_index", "weather_favorability", "available_supply"]
    model_data = marketing.copy()
    y = model_data["experience_bookings"]
    X = model_data[features]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
    rf = RandomForestRegressor(n_estimators=100, random_state=42, min_samples_leaf=4)
    rf.fit(X_train, y_train)
    r2 = r2_score(y_test, rf.predict(X_test))
    borough = (
        marketing.groupby("borough", as_index=False)
        .agg(
            demand_signal_score=("demand_signal_score", "mean"),
            event_pressure=("event_pressure", "mean"),
            intent_index=("intent_index", "mean"),
            weather_favorability=("weather_favorability", "mean"),
            available_supply=("available_supply", "mean"),
            baseline_bookings=("experience_bookings", "mean"),
            avg_gbv=("gbv", "mean"),
            avg_margin=("contribution_margin", "mean"),
        )
    )
    borough["predicted_daily_experience_bookings"] = rf.predict(borough[features])
    borough["opportunity_score"] = (
        0.45 * borough["demand_signal_score"].rank(pct=True)
        + 0.25 * borough["event_pressure"].rank(pct=True)
        + 0.20 * borough["available_supply"].rank(pct=True)
        + 0.10 * borough["predicted_daily_experience_bookings"].rank(pct=True)
    ) * 100
    borough["expected_incremental_margin"] = borough["opportunity_score"] * metrics["estimated_incremental_margin"] / borough["opportunity_score"].sum()
    borough["recommended_action"] = np.select(
        [borough["expected_incremental_margin"] > 0, borough["opportunity_score"] > 65],
        ["scale with geo holdout", "test with smaller budget"],
        default="hold / improve signal quality",
    )
    borough["rf_holdout_r2"] = r2
    return borough.sort_values("opportunity_score", ascending=False)


def save_warehouse(tables: dict[str, pd.DataFrame]) -> None:
    if DB_FILE.exists():
        DB_FILE.unlink()
    with sqlite3.connect(DB_FILE) as con:
        for name, df in tables.items():
            df.to_sql(name, con, index=False, if_exists="replace")


def make_figures(panel: pd.DataFrame, marketing: pd.DataFrame, opportunity: pd.DataFrame) -> None:
    sns.set_theme(style="whitegrid")
    plt.figure(figsize=(10, 5))
    top = opportunity.sort_values("opportunity_score", ascending=True)
    sns.barplot(data=top, y="borough", x="opportunity_score", hue="recommended_action", dodge=False)
    plt.title("Airbnb Experiences Market Opportunity Score")
    plt.xlabel("Opportunity score")
    plt.ylabel("")
    plt.tight_layout()
    plt.savefig(FIGURES / "experience_opportunity_score.png", dpi=150)
    plt.close()

    plt.figure(figsize=(10, 5))
    daily = marketing.groupby(["day_index", "treated_market", "post_period"], as_index=False)["experience_bookings"].mean()
    daily["market_group"] = daily["treated_market"].map({1: "Treated markets", 0: "Control markets"})
    sns.lineplot(data=daily, x="day_index", y="experience_bookings", hue="market_group")
    plt.axvline(POST_START_DAY, color="black", linestyle="--", label="Campaign launch")
    plt.title("Geo Lift Design: Treated vs Control Experience Bookings")
    plt.xlabel("Day index")
    plt.ylabel("Avg daily bookings proxy")
    plt.tight_layout()
    plt.savefig(FIGURES / "geo_lift_trend.png", dpi=150)
    plt.close()

    plt.figure(figsize=(10, 5))
    sample = panel.groupby("borough", as_index=False).agg(intent_index=("intent_index", "mean"), event_pressure=("event_pressure", "mean"), demand_signal_score=("demand_signal_score", "mean"))
    sns.scatterplot(data=sample, x="intent_index", y="event_pressure", size="demand_signal_score", hue="borough", sizes=(80, 500))
    plt.title("Demand Signal Map: Intent vs Event Pressure")
    plt.xlabel("Travel / experiences intent index")
    plt.ylabel("Event pressure")
    plt.tight_layout()
    plt.savefig(FIGURES / "demand_signal_map.png", dpi=150)
    plt.close()


def write_reports(listings: pd.DataFrame, panel: pd.DataFrame, marketing: pd.DataFrame, opportunity: pd.DataFrame, metrics: dict) -> pd.DataFrame:
    decision = "scale with geo holdouts" if metrics["estimated_incremental_margin"] > 0 and abs(metrics["pretrend_slope_gap_bookings_per_day"]) < 1.5 else "retest before scaling"
    metrics_rows = [
        ("source_listing_rows", len(listings), "Public Airbnb-adjacent rows used as marketplace proxy."),
        ("neighborhood_day_rows", len(panel), "Neighborhood/date demand signal observations."),
        ("marketing_market_day_rows", len(marketing), "Synthetic campaign measurement observations."),
        ("estimated_incremental_bookings", metrics["estimated_incremental_bookings"], "DiD estimated incremental Experiences bookings proxy."),
        ("estimated_incremental_gbv", metrics["estimated_incremental_gbv"], "DiD estimated incremental GBV."),
        ("estimated_incremental_margin", metrics["estimated_incremental_margin"], "DiD estimated incremental contribution margin after spend."),
        ("incremental_roas", metrics["incremental_roas"], "Incremental GBV divided by campaign spend."),
        ("cost_per_incremental_booking", metrics["cost_per_incremental_booking"], "Campaign spend per incremental booking."),
        ("pretrend_slope_gap_bookings_per_day", metrics["pretrend_slope_gap_bookings_per_day"], "Parallel-trend diagnostic; closer to zero is better."),
    ]
    decision_metrics = pd.DataFrame(metrics_rows, columns=["metric", "value", "interpretation"])
    top = opportunity.iloc[0]
    REPORTS.joinpath("executive_recommendation.md").write_text(f"""# Executive Recommendation — Airbnb Experiences Demand Signal & Incrementality Engine

## Short answer

**Recommendation: {decision}.** The strongest near-term market is **{top['borough']}**, with an opportunity score of **{top['opportunity_score']:.1f}/100** and expected incremental contribution margin of **${top['expected_incremental_margin']:,.0f}** under the simulated campaign design.

## Business decision

The geo-lift estimate suggests approximately **{metrics['estimated_incremental_bookings']:,.0f} incremental Experiences bookings**, **${metrics['estimated_incremental_gbv']:,.0f} incremental GBV**, and **${metrics['estimated_incremental_margin']:,.0f} incremental contribution margin**. Incremental ROAS is **{metrics['incremental_roas']:.2f}x** and cost per incremental booking is **${metrics['cost_per_incremental_booking']:.2f}**.

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
- Difference-in-differences relies on parallel trends; the pretrend slope gap is **{metrics['pretrend_slope_gap_bookings_per_day']:.2f} bookings/day**.
""")
    REPORTS.joinpath("measurement_whitepaper.md").write_text("""# Measurement Whitepaper — From Attribution to Incrementality for Airbnb Experiences

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
""")
    REPORTS.joinpath("model_card.md").write_text(f"""# Model Card — Airbnb Experiences Incrementality Simulation

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

- Source row count: {len(listings):,}
- Demand panel rows: {len(panel):,}
- Marketing panel rows: {len(marketing):,}
- Pretrend slope gap: {metrics['pretrend_slope_gap_bookings_per_day']:.2f} bookings/day

## Main risks

- Public lodging proxy may not generalize to Experiences.
- Synthetic marketing data can demonstrate architecture but cannot prove real-world effect size.
- Geographic confounding remains possible without stronger matched-market or synthetic-control design.
""")
    REPORTS.joinpath("index.html").write_text(f"""<!doctype html><html><head><meta charset='utf-8'><title>Airbnb Experiences Incrementality Engine</title><style>body{{font-family:Arial,sans-serif;margin:40px;max-width:960px}} .kpi{{display:inline-block;background:#f5f5f5;margin:8px;padding:16px;border-radius:8px}} img{{max-width:100%;}}</style></head><body><h1>Airbnb Experiences Demand Signal & Incrementality Engine</h1><p><b>Decision:</b> {decision}</p><div class='kpi'>Incremental bookings<br><b>{metrics['estimated_incremental_bookings']:,.0f}</b></div><div class='kpi'>Incremental GBV<br><b>${metrics['estimated_incremental_gbv']:,.0f}</b></div><div class='kpi'>iROAS<br><b>{metrics['incremental_roas']:.2f}x</b></div><h2>Figures</h2><img src='../figures/experience_opportunity_score.png'><img src='../figures/geo_lift_trend.png'><img src='../figures/demand_signal_map.png'></body></html>""")
    quality = {
        "raw_listing_rows": int(len(listings)),
        "demand_panel_rows": int(len(panel)),
        "marketing_panel_rows": int(len(marketing)),
        "boroughs": sorted(marketing["borough"].unique().tolist()),
        "synthetic_fields": ["event_pressure", "intent_index", "weather_favorability", "campaign spend/impressions/clicks/bookings/gbv/margin"],
        "public_source_url": DATA_URL,
    }
    (PROCESSED / "data_quality_summary.json").write_text(json.dumps(quality, indent=2))
    return decision_metrics


def main() -> None:
    ensure_dirs()
    download_data()
    listings = load_public_airbnb_proxy()
    panel = build_neighborhood_panel(listings)
    marketing = build_marketing_panel(panel)
    metrics = did_estimate(marketing)
    opportunity = build_opportunity_scores(marketing, metrics)
    decision_metrics = write_reports(listings, panel, marketing, opportunity, metrics)

    panel.to_csv(PROCESSED / "neighborhood_demand_panel.csv", index=False)
    marketing.to_csv(PROCESSED / "marketing_experiment_panel.csv", index=False)
    opportunity.to_csv(PROCESSED / "experience_opportunity_scores.csv", index=False)
    decision_metrics.to_csv(PROCESSED / "decision_metrics.csv", index=False)
    save_warehouse({
        "neighborhood_demand_panel": panel,
        "marketing_experiment_panel": marketing,
        "experience_opportunity_scores": opportunity,
        "decision_metrics": decision_metrics,
    })
    make_figures(panel, marketing, opportunity)
    print(f"raw_listing_rows={len(listings)}")
    print(f"neighborhood_demand_panel_rows={len(panel)}")
    print(f"marketing_experiment_panel_rows={len(marketing)}")
    print(f"estimated_incremental_bookings={metrics['estimated_incremental_bookings']:.2f}")
    print(f"estimated_incremental_gbv={metrics['estimated_incremental_gbv']:.2f}")
    print(f"incremental_roas={metrics['incremental_roas']:.2f}")
    print(f"warehouse={DB_FILE}")


if __name__ == "__main__":
    main()

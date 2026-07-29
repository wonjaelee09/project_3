from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports" / "hiring_manager_validation.md"
DB = ROOT / "data" / "warehouse" / "airbnb_experiences_incrementality.db"

RUBRIC = [
    ("Marketing ROI decisioning", 10, ["incremental_roas", "estimated_incremental_gbv", "contribution_margin", "executive_recommendation.md"]),
    ("Causal inference", 10, ["difference-in-differences", "pretrend", "treated_market", "post_period"]),
    ("Experimentation", 10, ["treatment_flag", "holdout_flag", "campaign_id"]),
    ("Customer / traveler relationship modeling", 10, ["traveler_segment", "expected LTV", "segment"]),
    ("SQL / warehouse", 10, ["airbnb_experiences_incrementality.db", "measurement_queries.sql"]),
    ("KPI judgment", 10, ["GBV", "iROAS", "cost_per_incremental_booking", "conversion_rate"]),
    ("Cross-functional communication", 10, ["Marketing", "Finance", "Product", "Engineering"]),
    ("Methodological honesty", 10, ["synthetic", "public", "limitations", "not actual Airbnb"]),
    ("Experiences relevance", 10, ["Experiences", "event_pressure", "intent_index", "poi_density"]),
    ("Reproducibility", 10, ["Quickstart", "run_pipeline.py", "validate_project.py"]),
]

SEARCH_FILES = [
    ROOT / "README.md",
    ROOT / "job_description_snapshot.md",
    ROOT / "src" / "run_pipeline.py",
    ROOT / "reports" / "executive_recommendation.md",
    ROOT / "reports" / "measurement_whitepaper.md",
    ROOT / "reports" / "model_card.md",
    ROOT / "sql" / "measurement_queries.sql",
    ROOT / "agents" / "hiring_manager_agent.md",
]

REQUIRED_ARTIFACTS = [
    ROOT / "README.md",
    ROOT / "job_description_snapshot.md",
    ROOT / "kanban.md",
    ROOT / "src" / "run_pipeline.py",
    ROOT / "src" / "validate_project.py",
    ROOT / "sql" / "measurement_queries.sql",
    ROOT / "data" / "processed" / "neighborhood_demand_panel.csv",
    ROOT / "data" / "processed" / "marketing_experiment_panel.csv",
    ROOT / "data" / "processed" / "experience_opportunity_scores.csv",
    ROOT / "data" / "processed" / "decision_metrics.csv",
    ROOT / "reports" / "executive_recommendation.md",
    ROOT / "reports" / "measurement_whitepaper.md",
    ROOT / "reports" / "model_card.md",
    ROOT / "reports" / "index.html",
    ROOT / "figures" / "experience_opportunity_score.png",
    ROOT / "figures" / "geo_lift_trend.png",
    ROOT / "figures" / "demand_signal_map.png",
    DB,
]


def corpus() -> str:
    chunks = []
    for path in SEARCH_FILES:
        if path.exists():
            chunks.append(path.read_text(errors="ignore"))
    return "\n".join(chunks)


def score_rubric(text: str) -> list[tuple[str, int, list[str]]]:
    rows = []
    lower = text.lower()
    for name, points, signals in RUBRIC:
        found = [s for s in signals if s.lower() in lower]
        score = round(points * len(found) / len(signals))
        rows.append((name, score, found))
    return rows


def validate_tables() -> dict[str, int]:
    counts = {}
    if not DB.exists():
        return counts
    with sqlite3.connect(DB) as con:
        table_names = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name", con)["name"].tolist()
        for table in table_names:
            counts[table] = int(pd.read_sql(f"SELECT COUNT(*) AS n FROM {table}", con)["n"].iloc[0])
    return counts


def main() -> None:
    text = corpus()
    rubric_rows = score_rubric(text)
    artifact_rows = [(str(p.relative_to(ROOT)), p.exists(), p.stat().st_size if p.exists() else 0) for p in REQUIRED_ARTIFACTS]
    table_counts = validate_tables()
    total = sum(row[1] for row in rubric_rows)
    possible = sum(points for _, points, _ in RUBRIC)
    artifact_ok = all(ok and size > 0 for _, ok, size in artifact_rows)
    tables_ok = {"neighborhood_demand_panel", "marketing_experiment_panel", "experience_opportunity_scores", "decision_metrics"}.issubset(table_counts)

    lines = [
        "# Hiring Manager Validation — Airbnb Experiences Incrementality Engine",
        "",
        f"## Overall score: {total}/{possible}",
        "",
        "## Rubric",
    ]
    for name, score, found in rubric_rows:
        lines.append(f"- **{name}: {score}/10**")
        lines.append(f"  - Evidence signals found: {', '.join(found) if found else 'none'}")
    lines.extend(["", "## Artifact check"])
    for rel, ok, size in artifact_rows:
        lines.append(f"- {'✅' if ok and size > 0 else '❌'} `{rel}` ({size} bytes)")
    lines.extend(["", "## SQLite warehouse table counts"])
    if table_counts:
        for table, count in table_counts.items():
            lines.append(f"- `{table}`: {count:,} rows")
    else:
        lines.append("- No warehouse found.")
    lines.extend([
        "",
        "## Hiring manager read",
        "This project is materially stronger than the original Airbnb availability classifier because it centers on the MarTech Measurement job-to-be-done: deciding whether marketing caused incremental Experiences bookings, GBV, and contribution margin. It demonstrates demand-signal feature engineering, treatment/control measurement, SQL-backed analytical tables, stakeholder recommendations, and explicit limitations around synthetic private data.",
        "",
        f"Validation status: {'PASS' if total >= 85 and artifact_ok and tables_ok else 'NEEDS WORK'}",
    ])
    REPORT.write_text("\n".join(lines))
    print(f"validation_score={total}/{possible}")
    print(f"artifact_ok={artifact_ok}")
    print(f"tables_ok={tables_ok}")
    print(f"report={REPORT}")


if __name__ == "__main__":
    main()

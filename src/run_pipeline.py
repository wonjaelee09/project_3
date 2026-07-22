from __future__ import annotations

import json
import sqlite3
import urllib.request
from dataclasses import dataclass
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"
WAREHOUSE = ROOT / "data" / "warehouse"
FIGURES = ROOT / "figures"
REPORTS = ROOT / "reports"
MODELS = ROOT / "models"

DATA_URL = "https://raw.githubusercontent.com/4GeeksAcademy/data-preprocessing-project-tutorial/main/AB_NYC_2019.csv"
RAW_CSV = DATA_RAW / "AB_NYC_2019.csv"
TARGET = "high_availability"
RANDOM_STATE = 42


@dataclass(frozen=True)
class ModelResult:
    name: str
    accuracy: float
    precision: float
    recall: float
    f1: float
    roc_auc: float | None


def ensure_dirs() -> None:
    for path in [DATA_RAW, DATA_PROCESSED, WAREHOUSE, FIGURES, REPORTS, MODELS]:
        path.mkdir(parents=True, exist_ok=True)


def download_data() -> Path:
    if RAW_CSV.exists() and RAW_CSV.stat().st_size > 1_000_000:
        return RAW_CSV
    req = urllib.request.Request(DATA_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as response:
        RAW_CSV.write_bytes(response.read())
    return RAW_CSV


def load_and_clean() -> pd.DataFrame:
    raw = pd.read_csv(download_data())
    df = raw.copy()
    df["reviews_per_month"] = df["reviews_per_month"].fillna(0)
    df["last_review_missing"] = df["last_review"].isna().astype(int)
    df["high_availability"] = (df["availability_365"] > 165).astype(int)
    df = df[df["price"] > 0].copy()
    df["log_price"] = np.log1p(df["price"])
    df["multi_listing_host"] = (df["calculated_host_listings_count"] > 1).astype(int)
    df["large_multi_listing_host"] = (df["calculated_host_listings_count"] > 5).astype(int)
    df["review_intensity"] = df["number_of_reviews"] * df["reviews_per_month"]
    keep = [
        "id",
        "neighbourhood_group",
        "neighbourhood",
        "latitude",
        "longitude",
        "room_type",
        "price",
        "log_price",
        "minimum_nights",
        "number_of_reviews",
        "reviews_per_month",
        "review_intensity",
        "calculated_host_listings_count",
        "multi_listing_host",
        "large_multi_listing_host",
        "last_review_missing",
        "availability_365",
        "high_availability",
    ]
    return df[keep]


def write_warehouse(df: pd.DataFrame) -> None:
    db = WAREHOUSE / "nyc_airbnb.db"
    if db.exists():
        db.unlink()
    with sqlite3.connect(db) as con:
        df.to_sql("listings_model", con, index=False)


def build_preprocessor(df: pd.DataFrame) -> tuple[ColumnTransformer, list[str], list[str]]:
    categorical = ["neighbourhood_group", "neighbourhood", "room_type"]
    numeric = [
        "latitude",
        "longitude",
        "log_price",
        "minimum_nights",
        "number_of_reviews",
        "reviews_per_month",
        "review_intensity",
        "calculated_host_listings_count",
        "multi_listing_host",
        "large_multi_listing_host",
        "last_review_missing",
    ]
    preprocessor = ColumnTransformer(
        transformers=[
            ("categorical", OneHotEncoder(handle_unknown="ignore", min_frequency=20), categorical),
            ("numeric", StandardScaler(), numeric),
        ]
    )
    return preprocessor, categorical, numeric


def evaluate_model(name: str, pipe: Pipeline, X_test: pd.DataFrame, y_test: pd.Series) -> tuple[ModelResult, np.ndarray]:
    pred = pipe.predict(X_test)
    if hasattr(pipe, "predict_proba"):
        proba = pipe.predict_proba(X_test)[:, 1]
        auc = roc_auc_score(y_test, proba)
    else:
        auc = None
    return (
        ModelResult(
            name=name,
            accuracy=accuracy_score(y_test, pred),
            precision=precision_score(y_test, pred, zero_division=0),
            recall=recall_score(y_test, pred, zero_division=0),
            f1=f1_score(y_test, pred, zero_division=0),
            roc_auc=auc,
        ),
        pred,
    )


def train_models(df: pd.DataFrame) -> tuple[pd.DataFrame, str, Pipeline, pd.DataFrame, pd.Series, np.ndarray]:
    features = df.drop(columns=["id", "availability_365", TARGET])
    target = df[TARGET]
    X_train, X_test, y_train, y_test = train_test_split(
        features, target, test_size=0.25, random_state=RANDOM_STATE, stratify=target
    )
    preprocessor, _, _ = build_preprocessor(df)
    models = {
        "Dummy most-frequent": DummyClassifier(strategy="most_frequent"),
        "Logistic Regression": LogisticRegression(max_iter=1000, class_weight="balanced", n_jobs=None),
        "Decision Tree": DecisionTreeClassifier(max_depth=6, min_samples_leaf=100, class_weight="balanced", random_state=RANDOM_STATE),
        "Random Forest": RandomForestClassifier(
            n_estimators=80,
            min_samples_leaf=25,
            max_depth=14,
            max_features="sqrt",
            class_weight="balanced_subsample",
            random_state=RANDOM_STATE,
            n_jobs=-1,
        ),
    }
    results: list[ModelResult] = []
    predictions = {}
    fitted = {}
    for name, model in models.items():
        pipe = Pipeline(steps=[("preprocess", preprocessor), ("model", model)])
        pipe.fit(X_train, y_train)
        result, pred = evaluate_model(name, pipe, X_test, y_test)
        results.append(result)
        predictions[name] = pred
        fitted[name] = pipe

    metrics = pd.DataFrame([r.__dict__ for r in results]).sort_values("f1", ascending=False)
    best_name = str(metrics.iloc[0]["name"])
    best_model = fitted[best_name]
    best_pred = predictions[best_name]
    joblib.dump(best_model, MODELS / "best_availability_classifier.joblib")
    return metrics, best_name, best_model, X_test, y_test, best_pred


def feature_importance(best_model: Pipeline, best_name: str) -> pd.DataFrame:
    pre = best_model.named_steps["preprocess"]
    names = pre.get_feature_names_out()
    model = best_model.named_steps["model"]
    if hasattr(model, "feature_importances_"):
        values = model.feature_importances_
        kind = "importance"
    elif hasattr(model, "coef_"):
        values = np.abs(model.coef_[0])
        kind = "abs_coefficient"
    else:
        return pd.DataFrame(columns=["feature", "value", "kind"])
    out = pd.DataFrame({"feature": names, "value": values, "kind": kind}).sort_values("value", ascending=False)
    out.to_csv(DATA_PROCESSED / "feature_importance.csv", index=False)
    return out


def write_figures(df: pd.DataFrame, metrics: pd.DataFrame, y_test: pd.Series, best_pred: np.ndarray, importance: pd.DataFrame) -> None:
    sns.set_theme(style="whitegrid")

    plt.figure(figsize=(8, 5))
    order = df.groupby("neighbourhood_group")[TARGET].mean().sort_values(ascending=False).index
    sns.barplot(data=df, x="neighbourhood_group", y=TARGET, order=order, errorbar=None)
    plt.title("High-Availability Listing Rate by NYC Borough")
    plt.xlabel("Borough")
    plt.ylabel("Share with availability > 165 days")
    plt.xticks(rotation=20, ha="right")
    plt.tight_layout()
    plt.savefig(FIGURES / "high_availability_by_borough.png", dpi=160)
    plt.close()

    plt.figure(figsize=(8, 5))
    sns.barplot(data=df, x="room_type", y=TARGET, errorbar=None)
    plt.title("High-Availability Rate by Room Type")
    plt.xlabel("Room type")
    plt.ylabel("Share with availability > 165 days")
    plt.xticks(rotation=20, ha="right")
    plt.tight_layout()
    plt.savefig(FIGURES / "high_availability_by_room_type.png", dpi=160)
    plt.close()

    plt.figure(figsize=(9, 5))
    plot_metrics = metrics.melt(id_vars="name", value_vars=["accuracy", "precision", "recall", "f1", "roc_auc"])
    sns.barplot(data=plot_metrics, x="name", y="value", hue="variable")
    plt.title("Classifier Evaluation Metrics")
    plt.xlabel("Model")
    plt.ylabel("Score")
    plt.ylim(0, 1)
    plt.xticks(rotation=20, ha="right")
    plt.legend(loc="lower right")
    plt.tight_layout()
    plt.savefig(FIGURES / "model_metrics.png", dpi=160)
    plt.close()

    ConfusionMatrixDisplay(confusion_matrix(y_test, best_pred), display_labels=["<=165 days", ">165 days"]).plot(cmap="Blues")
    plt.title("Best Model Confusion Matrix")
    plt.tight_layout()
    plt.savefig(FIGURES / "confusion_matrix.png", dpi=160)
    plt.close()

    if not importance.empty:
        top = importance.head(15).copy()
        plt.figure(figsize=(10, 6))
        sns.barplot(data=top, y="feature", x="value")
        plt.title("Top Model Drivers")
        plt.xlabel(top["kind"].iloc[0])
        plt.ylabel("Feature")
        plt.tight_layout()
        plt.savefig(FIGURES / "feature_importance.png", dpi=160)
        plt.close()


def data_quality_summary(raw: pd.DataFrame, model_df: pd.DataFrame) -> dict[str, object]:
    return {
        "raw_rows": int(len(raw)),
        "model_rows": int(len(model_df)),
        "removed_zero_price_rows": int((raw["price"] <= 0).sum()),
        "target_positive_rate": float(model_df[TARGET].mean()),
        "missing_reviews_per_month_raw": int(raw["reviews_per_month"].isna().sum()),
        "missing_last_review_raw": int(raw["last_review"].isna().sum()),
        "borough_counts": model_df["neighbourhood_group"].value_counts().to_dict(),
    }


def write_reports(df: pd.DataFrame, metrics: pd.DataFrame, best_name: str, importance: pd.DataFrame, quality: dict[str, object]) -> None:
    best = metrics.iloc[0]
    metrics_md = metrics.to_markdown(index=False, floatfmt=".3f")
    top_features = importance.head(10)[["feature", "value"]].to_markdown(index=False, floatfmt=".4f") if not importance.empty else "No importance available."
    borough = df.groupby("neighbourhood_group").agg(
        listings=("id", "count"),
        high_availability_rate=(TARGET, "mean"),
        avg_price=("price", "mean"),
        avg_host_listing_count=("calculated_host_listings_count", "mean"),
    ).sort_values("high_availability_rate", ascending=False)

    executive = f"""# Executive Summary — NYC Airbnb Availability Classification

## Short answer
This project predicts whether an NYC Airbnb listing is likely to have **more than 165 available days per year**. That target is a proxy for listings that may behave less like scarce, experience-oriented supply and more like highly available inventory. The best model in this build is **{best_name}** with F1={best['f1']:.3f} and ROC AUC={best['roc_auc']:.3f}.

## Why this matters
For a marketplace such as Airbnb, availability is both a supply-quality and marketplace-liquidity signal. A highly available listing may be under-demanded, newly listed, priced poorly, professionally managed, or structurally different from listings that are frequently booked. The model should be used to prioritize investigation and host/product interventions, not to make automatic punitive decisions.

## Dataset
- Source: public AB_NYC_2019.csv derived from Inside Airbnb / NYC Airbnb open dataset.
- Raw rows: {quality['raw_rows']:,}
- Modeling rows after zero-price cleanup: {quality['model_rows']:,}
- Positive target rate, availability > 165 days: {quality['target_positive_rate']:.1%}

## Model performance

{metrics_md}

## Highest-signal model drivers

{top_features}

## Borough-level pattern

{borough.to_markdown(floatfmt='.3f')}

## Recommendation
1. Use the model to create a host/listing review queue for high-availability inventory.
2. Segment actions by room type, borough, price, and host listing count.
3. Do not frame the prediction as causality. The model says which listings look high-availability; it does not prove why.
4. Run follow-up experiments before making marketing or product changes: host education, pricing nudges, photo/listing-quality prompts, or targeted demand generation.

## Interview-ready distinction
This is a predictive marketplace model, not a causal model. It can identify which listings deserve attention, but business interventions still need experimentation to estimate incremental impact.
"""
    (REPORTS / "executive_summary.md").write_text(executive)

    model_card = f"""# Model Card — High Availability Classifier

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
- Name: {best_name}
- Accuracy: {best['accuracy']:.3f}
- Precision: {best['precision']:.3f}
- Recall: {best['recall']:.3f}
- F1: {best['f1']:.3f}
- ROC AUC: {best['roc_auc']:.3f}

## Data quality notes
- Zero-price rows removed: {quality['removed_zero_price_rows']}
- Missing `reviews_per_month` filled with 0: {quality['missing_reviews_per_month_raw']}
- Missing `last_review` represented with `last_review_missing`: {quality['missing_last_review_raw']}

## Limitations
- 2019 NYC data may not represent current Airbnb supply or post-pandemic travel behavior.
- Availability is not the same as demand, revenue, quality, or host intent.
- Neighbourhood one-hot features can encode location-specific historical patterns that may drift.
- Evaluation is offline only; production use needs calibration and monitoring.
"""
    (REPORTS / "model_card.md").write_text(model_card)

    html = f"""<!doctype html>
<html lang=\"en\">
<head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\"><title>NYC Airbnb Availability Project</title>
<style>body{{font-family:Arial,sans-serif;max-width:980px;margin:32px auto;padding:0 16px;line-height:1.5}} img{{max-width:100%;border:1px solid #ddd;border-radius:8px}} code{{background:#f5f5f5;padding:2px 4px}}</style></head>
<body>
<h1>NYC Airbnb Availability Classification</h1>
<p><strong>Best model:</strong> {best_name} · <strong>F1:</strong> {best['f1']:.3f} · <strong>ROC AUC:</strong> {best['roc_auc']:.3f}</p>
<p>This project predicts listings with more than 165 available days/year and translates the result into marketplace actions.</p>
<h2>Figures</h2>
<h3>Model metrics</h3><img src=\"../figures/model_metrics.png\" alt=\"Model metrics\">
<h3>Confusion matrix</h3><img src=\"../figures/confusion_matrix.png\" alt=\"Confusion matrix\">
<h3>Top model drivers</h3><img src=\"../figures/feature_importance.png\" alt=\"Feature importance\">
<h3>Borough pattern</h3><img src=\"../figures/high_availability_by_borough.png\" alt=\"High availability by borough\">
<h2>Read next</h2>
<ul><li><code>executive_summary.md</code></li><li><code>model_card.md</code></li><li><code>hiring_manager_validation.md</code></li></ul>
</body></html>
"""
    (REPORTS / "index.html").write_text(html)


def main() -> None:
    ensure_dirs()
    raw_path = download_data()
    raw = pd.read_csv(raw_path)
    df = load_and_clean()
    df.to_csv(DATA_PROCESSED / "listings_model.csv", index=False)
    write_warehouse(df)
    metrics, best_name, best_model, X_test, y_test, best_pred = train_models(df)
    metrics.to_csv(DATA_PROCESSED / "model_metrics.csv", index=False)
    importance = feature_importance(best_model, best_name)
    write_figures(df, metrics, y_test, best_pred, importance)
    quality = data_quality_summary(raw, df)
    (DATA_PROCESSED / "data_quality_summary.json").write_text(json.dumps(quality, indent=2))
    write_reports(df, metrics, best_name, importance, quality)
    print(f"raw_rows={len(raw)}")
    print(f"model_rows={len(df)}")
    print(f"best_model={best_name}")
    print(f"best_f1={metrics.iloc[0]['f1']:.3f}")
    print(f"best_roc_auc={metrics.iloc[0]['roc_auc']:.3f}")
    print(f"wrote_reports={REPORTS}")
    print(f"wrote_figures={FIGURES}")


if __name__ == "__main__":
    main()

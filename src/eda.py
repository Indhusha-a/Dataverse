"""Phase 6: descriptive EDA over cleaned Parquet files. Run with `python -m src.eda`."""
import pandas as pd
import matplotlib.pyplot as plt
from src.config import PROCESSED_DIR, OUTPUTS_DIR

def load_all_processed(columns=None):
    """Concatenates the *processed* (already-cleaned, already-shrunk) monthly Parquet
    files, optionally column-pruned. Safe for EDA -- these are far smaller than the
    raw CSVs and this is descriptive analysis, not the ML training pipeline."""
    frames = [pd.read_parquet(p, columns=columns) for p in sorted(PROCESSED_DIR.glob("*.parquet"))]
    return pd.concat(frames, ignore_index=True)

def _save(fig, name):
    fig.savefig(OUTPUTS_DIR / "figures" / name, dpi=140, bbox_inches="tight")
    plt.close(fig)

def fare_distribution(df):
    fig, ax = plt.subplots(figsize=(7, 4))
    df["base_fare"].clip(upper=df["base_fare"].quantile(0.99)).hist(bins=60, ax=ax)
    ax.set_title("Base fare distribution (clipped at 99th percentile)")
    ax.set_xlabel("Base fare (USD)"); ax.set_ylabel("Trip count")
    _save(fig, "fare_distribution.png")

def distance_distribution(df):
    fig, ax = plt.subplots(figsize=(7, 4))
    df["distance_miles"].clip(upper=df["distance_miles"].quantile(0.99)).hist(bins=60, ax=ax)
    ax.set_title("Trip distance distribution (clipped at 99th percentile)")
    ax.set_xlabel("Distance (miles)"); ax.set_ylabel("Trip count")
    _save(fig, "distance_distribution.png")

def duration_distribution(df):
    dur_min = (df["dropoff_timestamp"] - df["pickup_timestamp"]).dt.total_seconds() / 60
    fig, ax = plt.subplots(figsize=(7, 4))
    dur_min.clip(upper=dur_min.quantile(0.99)).hist(bins=60, ax=ax)
    ax.set_title("Trip duration distribution (clipped at 99th percentile)")
    ax.set_xlabel("Duration (minutes)"); ax.set_ylabel("Trip count")
    _save(fig, "duration_distribution.png")

def hourly_demand(df):
    hour = df["pickup_timestamp"].dt.hour
    counts = hour.value_counts().sort_index()
    fig, ax = plt.subplots(figsize=(7, 4))
    counts.plot(kind="bar", ax=ax)
    ax.set_title("Pickup demand by hour of day"); ax.set_xlabel("Hour"); ax.set_ylabel("Trip count")
    _save(fig, "hourly_demand.png")

def weekday_demand(df):
    dow = df["pickup_timestamp"].dt.day_name()
    order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    counts = dow.value_counts().reindex(order)
    fig, ax = plt.subplots(figsize=(7, 4))
    counts.plot(kind="bar", ax=ax)
    ax.set_title("Pickup demand by day of week"); ax.set_xlabel("Day"); ax.set_ylabel("Trip count")
    _save(fig, "weekday_demand.png")

def missingness(df):
    pct = (df.isna().mean() * 100).sort_values(ascending=False)
    pct = pct[pct > 0]
    fig, ax = plt.subplots(figsize=(7, 4))
    pct.plot(kind="barh", ax=ax)
    ax.set_title("Missing values by column"); ax.set_xlabel("% missing"); ax.set_ylabel("Column")
    _save(fig, "missingness.png")

if __name__ == "__main__":
    (OUTPUTS_DIR / "figures").mkdir(parents=True, exist_ok=True)
    df = load_all_processed(columns=["pickup_timestamp", "dropoff_timestamp", "base_fare",
                                      "distance_miles", "rider_count"])
    fare_distribution(df)
    distance_distribution(df)
    duration_distribution(df)
    hourly_demand(df)
    weekday_demand(df)
    missingness(df)
    print(df[["base_fare", "distance_miles", "rider_count"]].describe())
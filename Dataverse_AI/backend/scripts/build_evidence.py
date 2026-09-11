"""Generates backend/data/evidence/*.json from the root project's cleaned outputs.
No raw-CSV scan; only processed/*.parquet and existing outputs/ tables.

Run with: python -m scripts.build_evidence   (from Dataverse_AI/backend/)
"""
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.config import ROOT_OUTPUTS, ROOT_PROCESSED, ZONE_FILE, EVIDENCE_DIR


def load_zones():
    return pd.read_csv(ZONE_FILE)


def zone_lookup(zones, loc_id):
    row = zones.loc[zones["loc_id"] == loc_id]
    if row.empty:
        return {"zone_name": f"Zone {loc_id}", "borough_name": None, "service_zone": None}
    r = row.iloc[0]
    return {"zone_name": r["zone_name"], "borough_name": r["borough_name"], "service_zone": r["service_zone"]}


def build_top_zones(zones):
    pickups = pd.read_csv(ROOT_OUTPUTS / "tables" / "top_pickup_zones.csv")
    dropoffs = pd.read_csv(ROOT_OUTPUTS / "tables" / "top_dropoff_zones.csv")
    records = []
    for rank, row in enumerate(pickups.itertuples(index=False), start=1):
        records.append({
            "metric": "top_pickup_zone", "rank": rank, "loc_id": int(row.loc_id),
            "zone_name": row.zone_name, "borough_name": row.borough_name,
            "service_zone": row.service_zone, "value": int(row.pickup_count),
            "source": "outputs/tables/top_pickup_zones.csv",
            "calculation": "value_counts() of origin_loc_id across all cleaned trips",
        })
    for rank, row in enumerate(dropoffs.itertuples(index=False), start=1):
        records.append({
            "metric": "top_dropoff_zone", "rank": rank, "loc_id": int(row.loc_id),
            "zone_name": row.zone_name, "borough_name": row.borough_name,
            "service_zone": row.service_zone, "value": int(row.dropoff_count),
            "source": "outputs/tables/top_dropoff_zones.csv",
            "calculation": "value_counts() of dest_loc_id across all cleaned trips",
        })
    return records


def build_top_od_pairs():
    od = pd.read_csv(ROOT_OUTPUTS / "tables" / "top_od_pairs.csv")
    records = []
    for rank, row in enumerate(od.itertuples(index=False), start=1):
        records.append({
            "metric": "top_od_pair", "rank": rank,
            "origin_loc_id": int(row.origin_loc_id), "origin_zone": row.origin_zone,
            "dest_loc_id": int(row.dest_loc_id), "dest_zone": row.dest_zone,
            "value": int(row.trip_count),
            "source": "outputs/tables/top_od_pairs.csv",
            "calculation": "groupby(origin_loc_id, dest_loc_id).size(), sorted desc, top 20",
        })
    return records


def build_demand_opportunities(zones):
    """Historical baseline per zone = mean actual hourly pickups over the TEST period
    (real held-out data, never touched during model selection)."""
    test_pred = pd.read_csv(ROOT_OUTPUTS / "forecasts" / "demand_test_predictions.csv",
                             parse_dates=["hour_bucket"])
    baseline = (test_pred.groupby("origin_loc_id")["pickups"].mean()
                .rename("baseline_avg_hourly_pickups").reset_index())
    peak_hour = (test_pred.assign(hour=test_pred["hour_bucket"].dt.hour)
                 .groupby(["origin_loc_id", "hour"])["pickups"].mean()
                 .reset_index().sort_values("pickups", ascending=False)
                 .drop_duplicates("origin_loc_id").set_index("origin_loc_id")["hour"])

    records = []
    for row in baseline.itertuples(index=False):
        zid = int(row.origin_loc_id)
        z = zone_lookup(zones, zid)
        records.append({
            "metric": "historical_demand_baseline", "loc_id": zid, **z,
            "value": round(float(row.baseline_avg_hourly_pickups), 2),
            "peak_hour_of_day": int(peak_hour.get(zid, -1)),
            "time_window": "test period (2026-03), hourly, averaged",
            "source": "outputs/forecasts/demand_test_predictions.csv",
            "calculation": "mean(actual pickups) grouped by origin_loc_id over the held-out test period",
        })
    return records, baseline.set_index("origin_loc_id")["baseline_avg_hourly_pickups"]


def build_forecast_opportunities(zones, baseline_by_zone):
    fc72 = pd.read_csv(ROOT_OUTPUTS / "forecasts" / "demand_forecast_72h.csv", parse_dates=["hour_bucket"])
    forecast_avg = (fc72.groupby("origin_loc_id")["predicted_pickups"].mean()
                    .rename("forecast_avg_hourly_pickups"))
    window_start = fc72["hour_bucket"].min().isoformat()
    window_end = fc72["hour_bucket"].max().isoformat()

    records = []
    for zid, fc_val in forecast_avg.items():
        zid = int(zid)
        baseline = float(baseline_by_zone.get(zid, float("nan")))
        uplift = (fc_val / baseline - 1) if baseline > 0 else None
        z = zone_lookup(zones, zid)
        records.append({
            "metric": "forecast_demand_uplift", "loc_id": zid, **z,
            "forecast_avg_hourly_pickups": round(float(fc_val), 2),
            "baseline_avg_hourly_pickups": round(baseline, 2) if baseline == baseline else None,
            "uplift_pct": round(uplift * 100, 2) if uplift is not None else None,
            "time_window": f"{window_start} to {window_end} (forward 72h forecast)",
            "source": "outputs/forecasts/demand_forecast_72h.csv + demand_test_predictions.csv",
            "calculation": "forecast_avg_hourly_pickups / baseline_avg_hourly_pickups - 1",
        })
    records.sort(key=lambda r: (r["uplift_pct"] if r["uplift_pct"] is not None else -999), reverse=True)
    for rank, r in enumerate(records, start=1):
        r["rank"] = rank
    return records


def build_business_kpis(zones):
    """The one genuinely new computation: no existing output holds these top-line
    totals. Reads only the already-CLEANED processed/*.parquet (not raw CSVs),
    selecting 5 needed columns only."""
    cols = ["pickup_timestamp", "dropoff_timestamp", "base_fare", "distance_miles", "origin_loc_id"]
    frames = [pd.read_parquet(p, columns=cols) for p in sorted(ROOT_PROCESSED.glob("*.parquet"))]
    df = pd.concat(frames, ignore_index=True)

    duration_min = (df["dropoff_timestamp"] - df["pickup_timestamp"]).dt.total_seconds() / 60
    hourly_counts = df["pickup_timestamp"].dt.hour.value_counts()
    peak_hour = int(hourly_counts.idxmax())
    top_zone_id = int(df["origin_loc_id"].value_counts().idxmax())
    top_zone = zone_lookup(zones, top_zone_id)

    kpis = [
        {"metric": "total_trips", "value": int(len(df)),
         "source": "processed/*.parquet (12 months, cleaned)", "calculation": "row count across all cleaned monthly files"},
        {"metric": "average_base_fare", "value": round(float(df["base_fare"].mean()), 2), "unit": "USD",
         "source": "processed/*.parquet", "calculation": "mean(base_fare)"},
        {"metric": "average_trip_duration", "value": round(float(duration_min.mean()), 2), "unit": "minutes",
         "source": "processed/*.parquet", "calculation": "mean(dropoff_timestamp - pickup_timestamp)"},
        {"metric": "average_distance", "value": round(float(df["distance_miles"].mean()), 2), "unit": "miles",
         "source": "processed/*.parquet", "calculation": "mean(distance_miles)"},
        {"metric": "peak_demand_hour", "value": peak_hour, "unit": "hour_of_day_0_23",
         "source": "processed/*.parquet", "calculation": "hour of day with the highest system-wide pickup count"},
        {"metric": "highest_demand_zone", "value": top_zone["zone_name"], "loc_id": top_zone_id,
         "borough_name": top_zone["borough_name"],
         "source": "processed/*.parquet", "calculation": "origin_loc_id with the highest pickup count"},
        {"metric": "date_range_start", "value": df["pickup_timestamp"].min().isoformat(),
         "source": "processed/*.parquet", "calculation": "min(pickup_timestamp)"},
        {"metric": "date_range_end", "value": df["pickup_timestamp"].max().isoformat(),
         "source": "processed/*.parquet", "calculation": "max(pickup_timestamp)"},
    ]
    return kpis


def main():
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    zones = load_zones()

    top_zones = build_top_zones(zones)
    (EVIDENCE_DIR / "top_zones.json").write_text(json.dumps(top_zones, indent=2))
    print(f"Wrote top_zones.json ({len(top_zones)} records)")

    top_od = build_top_od_pairs()
    (EVIDENCE_DIR / "top_od_pairs.json").write_text(json.dumps(top_od, indent=2))
    print(f"Wrote top_od_pairs.json ({len(top_od)} records)")

    demand_opp, baseline_by_zone = build_demand_opportunities(zones)
    (EVIDENCE_DIR / "demand_opportunities.json").write_text(json.dumps(demand_opp, indent=2))
    print(f"Wrote demand_opportunities.json ({len(demand_opp)} records)")

    forecast_opp = build_forecast_opportunities(zones, baseline_by_zone)
    (EVIDENCE_DIR / "forecast_opportunities.json").write_text(json.dumps(forecast_opp, indent=2))
    print(f"Wrote forecast_opportunities.json ({len(forecast_opp)} records)")

    print("Computing business_kpis.json (one pass over processed/*.parquet)...")
    kpis = build_business_kpis(zones)
    (EVIDENCE_DIR / "business_kpis.json").write_text(json.dumps(kpis, indent=2))
    print(f"Wrote business_kpis.json ({len(kpis)} records)")


if __name__ == "__main__":
    main()

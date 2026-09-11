"""Phases 3-5: anomaly detection + deterministic cleaning + Parquet write.
Run with `python -m src.cleaning`. One chunked pass per file -- CSV is read once."""
import re
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from collections import defaultdict
from src.config import RAW_DATA_DIR, TAXI_FILE_GLOB, PROCESSED_DIR, OUTPUTS_DIR, CHUNK_SIZE

# Deterministic validity rules only. Speed threshold is set from a documented
# EDA pass (see outputs/profiles) -- NOT fitted on train/val/test splits, because
# "implausible trip" is a data-quality fact about the row, not a learned model input.
#
# Percentile check on 2025-04 (3,845,182 rows with distance>0 and duration>0):
#   95th=24.0mph  99th=34.0mph  99.9th=46.2mph  99.99th=2,479mph  99.999th=394,411mph
# The distribution breaks cleanly between the 99.9th and 99.99th percentile (a ~50x
# jump) -- everything past that is GPS/timestamp corruption, not a fast trip.
# 100mph sits just above the real-world break and only affects 0.025% of rows.
MAX_PLAUSIBLE_MPH = 100

def month_key(path):
    return re.search(r"(\d{4}-\d{2})", path.name).group(1).replace("-", "_")

def clean_month(path):
    counts = defaultdict(int)
    total_rows = 0
    writer = None
    out_path = PROCESSED_DIR / f"taxi_{month_key(path)}.parquet"

    for chunk in pd.read_csv(
        path, chunksize=CHUNK_SIZE, parse_dates=["pickup_timestamp", "dropoff_timestamp"],
        dtype={"offline_record_flag": "string"}
    ):
        total_rows += len(chunk)
        dur_min = (chunk["dropoff_timestamp"] - chunk["pickup_timestamp"]).dt.total_seconds() / 60
        speed_mph = chunk["distance_miles"] / (dur_min / 60)

        neg_fare = chunk["base_fare"] < 0
        zero_dist_paid = (chunk["distance_miles"] == 0) & (chunk["base_fare"] > 0)
        zero_pax = chunk["rider_count"] == 0
        dropoff_before_pickup = chunk["dropoff_timestamp"] < chunk["pickup_timestamp"]
        bad_duration = dur_min <= 0
        valid_speed_domain = (chunk["distance_miles"] > 0) & (dur_min > 0)
        unrealistic_speed = valid_speed_domain & (speed_mph > MAX_PLAUSIBLE_MPH)

        for name, mask in [
            ("negative_fare", neg_fare), ("zero_distance_nonzero_fare", zero_dist_paid),
            ("zero_passengers", zero_pax), ("dropoff_before_pickup", dropoff_before_pickup),
            ("nonpositive_duration", bad_duration), ("unrealistic_speed", unrealistic_speed),
        ]:
            counts[name] += int(mask.sum())

        # Deterministic treatment (documented per Activity.md SS24/27/28 and PDF Problem 1):
        #   negative fare / dropoff-before-pickup / nonpositive duration / unrealistic
        #   speed -> DROP (logically impossible or off-distribution).
        #   zero passengers / zero-distance-paid -> KEEP + flag (needs context per SS25/26).
        drop_mask = neg_fare | dropoff_before_pickup | bad_duration | unrealistic_speed
        clean_chunk = chunk.loc[~drop_mask].copy()
        clean_chunk["zero_distance_nonzero_fare_flag"] = zero_dist_paid.loc[~drop_mask]
        clean_chunk["zero_passengers_flag"] = zero_pax.loc[~drop_mask]
        counts["rows_kept"] += len(clean_chunk)

        table = pa.Table.from_pandas(clean_chunk, preserve_index=False)
        if writer is None:
            writer = pq.ParquetWriter(out_path, table.schema)
        writer.write_table(table)

    if writer:
        writer.close()
    counts["total_rows"] = total_rows
    return counts

def main():
    PROCESSED_DIR.mkdir(exist_ok=True)
    OUTPUTS_DIR.joinpath("cleaning").mkdir(parents=True, exist_ok=True)
    files = sorted(RAW_DATA_DIR.glob(TAXI_FILE_GLOB))

    rows = []
    for f in files:
        print("Cleaning", f.name, "...")
        c = clean_month(f)
        for anomaly in ["negative_fare", "zero_distance_nonzero_fare", "zero_passengers",
                         "dropoff_before_pickup", "nonpositive_duration", "unrealistic_speed"]:
            rows.append({
                "month": month_key(f), "anomaly_name": anomaly,
                "affected_rows": c[anomaly],
                "percentage_total": round(c[anomaly] / c["total_rows"] * 100, 4),
                "treatment": "drop" if anomaly in (
                    "negative_fare", "dropoff_before_pickup", "nonpositive_duration", "unrealistic_speed"
                ) else "keep_and_flag",
                "justification": {
                    "negative_fare": "Negative base_fare is not a valid charge; no data-dictionary meaning found.",
                    "dropoff_before_pickup": "Logically impossible ordering of timestamps.",
                    "nonpositive_duration": "Zero/negative duration cannot represent a real trip.",
                    "unrealistic_speed": (
                        f"Implied speed exceeds {MAX_PLAUSIBLE_MPH} mph. Percentile check on 2025-04 showed "
                        "the distribution breaking sharply between the 99.9th percentile (46.2 mph) and the "
                        "99.99th percentile (2,479 mph) -- a ~50x jump consistent with GPS/timestamp errors "
                        f"rather than real trips. {MAX_PLAUSIBLE_MPH} mph sits just above the real-world break."
                    ),
                    "zero_distance_nonzero_fare": "Plausible for short/cancelled-but-charged trips; kept with a flag column for downstream review.",
                    "zero_passengers": "May reflect a sensor/logging default rather than an empty cab; kept with a flag column.",
                }[anomaly],
            })
    pd.DataFrame(rows).to_csv(OUTPUTS_DIR / "cleaning" / "anomaly_summary.csv", index=False)
    print("Done. See outputs/cleaning/anomaly_summary.csv and processed/*.parquet")

if __name__ == "__main__":
    main()
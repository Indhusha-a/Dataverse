"""Phase 7: leakage audit tables. Run with `python -m src.features`."""
import pandas as pd
from src.config import OUTPUTS_DIR

FARE_LEAKAGE_AUDIT = pd.DataFrame([
    {"feature_name": "pickup_hour", "source_column": "pickup_timestamp", "available_at_prediction_time": True,
     "uses_target_information": False, "uses_future_information": False, "decision": "include",
     "reason": "Deterministic, known at booking"},
    {"feature_name": "pickup_zone", "source_column": "origin_loc_id", "available_at_prediction_time": True,
     "uses_target_information": False, "uses_future_information": False, "decision": "include",
     "reason": "Known at booking"},
    {"feature_name": "dropoff_zone", "source_column": "dest_loc_id", "available_at_prediction_time": True,
     "uses_target_information": False, "uses_future_information": False, "decision": "include",
     "reason": "Assume destination entered at booking -- state this assumption in the notebook"},
    {"feature_name": "distance_miles", "source_column": "distance_miles", "available_at_prediction_time": True,
     "uses_target_information": False, "uses_future_information": False, "decision": "include",
     "reason": "Treated as a pre-trip estimate; document this assumption explicitly in the notebook"},
    {"feature_name": "rider_count", "source_column": "rider_count", "available_at_prediction_time": True,
     "uses_target_information": False, "uses_future_information": False, "decision": "include",
     "reason": "Known at booking"},
    {"feature_name": "dropoff_timestamp", "source_column": "dropoff_timestamp", "available_at_prediction_time": False,
     "uses_target_information": False, "uses_future_information": True, "decision": "exclude", "reason": "Post-trip"},
    {"feature_name": "charge_total/tips/tolls/fees", "source_column": "fee columns", "available_at_prediction_time": False,
     "uses_target_information": True, "uses_future_information": True, "decision": "exclude",
     "reason": "Derived from/settled with base_fare after the trip"},
    {"feature_name": "fare_settlement_method", "source_column": "fare_settlement_method", "available_at_prediction_time": False,
     "uses_target_information": False, "uses_future_information": True, "decision": "exclude",
     "reason": "Correlates strongly with negative base_fare (method 4 -> 46.9% negative, method 1 -> ~0%); a post-trip settlement outcome code, not known at booking"},
    {"feature_name": "provider_code", "source_column": "provider_code", "available_at_prediction_time": True,
     "uses_target_information": False, "uses_future_information": False, "decision": "include_optional",
     "reason": "Known before the trip starts; no missingness; test empirically whether it improves validation MAE"},
])

DURATION_LEAKAGE_AUDIT = FARE_LEAKAGE_AUDIT.copy()  # same feature universe; target differs, see src/modeling.py

def save_audit(df, name):
    OUTPUTS_DIR.joinpath("tables").mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUTS_DIR / "tables" / f"leakage_audit_{name}.csv", index=False)

if __name__ == "__main__":
    save_audit(FARE_LEAKAGE_AUDIT, "fare")
    save_audit(DURATION_LEAKAGE_AUDIT, "duration")
    print("Saved outputs/tables/leakage_audit_fare.csv and leakage_audit_duration.csv")
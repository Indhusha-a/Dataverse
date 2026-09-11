"""Generates backend/data/analytics_contract.json, mapping each tool/KPI to its
real source file. Run with: python -m scripts.build_analytics_contract"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.config import CONTRACT_PATH

CONTRACT = {
    "datasets": {
        "cleaned_trips": "processed/*.parquet (12 monthly files, 45,538,913 rows after cleaning)",
        "zones": "data/Urban_Flow_Analytics_Zone_Dataset.csv (265 zones)",
    },
    "targets": {
        "fare": "base_fare",
        "duration": "trip_duration_minutes (derived: dropoff_timestamp - pickup_timestamp)",
        "demand": "hourly pickup count per origin_loc_id, top 10 busiest zones",
    },
    "metrics": {
        "fare": "outputs/metrics/fare_model_comparison.csv",
        "duration": "outputs/metrics/duration_model_comparison.csv",
        "demand": "outputs/metrics/demand_model_comparison.csv",
    },
    "models": {
        "fare": "models/fare_model.pkl",
        "duration": "models/duration_model.pkl",
        "demand": "models/demand_model.pkl",
    },
    "tables": {
        "top_pickup_zones": "outputs/tables/top_pickup_zones.csv",
        "top_dropoff_zones": "outputs/tables/top_dropoff_zones.csv",
        "top_od_pairs": "outputs/tables/top_od_pairs.csv",
        "zone_clusters": "outputs/tables/zone_clusters.csv",
        "split_definition": "outputs/tables/split_definition.json",
    },
    "forecasts": {
        "demand_forecast_24h": "outputs/forecasts/demand_forecast_24h.csv",
        "demand_forecast_48h": "outputs/forecasts/demand_forecast_48h.csv",
        "demand_forecast_72h": "outputs/forecasts/demand_forecast_72h.csv",
        "demand_test_predictions": "outputs/forecasts/demand_test_predictions.csv",
    },
    "cleaning": {
        "anomaly_summary": "outputs/cleaning/anomaly_summary.csv",
    },
    "business_kpis": {
        "file": "Dataverse_AI/backend/data/evidence/business_kpis.json",
        "generated_by": "Dataverse_AI/backend/scripts/build_evidence.py",
        "fields": ["total_trips", "average_base_fare", "average_trip_duration", "average_distance",
                    "peak_demand_hour", "highest_demand_zone", "date_range_start", "date_range_end"],
    },
    "evidence_files": {
        "top_zones": "Dataverse_AI/backend/data/evidence/top_zones.json",
        "top_od_pairs": "Dataverse_AI/backend/data/evidence/top_od_pairs.json",
        "demand_opportunities": "Dataverse_AI/backend/data/evidence/demand_opportunities.json",
        "forecast_opportunities": "Dataverse_AI/backend/data/evidence/forecast_opportunities.json",
        "business_kpis": "Dataverse_AI/backend/data/evidence/business_kpis.json",
    },
    "knowledge_sources": [
        "Dataverse_AI/backend/data/knowledge/data_dictionary.md",
        "Dataverse_AI/backend/data/knowledge/data_quality_rules.md",
        "Dataverse_AI/backend/data/knowledge/feature_definitions.md",
        "Dataverse_AI/backend/data/knowledge/modeling_methodology.md",
        "Dataverse_AI/backend/data/knowledge/forecasting_methodology.md",
        "Dataverse_AI/backend/data/knowledge/business_kpi_definitions.md",
        "Dataverse_AI/backend/data/knowledge/insight_catalog.md",
    ],
}


def main():
    CONTRACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONTRACT_PATH.write_text(json.dumps(CONTRACT, indent=2))
    print(f"Wrote {CONTRACT_PATH}")


if __name__ == "__main__":
    main()

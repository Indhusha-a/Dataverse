"""Cached loaders for the generated evidence JSON files."""
import json
from functools import lru_cache

from app.config import EVIDENCE_DIR, CONTRACT_PATH


@lru_cache(maxsize=1)
def load_top_zones():
    return json.loads((EVIDENCE_DIR / "top_zones.json").read_text())


@lru_cache(maxsize=1)
def load_top_od_pairs():
    return json.loads((EVIDENCE_DIR / "top_od_pairs.json").read_text())


@lru_cache(maxsize=1)
def load_demand_opportunities():
    return json.loads((EVIDENCE_DIR / "demand_opportunities.json").read_text())


@lru_cache(maxsize=1)
def load_forecast_opportunities():
    return json.loads((EVIDENCE_DIR / "forecast_opportunities.json").read_text())


@lru_cache(maxsize=1)
def load_business_kpis():
    return json.loads((EVIDENCE_DIR / "business_kpis.json").read_text())


@lru_cache(maxsize=1)
def load_contract():
    return json.loads(CONTRACT_PATH.read_text())


def kpi_by_name(name: str):
    for row in load_business_kpis():
        if row["metric"] == name:
            return row
    return None

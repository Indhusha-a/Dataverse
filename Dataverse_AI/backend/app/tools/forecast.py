"""forecast_demand: forward 72h demand forecast, baseline, and uplift per zone."""
from app.evidence import load_forecast_opportunities


def forecast_demand(zone: str | None = None, top_n: int = 10, min_uplift_pct: float | None = None) -> dict:
    """
    zone: optional zone name (case-insensitive substring match) to filter to one zone.
    top_n: how many ranked-by-uplift rows to return.
    min_uplift_pct: optional filter, e.g. 10 to only show zones forecast to grow >=10%.
    """
    rows = load_forecast_opportunities()
    if zone:
        zone_lower = zone.lower()
        rows = [r for r in rows if zone_lower in r["zone_name"].lower()]
    if min_uplift_pct is not None:
        rows = [r for r in rows if (r["uplift_pct"] or -999) >= min_uplift_pct]
    return {"horizon": "forward 72 hours (recursive forecast)", "results": rows[:top_n]}

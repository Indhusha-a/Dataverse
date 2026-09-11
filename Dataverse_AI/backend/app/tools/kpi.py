"""query_kpi: verified business KPIs. Unknown metrics return an error, not a guess."""
from app.evidence import load_business_kpis, kpi_by_name

VALID_METRICS = [row["metric"] for row in load_business_kpis()]


def query_kpi(metric: str | None = None) -> dict:
    """metric: one of VALID_METRICS, or None to return all KPIs."""
    if metric is None:
        return {"kpis": load_business_kpis()}
    row = kpi_by_name(metric)
    if row is None:
        return {
            "error": f"'{metric}' is not a tracked KPI.",
            "available_metrics": VALID_METRICS,
        }
    return {"kpi": row}

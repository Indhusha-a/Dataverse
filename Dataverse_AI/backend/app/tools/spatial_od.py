"""Tool 4: query_spatial_od -- top pickup zones, top drop-off zones, top OD pairs."""
from app.evidence import load_top_zones, load_top_od_pairs


def query_spatial_od(kind: str = "top_pickup", top_n: int = 10) -> dict:
    """kind: "top_pickup", "top_dropoff", or "top_od_pairs"."""
    if kind == "top_od_pairs":
        return {"kind": kind, "results": load_top_od_pairs()[:top_n]}
    metric = "top_pickup_zone" if kind == "top_pickup" else "top_dropoff_zone"
    rows = [r for r in load_top_zones() if r["metric"] == metric]
    return {"kind": kind, "results": rows[:top_n]}

"""query_demand: historical demand -- top zones, hourly patterns, zone rankings.
`basis` picks between all-time pickup counts and the recent test-period baseline,
since those are two different numbers and shouldn't get conflated."""
from app.evidence import load_top_zones, load_demand_opportunities


def query_demand(basis: str = "all_time_pickups", direction: str = "pickup", zone: str | None = None,
                  top_n: int = 10) -> dict:
    """
    basis: "all_time_pickups" (total historical pickup/dropoff counts) or
           "recent_baseline" (mean hourly pickups over the test period, with peak hour).
    direction: "pickup" or "dropoff" (only used when basis="all_time_pickups").
    zone: optional zone name (case-insensitive substring match) to filter to one zone.
    top_n: how many ranked rows to return.
    """
    if basis == "recent_baseline":
        rows = load_demand_opportunities()
        rows = sorted(rows, key=lambda r: r["value"], reverse=True)
    else:
        metric = "top_pickup_zone" if direction == "pickup" else "top_dropoff_zone"
        rows = [r for r in load_top_zones() if r["metric"] == metric]

    if zone:
        zone_lower = zone.lower()
        rows = [r for r in rows if zone_lower in r["zone_name"].lower()]

    return {"basis": basis, "direction": direction, "results": rows[:top_n]}

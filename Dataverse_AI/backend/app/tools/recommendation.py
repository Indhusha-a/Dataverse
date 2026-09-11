"""build_recommendation: turns forecast + historical evidence into a structured
recommendation. Deterministic -- the LLM only phrases it, never picks the numbers."""
from app.evidence import load_forecast_opportunities, load_demand_opportunities


def build_recommendation(zone: str | None = None, top_n: int = 1) -> dict:
    """
    zone: optional zone name to build a recommendation for a specific zone;
          otherwise recommends the top-uplift zone(s) system-wide.
    top_n: how many ranked opportunities to include (default: the single best).
    """
    forecast_rows = load_forecast_opportunities()
    if zone:
        zone_lower = zone.lower()
        forecast_rows = [r for r in forecast_rows if zone_lower in r["zone_name"].lower()]
    forecast_rows = forecast_rows[:top_n]

    if not forecast_rows:
        return {"error": f"No forecast evidence available for '{zone}'." if zone else
                          "No forecast evidence available."}

    recommendations = []
    for row in forecast_rows:
        recommendations.append({
            "zone": row["zone_name"],
            "loc_id": row["loc_id"],
            "borough_name": row["borough_name"],
            "time_window": row["time_window"],
            "forecast_avg_hourly_pickups": row["forecast_avg_hourly_pickups"],
            "historical_baseline_avg_hourly_pickups": row["baseline_avg_hourly_pickups"],
            "uplift_pct": row["uplift_pct"],
            "recommended_action": (
                f"Prioritize fleet availability in {row['zone_name']} during the forecast window."
                if (row["uplift_pct"] or 0) > 0 else
                f"No strong reallocation signal for {row['zone_name']} -- forecast demand is at or below its recent baseline."
            ),
            "reasoning": [
                "Forecasted demand is above historical baseline." if (row["uplift_pct"] or 0) > 0
                else "Forecasted demand is not meaningfully above historical baseline.",
                f"{row['zone_name']} has a historical baseline of {row['baseline_avg_hourly_pickups']} pickups/hour over the test period.",
                "The forecast covers a forward 72-hour recursive prediction window.",
            ],
            "limitation": (
                "Forecast is based on historical hourly patterns (lag/rolling features) for this zone only; "
                "it does not incorporate live traffic, weather, or event data, and recursive forecasting "
                "compounds prediction error the further out the horizon goes."
            ),
            "source": row["source"],
            "calculation": row["calculation"],
        })
    return {"recommendations": recommendations}

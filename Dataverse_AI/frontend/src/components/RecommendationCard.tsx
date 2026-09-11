import type { ForecastOpportunity } from "../api/client"

interface Props {
  top: ForecastOpportunity
}

export default function RecommendationCard({ top }: Props) {
  return (
    <div className="glass glass-border-glow relative overflow-hidden rounded-2xl p-5 sm:p-6">
      <div className="pointer-events-none absolute -right-10 -top-16 h-48 w-48 rounded-full bg-taxi-500/10 blur-3xl" />
      <div className="relative">
        <div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-wider text-taxi-400">
          <span className="h-1.5 w-1.5 animate-pulse-glow rounded-full bg-taxi-500" />
          Opportunity Detected
        </div>

        <h3 className="font-display mt-2 text-xl font-semibold text-white">{top.zone_name}</h3>
        <p className="text-xs text-white/40">{top.borough_name} &middot; {top.time_window}</p>

        <div className="mt-4 grid grid-cols-3 gap-2 text-center">
          <div className="rounded-xl bg-white/[0.03] px-2 py-2.5">
            <div className="font-display text-base font-semibold text-white">{top.forecast_avg_hourly_pickups.toFixed(0)}</div>
            <div className="text-[10px] uppercase tracking-wide text-white/40">Forecast / hr</div>
          </div>
          <div className="rounded-xl bg-white/[0.03] px-2 py-2.5">
            <div className="font-display text-base font-semibold text-white">{top.baseline_avg_hourly_pickups?.toFixed(0)}</div>
            <div className="text-[10px] uppercase tracking-wide text-white/40">Baseline / hr</div>
          </div>
          <div className="rounded-xl bg-signal-500/10 px-2 py-2.5">
            <div className="font-display text-base font-semibold text-signal-400">+{top.uplift_pct?.toFixed(1)}%</div>
            <div className="text-[10px] uppercase tracking-wide text-white/40">Uplift</div>
          </div>
        </div>

        <div className="my-4 h-px bg-white/8" />

        <div className="text-xs font-semibold uppercase tracking-wider text-white/45">Recommended Action</div>
        <p className="mt-1.5 text-sm text-white/85">
          Prioritize fleet availability in <span className="text-taxi-400">{top.zone_name}</span> during the
          forecast window &mdash; forecast demand exceeds its recent historical baseline.
        </p>

        <div className="mt-3 text-xs font-semibold uppercase tracking-wider text-white/45">Why</div>
        <ul className="mt-1.5 space-y-1 text-sm text-white/70">
          <li>&bull; Forecasted demand is above historical baseline.</li>
          <li>&bull; {top.zone_name} has historically strong pickup volume.</li>
          <li>&bull; The period aligns with a recurring demand pattern for this zone.</li>
        </ul>

        <div className="mt-3 text-xs font-semibold uppercase tracking-wider text-white/45">Limitation</div>
        <p className="mt-1.5 text-xs text-white/50">
          Based on historical hourly patterns only &mdash; no live traffic, weather, or event data.
          Recursive 72h forecasting compounds prediction error further out.
        </p>

        <div className="mt-3 truncate text-[10px] text-white/30">Source: {top.source}</div>
      </div>
    </div>
  )
}

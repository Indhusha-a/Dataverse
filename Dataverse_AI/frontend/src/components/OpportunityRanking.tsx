import type { ForecastOpportunity } from "../api/client"

interface Props {
  data: ForecastOpportunity[]
}

export default function OpportunityRanking({ data }: Props) {
  return (
    <div className="glass rounded-2xl p-5 sm:p-6">
      <div className="mb-1 flex items-center justify-between">
        <h3 className="font-display text-lg font-semibold text-white">Demand Opportunity Ranking</h3>
        <span className="rounded-full bg-white/5 px-2.5 py-1 text-[11px] text-white/45">by uplift %</span>
      </div>
      <p className="mb-4 text-xs text-white/40">Zones forecast to exceed their recent historical baseline</p>

      <div className="scroll-glass -mx-1 max-h-80 space-y-1.5 overflow-y-auto px-1">
        {data.map((row) => {
          const positive = (row.uplift_pct ?? 0) > 0
          return (
            <div
              key={row.loc_id}
              className="flex items-center gap-3 rounded-xl border border-white/5 bg-white/[0.02] px-3 py-2.5 transition-colors hover:bg-white/[0.05]"
            >
              <div className="flex h-7 w-7 flex-none items-center justify-center rounded-full bg-white/5 font-display text-xs font-semibold text-white/70">
                {row.rank}
              </div>
              <div className="min-w-0 flex-1">
                <div className="truncate text-sm font-medium text-white">{row.zone_name}</div>
                <div className="truncate text-[11px] text-white/40">{row.borough_name} &middot; {row.forecast_avg_hourly_pickups.toFixed(0)} pickups/hr forecast</div>
              </div>
              <div
                className={`flex-none rounded-full px-2.5 py-1 text-xs font-semibold ${
                  positive ? "bg-signal-500/15 text-signal-400" : "bg-white/5 text-white/50"
                }`}
              >
                {positive ? "+" : ""}
                {row.uplift_pct?.toFixed(1)}%
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

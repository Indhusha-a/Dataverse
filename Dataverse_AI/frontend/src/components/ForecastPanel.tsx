import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts"
import type { ForecastOpportunity } from "../api/client"

interface Props {
  data: ForecastOpportunity[]
}

function CustomTooltip({ active, payload }: any) {
  if (!active || !payload?.length) return null
  const row = payload[0].payload as ForecastOpportunity
  return (
    <div className="glass-strong rounded-xl px-3.5 py-3 text-xs">
      <div className="font-display text-sm font-semibold text-white">{row.zone_name}</div>
      <div className="mt-1.5 space-y-1 text-white/70">
        <div className="flex items-center justify-between gap-6">
          <span className="text-white/45">Baseline</span>
          <span>{row.baseline_avg_hourly_pickups?.toFixed(1)} / hr</span>
        </div>
        <div className="flex items-center justify-between gap-6">
          <span className="text-white/45">Forecast</span>
          <span className="text-taxi-400">{row.forecast_avg_hourly_pickups.toFixed(1)} / hr</span>
        </div>
        <div className="flex items-center justify-between gap-6">
          <span className="text-white/45">Uplift</span>
          <span className="text-signal-400">+{row.uplift_pct?.toFixed(1)}%</span>
        </div>
      </div>
    </div>
  )
}

export default function ForecastPanel({ data }: Props) {
  const chartData = [...data].slice(0, 8).reverse().map((d) => ({
    ...d,
    name: d.zone_name.length > 16 ? d.zone_name.slice(0, 15) + "…" : d.zone_name,
  }))

  return (
    <div className="glass rounded-2xl p-5 sm:p-6">
      <div className="mb-1 flex items-center justify-between">
        <h3 className="font-display text-lg font-semibold text-white">Forecast vs. Historical Baseline</h3>
        <span className="rounded-full bg-white/5 px-2.5 py-1 text-[11px] text-white/45">forward 72h</span>
      </div>
      <p className="mb-4 text-xs text-white/40">Avg. hourly pickups &middot; top zones ranked by forecast uplift</p>
      <div className="h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} layout="vertical" margin={{ left: 8, right: 12, top: 4, bottom: 4 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" horizontal={false} />
            <XAxis type="number" stroke="rgba(255,255,255,0.3)" tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
            <YAxis type="category" dataKey="name" stroke="rgba(255,255,255,0.5)" tick={{ fontSize: 11 }} width={100} tickLine={false} axisLine={false} />
            <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(255,255,255,0.04)" }} />
            <Bar dataKey="baseline_avg_hourly_pickups" name="Baseline" fill="rgba(255,255,255,0.18)" radius={[0, 6, 6, 0]} barSize={9} />
            <Bar dataKey="forecast_avg_hourly_pickups" name="Forecast" fill="#ffd23f" radius={[0, 6, 6, 0]} barSize={9} />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-2 flex items-center gap-4 text-[11px] text-white/45">
        <span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-white/25" /> Historical baseline</span>
        <span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-taxi-500" /> Forecast (72h)</span>
      </div>
    </div>
  )
}

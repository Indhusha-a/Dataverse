import { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"
import { api, type Kpi, type ForecastOpportunity } from "../api/client"
import KpiTile from "../components/KpiTile"
import ForecastPanel from "../components/ForecastPanel"
import OpportunityRanking from "../components/OpportunityRanking"
import RecommendationCard from "../components/RecommendationCard"
import ChatPanel from "../components/ChatPanel"

function findKpi(kpis: Kpi[], metric: string) {
  return kpis.find((k) => k.metric === metric)
}

function fmtHour(h: number) {
  const period = h >= 12 ? "PM" : "AM"
  const hour12 = h % 12 === 0 ? 12 : h % 12
  return `${hour12}${period}`
}

export default function Dashboard() {
  const navigate = useNavigate()
  const [kpis, setKpis] = useState<Kpi[] | null>(null)
  const [forecasts, setForecasts] = useState<ForecastOpportunity[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    Promise.all([api.kpis(), api.forecastOpportunities()])
      .then(([k, f]) => {
        setKpis(k.kpis)
        setForecasts(f.opportunities)
      })
      .catch(() => setError("Could not reach the backend API. Make sure it's running on port 8000."))
  }, [])

  const totalTrips = kpis && findKpi(kpis, "total_trips")
  const avgFare = kpis && findKpi(kpis, "average_base_fare")
  const avgDuration = kpis && findKpi(kpis, "average_trip_duration")
  const avgDistance = kpis && findKpi(kpis, "average_distance")
  const peakHour = kpis && findKpi(kpis, "peak_demand_hour")
  const topZone = kpis && findKpi(kpis, "highest_demand_zone")

  return (
    <div className="min-h-full bg-ink-950">
      <div className="pointer-events-none fixed -top-32 left-1/3 h-[30rem] w-[30rem] rounded-full bg-taxi-500/[0.06] blur-[130px]" />
      <div className="pointer-events-none fixed bottom-0 right-0 h-[26rem] w-[26rem] rounded-full bg-signal-500/[0.06] blur-[130px]" />

      <header className="glass-strong sticky top-0 z-20 flex items-center justify-between px-5 py-3.5 sm:px-8">
        <button onClick={() => navigate("/")} className="flex items-center gap-2.5">
          <span className="h-2 w-2 rounded-full bg-taxi-500" />
          <span className="font-display text-lg font-semibold text-white">
            Urban<span className="text-taxi-500">Flow</span>
          </span>
          <span className="hidden text-xs text-white/35 sm:inline">Operations Command Center</span>
        </button>
        <div className="flex items-center gap-2 text-[11px] text-white/40">
          <span className="h-1.5 w-1.5 rounded-full bg-signal-400 animate-pulse-glow" />
          Demand&ndash;Fleet Imbalance &amp; Revenue Opportunity
        </div>
      </header>

      <main className="relative z-10 mx-auto max-w-[1400px] px-5 py-6 sm:px-8 sm:py-8">
        {error && (
          <div className="glass mb-6 rounded-2xl border border-rose-500/20 p-4 text-sm text-rose-300">{error}</div>
        )}

        {/* Executive KPIs */}
        <section className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
          <KpiTile label="Total Trips" value={totalTrips ? (Number(totalTrips.value) / 1e6).toFixed(1) : "—"} unit="M cleaned" accent="taxi" />
          <KpiTile label="Avg. Fare" value={avgFare ? `$${Number(avgFare.value).toFixed(2)}` : "—"} accent="signal" />
          <KpiTile label="Avg. Duration" value={avgDuration ? Number(avgDuration.value).toFixed(1) : "—"} unit="min" accent="signal" />
          <KpiTile label="Avg. Distance" value={avgDistance ? Number(avgDistance.value).toFixed(1) : "—"} unit="mi" accent="signal" />
          <KpiTile label="Peak Demand" value={peakHour ? fmtHour(Number(peakHour.value)) : "—"} hint="system-wide" accent="taxi" />
          <KpiTile label="Top Zone" value={topZone ? String(topZone.value) : "—"} hint={topZone?.borough_name as string} accent="rose" />
        </section>

        {/* Main grid: analytics (left) + assistant (right) */}
        <section className="mt-6 grid grid-cols-1 gap-5 lg:grid-cols-[1fr_380px]">
          <div className="space-y-5">
            {forecasts && forecasts.length > 0 && <RecommendationCard top={forecasts[0]} />}
            {forecasts && <ForecastPanel data={forecasts} />}
            {forecasts && <OpportunityRanking data={forecasts} />}
          </div>

          <div className="h-[720px] lg:h-auto lg:sticky lg:top-20">
            <ChatPanel />
          </div>
        </section>
      </main>
    </div>
  )
}

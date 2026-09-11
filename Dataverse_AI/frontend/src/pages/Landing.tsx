import { Canvas } from "@react-three/fiber"
import { Suspense } from "react"
import { useNavigate } from "react-router-dom"
import TaxiCar from "../components/TaxiCar"

const STATS = [
  { label: "Trips analyzed", value: "45.5M" },
  { label: "Zones covered", value: "265" },
  { label: "Fare model R²", value: "0.70" },
  { label: "Forecast horizon", value: "72h" },
]

export default function Landing() {
  const navigate = useNavigate()

  return (
    <div className="relative h-full w-full overflow-hidden bg-ink-950">
      <div className="absolute inset-0">
        <Canvas camera={{ position: [0, 0.4, 4.6], fov: 38 }} shadows dpr={[1, 1.8]}>
          <Suspense fallback={null}>
            <TaxiCar />
          </Suspense>
        </Canvas>
      </div>

      {/* Ambient gradient glows */}
      <div className="pointer-events-none absolute -top-40 left-1/2 h-[36rem] w-[36rem] -translate-x-1/2 rounded-full bg-taxi-500/10 blur-[120px]" />
      <div className="pointer-events-none absolute bottom-[-10rem] right-[-10rem] h-[30rem] w-[30rem] rounded-full bg-signal-500/10 blur-[120px]" />

      <div className="pointer-events-none relative z-10 flex h-full flex-col items-center justify-between px-6 pb-10 pt-6 sm:py-14">
        <header className="glass animate-fade-up flex items-center gap-2.5 rounded-full px-4 py-2 text-[11px] tracking-[0.2em] text-white/60 sm:text-sm sm:tracking-[0.25em]">
          <span className="h-1.5 w-1.5 flex-none rounded-full bg-taxi-500 animate-pulse-glow" />
          <span className="whitespace-nowrap">DATAVERSE &middot; SLIIT CODEFEST DATATHON 2026</span>
        </header>

        <div className="animate-fade-up flex flex-col items-center text-center" style={{ animationDelay: "80ms" }}>
          <h1 className="font-display text-5xl font-semibold leading-[1.05] tracking-tight text-white sm:text-7xl">
            Urban<span className="text-taxi-500">Flow</span>
          </h1>
          <p className="mt-3 max-w-xl text-balance text-base text-white/60 sm:text-lg">
            Decision Intelligence Copilot &mdash; predictive analytics, demand forecasting, and an
            evidence-grounded AI assistant for taxi fleet operations.
          </p>

          <button
            onClick={() => navigate("/dashboard")}
            className="glass glass-border-glow group pointer-events-auto relative mt-8 flex items-center gap-3 overflow-hidden rounded-full px-7 py-3.5 text-sm font-medium text-white transition-transform duration-300 hover:scale-[1.03] active:scale-[0.98]"
          >
            <span className="relative z-10">Enter the Command Center</span>
            <svg className="relative z-10 h-4 w-4 transition-transform duration-300 group-hover:translate-x-1" viewBox="0 0 24 24" fill="none">
              <path d="M5 12h14M13 6l6 6-6 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            <span className="absolute inset-0 -z-0 bg-gradient-to-r from-taxi-500/0 via-taxi-500/15 to-signal-500/0 opacity-0 transition-opacity duration-300 group-hover:opacity-100" />
          </button>

          <p className="mt-3 text-xs text-white/35">Move your cursor &mdash; the taxi follows.</p>
        </div>

        <div className="animate-fade-up grid grid-cols-2 gap-3 sm:flex sm:gap-4" style={{ animationDelay: "160ms" }}>
          {STATS.map((s) => (
            <div key={s.label} className="glass pointer-events-auto rounded-2xl px-4 py-3 text-center sm:px-5">
              <div className="font-display text-xl font-semibold text-white sm:text-2xl">{s.value}</div>
              <div className="mt-0.5 text-[11px] uppercase tracking-wider text-white/45">{s.label}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

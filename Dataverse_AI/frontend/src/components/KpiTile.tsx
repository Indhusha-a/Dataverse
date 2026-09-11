interface Props {
  label: string
  value: string
  unit?: string
  hint?: string
  accent?: "taxi" | "signal" | "rose"
}

const ACCENTS: Record<string, string> = {
  taxi: "from-taxi-500/25 to-taxi-500/0 text-taxi-400",
  signal: "from-signal-500/25 to-signal-500/0 text-signal-400",
  rose: "from-rose-500/25 to-rose-500/0 text-rose-500",
}

export default function KpiTile({ label, value, unit, hint, accent = "signal" }: Props) {
  return (
    <div className="glass group relative overflow-hidden rounded-2xl p-4 transition-transform duration-300 hover:-translate-y-0.5 sm:p-5">
      <div className={`pointer-events-none absolute -right-6 -top-10 h-28 w-28 rounded-full bg-gradient-to-br blur-2xl ${ACCENTS[accent]}`} />
      <div className="relative">
        <div className="text-[11px] font-medium uppercase tracking-wider text-white/45">{label}</div>
        <div className="mt-1.5 flex items-baseline gap-1.5">
          <span className="font-display text-2xl font-semibold text-white sm:text-[1.7rem]">{value}</span>
          {unit && <span className="text-xs text-white/40">{unit}</span>}
        </div>
        {hint && <div className="mt-1 truncate text-[11px] text-white/35">{hint}</div>}
      </div>
    </div>
  )
}

export type EvidenceRow = Record<string, unknown>

export interface Kpi {
  metric: string
  value: number | string
  unit?: string
  loc_id?: number
  borough_name?: string
  source: string
  calculation: string
}

export interface ZoneEvidence {
  metric: string
  rank: number
  loc_id: number
  zone_name: string
  borough_name: string
  service_zone: string
  value: number
  source: string
  calculation: string
}

export interface OdPair {
  metric: string
  rank: number
  origin_loc_id: number
  origin_zone: string
  dest_loc_id: number
  dest_zone: string
  value: number
  source: string
  calculation: string
}

export interface ForecastOpportunity {
  metric: string
  loc_id: number
  zone_name: string
  borough_name: string
  service_zone: string
  forecast_avg_hourly_pickups: number
  baseline_avg_hourly_pickups: number | null
  uplift_pct: number | null
  time_window: string
  source: string
  calculation: string
  rank: number
}

export interface DemandOpportunity {
  metric: string
  loc_id: number
  zone_name: string
  borough_name: string
  service_zone: string
  value: number
  peak_hour_of_day: number
  time_window: string
  source: string
  calculation: string
}

async function getJSON<T>(path: string): Promise<T> {
  const res = await fetch(`/api${path}`)
  if (!res.ok) throw new Error(`GET ${path} failed: ${res.status}`)
  return res.json() as Promise<T>
}

export const api = {
  kpis: () => getJSON<{ kpis: Kpi[] }>("/dashboard/kpis"),
  topZones: () => getJSON<{ zones: ZoneEvidence[] }>("/dashboard/top-zones"),
  odPairs: () => getJSON<{ pairs: OdPair[] }>("/dashboard/od-pairs"),
  demandOpportunities: () => getJSON<{ opportunities: DemandOpportunity[] }>("/dashboard/demand-opportunities"),
  forecastOpportunities: () => getJSON<{ opportunities: ForecastOpportunity[] }>("/dashboard/forecast-opportunities"),
}

export interface ChatMessage {
  role: "user" | "assistant"
  content: string
}

export interface ToolCallTrace {
  tool: string
  arguments: Record<string, unknown>
  result: Record<string, unknown>
}

export interface ChatResponse {
  type: "answer" | "clarification" | "unsupported"
  message: string
  tool_calls: ToolCallTrace[]
}

export async function sendChat(question: string, history: ChatMessage[]): Promise<ChatResponse> {
  const res = await fetch("/api/assistant/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, history }),
  })
  if (!res.ok) throw new Error(`chat failed: ${res.status}`)
  return res.json()
}

import { useEffect, useRef, useState } from "react"
import { sendChat, type ChatMessage } from "../api/client"

const SUGGESTIONS = [
  "Where should we position taxis tomorrow evening?",
  "Which zones have the highest demand?",
  "Why did you recommend that zone?",
  "What is the busiest zone?",
  "How was trip duration calculated?",
]

const HEADERS = ["ANSWER", "EVIDENCE", "REASONING", "RECOMMENDED ACTION", "LIMITATIONS"]

function parseStructured(text: string) {
  const found = HEADERS.filter((h) => new RegExp(`(^|\\n)${h}\\b`, "i").test(text))
  if (found.length < 2) return null
  const pattern = new RegExp(`(?:^|\\n)(${HEADERS.join("|")})\\s*\\n`, "gi")
  const indices: { header: string; matchStart: number; bodyStart: number }[] = []
  let match: RegExpExecArray | null
  while ((match = pattern.exec(text))) {
    indices.push({ header: match[1].toUpperCase(), matchStart: match.index, bodyStart: match.index + match[0].length })
  }
  const parts: { header: string; body: string }[] = []
  for (let i = 0; i < indices.length; i++) {
    const end = i + 1 < indices.length ? indices[i + 1].matchStart : text.length
    parts.push({ header: indices[i].header, body: text.slice(indices[i].bodyStart, end).trim() })
  }
  return parts.length ? parts : null
}

function StructuredAnswer({ text }: { text: string }) {
  const parts = parseStructured(text)
  if (!parts) return <p className="whitespace-pre-wrap text-sm text-white/85">{text}</p>

  const styleFor = (header: string) => {
    if (header === "ANSWER") return "text-white text-sm font-medium"
    if (header === "RECOMMENDED ACTION") return "text-taxi-300 text-sm"
    if (header === "LIMITATIONS") return "text-white/45 text-xs"
    return "text-white/75 text-sm"
  }

  return (
    <div className="space-y-2.5">
      {parts.map((p) => (
        <div key={p.header}>
          <div className="mb-0.5 text-[10px] font-semibold uppercase tracking-wider text-white/35">{p.header}</div>
          <div className={`whitespace-pre-wrap ${styleFor(p.header)}`}>{p.body}</div>
        </div>
      ))}
    </div>
  )
}

interface Turn {
  role: "user" | "assistant"
  content: string
  kind?: "answer" | "clarification" | "unsupported" | "error"
}

export default function ChatPanel() {
  const [turns, setTurns] = useState<Turn[]>([])
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" })
  }, [turns, loading])

  async function ask(question: string) {
    if (!question.trim() || loading) return
    const history: ChatMessage[] = turns.map((t) => ({ role: t.role, content: t.content }))
    setTurns((t) => [...t, { role: "user", content: question }])
    setInput("")
    setLoading(true)
    try {
      const res = await sendChat(question, history)
      setTurns((t) => [...t, { role: "assistant", content: res.message, kind: res.type }])
    } catch (e) {
      setTurns((t) => [
        ...t,
        { role: "assistant", kind: "error", content: "Could not reach the assistant backend. Is the API server running?" },
      ])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="glass flex h-full flex-col rounded-2xl p-4 sm:p-5">
      <div className="mb-3 flex items-center gap-2">
        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-taxi-500/30 to-signal-500/20">
          <svg className="h-4 w-4 text-taxi-400" viewBox="0 0 24 24" fill="none">
            <path d="M12 2a4 4 0 014 4v1h1a2 2 0 012 2v9a2 2 0 01-2 2H7a2 2 0 01-2-2v-9a2 2 0 012-2h1V6a4 4 0 014-4z" stroke="currentColor" strokeWidth="1.6" />
          </svg>
        </div>
        <div>
          <div className="font-display text-sm font-semibold text-white">Mobility Assistant</div>
          <div className="text-[11px] text-white/40">Evidence-grounded &middot; 6 analytical tools</div>
        </div>
      </div>

      <div ref={scrollRef} className="scroll-glass min-h-0 flex-1 space-y-3 overflow-y-auto pr-1">
        {turns.length === 0 && (
          <div className="flex h-full items-center justify-center px-4 text-center text-sm text-white/35">
            Ask a question, or tap a suggestion below to get started.
          </div>
        )}
        {turns.map((t, i) => (
          <div key={i} className={`flex ${t.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-[92%] rounded-2xl px-3.5 py-3 text-sm ${
                t.role === "user"
                  ? "bg-taxi-500/15 text-white"
                  : t.kind === "error"
                    ? "bg-rose-500/10 text-rose-300"
                    : "bg-white/[0.04] border border-white/5"
              }`}
            >
              {t.role === "assistant" && t.kind !== "error" ? <StructuredAnswer text={t.content} /> : t.content}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="flex items-center gap-1.5 rounded-2xl border border-white/5 bg-white/[0.04] px-4 py-3">
              <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-white/50 [animation-delay:-0.3s]" />
              <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-white/50 [animation-delay:-0.15s]" />
              <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-white/50" />
            </div>
          </div>
        )}
      </div>

      <div className="mt-3 flex flex-wrap gap-1.5">
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            onClick={() => ask(s)}
            className="rounded-full border border-white/8 bg-white/[0.03] px-2.5 py-1 text-[11px] text-white/55 transition-colors hover:border-taxi-500/40 hover:text-white"
          >
            {s}
          </button>
        ))}
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault()
          ask(input)
        }}
        className="mt-3 flex items-center gap-2"
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about demand, forecasts, zones…"
          className="min-w-0 flex-1 rounded-full border border-white/8 bg-white/[0.03] px-4 py-2.5 text-sm text-white placeholder:text-white/30 focus:border-taxi-500/50 focus:outline-none"
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="flex h-10 w-10 flex-none items-center justify-center rounded-full bg-taxi-500 text-ink-950 transition-transform hover:scale-105 disabled:opacity-30 disabled:hover:scale-100"
        >
          <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none">
            <path d="M5 12h14M13 6l6 6-6 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </button>
      </form>
    </div>
  )
}

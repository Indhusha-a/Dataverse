# UrbanFlow — Track 5 (AI Mobility Assistant) + Track 6 (Management Dashboard)

Built on top of the completed Parts 1-4 work in the project root (`../src`, `../models`, `../outputs`,
`../reports`) — this directory never modifies anything outside itself. It reads the root project's
outputs to generate an evidence layer and knowledge base, then serves them through a FastAPI backend
and a React dashboard/assistant frontend.

## Layout

```
Dataverse_AI/
├── backend/
│   ├── app/          # FastAPI app: 6 tools, router, RAG, dashboard/assistant endpoints
│   ├── data/          # generated: analytics_contract.json, evidence/*.json, knowledge/*.md
│   ├── scripts/        # build_analytics_contract.py, build_evidence.py
│   └── tests/          # the 7 required assistant test scenarios
├── frontend/            # React + Vite + TS + Tailwind + react-three-fiber
├── .env                 # GEMINI_API_KEY (gitignored, never committed)
└── .env.example
```

## Prerequisites

- The shared project venv at `../.venv` with `../requirements.txt` installed (includes `fastapi`,
  `uvicorn`, `python-dotenv`, `google-genai` on top of the Parts 1-4 dependencies).
- Node.js (v20+) for the frontend.
- `../processed/*.parquet` must already exist (output of `python -m src.cleaning` at the project root)
  — the evidence-generation script reads from it.

## 1. Generate the evidence layer + analytics contract (one-time, re-run if Parts 1-4 outputs change)

```bash
cd Dataverse_AI/backend
../../.venv/Scripts/python.exe -m scripts.build_analytics_contract
../../.venv/Scripts/python.exe -m scripts.build_evidence
```

This writes `backend/data/analytics_contract.json` and `backend/data/evidence/*.json`, computed
directly from `../outputs/tables/*`, `../outputs/forecasts/*`, and one pass over `../processed/*.parquet`
for top-line KPIs. Nothing is hardcoded.

## 2. Run the backend

```bash
cd Dataverse_AI/backend
../../.venv/Scripts/python.exe -m uvicorn app.main:app --port 8000
```

Health check: `curl http://127.0.0.1:8000/api/health`

## 3. Run the frontend

```bash
cd Dataverse_AI/frontend
npm install
npm run dev
```

Opens on `http://localhost:5173`. `/` is the landing page (3D taxi), `/#/dashboard` is the command
center. Vite proxies `/api/*` to the backend on port 8000 (see `vite.config.ts`).

## 4. Run the backend test suite

```bash
cd Dataverse_AI/backend
../../.venv/Scripts/python.exe tests/test_assistant_scenarios.py
```

Covers all 7 required scenarios. The ambiguity/malformed-question tests (Tests 4 & 5) and every tool's
output-matches-evidence check (feeding Tests 1, 2, 3, 7) run without needing the Gemini API. The final
natural-language synthesis step (turning tool results into the ANSWER/EVIDENCE/REASONING/RECOMMENDED
ACTION/LIMITATIONS response) requires a working `GEMINI_API_KEY` in `.env` — verified working live as of
this build (model: `gemini-flash-latest`), including a full tool-calling round trip and follow-up
questions using conversation history.

## The 6 tools (Track 5)

`query_kpi`, `query_demand`, `forecast_demand`, `query_spatial_od`, `retrieve_knowledge`,
`build_recommendation` — see `backend/app/tools/`. The model can only call these 6 typed functions; there
is no code/SQL execution tool exposed at all, which is the entire safety boundary.

## Business problem (Track 6)

**Demand-Fleet Imbalance and Revenue Opportunity**: where and when should the taxi company position its
fleet to capture upcoming demand while reducing under-utilization? Answered via the forecast-vs-baseline
uplift ranking (`backend/data/evidence/forecast_opportunities.json`), generated from
`../outputs/forecasts/demand_forecast_72h.csv` and `../outputs/forecasts/demand_test_predictions.csv`.

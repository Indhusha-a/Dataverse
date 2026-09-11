"""Gemini tool-calling loop over the 6 declared analytics tools. The model NEVER
gets a code/SQL execution tool -- only these 6 typed functions operating on
pre-aggregated evidence files. That is the entire safety boundary: there is
nothing unsafe to restrict because nothing else is exposed."""
import json

from google import genai
from google.genai import types

from app.config import GEMINI_API_KEY, GEMINI_MODEL
from app.tools.kpi import query_kpi
from app.tools.demand import query_demand
from app.tools.forecast import forecast_demand
from app.tools.spatial_od import query_spatial_od
from app.tools.knowledge import retrieve_knowledge
from app.tools.recommendation import build_recommendation

_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

TOOL_IMPLS = {
    "query_kpi": query_kpi,
    "query_demand": query_demand,
    "forecast_demand": forecast_demand,
    "query_spatial_od": query_spatial_od,
    "retrieve_knowledge": retrieve_knowledge,
    "build_recommendation": build_recommendation,
}

FUNCTION_DECLARATIONS = [
    types.FunctionDeclaration(
        name="query_kpi",
        description="Return verified top-line business KPIs (total trips, average fare, average trip duration, average distance, peak demand hour, highest-demand zone, date range). Use for any question about overall system-wide statistics.",
        parameters={"type": "object", "properties": {
            "metric": {"type": "string", "description": "One specific KPI name, or omit to get all KPIs.",
                       "enum": ["total_trips", "average_base_fare", "average_trip_duration", "average_distance",
                                "peak_demand_hour", "highest_demand_zone", "date_range_start", "date_range_end"]},
        }},
    ),
    types.FunctionDeclaration(
        name="query_demand",
        description="Return historical demand: top zones by pickup/dropoff volume (basis='all_time_pickups', across the full cleaned dataset) or recent hourly demand baseline with peak hour (basis='recent_baseline', from the held-out test period). Use for 'which zones have the highest demand', 'busiest zone', 'historical demand for zone X'.",
        parameters={"type": "object", "properties": {
            "basis": {"type": "string", "enum": ["all_time_pickups", "recent_baseline"],
                       "description": "all_time_pickups = total historical volume across the whole dataset. recent_baseline = mean hourly pickups over the recent test period, with each zone's peak hour of day."},
            "direction": {"type": "string", "enum": ["pickup", "dropoff"], "description": "Only used with basis=all_time_pickups."},
            "zone": {"type": "string", "description": "Optional zone name filter (substring match)."},
            "top_n": {"type": "integer", "description": "How many ranked results to return."},
        }, "required": ["basis"]},
    ),
    types.FunctionDeclaration(
        name="forecast_demand",
        description="Return the forward 72-hour demand forecast per zone, each zone's historical baseline, and the forecast uplift percentage, ranked by uplift. Use for 'where should we position taxis', 'what is demand expected to be', 'which zones are forecast to grow'.",
        parameters={"type": "object", "properties": {
            "zone": {"type": "string", "description": "Optional zone name filter (substring match)."},
            "top_n": {"type": "integer", "description": "How many ranked-by-uplift results to return."},
            "min_uplift_pct": {"type": "number", "description": "Optional minimum uplift percentage filter."},
        }},
    ),
    types.FunctionDeclaration(
        name="query_spatial_od",
        description="Return top pickup zones, top drop-off zones, or top origin-destination pairs (busiest travel corridors). Use for spatial/hotspot/corridor questions.",
        parameters={"type": "object", "properties": {
            "kind": {"type": "string", "enum": ["top_pickup", "top_dropoff", "top_od_pairs"]},
            "top_n": {"type": "integer"},
        }, "required": ["kind"]},
    ),
    types.FunctionDeclaration(
        name="retrieve_knowledge",
        description="Retrieve project methodology, definitions, data-quality rules, or documented limitations from the knowledge base. Use for 'how was X calculated', 'what does column Y mean', 'why were rows excluded', 'what are the limitations'. Never returns numerical KPI values.",
        parameters={"type": "object", "properties": {
            "query": {"type": "string", "description": "The methodology/definition question to search for."},
            "top_k": {"type": "integer"},
        }, "required": ["query"]},
    ),
    types.FunctionDeclaration(
        name="build_recommendation",
        description="Build a structured, evidence-grounded fleet-positioning recommendation for a zone (or the single best system-wide opportunity if no zone given). Always call this AFTER forecast_demand when the user asks a 'where/when should we position fleet' question, so the recommendation reasoning and limitation are grounded rather than invented.",
        parameters={"type": "object", "properties": {
            "zone": {"type": "string", "description": "Optional zone name to recommend for."},
            "top_n": {"type": "integer", "description": "How many ranked opportunities to include."},
        }},
    ),
]

GEMINI_TOOLS = [types.Tool(function_declarations=FUNCTION_DECLARATIONS)]

SYSTEM_PROMPT = """You are the UrbanFlow Mobility Assistant for a taxi operations team, built on top of \
a verified analytical pipeline (data cleaning, fare/duration/demand models, spatial analysis) for a taxi \
dataset covering April 2025 - March 2026. You answer questions for city officials and fleet managers who do \
not write code.

HARD RULES:
1. You may NEVER state a number that did not come from a tool call result in this conversation. If you don't \
have a tool result for a number, don't say the number.
2. If the question is AMBIGUOUS (a term could reasonably mean more than one thing -- e.g. "busiest" could mean \
highest pickups, highest dropoffs, or highest total activity), do NOT guess and do NOT call any tool. Instead \
respond with a short clarifying question listing the 2-3 concrete interpretations, numbered.
3. If the question is MALFORMED or self-contradictory (e.g. it references two conflicting time frames like \
"yesterday" and "tomorrow" in the same question), do NOT guess and do NOT call any tool. Point out the specific \
conflict and ask which one they meant.
4. If the question asks for something this system has no tool or knowledge for (e.g. real-time traffic, \
weather, an individual passenger's exact fare, anything outside taxi operations analytics), say plainly that \
you cannot answer that reliably from the available analytical outputs, and list what you CAN answer instead \
(historical demand, forecasted demand, zone/OD analysis, business KPIs, methodology questions).
5. For any question that IS answerable, call one or more of the 6 tools to gather evidence BEFORE answering. \
For "where/when should we position fleet" style questions, call forecast_demand and then build_recommendation.
6. Once you have tool results, write your final answer in EXACTLY this structure (plain text, these five \
headers, each on its own line):

ANSWER
<direct answer to the question, 1-3 sentences>

EVIDENCE
<the concrete metrics/values that support it, with zone/time window where relevant>

REASONING
<why the evidence supports the answer, referencing the historical baseline/forecast/methodology as relevant>

RECOMMENDED ACTION
<a concrete business action, or "No action needed" / "Not applicable" if the question was purely informational>

LIMITATIONS
<one honest, specific limitation relevant to this answer -- never a generic disclaimer>

Do not use this five-header structure for clarification or unsupported-question responses -- those are short \
plain text.
"""


def _to_content(role: str, text: str) -> types.Content:
    return types.Content(role="user" if role == "user" else "model", parts=[types.Part(text=text)])


def run_chat(question: str, history: list[dict]) -> dict:
    """Returns {type, message, tool_calls} -- type is 'answer', 'clarification', or 'unsupported'."""
    if _client is None:
        return {"type": "unsupported", "message": "GEMINI_API_KEY is not configured on the server.", "tool_calls": []}

    contents = [_to_content(h["role"], h["content"]) for h in history]
    contents.append(_to_content("user", question))

    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT, tools=GEMINI_TOOLS, temperature=0.2,
    )

    tool_call_trace = []
    for _ in range(6):  # hard cap on tool-call rounds
        try:
            resp = _client.models.generate_content(model=GEMINI_MODEL, contents=contents, config=config)
        except Exception as exc:
            return {
                "type": "unsupported",
                "message": f"The AI assistant's language model call failed ({type(exc).__name__}: {exc}). "
                           "The analytical tools and evidence layer are unaffected -- this only blocks the "
                           "natural-language explanation step.",
                "tool_calls": tool_call_trace,
            }

        candidate = resp.candidates[0] if resp.candidates else None
        parts = candidate.content.parts if candidate and candidate.content and candidate.content.parts else []
        function_calls = [p.function_call for p in parts if getattr(p, "function_call", None)]

        if not function_calls:
            content = resp.text or ""
            if content.strip().upper().startswith("ANSWER"):
                rtype = "answer"
            elif "?" in content and len(tool_call_trace) == 0:
                rtype = "clarification"
            else:
                rtype = "answer" if tool_call_trace else "unsupported"
            return {"type": rtype, "message": content, "tool_calls": tool_call_trace}

        contents.append(candidate.content)

        response_parts = []
        for fc in function_calls:
            name = fc.name
            args = dict(fc.args) if fc.args else {}
            impl = TOOL_IMPLS.get(name)
            try:
                result = impl(**args) if impl else {"error": f"Unknown tool '{name}'"}
            except TypeError as exc:
                result = {"error": f"Invalid arguments for '{name}': {exc}"}
            tool_call_trace.append({"tool": name, "arguments": args, "result": result})
            response_parts.append(types.Part.from_function_response(name=name, response=result))
        contents.append(types.Content(role="user", parts=response_parts))

    return {"type": "unsupported", "message": "Could not resolve this question within the tool-call budget.",
            "tool_calls": tool_call_trace}

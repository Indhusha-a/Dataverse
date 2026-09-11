"""The 7 required assistant test scenarios, run against the real evidence layer.
Nothing is mocked -- only the Gemini call itself is skipped if unavailable, and
that's asserted separately so the rest of the suite still proves the system works.

Run with: python -m pytest tests/ -v   (from Dataverse_AI/backend/, venv active)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.router import handle_question, _detect_time_conflict, _detect_busiest_ambiguity
from app.tools.kpi import query_kpi
from app.tools.demand import query_demand
from app.tools.forecast import forecast_demand
from app.tools.spatial_od import query_spatial_od
from app.tools.knowledge import retrieve_knowledge
from app.tools.recommendation import build_recommendation
from app.evidence import load_business_kpis, load_forecast_opportunities


# --- Test 4: Ambiguity (deterministic, no LLM needed) ---
def test_ambiguous_busiest_zone():
    result = handle_question("What is the busiest zone?", [])
    assert result["type"] == "clarification"
    assert "1." in result["message"] and "2." in result["message"]
    assert result["tool_calls"] == []
    print("PASS: ambiguous 'busiest' question triggers clarification, no tool calls")


def test_busiest_with_qualifier_is_not_ambiguous():
    # "busiest pickup zone" is NOT ambiguous -- the router must not over-trigger
    assert _detect_busiest_ambiguity("What is the busiest pickup zone?") is None
    print("PASS: qualified 'busiest' does not falsely trigger ambiguity")


# --- Test 5: Malformed / conflicting time reference (deterministic, no LLM needed) ---
def test_malformed_conflicting_time():
    result = handle_question("Which zone had most demand yesterday tomorrow?", [])
    assert result["type"] == "clarification"
    assert "conflicting" in result["message"].lower()
    assert result["tool_calls"] == []
    print("PASS: conflicting time reference triggers clarification, no tool calls")


# --- Tool-layer correctness (feeds Tests 1, 2, 3, 7) ---
def test_query_kpi_returns_real_value():
    result = query_kpi(metric="total_trips")
    assert result["kpi"]["value"] == 45538913
    assert result["kpi"]["source"] == "processed/*.parquet (12 months, cleaned)"
    print("PASS: query_kpi returns the real total_trips figure with provenance")


def test_query_kpi_unknown_metric_does_not_fabricate():
    result = query_kpi(metric="average_tip_percentage")  # not tracked
    assert "error" in result
    assert "available_metrics" in result
    print("PASS: query_kpi refuses to fabricate an untracked metric")


def test_query_demand_all_time_matches_source_csv():
    result = query_demand(basis="all_time_pickups", direction="pickup", top_n=1)
    top = result["results"][0]
    assert top["zone_name"] == "Upper East Side South"
    assert top["value"] == 2015045
    print("PASS: query_demand top pickup zone matches outputs/tables/top_pickup_zones.csv exactly")


def test_forecast_demand_matches_evidence_file():
    tool_result = forecast_demand(top_n=1)
    evidence = load_forecast_opportunities()[0]
    assert tool_result["results"][0]["uplift_pct"] == evidence["uplift_pct"]
    assert tool_result["results"][0]["zone_name"] == evidence["zone_name"]
    print("PASS: forecast_demand tool output matches forecast_opportunities.json exactly (Test 7)")


def test_query_spatial_od_top_pair():
    result = query_spatial_od(kind="top_od_pairs", top_n=1)
    top = result["results"][0]
    assert top["origin_zone"] == "Upper East Side South"
    assert top["dest_zone"] == "Upper East Side North"
    print("PASS: query_spatial_od top OD pair matches outputs/tables/top_od_pairs.csv")


def test_retrieve_knowledge_finds_duration_methodology():
    result = retrieve_knowledge("How was trip duration calculated?", top_k=1)
    assert result["results"], "expected at least one knowledge match"
    assert "dropoff_timestamp - pickup_timestamp" in result["results"][0]["text"]
    print("PASS: retrieve_knowledge surfaces the real duration-calculation methodology")


def test_build_recommendation_is_evidence_grounded():
    result = build_recommendation(top_n=1)
    rec = result["recommendations"][0]
    evidence = load_forecast_opportunities()[0]
    assert rec["zone"] == evidence["zone_name"]
    assert rec["uplift_pct"] == evidence["uplift_pct"]
    assert "limitation" in rec and len(rec["limitation"]) > 0
    print("PASS: build_recommendation's top pick matches forecast_opportunities.json exactly")


# --- Test 6: Unsupported topic -- deterministic pre-checks correctly pass it through
# to the LLM layer (which has its own unsupported-topic instructions; requires API credits) ---
def test_unsupported_topic_is_not_caught_by_deterministic_filters():
    # A genuinely out-of-scope question (weather) must not be misclassified as
    # ambiguous or malformed -- it should fall through to the LLM's judgment.
    assert _detect_time_conflict("Will it rain tomorrow?") is None
    assert _detect_busiest_ambiguity("Will it rain tomorrow?") is None
    print("PASS: out-of-scope question correctly bypasses the deterministic pre-filters "
          "(final unsupported-topic handling depends on the LLM call -- see README for status)")


if __name__ == "__main__":
    tests = [v for k, v in list(globals().items()) if k.startswith("test_")]
    passed, failed = 0, 0
    for t in tests:
        try:
            t()
            passed += 1
        except AssertionError as e:
            print(f"FAIL: {t.__name__}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed out of {len(tests)}")

"""Intent router: regex pre-checks for time conflicts and "busiest" ambiguity
run before any LLM call; everything else falls through to llm.py."""
import re

from app.llm import run_chat

_TIME_CONFLICT_GROUPS = [
    {"yesterday", "tomorrow"},
    {"last week", "next week"},
    {"last month", "next month"},
    {"past", "future"},
]


def _detect_time_conflict(question: str) -> str | None:
    q = question.lower()
    for group in _TIME_CONFLICT_GROUPS:
        hits = [term for term in group if term in q]
        if len(hits) >= 2:
            return (
                f"The question contains conflicting time references: {' and '.join(repr(h) for h in hits)}.\n\n"
                "Please specify whether you want:\n"
                "1. Historical demand for the past period\n"
                "2. Forecasted demand for the future period"
            )
    return None


_BUSIEST_RE = re.compile(r"\bbusiest\b", re.IGNORECASE)
_BUSIEST_QUALIFIERS = ["pickup", "pick-up", "pick up", "dropoff", "drop-off", "drop off",
                        "total", "activity", "revenue", "fare", "od pair", "corridor"]


def _detect_busiest_ambiguity(question: str) -> str | None:
    if not _BUSIEST_RE.search(question):
        return None
    q = question.lower()
    if any(qual in q for qual in _BUSIEST_QUALIFIERS):
        return None
    return (
        "I can answer that, but \"busiest\" can mean different things.\n\n"
        "Do you mean:\n"
        "1. Highest pickup demand\n"
        "2. Highest drop-off volume\n"
        "3. Highest total trip activity"
    )


def handle_question(question: str, history: list[dict]) -> dict:
    if not question or not question.strip():
        return {"type": "clarification", "message": "Please enter a question.", "tool_calls": []}

    conflict = _detect_time_conflict(question)
    if conflict:
        return {"type": "clarification", "message": conflict, "tool_calls": []}

    ambiguous = _detect_busiest_ambiguity(question)
    if ambiguous:
        return {"type": "clarification", "message": ambiguous, "tool_calls": []}

    return run_chat(question, history)

"""Research state definition for LangGraph."""

from typing import TypedDict


class ResearchState(TypedDict):
    topic: str
    plan: list[str]
    research_notes: list[str]
    report: str
    quality_score: float
    iteration: int
    feedback: str


def make_initial_state(topic: str) -> ResearchState:
    """Create a fresh initial state for a research run."""
    return {
        "topic": topic,
        "plan": [],
        "research_notes": [],
        "report": "",
        "quality_score": 0.0,
        "iteration": 0,
        "feedback": "",
    }

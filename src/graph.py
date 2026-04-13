"""LangGraph StateGraph assembly and compilation."""

import os
import sqlite3

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, StateGraph

from .nodes import planner, researcher, reviewer, writer
from .state import ResearchState

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "checkpoints.db")

QUALITY_THRESHOLD = 7
MAX_ITERATIONS = 2


def should_continue(state: dict) -> str:
    """Route to END if quality is sufficient or max iterations reached."""
    if state.get("quality_score", 0) >= QUALITY_THRESHOLD:
        return "end"
    if state.get("iteration", 0) >= MAX_ITERATIONS:
        return "end"
    return "revise"


def build_graph() -> StateGraph:
    """Build the research state graph (uncompiled)."""
    graph = StateGraph(ResearchState)

    graph.add_node("planner", planner)
    graph.add_node("researcher", researcher)
    graph.add_node("writer", writer)
    graph.add_node("reviewer", reviewer)

    graph.set_entry_point("planner")
    graph.add_edge("planner", "researcher")
    graph.add_edge("researcher", "writer")
    graph.add_edge("writer", "reviewer")
    graph.add_conditional_edges(
        "reviewer",
        should_continue,
        {"revise": "planner", "end": END},
    )

    return graph


def get_app(checkpointer=None):
    """Compile the graph with optional checkpointer."""
    graph = build_graph()
    return graph.compile(checkpointer=checkpointer)


def get_checkpointer():
    """Create a SQLite checkpointer."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    return SqliteSaver(conn)


def get_mermaid() -> str:
    """Return the Mermaid diagram of the graph."""
    graph = build_graph()
    return graph.compile().get_graph().draw_mermaid()

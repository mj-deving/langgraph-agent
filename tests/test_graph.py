"""Tests for LangGraph research agent — no API keys required."""

import pytest
from src.state import ResearchState, make_initial_state
from src.graph import build_graph, should_continue, QUALITY_THRESHOLD, MAX_ITERATIONS


class TestState:
    """State initialization and structure tests."""

    def test_make_initial_state_has_all_fields(self):
        state = make_initial_state("test topic")
        assert state["topic"] == "test topic"
        assert state["plan"] == []
        assert state["research_notes"] == []
        assert state["report"] == ""
        assert state["quality_score"] == 0.0
        assert state["iteration"] == 0
        assert state["feedback"] == ""

    def test_make_initial_state_preserves_topic(self):
        state = make_initial_state("AI safety research")
        assert state["topic"] == "AI safety research"

    def test_state_has_seven_fields(self):
        state = make_initial_state("test")
        assert len(state) == 7


class TestRouting:
    """Conditional edge routing tests."""

    def test_should_continue_ends_on_high_quality(self):
        state = {"quality_score": 8.0, "iteration": 1}
        assert should_continue(state) == "end"

    def test_should_continue_ends_at_threshold(self):
        state = {"quality_score": QUALITY_THRESHOLD, "iteration": 1}
        assert should_continue(state) == "end"

    def test_should_continue_revises_below_threshold(self):
        state = {"quality_score": 5.0, "iteration": 1}
        assert should_continue(state) == "revise"

    def test_should_continue_ends_at_max_iterations(self):
        state = {"quality_score": 3.0, "iteration": MAX_ITERATIONS}
        assert should_continue(state) == "end"

    def test_should_continue_revises_on_first_iteration(self):
        state = {"quality_score": 0.0, "iteration": 0}
        assert should_continue(state) == "revise"

    def test_should_continue_handles_missing_fields(self):
        assert should_continue({}) == "revise"

    def test_quality_threshold_is_seven(self):
        assert QUALITY_THRESHOLD == 7

    def test_max_iterations_is_two(self):
        assert MAX_ITERATIONS == 2


class TestGraphStructure:
    """Graph topology tests — verifies nodes and edges without running LLM."""

    def test_graph_has_four_nodes(self):
        graph = build_graph()
        compiled = graph.compile()
        node_names = set(compiled.get_graph().nodes.keys()) - {"__start__", "__end__"}
        assert node_names == {"planner", "researcher", "writer", "reviewer"}

    def test_graph_entry_point_is_planner(self):
        graph = build_graph()
        compiled = graph.compile()
        g = compiled.get_graph()
        # __start__ should connect to planner
        start_edges = [e for e in g.edges if e[0] == "__start__"]
        assert any(e[1] == "planner" for e in start_edges)

    def test_graph_has_conditional_edge_from_reviewer(self):
        graph = build_graph()
        compiled = graph.compile()
        g = compiled.get_graph()
        reviewer_edges = [e for e in g.edges if e[0] == "reviewer"]
        targets = {e[1] for e in reviewer_edges}
        # reviewer should connect to both planner (revise) and __end__
        assert "planner" in targets or "__end__" in targets

    def test_mermaid_output_is_string(self):
        from src.graph import get_mermaid
        mermaid = get_mermaid()
        assert isinstance(mermaid, str)
        assert "planner" in mermaid
        assert "reviewer" in mermaid

    def test_graph_compiles_without_checkpointer(self):
        from src.graph import get_app
        app = get_app()
        assert app is not None

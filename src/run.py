"""CLI runner for the research graph."""

import sys
import time

from dotenv import load_dotenv

load_dotenv()

from .graph import MAX_ITERATIONS, QUALITY_THRESHOLD, get_app, get_checkpointer
from .state import make_initial_state


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m src.run <topic>")
        sys.exit(1)

    topic = " ".join(sys.argv[1:])
    print(f"\n{'='*60}")
    print(f"  Research Topic: {topic}")
    print(f"{'='*60}\n")

    checkpointer = get_checkpointer()
    app = get_app(checkpointer=checkpointer)

    initial_state = make_initial_state(topic)

    config = {"configurable": {"thread_id": f"cli-{int(time.time())}"}}

    start = time.time()
    print("Starting research pipeline...\n")

    for event in app.stream(initial_state, config=config):
        for node_name, node_output in event.items():
            print(f"[{node_name}] completed")
            if node_name == "planner":
                plan = node_output.get("plan", [])
                for i, step in enumerate(plan, 1):
                    print(f"  {i}. {step}")
            elif node_name == "researcher":
                notes = node_output.get("research_notes", [])
                print(f"  Collected {len(notes)} research notes")
            elif node_name == "reviewer":
                score = node_output.get("quality_score", 0)
                iteration = node_output.get("iteration", 0)
                print(f"  Score: {score}/10")
                if score < QUALITY_THRESHOLD and iteration < MAX_ITERATIONS:
                    print("  → Revising (score below 7)...")
                else:
                    print("  → Complete!")
        print()

    duration = time.time() - start

    # Get final state
    final_state = app.get_state(config).values

    print(f"\n{'='*60}")
    print(f"  RESULTS")
    print(f"{'='*60}")
    print(f"  Duration:   {duration:.1f}s")
    print(f"  Iterations: {final_state.get('iteration', 0)}")
    print(f"  Score:      {final_state.get('quality_score', 0)}/10")
    print(f"{'='*60}\n")
    print(final_state.get("report", "No report generated."))


if __name__ == "__main__":
    main()

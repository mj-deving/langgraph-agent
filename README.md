# P7: LangGraph Multi-Agent Research System

A Multi-Agent Research System built with **LangGraph** demonstrating State Machines, Tool Use, Streaming, and Persistence. Takes a research topic, plans research steps, searches the web, writes a structured report, and reviews quality — looping until the report meets a quality threshold.

## Architecture

```mermaid
graph TD;
	__start__([__start__]):::first
	planner(planner)
	researcher(researcher)
	writer(writer)
	reviewer(reviewer)
	__end__([__end__]):::last
	__start__ --> planner;
	planner --> researcher;
	researcher --> writer;
	writer --> reviewer;
	reviewer -. end .-> __end__;
	reviewer -. revise .-> planner;
	classDef default fill:#f2f0ff,line-height:1.2
	classDef first fill-opacity:0
	classDef last fill:#bfb6fc
```

### Pipeline

1. **Planner** — Generates 3-5 specific research questions from the topic
2. **Researcher** — Executes web searches via Tavily for each question, collects sources
3. **Writer** — Synthesizes all research notes into a structured report (Executive Summary, Key Findings, Sources, Conclusions)
4. **Reviewer** — Scores the report 0-10 with feedback. If score < 7 and iteration < 2, loops back to Planner

## Tech Stack

| Component | Tool | Why |
|---|---|---|
| Agent Framework | **LangGraph** | State Machines, Conditional Edges, Persistence |
| LLM | **Claude Sonnet 4** (via OpenRouter) | Consistent with portfolio projects |
| Web Search | **Tavily** | LangChain-native, good quality, Free Tier |
| API Layer | **FastAPI** | Async, SSE-Support, Swagger UI |
| Persistence | **SQLite** (LangGraph Checkpointer) | Zero-Config, file-based |

## Setup

```bash
# 1. Clone and create venv
cd ~/projects/langgraph-agent
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure API keys
cp .env.example .env
# Edit .env with your keys:
#   OPENROUTER_API_KEY=sk-or-...
#   TAVILY_API_KEY=tvly-...

# 4. Run CLI
python -m src.run "State of AI Coding Agents 2026"

# 5. Run API
uvicorn src.api:app --reload
# Open http://localhost:8000/docs for Swagger UI
```

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/research` | Start research, returns `{id, status}` |
| GET | `/research/{id}` | Status + result (when complete) |
| GET | `/research/{id}/stream` | SSE stream of node transitions |
| GET | `/health` | Health check |
| GET | `/graph` | Mermaid diagram of the graph |

### Example

```bash
# Start research
curl -X POST http://localhost:8000/research \
  -H "Content-Type: application/json" \
  -d '{"topic": "RAG Architekturen 2026"}'
# → {"id": "abc123", "status": "running"}

# Check status
curl http://localhost:8000/research/abc123
# → {"id": "abc123", "topic": "...", "status": "completed", "result": {...}}

# Stream events
curl -N http://localhost:8000/research/abc123/stream
# → event: node_transition
# → data: {"node": "planner", "timestamp": 1776091987.6}
```

## Test Results

All 5 spec topics executed. 3/5 passed the quality gate (score >= 7) on first iteration.

| # | Topic | Score | Iterations | Duration |
|---|---|---|---|---|
| 1 | State of AI Coding Agents 2026 | 6.5/10 | 2 | 155s |
| 2 | LangGraph vs CrewAI vs Claude Agent SDK | 6.5/10 | 2 | 144s |
| 3 | DSGVO-konforme KI im deutschen Mittelstand | 7.2/10 | 1 | 98s |
| 4 | Voice AI Markt DACH 2026 | 4.5/10 | 2 | 153s |
| 5 | RAG Architekturen 2026 | 7.2/10 | 1 | 56s |

**Averages:** Score 5.4/10 | 1.6 iterations | 121s per run

## LangGraph Features Demonstrated

### 1. State Machine
- `StateGraph` with typed `ResearchState` (7 fields)
- Conditional edges (quality gate: score >= 7 → END, else → revise)
- Cycle: Reviewer → Planner (max 2 iterations)

### 2. Tool Use
- Tavily web search integrated as LangChain tool
- Results collected with URLs and content per research question

### 3. Streaming
- FastAPI SSE endpoint streams node transitions in real-time
- Client sees live progress: planner → researcher → writer → reviewer

### 4. Persistence
- SQLite Checkpointer saves state after each node
- API can retrieve results by job ID after completion

## Framework Comparison Matrix

| Feature | P3 (Claude SDK) | P7 (LangGraph) | P19 (CrewAI) |
|---|---|---|---|
| Framework | Claude Agent SDK | LangGraph | CrewAI |
| State Mgmt | Implicit (turns) | **Explicit (StateGraph)** | Implicit (context) |
| Cycles | Manual (prompt) | **Conditional Edges** | Flow @router |
| Persistence | None | **SQLite Checkpointer** | None (v1) |
| Streaming | SDK events | **Node transitions (SSE)** | None (v1) |
| Tool Use | WebSearch, WebFetch | Tavily, Custom | SerperDev, Scrape |
| Multi-Agent | Sub-agents via SDK | **Nodes in Graph** | Crews (YAML) |
| Async | SDK handles | **FastAPI + asyncio** | FastAPI + threads |
| Quality Gate | Manual | **Automatic (score-based loop)** | Manual |

**Why LangGraph here?** Explicit state management + conditional edges make the research loop transparent and debuggable. The graph is visible as Mermaid, state is inspectable at every node, and the quality gate is a first-class graph construct — not a prompt hack.

## Project Structure

```
src/
  state.py    — ResearchState TypedDict definition
  nodes.py    — 4 node functions (planner, researcher, writer, reviewer)
  graph.py    — StateGraph assembly, compilation, checkpointer
  api.py      — FastAPI endpoints with SSE streaming
  run.py      — CLI runner
```

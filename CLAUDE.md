# LangGraph Multi-Agent Research System

## Project
Portfolio project P7 — LangGraph-based research agent with state machine, web search, quality loop.

## Stack
- Python 3.12+, LangGraph (StateGraph), FastAPI, SQLite
- LLM: Claude Sonnet 4 via OpenRouter (langchain-openai ChatOpenAI)
- Search: Tavily (langchain-tavily TavilySearch)
- SSE: sse-starlette

## Key Architecture Decisions
- OpenRouter as LLM proxy (not direct Anthropic SDK)
- Lazy initialization of LLM and search tools (avoids import-time API key validation)
- Background task pattern for API research jobs (asyncio.create_task + run_in_executor)
- In-memory job registry (not SQLite) for API job tracking

## Commands
```bash
# CLI
python -m src.run "topic"

# API
uvicorn src.api:app --reload

# Graph visualization
python -c "from src.graph import get_mermaid; print(get_mermaid())"
```

## Environment
Requires `.env` with `OPENROUTER_API_KEY` and `TAVILY_API_KEY`.

## Constants
- QUALITY_THRESHOLD = 7 (in graph.py) — reviewer score needed to end loop
- MAX_ITERATIONS = 2 (in graph.py) — hard cap on revision loops
- OpenRouter model = "anthropic/claude-sonnet-4" (in nodes.py)
- Tavily max_results = 3 per search query

## Test Results (5 topics, 2026-04-13)
Avg score 5.4/10, avg 1.6 iterations, avg 121s. 3/5 passed quality gate on first try.

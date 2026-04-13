"""FastAPI endpoints for the research system."""

import asyncio
import json
import time
import uuid
from contextlib import asynccontextmanager

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from .graph import get_app, get_checkpointer, get_mermaid
from .state import make_initial_state

# In-memory job registry
jobs: dict[str, dict] = {}

checkpointer = None
app_graph = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global checkpointer, app_graph
    checkpointer = get_checkpointer()
    app_graph = get_app(checkpointer=checkpointer)
    yield


app = FastAPI(
    title="LangGraph Research Agent",
    description="Multi-Agent Research System with LangGraph",
    version="1.0.0",
    lifespan=lifespan,
)


class ResearchRequest(BaseModel):
    topic: str


class ResearchResponse(BaseModel):
    id: str
    status: str


@app.post("/research", response_model=ResearchResponse)
async def start_research(request: ResearchRequest):
    """Start a new research job."""
    job_id = str(uuid.uuid4())[:8]
    thread_id = f"api-{job_id}"

    jobs[job_id] = {
        "status": "running",
        "topic": request.topic,
        "thread_id": thread_id,
        "started": time.time(),
        "result": None,
        "events": [],
    }

    asyncio.create_task(_run_research(job_id, request.topic, thread_id))

    return ResearchResponse(id=job_id, status="running")


async def _run_research(job_id: str, topic: str, thread_id: str):
    """Run research in background."""
    try:
        initial_state = make_initial_state(topic)
        config = {"configurable": {"thread_id": thread_id}}

        loop = asyncio.get_running_loop()
        final_state = await loop.run_in_executor(
            None, lambda: _run_sync(initial_state, config, job_id)
        )

        jobs[job_id]["status"] = "completed"
        jobs[job_id]["result"] = {
            "report": final_state.get("report", ""),
            "quality_score": final_state.get("quality_score", 0),
            "iterations": final_state.get("iteration", 0),
            "duration": time.time() - jobs[job_id]["started"],
        }
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["result"] = {"error": str(e)}


def _run_sync(initial_state: dict, config: dict, job_id: str) -> dict:
    """Synchronous graph execution with event tracking."""
    for event in app_graph.stream(initial_state, config=config):
        for node_name in event:
            jobs[job_id]["events"].append(
                {"node": node_name, "timestamp": time.time()}
            )

    return app_graph.get_state(config).values


@app.get("/research/{job_id}")
async def get_research(job_id: str):
    """Get research status and result."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Research job not found")

    job = jobs[job_id]
    response = {
        "id": job_id,
        "topic": job["topic"],
        "status": job["status"],
    }

    if job["result"]:
        response["result"] = job["result"]

    return JSONResponse(content=response)


@app.get("/research/{job_id}/stream")
async def stream_research(job_id: str):
    """SSE stream of node transitions."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Research job not found")

    async def event_generator():
        seen = 0
        while True:
            job = jobs.get(job_id)
            if not job:
                break

            events = job["events"]
            while seen < len(events):
                evt = events[seen]
                yield {
                    "event": "node_transition",
                    "data": json.dumps({"node": evt["node"], "timestamp": evt["timestamp"]}),
                }
                seen += 1

            if job["status"] in ("completed", "failed"):
                yield {
                    "event": "done",
                    "data": json.dumps({"status": job["status"]}),
                }
                break

            await asyncio.sleep(0.5)

    return EventSourceResponse(event_generator())


@app.get("/health")
async def health():
    """Health check."""
    return {"status": "ok", "service": "langgraph-research-agent"}


@app.get("/graph")
async def graph_visualization():
    """Return Mermaid diagram of the graph."""
    mermaid = get_mermaid()
    return {"mermaid": mermaid}

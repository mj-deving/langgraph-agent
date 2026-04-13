"""Graph nodes: planner, researcher, writer, reviewer."""

import os
import re

from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch

MODEL = "anthropic/claude-sonnet-4"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

_llm = None
_search_tool = None


def _get_llm():
    global _llm
    if _llm is None:
        _llm = ChatOpenAI(
            model=MODEL,
            openai_api_key=os.environ["OPENROUTER_API_KEY"],
            openai_api_base=OPENROUTER_BASE_URL,
            max_tokens=4096,
        )
    return _llm


def _get_search_tool():
    global _search_tool
    if _search_tool is None:
        _search_tool = TavilySearch(max_results=3)
    return _search_tool


def planner(state: dict) -> dict:
    """Generate 3-5 research questions from the topic."""
    topic = state["topic"]
    iteration = state.get("iteration", 0)
    feedback = state.get("feedback", "")

    prompt = f"""You are a research planner. Create 3-5 specific research questions for the topic: "{topic}"

Each question should be concrete and searchable on the web.
Return ONLY the questions, one per line, numbered 1-5.
No preamble, no explanation."""

    if iteration > 0 and feedback:
        prompt += f"""

This is iteration {iteration + 1}. Previous feedback from the reviewer:
{feedback}

Adjust your research questions to address the gaps identified above."""

    response = _get_llm().invoke(prompt)
    lines = [
        line.strip()
        for line in response.content.strip().split("\n")
        if line.strip() and line.strip()[0].isdigit()
    ]
    plan = [re.sub(r"^\d+[\.\)]\s*", "", line) for line in lines]

    return {"plan": plan, "iteration": iteration + 1}


def researcher(state: dict) -> dict:
    """Execute Tavily search for each plan step, collect results and sources."""
    plan = state.get("plan", [])
    notes = []

    for i, question in enumerate(plan):
        try:
            raw = _get_search_tool().invoke(question)
            # TavilySearch returns dict with 'results' key or a list
            results = raw.get("results", raw) if isinstance(raw, dict) else raw
            note = f"### Question {i + 1}: {question}\n\n"
            for r in results:
                url = r.get("url", "unknown") if isinstance(r, dict) else ""
                content = r.get("content", "") if isinstance(r, dict) else str(r)
                note += f"- **Source:** {url}\n  {content}\n\n"
            notes.append(note)
        except Exception as e:
            notes.append(f"### Question {i + 1}: {question}\n\nSearch failed: {e}\n")

    return {"research_notes": notes}


def writer(state: dict) -> dict:
    """Synthesize research notes into a structured report."""
    topic = state["topic"]
    notes = state.get("research_notes", [])
    notes_text = "\n\n".join(notes)

    prompt = f"""You are a research report writer. Write a comprehensive report on: "{topic}"

Based on these research notes:
{notes_text}

Structure the report with these exact sections:
## Executive Summary
(2-3 paragraph overview)

## Key Findings
(Bullet points of the most important findings)

## Detailed Analysis
(In-depth discussion organized by theme)

## Sources
(List all URLs from the research notes)

## Conclusions
(Key takeaways and implications)

Write in a professional, analytical tone. Include specific data and facts from the research."""

    response = _get_llm().invoke(prompt)
    return {"report": response.content}


def reviewer(state: dict) -> dict:
    """Review the report and return a quality score 0-10 plus feedback."""
    report = state.get("report", "")
    topic = state["topic"]

    prompt = f"""You are a research report reviewer. Evaluate this report on "{topic}":

{report}

Rate the report on a scale of 0-10 based on:
- Completeness: Are all aspects of the topic covered?
- Accuracy: Are claims supported by sources?
- Structure: Is it well-organized with clear sections?
- Depth: Does it go beyond surface-level analysis?
- Sources: Are sources cited and relevant?

Respond in EXACTLY this format:
SCORE: X.X
FEEDBACK: Your detailed feedback here, including what's strong and what needs improvement."""

    response = _get_llm().invoke(prompt)
    text = response.content.strip()

    # Parse score
    score = 5.0
    score_match = re.search(r"SCORE:\s*([\d.]+)", text)
    if score_match:
        try:
            score = float(score_match.group(1))
            score = max(0.0, min(10.0, score))
        except ValueError:
            pass

    # Parse feedback
    feedback = text
    feedback_match = re.search(r"FEEDBACK:\s*(.*)", text, re.DOTALL)
    if feedback_match:
        feedback = feedback_match.group(1).strip()

    return {"quality_score": score, "feedback": feedback}

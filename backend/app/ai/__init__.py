"""AI ask bar: plain English -> terminal command -> narrated answer.

Public surface for the FastAPI layer:
    enabled() -> bool          is a local model usable right now?
    status()  -> dict          payload for GET /api/ai
    ask()     -> dict          run a query (raises AIUnavailable if no model)
"""
from __future__ import annotations

from .agent import run_agent
from .llm import AIUnavailable, OllamaProvider, detect, enabled, status

__all__ = ["AIUnavailable", "ask", "enabled", "status"]


def ask(query: str, data_provider) -> dict:
    info = detect()
    if info is None:
        raise AIUnavailable(status()["hint"])
    llm = OllamaProvider(model=info["model"], host=info["host"])
    answer, executed = run_agent(llm, query, data_provider)
    parsed, screen = executed or (None, None)
    return {"answer": answer, "parsed": parsed, "screen": screen}

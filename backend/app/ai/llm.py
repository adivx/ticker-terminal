"""LLM provider layer for the AI ask bar.

Kept deliberately small and swappable: the rest of the package talks to a
`chat()` method, so a future provider (remote, OpenAI-compatible, …) can be
added without touching the agent loop.

Current provider: **Ollama** (local, free, offline). Nothing here needs an
API key. Detection is cheap and memoized; when Ollama is absent, `enabled()`
is False and the UI simply hides AI actions.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Protocol

import requests

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "")  # optional explicit override

# Models we prefer, in order, matched by case-insensitive substring against
# `ollama list` names (tags like "qwen3:8b" match "qwen3"). All are free and
# support tool calling.
MODEL_PREFERENCES = [
    "qwen3",
    "qwen2.5",
    "llama3.1",
    "llama3",
    "mistral",
    "gemma3",
    "gemma2",
    "phi4",
]

# Local CPU inference is slow; the *connect* timeout stays tight so a dead
# server fails fast, but the *read* timeout is generous.
HTTP_TIMEOUT = (0.5, 600)
DETECT_TIMEOUT = 0.6
DETECT_TTL = 10  # seconds between /api/tags probes


class AIUnavailable(Exception):
    """Raised when the user asks but no usable local model is present."""


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict


@dataclass
class LLMResponse:
    text: str
    tool_calls: list[ToolCall] = field(default_factory=list)


class LLMProvider(Protocol):
    """Minimal contract the agent loop depends on."""

    def chat(self, messages: list[dict], system: str, tools: list[dict]) -> LLMResponse:
        """`messages` are Ollama-style chat dicts; returns text + tool calls."""
        ...


class OllamaProvider:
    """Talks to a local Ollama server over POST /api/chat (native API)."""

    name = "ollama"

    def __init__(self, model: str, host: str = OLLAMA_HOST):
        self.model = model
        self.host = host.rstrip("/")

    def chat(self, messages: list[dict], system: str, tools: list[dict]) -> LLMResponse:
        payload = {
            "model": self.model,
            "stream": False,
            "messages": [{"role": "system", "content": system}, *messages],
            "tools": tools,
            "options": {"temperature": 0.1, "num_predict": 900},
        }
        try:
            resp = requests.post(f"{self.host}/api/chat", json=payload, timeout=HTTP_TIMEOUT)
            resp.raise_for_status()
        except requests.RequestException as exc:
            raise AIUnavailable(f"Ollama request failed: {exc}") from exc
        message = resp.json().get("message", {})
        tool_calls = []
        for i, raw in enumerate(message.get("tool_calls") or []):
            fn = raw.get("function", {})
            tool_calls.append(
                ToolCall(
                    id=raw.get("id") or f"call_{i}",
                    name=fn.get("name", ""),
                    arguments=_parse_arguments(fn.get("arguments")),
                )
            )
        return LLMResponse(text=message.get("content") or "", tool_calls=tool_calls)


def _parse_arguments(raw) -> dict:
    """Ollama may return arguments as a dict or a JSON-encoded string."""
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


# --- detection --------------------------------------------------------------


_detect_cache: dict = {"at": 0.0, "result": None}


def _probe() -> dict | None:
    """One-shot probe of the Ollama server; None when unreachable/empty."""
    try:
        resp = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=DETECT_TIMEOUT)
        if resp.status_code != 200:
            return None
        names = [m.get("name", "") for m in resp.json().get("models", [])]
        if not names:
            return None
        model = OLLAMA_MODEL or pick_model(names)
        return {"host": OLLAMA_HOST, "models": names, "model": model}
    except (requests.RequestException, ValueError):
        return None


def detect() -> dict | None:
    """Memoized detection; cheap enough to call on every /api/ai request."""
    now = time.time()
    if now - _detect_cache["at"] < DETECT_TTL:
        return _detect_cache["result"]
    result = _probe()
    _detect_cache.update(at=now, result=result)
    return result


def pick_model(names: list[str]) -> str:
    """Choose the best available model: explicit override, then preference
    substring, then first available."""
    for name in names:
        if OLLAMA_MODEL and OLLAMA_MODEL.lower() in name.lower():
            return name
    low = [n.lower() for n in names]
    for pref in MODEL_PREFERENCES:
        for i, name in enumerate(low):
            if pref in name:
                return names[i]
    return names[0] if names else ""


def enabled() -> bool:
    return detect() is not None


def status() -> dict:
    info = detect()
    if info is None:
        return {
            "enabled": False,
            "provider": None,
            "model": None,
            "models": [],
            "hint": "AI off — install Ollama and pull a model (ollama pull qwen3:4b)",
        }
    return {
        "enabled": True,
        "provider": "ollama",
        "host": info["host"],
        "model": info["model"],
        "models": info["models"],
        "hint": "",
    }

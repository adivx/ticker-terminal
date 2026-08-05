"""Tests for the local-AI ask bar (Ollama provider + agent loop).

Hermetic: no network, no Ollama server. The agent loop is driven by a
scripted fake LLM and a stub data provider so the full
translate -> dispatch -> digest -> narrate path runs in-memory.
"""
import pytest

from app.ai import agent, llm
from app.ai.llm import LLMResponse, ToolCall, AIUnavailable


# --- pick_model --------------------------------------------------------------


def test_pick_model_preference_substring(monkeypatch):
    monkeypatch.setattr(llm, "OLLAMA_MODEL", "")
    names = ["mistral:7b", "qwen3:8b", "llama3.1:8b"]
    assert llm.pick_model(names) == "qwen3:8b"


def test_pick_model_env_override(monkeypatch):
    monkeypatch.setattr(llm, "OLLAMA_MODEL", "mistral")
    names = ["qwen3:8b", "mistral:7b"]
    assert llm.pick_model(names) == "mistral:7b"


def test_pick_model_fallback_first(monkeypatch):
    monkeypatch.setattr(llm, "OLLAMA_MODEL", "")
    names = ["custom:latest", "other:4b"]
    assert llm.pick_model(names) == "custom:latest"


def test_pick_model_empty(monkeypatch):
    monkeypatch.setattr(llm, "OLLAMA_MODEL", "")
    assert llm.pick_model([]) == ""


# --- agent loop --------------------------------------------------------------


class FakeLLM:
    """Returns scripted responses in order; records the messages it saw."""

    def __init__(self, script):
        self.script = list(script)
        self.calls = []

    def chat(self, messages, system, tools):
        self.calls.append(messages)
        return self.script.pop(0)


class StubProvider:
    """Canned data so dispatch + digest never touch the network."""

    def quote_full(self, symbol):
        return {
            "symbol": symbol,
            "name": "Apple Inc.",
            "last": 308.91,
            "change": -24.52,
            "changePercent": -7.35,
            "prevClose": 333.43,
            "open": 304.81,
            "volume": 10,
        }

    def history(self, symbol, range_key="1y"):
        return [
            {"time": 1700000000 + i * 86400, "open": 1, "high": 2, "low": 0.5,
             "close": 1.5, "volume": 10}
            for i in range(60)
        ]

    def news(self, query, limit=15):
        return [{"title": f"headline {i}", "link": "", "source": "s", "published": ""}
                for i in range(3)]

    def fundamentals(self, symbol):
        return {"symbol": symbol, "name": "Apple Inc.", "fields": [], "description": ""}

    def movers(self):
        return {"topGainers": [self.quote_full("AAPL")], "topLosers": [self.quote_full("MSFT")]}

    def indices(self):
        return [{"quote": self.quote_full("^NSEI")}]

    def peers(self, sector):
        return [self.quote_full("GS"), self.quote_full("BAC")]


def _tool_call(name, arguments):
    return ToolCall(id="call_0", name=name, arguments=arguments)


def test_run_agent_executes_command_then_narrates():
    llm_fake = FakeLLM([
        LLMResponse(text="", tool_calls=[
            _tool_call("run_terminal_command", {"cmd": "AAPL US Equity GP <GO>", "range": "1y"})
        ]),
        LLMResponse(text="AAPL fell 7% on weak guidance.", tool_calls=[]),
    ])
    answer, executed = agent.run_agent(llm_fake, "show me apple chart and why it moved", StubProvider())

    assert answer == "AAPL fell 7% on weak guidance."
    assert executed is not None
    parsed, screen = executed
    assert parsed["symbol"] == "AAPL" and parsed["function"] == "GP"
    assert screen["type"] == "chart"
    # The second round-trip fed the model an assistant tool_call + a tool result.
    assert len(llm_fake.calls) == 2
    assert llm_fake.calls[1][-1]["role"] == "tool"
    assert "Apple Inc." in llm_fake.calls[1][-1]["content"]


def test_run_agent_recovers_from_bad_command():
    llm_fake = FakeLLM([
        LLMResponse(text="", tool_calls=[
            _tool_call("run_terminal_command", {"cmd": "AAPL US Equity XYZ <GO>"})
        ]),
        LLMResponse(text="That function code is invalid.", tool_calls=[]),
    ])
    answer, executed = agent.run_agent(llm_fake, "bogus", StubProvider())
    assert answer == "That function code is invalid."
    assert executed is None
    assert "Command error" in llm_fake.calls[1][-1]["content"]


def test_run_agent_guards_tool_loop():
    llm_fake = FakeLLM([
        LLMResponse(text="", tool_calls=[_tool_call("run_terminal_command", {"cmd": "AAPL US Equity DES <GO>"})])
    ] * agent.MAX_ITERATIONS)
    answer, executed = agent.run_agent(llm_fake, "spin", StubProvider())
    assert "allowed steps" in answer
    assert executed is not None  # the single DES command did run


# --- graceful degradation -----------------------------------------------------


def test_detect_none_when_server_down(monkeypatch):
    monkeypatch.setattr(llm, "_probe", lambda: None)
    monkeypatch.setattr(llm, "_detect_cache", {"at": 0.0, "result": None})
    assert llm.detect() is None
    assert llm.enabled() is False
    assert "Ollama" in llm.status()["hint"]


def test_ask_raises_ai_unavailable_when_off(monkeypatch):
    from app.ai import ask

    monkeypatch.setattr(llm, "_probe", lambda: None)
    monkeypatch.setattr(llm, "_detect_cache", {"at": 0.0, "result": None})
    with pytest.raises(AIUnavailable):
        ask("show me apple", None)

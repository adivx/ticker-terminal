"""AI agent loop: plain English -> terminal command -> narrated answer.

One tool-use conversation against any `LLMProvider`:
  1. The model translates the user's request into a Bloomberg command and
     calls `run_terminal_command`.
  2. We execute it through the same dispatch path as /api/function and feed
     back a digest of the screen + headlines.
  3. The model narrates the answer from that price action and news.

Provider-agnostic: the loop only depends on `llm.chat(messages, system, tools)`
returning an `LLMResponse` with `text` and `tool_calls`.
"""
from __future__ import annotations

from ..dispatch import dispatch
from ..parser import CommandError, parse
from .digest import screen_digest
from .llm import ToolCall

MAX_ITERATIONS = 4  # guard against tool-call loops

SYSTEM_PROMPT = """You are the AI copilot inside a Bloomberg-style terminal.

The user speaks plain English. Translate their request into ONE terminal
command and run it with the `run_terminal_command` tool. Grammar:

    SYMBOL [COUNTRY] ASSET [FUNCTION] <GO>

- ASSET: Equity, Index, Curncy, Gov't, Comdty, ETF
- FUNCTION: DES (quote), GP (price graph), FA (fundamentals), CN (news),
  CRPR (comparables), WEI (world indices), TOP (movers)
- COUNTRY defaults to US; IN = NSE/BSE, GB/UK = London, JP = Tokyo, DE = Frankfurt.
- Bare special screens: TOP <GO>, WEI <GO>, HELP <GO>.
- Examples:
    "show me Apple's chart and why it moved" -> AAPL US Equity GP <GO>
    "Nvidia fundamentals"                    -> NVDA US Equity FA <GO>
    "what is the Nifty doing"                -> NIFTY Index GP <GO>
    "sensex news"                            -> SENSEX Index CN <GO>
    "Reliance P/E ratio"                     -> RELIANCE IN Equity FA <GO>
    "which stocks moved most today"          -> TOP <GO>
    "global market snapshot"                 -> WEI <GO>
    "JPMorgan vs its peers"                  -> JPM US Equity CRPR <GO>

Set a sensible `range` when the user mentions a window ("this week" -> 5d,
"this month" -> 1m, "last year" -> 1y); default 1y for GP.

After the tool runs you will receive the real market data and headlines.
Answer the user's question in 2-4 short terminal-style sentences: lead with
what the price did, then explain WHY from the headlines and price action. If
the tool reports an error, explain it and offer a corrected command. If the
request is not about markets, say so plainly — never invent a command."""

RUN_TERMINAL_COMMAND = {
    "type": "function",
    "function": {
        "name": "run_terminal_command",
        "description": (
            "Run a Bloomberg-style terminal command and return a digest of the "
            "resulting screen (quote, chart indicators, fundamentals, news, "
            "indices, movers, peers) plus recent headlines for the symbol."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "cmd": {
                    "type": "string",
                    "description": "Bloomberg command, e.g. 'AAPL US Equity GP <GO>'.",
                },
                "range": {
                    "type": "string",
                    "enum": ["1d", "5d", "1m", "6m", "1y", "5y"],
                    "description": "Chart range when cmd uses the GP function.",
                },
            },
            "required": ["cmd"],
        },
    },
}


def run_agent(llm, query: str, data_provider) -> tuple[str, tuple | None]:
    """Run the NL->command->narrate loop.

    Returns `(answer, executed)` where `executed` is `(parsed_dict, screen)`
    from the last successfully run command, or None if no command ran.
    """
    messages = [{"role": "user", "content": query}]
    executed = None

    for _ in range(MAX_ITERATIONS):
        response = llm.chat(messages, SYSTEM_PROMPT, [RUN_TERMINAL_COMMAND])
        if not response.tool_calls:
            return response.text.strip(), executed

        assistant = {"role": "assistant", "content": response.text or ""}
        for tc in response.tool_calls:
            assistant.setdefault("tool_calls", []).append(
                {"function": {"name": tc.name, "arguments": tc.arguments}}
            )
        messages.append(assistant)

        for tc in response.tool_calls:
            result, parsed, screen = _run_tool(tc, data_provider)
            if parsed is not None:
                executed = (parsed, screen)
            messages.append({"role": "tool", "content": result})

    return "I could not finish that within the allowed steps — try rephrasing.", executed


def _run_tool(tc: ToolCall, data_provider) -> tuple[str, dict | None, dict | None]:
    """Execute one tool call; errors become results the model can recover from."""
    if tc.name != "run_terminal_command":
        return "Unknown tool.", None, None
    cmd = tc.arguments.get("cmd", "")
    rng = tc.arguments.get("range", "1y")
    try:
        p = parse(cmd)
        screen = dispatch(data_provider, p, rng)
        return screen_digest(data_provider, p, screen), p.__dict__, screen
    except CommandError as exc:
        return f"Command error: {exc}. Fix the command and retry.", None, None
    except Exception as exc:  # upstream data failure -> recoverable result
        return f"Data error for `{cmd}`: {exc}. Try a different symbol.", None, None

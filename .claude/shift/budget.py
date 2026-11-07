"""Context and usage budget of the chief-engineer session.

PostToolUse hooks, acting on the main thread only (subagents have their own context):
* shorten long tool output before it enters the context;
* tell the chief engineer to wrap up once the context passes the soft limit
  (the runner interrupts at the hard limit);
* tell the chief engineer to start no new agent once the 5-hour usage is nearly
  spent, so that no agent is cut mid-task by the limit.
"""

import time

from config import LIMITS

WRAP_UP_PCT = LIMITS["wrap_up_pct"]
HARD_PCT = LIMITS["hard_pct"]
USAGE_WRAP_UP = LIMITS["usage_wrap_up"]
USAGE_START_MAX = LIMITS["usage_start_max"]
TOOL_CHARS = 8000    # Read, Bash, Grep, ... output
AGENT_CHARS = 3000   # agent reports are meant to be 150 words
AGENT_TOOLS = {"Agent", "Task"}

WRAP_UP_NOTE = (
    "CONTEXT BUDGET: the context is at {pct:.0f}%. Finish the current step only: "
    "make sure the agents' work is committed, update handover.md and timeline.md, commit, and end the "
    "cycle with state 'continue'. The next cycle starts with a fresh context."
)
USAGE_NOTE = (
    "USAGE BUDGET: {pct:.0f}% of the 5-hour usage limit is spent. Start no new agent: an "
    "agent cut by the limit loses its unfinished step. Make sure the work is committed, "
    "update handover.md and timeline.md, commit, push, and end the cycle with state 'continue'. The runner "
    "waits for the reset before the next cycle."
)


class Usage:
    """Last known utilization (0..1) and reset time per limit window, kept across cycles."""

    def __init__(self) -> None:
        self.util: dict[str, float] = {}
        self.resets: dict[str, int] = {}
        self.cycle_windows: set[int] = set()  # 5-hour windows the current cycle ran in, by reset time

    def update(self, info) -> None:
        kind = info.rate_limit_type
        if not kind:
            return
        if kind == "five_hour" and info.resets_at:
            self.cycle_windows.add(info.resets_at)
        if info.resets_at:
            if self.resets.get(kind) and info.resets_at > self.resets[kind]:
                self.util[kind] = 0.0  # a new window started
            self.resets[kind] = info.resets_at
        if info.utilization is not None:
            self.util[kind] = info.utilization
        elif info.status == "allowed":
            self.util[kind] = min(self.util.get(kind, 0.0), 0.5)  # below the warning level
        elif info.status == "rejected":
            self.util[kind] = 1.0

    def five_hour(self) -> float:
        if self.resets.get("five_hour", 0) and self.resets["five_hour"] < time.time():
            return 0.0  # the window has reset since the last event
        return self.util.get("five_hour", 0.0)

    def line(self) -> str:
        weekly = self.util.get("seven_day")
        return (f"Usage: 5-hour {100 * self.five_hour():.0f}%"
                + (f", weekly {100 * weekly:.0f}%" if weekly is not None else ", weekly below the warning level") + ".")


def _shorten(value, limit: int, hint: str):
    """Cut every string longer than limit, keeping the output's structure."""
    if isinstance(value, str) and len(value) > limit:
        return value[:limit] + f"\n[... {len(value) - limit} characters cut for the chief engineer's context. {hint}]"
    if isinstance(value, list):
        return [_shorten(v, limit, hint) for v in value]
    if isinstance(value, dict):
        return {k: _shorten(v, limit, hint) for k, v in value.items()}
    return value


class Budget:
    """Fill level of the main context, fed by the runner, read by the hooks."""

    def __init__(self, usage: Usage | None = None) -> None:
        self.pct = 0.0
        self.max_tokens: int | None = None
        self.usage = usage or Usage()

    def update(self, usage: dict | None) -> None:
        if not usage or not self.max_tokens:
            return
        tokens = sum(usage.get(k) or 0 for k in
                     ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens"))
        if tokens:
            self.pct = 100.0 * tokens / self.max_tokens

    async def post_tool_use(self, hook_input, tool_use_id, context):
        if hook_input.get("agent_id"):
            return {}
        out = {"hookEventName": "PostToolUse"}
        name = hook_input.get("tool_name", "")
        limit, hint = ((AGENT_CHARS, "Ask the agent for IDs and decisions only, or read the items with plm show.")
                       if name in AGENT_TOOLS else
                       (TOOL_CHARS, "Read narrowly: grep, a line range, or plm show; or have the owning agent summarise."))
        response = hook_input.get("tool_response")
        shortened = _shorten(response, limit, hint)
        if shortened != response:
            out["updatedToolOutput"] = shortened
        notes = []
        if self.pct >= WRAP_UP_PCT:
            notes.append(WRAP_UP_NOTE.format(pct=self.pct))
        if self.usage.five_hour() >= USAGE_WRAP_UP:
            notes.append(USAGE_NOTE.format(pct=100 * self.usage.five_hour()))
        if notes:
            out["additionalContext"] = "\n".join(notes)
        return {"hookSpecificOutput": out} if len(out) > 1 else {}

"""The shift: the chief engineer works unattended until an owner meeting, a blocker or the end.

Each cycle is a fresh chief-engineer session in the shift's own worktree that does
one work package, updates handover.md and timeline.md, commits and reports a state. When the usage
limit is hit, the job sleeps until the limit resets and resumes the same session.
When the state needs the owner, it stops and notifies.

    .claude/shift/run.sh [--max-cycles N] [--model opus] [--smoke]
"""

import argparse
import asyncio
import itertools
import json
import logging
import os
import subprocess
import sys
import time
import urllib.request
from datetime import datetime

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    HookMatcher,
    RateLimitEvent,
    ResultMessage,
    SystemMessage,
    TextBlock,
    ToolUseBlock,
)

from budget import HARD_PCT, USAGE_START_MAX, Budget, Usage
from config import CFG, HERE, WORKDIR
from guard import pre_tool_use
from progress import Progress, read_status

NAME = CFG["name"]
LOG_DIR = HERE / "logs"

STOP_STATES = {"meeting", "blocked", "done"}
LIMIT_FALLBACK_WAIT_S = 30 * 60   # when the CLI gives no reset time
LIMIT_MARGIN_S = 120              # wait a little past the reset
LONG_WAIT_NOTIFY_S = 6 * 3600     # tell the owner about a weekly-limit wait
MAX_ERRORS = 3

STATE_SCHEMA = {
    "type": "json_schema",
    "schema": {
        "type": "object",
        "properties": {
            "state": {"type": "string", "enum": ["continue", *sorted(STOP_STATES)]},
            "summary": {"type": "string", "description": "At most 80 words: what was done, IDs, commit."},
            "for_owner": {"type": "string", "description": "The MTG ID of the prepared meeting, or the blocker the owner must act on; empty for continue."},
        },
        "required": ["state", "summary", "for_owner"],
    },
}

RUN_RULES = """
# Shift

You are the chief engineer on shift: you work unattended in the shift's own worktree on `develop`. The owner is not available until you stop. Owner answers arrive as comments on `needs-owner` issues.

## Cycles

* One cycle is one work package. Take an open entry condition of the active milestone from `timeline.md` and close it as a whole, several agents one after the other if needed. Work that closes no entry condition becomes a backlog issue, not part of this cycle.
* At the start of a cycle, read the `needs-owner` issues with new owner comments (`gh issue list --label needs-owner`, `gh issue view <n> --comments`). Record each answer as an item and close the issue (CLAUDE.md, GitHub), then go on.
* Each work package is a branch `wp/<name>` and a pull request into `develop` (`gh pr create --base develop`). Merge it (`gh pr merge --merge`) when CI is green and the reviews it needs are done, then `git pull` in the shift's worktree.
* When `plm` gets in the way, open an issue on the PLM repository (CLAUDE.md, PLM tool). If the workaround would cost more than about one cycle, don't build it: work on another entry condition.

## Progress in usage windows

Progress is measured in 5-hour usage windows, not dates. The runner counts the windows used and the entry conditions closed; the cycle prompt gives the result. It reads these lines of `timeline.md`, keep their form exactly: in the section `## Active milestone`, `**Next milestone: <name>.**`, `Budget: <n> windows.`, and the entry conditions as `- [ ]` / `- [x]` lines under `### Entry conditions`. Tick a condition only when it is done and merged on `develop`.

* The budget belongs to the owner: never change the Budget line. When the prompt says OVER BUDGET, or the remaining work cannot fit the budget, prepare a re-plan meeting.
* When every entry condition of the milestone is ticked and its review items are written, prepare the gate or milestone meeting. The next milestone is set in that meeting.
* The runner stops the shift by itself after several windows without a closed entry condition, or when a milestone uses much more than its budget.

## Topics are finished once

* Every topic (entry condition, issue taken up) has a **done-when** criterion written before work starts: the concrete result, e.g. "`REQ-AFVYXW` states the assumption, merged".
* A cycle leaves each topic it touched done (criterion met, merged, ticked or issue closed), stopped (issue closed as `won't do` with the reason), or in progress with the one remaining step named. At most one topic is in progress.
* **Done is final.** A done topic is not reopened, re-reviewed, recounted or polished. Only a `major` finding or an owner decision reopens it; name it in the topic's line.

## Steering: look at the work, prioritise, stop

You judge the work itself, not only the agents' reports.

* **At the start of a cycle,** look at every open topic: open pull requests and branches, worktrees, the items changed since the last cycle, open findings and issues. For each, decide: continue, redirect or stop. A topic that has used windows without closing anything is a candidate to stop.
* **When an agent returns,** check what it actually did: its commits and `git diff --stat`, and the parts that decide whether it serves the entry condition. If it drifted, brief it again, narrower.
* **Stop** spending on work that closes no entry condition: polishing, review rounds on minors, analyses of options not taken, bookkeeping.
* You decide and brief; the agents do the work. You edit only your four files (`handover.md`, `timeline.md`, `project-plan.md`, `risks.md`; the plan only as the owner decided it), meeting items and issues. When the method itself gets in the way, open an issue on the Hangar repository (CLAUDE.md, GitHub).

## Reviews

* Peer review only for a work package that changes an interface or another owner's items, in its pull request; all other work is covered by the independent review at the milestone.
* Only `major` findings block and get a second review round. Minors and remarks are fixed in the same work package when cheap, otherwise they become backlog issues.
* Don't keep counts, denominators or review packs in prose. Generate them at the gate.

## Usage budget

When the usage limit is hit, every running agent is cut and its unfinished step is lost; the run sleeps until the reset.

* The cycle prompt gives the current usage. Choose a work package that fits it.
* Brief each agent with one bounded task (one item or one step, not a whole phase). Agents commit and push after every step, so a cut loses at most one step.
* When you are told the usage budget is reached, start no new agent: commit, update `handover.md` and `timeline.md`, push, and end the cycle with `continue`.

## Context and handover

* Wait for every agent you start to finish before you end your turn. Background agents die when your turn ends.
* When an agent returns, check `git -C <worktree> status --short`; if anything is uncommitted, have the agent commit it.
* Keep your own context small: read narrowly (`plm show`, `git diff --stat`, `grep`, line ranges). Long tool output is cut for you.
* When you are told the context budget is reached, finish the current step and end the cycle with `continue`.
* Before ending: no uncommitted changes in any worktree; update `handover.md` and `timeline.md` and commit them; push every branch you or an agent committed to. Never force-push, never touch `main`, never set `status: approved`. A guard blocks these.

## Stop for the owner, never decide for them

* `meeting`: a meeting is prepared with the skill `meeting` (a gate or milestone is ready, a re-plan is needed, or a decision blocks all remaining work). Put its MTG ID in `for_owner`.
* `blocked`: something you cannot solve (a tool fails, the guard blocked a needed action, hardware or access is needed).
* `done`: nothing is left to do.
* Otherwise `continue`. A decision that blocks only part of the work becomes a `needs-owner` issue with options and a recommendation; continue with the rest. Prepare a decision meeting only when nothing useful is left without the owner, or when three or more `needs-owner` issues are open.
"""

CYCLE_PROMPT = (
    "Start the next cycle of the shift. {usage} {progress} Read handover.md and timeline.md (active "
    "milestone and entry conditions), the open needs-owner issues with new comments, `git status`, `git worktree list`, "
    "the open pull requests and branches, then do the next work package. End with the state."
)
RESUME_PROMPT = (
    "The usage limit has reset. Continue the cycle where you stopped. Agents that were "
    "running were cut: check `git status` and the worktrees, then restart the unfinished step "
    "from what they committed, with a smaller brief if the step was too large to finish before "
    "the limit. End with the state."
)
STATE_PROMPT = "Finish this cycle now: commit, update handover.md and timeline.md, and end with the state."
CONTEXT_PROMPT = (
    "The context budget of this cycle is used up and your turn was interrupted. Finish now: "
    "make sure the agents' work is committed, update handover.md and timeline.md, commit, and end with state 'continue'."
)
SMOKE_PROMPT = "This is a connection test. Do not use any tool. Report state 'done', summary 'smoke test', for_owner ''."

log = logging.getLogger("shift")


def notify(title: str, message: str, issue: bool = False) -> None:
    """Log, push via ntfy if configured, and for a blocker open a needs-owner issue."""
    log.info("NOTIFY %s: %s", title, message)
    topic = CFG.get("ntfy_topic")
    if topic:
        req = urllib.request.Request(f"https://ntfy.sh/{topic}", data=message.encode(), headers={"Title": title})
        try:
            urllib.request.urlopen(req, timeout=15)
        except OSError as e:
            log.warning("ntfy failed: %s", e)
    if issue:
        r = subprocess.run(["gh", "issue", "create", "--label", "needs-owner", "--label", "blocked",
                            "--title", title, "--body", message], cwd=WORKDIR, capture_output=True, text=True)
        if r.returncode:
            log.warning("gh issue create failed: %s", r.stderr.strip())


def options(model: str, resume: str | None, smoke: bool, budget: Budget) -> ClaudeAgentOptions:
    return ClaudeAgentOptions(
        cwd=str(WORKDIR),
        model=model,
        resume=resume,
        setting_sources=["project"],  # CLAUDE.md, .claude/agents and .claude/skills, not the user's plugins
        system_prompt={"type": "preset", "preset": "claude_code", "append": RUN_RULES},
        permission_mode="acceptEdits",
        allowed_tools=[] if smoke else [
            "Read", "Grep", "Glob", "Edit", "Write", "Bash", "Agent", "Task", "Skill",
            "SendMessage", "WebSearch", "WebFetch", "TodoWrite",
        ],
        hooks={
            "PreToolUse": [HookMatcher(matcher=None, hooks=[pre_tool_use])],
            "PostToolUse": [HookMatcher(matcher=None, hooks=[budget.post_tool_use])],
        },
        output_format=STATE_SCHEMA,
        stderr=lambda line: log.debug("cli: %s", line),
    )


async def run_turn(prompt: str, opts: ClaudeAgentOptions, budget: Budget) -> dict:
    """Run one turn. Returns session_id, state (or None), limit info and error.

    At the hard context limit the turn is interrupted and the chief engineer is
    asked, in the same session, to wrap up and report the state.
    """
    out = {"session_id": opts.resume, "state": None, "limit_reset": None, "limited": False, "error": None}
    async with ClaudeSDKClient(options=opts) as client:
        usage = await client.get_context_usage()
        budget.max_tokens = usage["maxTokens"]
        budget.pct = usage["percentage"]
        log.info("context %.0f%% of %d tokens at start", budget.pct, budget.max_tokens)
        interrupted = False
        await client.query(prompt)
        while True:
            async for msg in client.receive_response():
                if isinstance(msg, RateLimitEvent):
                    info = msg.rate_limit_info
                    budget.usage.update(info)
                    log.info("rate limit %s %s util=%s resets=%s overage=%s", info.status, info.rate_limit_type,
                             info.utilization, info.resets_at, info.overage_status)
                    # with extra usage credit allowed, the run carries on past a rejected window
                    if info.status == "rejected" and info.overage_status not in ("allowed", "allowed_warning"):
                        out["limited"], out["limit_reset"] = True, info.resets_at
                elif isinstance(msg, SystemMessage) and msg.subtype == "init":
                    log.info("session model %s", msg.data.get("model"))
                elif isinstance(msg, AssistantMessage):
                    if msg.parent_tool_use_id is None:
                        budget.update(msg.usage)
                    for block in msg.content:
                        if isinstance(block, ToolUseBlock):
                            detail = block.input.get("description") or block.input.get("command") or block.input.get("file_path") or ""
                            log.info("tool %s %s [ctx %.0f%%]", block.name, str(detail)[:160], budget.pct)
                        elif isinstance(block, TextBlock):
                            log.debug("text %s", block.text[:300])
                    if budget.pct >= HARD_PCT and not interrupted:
                        log.warning("context at %.0f%%: interrupting for wrap-up", budget.pct)
                        interrupted = True
                        await client.interrupt()
                elif isinstance(msg, ResultMessage):
                    out["session_id"] = msg.session_id
                    log.info("result %s error=%s turns=%s http=%s", msg.subtype, msg.is_error,
                             msg.num_turns, msg.api_error_status)
                    if msg.api_error_status == 429:
                        out["limited"] = True
                    if msg.is_error and not out["limited"] and not interrupted:
                        out["error"] = f"{msg.subtype}: {msg.result or msg.errors}"
                    if isinstance(msg.structured_output, dict):
                        out["state"] = msg.structured_output
            if interrupted and out["state"] is None and not out["limited"] and interrupted != "asked":
                interrupted = "asked"
                await client.query(CONTEXT_PROMPT)
                continue
            break
    return out


def dirty_worktrees() -> list[str]:
    """Worktrees (the repository included) with uncommitted changes."""
    out = subprocess.run(["git", "-C", str(WORKDIR), "worktree", "list", "--porcelain"],
                         capture_output=True, text=True).stdout
    paths = [line[9:] for line in out.splitlines() if line.startswith("worktree ")]
    return [p for p in paths if subprocess.run(["git", "-C", p, "status", "--porcelain"],
                                               capture_output=True, text=True).stdout.strip()]


async def wait_for_reset(resets_at: int | None) -> None:
    wait = (resets_at - time.time() + LIMIT_MARGIN_S) if resets_at else LIMIT_FALLBACK_WAIT_S
    wait = max(wait, 60)
    until = datetime.fromtimestamp(time.time() + wait).strftime("%a %H:%M")
    log.info("usage limit reached, sleeping %.0f min until %s", wait / 60, until)
    if wait > LONG_WAIT_NOTIFY_S:
        notify(f"{NAME}: shift paused", f"Usage limit reached. Resuming {until}.")
    await asyncio.sleep(wait)


async def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-cycles", type=int, default=0, help="0 = no limit")
    ap.add_argument("--model", default=CFG["model"], help="model of the chief-engineer session")
    ap.add_argument("--smoke", action="store_true", help="connection test, no tools, no work")
    args = ap.parse_args()

    LOG_DIR.mkdir(exist_ok=True)
    logfile = LOG_DIR / f"shift-{datetime.now():%Y%m%d-%H%M%S}.log"
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s %(message)s",
                        handlers=[logging.FileHandler(logfile), logging.StreamHandler(sys.stdout)])
    logging.getLogger().handlers[1].setLevel(logging.INFO)
    if os.environ.get("ANTHROPIC_API_KEY"):
        log.warning("ANTHROPIC_API_KEY is set: this run is billed to the API, not your plan")

    errors = 0
    usage = Usage()  # kept across cycles
    timeline_md = WORKDIR / "timeline.md"
    progress = Progress(HERE / "progress.json")
    if not args.smoke:
        progress.start(read_status(timeline_md))  # the owner started the shift: budget and stall so far accepted
        progress.save()
    for cycle in (range(1, args.max_cycles + 1) if args.max_cycles else itertools.count(1)):
        if usage.five_hour() >= USAGE_START_MAX and usage.resets.get("five_hour"):
            log.info("5-hour usage at %.0f%%: waiting for the reset before cycle %d", 100 * usage.five_hour(), cycle)
            await wait_for_reset(usage.resets["five_hour"])
        status = read_status(timeline_md)
        log.info("=== cycle %d (%s %s)", cycle, usage.line(), progress.line(status))
        cycle_prompt = CYCLE_PROMPT.format(usage=usage.line(), progress=progress.line(status))
        session, prompt = None, SMOKE_PROMPT if args.smoke else cycle_prompt
        usage.cycle_windows = set()
        state = None
        while state is None:
            try:
                budget = Budget(usage)
                r = await run_turn(prompt, options(args.model, session, args.smoke, budget), budget)
            except Exception as e:  # CLI crash, connection loss
                r = {"session_id": session, "state": None, "limited": False, "limit_reset": None, "error": repr(e)}
            session = r["session_id"] or session
            if r["limited"]:
                await wait_for_reset(r["limit_reset"])
                prompt = RESUME_PROMPT
                continue
            if r["error"] or r["state"] is None:
                errors += 1
                log.error("cycle %d: %s (error %d of %d)", cycle, r["error"] or "no state reported", errors, MAX_ERRORS)
                if errors >= MAX_ERRORS:
                    notify(f"{NAME}: shift stopped", f"Repeated errors: {r['error'] or 'no state'}. Log: {logfile.name}", issue=True)
                    return 1
                prompt = STATE_PROMPT if session else cycle_prompt
                continue
            state = r["state"]
        errors = 0
        log.info("cycle %d state=%s: %s", cycle, state["state"], state["summary"])
        dirty = dirty_worktrees()
        if dirty:
            log.warning("uncommitted changes after cycle %d in: %s", cycle, ", ".join(dirty))
        record = {**state, "session_id": session, "cycle": cycle, "time": datetime.now().isoformat(timespec="seconds")}
        (HERE / "last-state.json").write_text(json.dumps(record, indent=2))
        if not args.smoke:
            windows = usage.cycle_windows or ({usage.resets["five_hour"]} if usage.resets.get("five_hour") else set())
            after = read_status(timeline_md)
            progress.record_cycle(windows, after["closed"] if after["milestone"] == status["milestone"] else 0)
            progress.save()
            log.info("progress: %s", progress.line(after))
            reason = progress.stop_reason(after) if state["state"] not in STOP_STATES else None
            if reason:
                log.warning("runner stop: %s", reason)
                (HERE / "last-state.json").write_text(json.dumps(
                    {**record, "state": "meeting", "for_owner": "Runner: " + reason}, indent=2))
                notify(f"{NAME}: re-plan needed", reason, issue=True)
                return 0
        if state["state"] in STOP_STATES:
            titles = {"meeting": "meeting ready", "blocked": "run blocked", "done": "run done"}
            note = f" Uncommitted changes in {len(dirty)} worktree(s)." if dirty else ""
            notify(f"{NAME}: {titles[state['state']]}", (state["for_owner"] or state["summary"]) + note,
                   issue=state["state"] == "blocked")
            return 0
    notify(f"{NAME}: shift paused", f"Reached {args.max_cycles} cycles. See handover.md.")  # only with --max-cycles
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

# Shift

The shift runs the chief engineer unattended with the Claude Agent SDK until the owner is needed: a meeting is ready, the work is blocked, or nothing is left. How it fits into the process: `PROCESS.md`, The shift.

```sh
.claude/shift/run.sh                  # until a meeting, a blocker or done
.claude/shift/run.sh --max-cycles 3   # shorter leash
.claude/shift/run.sh --smoke          # connection test, no work
```

As a service: `systemd/shift.service` (start and stop by hand) and `systemd/remote.service` (Claude app access, starts at boot); install notes are in the files. Settings: `shift.toml` (owner only).

## How it works

* **Own worktree:** the shift works in `workdir` on `branch` (`develop`), created by `run.sh`. The owner's checkout stays on `main`, so an owner session never collides with it.
* **Cycle:** a fresh chief-engineer session does one work package, commits, updates `handover.md` and `timeline.md` and reports a state: `continue`, `meeting`, `blocked` or `done`.
* **Progress in windows:** the runner counts the 5-hour usage windows per milestone and the entry conditions ticked in `timeline.md` (`progress.py`, record in `progress.json`). The budget is the one in `timeline.md` when the owner started the shift; the shift cannot raise it. Over budget, it prepares a re-plan meeting. It stops by itself after `stall_windows` windows without a closed entry condition, or at `overrun_stop` times the budget.
* **Usage limit:** at `usage_wrap_up` of the 5-hour limit the chief engineer starts no new agent and ends the cycle; above `usage_start_max` the runner waits for the reset before a cycle. If the limit is hit anyway, it sleeps until the reset and resumes the same session.
* **Context budget (`budget.py`):** long tool output is cut; at `wrap_up_pct` the chief engineer ends the cycle, at `hard_pct` the turn is interrupted for a wrap-up.
* **Guard (`guard.py`):** a PreToolUse hook on every tool call, subagents included. It blocks forced, bulk and delete pushes, anything on `main`, baseline tags, `status: approved`, repository settings and deletions through `gh`, writes outside the worktrees, and changes to this folder. It guards against mistakes; branch protection on `main` is the real barrier.
* **Notifications:** a prepared meeting is a GitHub issue labelled `meeting`; a blocker or a runner stop opens a `needs-owner` issue. GitHub notifies the owner. Optional: a push via ntfy.sh (`ntfy_topic`; public, anyone who knows the topic can read it).
* **Stop:** any state but `continue`, 3 errors in a row, or `--max-cycles`. The last state is in `last-state.json`, the full log in `logs/`.

If `ANTHROPIC_API_KEY` is set, the shift is billed to the API instead of your plan, and the log warns about it.

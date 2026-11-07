# Shift

The shift runs the chief engineer unattended with the Claude Agent SDK until the owner is needed: a meeting is ready, the work is blocked, or nothing is left. How it fits into the process: `PROCESS.md`, The shift.

```sh
.claude/shift/run.sh                  # until a meeting, a blocker or done
.claude/shift/run.sh --max-cycles 3   # shorter leash
.claude/shift/run.sh --smoke          # connection test, no work
```

As a service: `systemd/shift.service` (start and stop by hand) and `systemd/remote.service` (Claude app access, starts at boot); install notes are in the files. Settings: `shift.toml` (owner only), per-host overrides in `shift.local.toml` (untracked). The service reads `~/.config/<name>-shift.env`: `CLAUDE_CODE_OAUTH_TOKEN` from `claude setup-token`, and optionally `SHIFT_NTFY_TOPIC`. Keep the token out of interactive shells: Remote Control needs the full login and fails with it set.

## How it works

* **Own clone:** the shift works in its own clone `workdir` on `branch` (`develop`), cloned by `run.sh`. The owner's checkout can stay on `develop` too: it pulls to see the shift's work and does not commit while the shift runs.
* **Cycle:** a fresh chief-engineer session does one work package, commits, updates `handover.md` and `timeline.md` and reports a state: `continue`, `meeting`, `blocked` or `done`.
* **Progress in windows:** the runner counts the 5-hour usage windows per milestone and the entry conditions ticked in `timeline.md` (`progress.py`, record in `progress.json`). The budget is the one in `timeline.md` when the owner started the shift; the shift cannot raise it. Over budget, it prepares a re-plan meeting. It stops by itself after `stall_windows` windows without a closed entry condition, or at `overrun_stop` times the budget.
* **Usage limit:** at `usage_wrap_up` of the 5-hour limit the chief engineer starts no new agent and ends the cycle; above `usage_start_max` the runner waits for the reset before a cycle. If the limit is hit anyway, it sleeps until the reset and resumes the same session.
* **Context budget (`budget.py`):** long tool output is cut; at `wrap_up_pct` the chief engineer ends the cycle, at `hard_pct` the turn is interrupted for a wrap-up.
* **Guard (`guard.py`):** a PreToolUse hook on every tool call, subagents included. It blocks forced, bulk and delete pushes, anything on `main`, baseline tags, `status: approved`, repository settings and deletions through `gh`, writes outside the shift's clone and the agents' worktrees, and changes to this folder. It guards against mistakes; branch protection on `main` is the real barrier.
* **Notifications:** a prepared meeting is a GitHub issue labelled `meeting`; a blocker or a runner stop opens a `needs-owner` issue. GitHub notifies the owner only when the shift uses its own GitHub account: GitHub sends no notification for issues the owner's own account opens, so a shift under the owner's account needs ntfy. Optional: a push via ntfy.sh (`SHIFT_NTFY_TOPIC` or `ntfy_topic`; public, anyone who knows the topic can read it).
* **Is it running?** `pgrep -f "shift[.]py --project <name>"`: `run.sh` marks the process with the project name, so this works for any Linux user.
* **Stop:** any state but `continue`, 3 errors in a row, or `--max-cycles`. The last state is in `last-state.json`, the full log in `logs/`.

If `ANTHROPIC_API_KEY` is set, the shift is billed to the API instead of your plan, and the log warns about it.

## Run the shift as its own user (recommended)

The guard catches mistakes; it is not a sandbox. Run as the owner, the shift can read the owner's home (keys, tokens, other repositories) and acts on GitHub with the owner's rights, so it could merge to `main` or change settings. A separate Linux user and a separate GitHub account make these limits real:

1. **GitHub:** create a machine account (e.g. `<owner>-shift`), add it to the repository as a collaborator with the **Write** role, and protect `main` with the owner's review (`scripts/setup.sh --protect`). The machine account cannot approve its own pull requests, merge to `main` or change settings.
2. **Linux:** `sudo adduser --disabled-password <name>-shift` and `sudo loginctl enable-linger <name>-shift`. As that user install the tools of the repository's `README.md`, clone the repository (step 3) and run `scripts/setup.sh` there (it installs `plm`), then `claude auth login` (the owner's Claude account; the shift uses the owner's plan) and `gh auth login` with the machine account.
3. **Clone:** as that user, clone the repository and write `.claude/shift/shift.local.toml` with `workdir = "."` and `worktrees = "../<name>-wt"`. The shift then works in this clone on `develop`.
4. **Service:** install `systemd/shift.service` for that user (`sudo -u <name>-shift …` or a login as it); start and stop it with `sudo systemctl --user -M <name>-shift@ start <name>-shift`.

The owner keeps working in their own checkout under their own account; the control room (`systemd/remote.service`) stays with the owner. Notifications reach the owner through the issues the machine account opens.

"""Progress of the shift, measured in 5-hour usage windows, kept by the runner.

The chief engineer keeps the milestone and its entry-condition checklist in
timeline.md; the owner sets the budget in an owner meeting. The runner counts the
windows used and the entry conditions closed, and stops the run when the
milestone stalls or overruns. progress.json is the runner's own record; the
guard keeps agents out of this folder.

timeline.md lines read here (section "## Active milestone"):
    **Next milestone: PDR.**
    Budget: 8 windows.
    - [ ] / - [x] entry conditions, under "### Entry conditions"

The budget counted against is the one in timeline.md when the owner started the
shift: a Budget line changed by the shift itself takes effect only at the next start.
"""

import json
import re
from pathlib import Path

from config import LIMITS


def read_status(path: Path) -> dict:
    """Milestone, budget and checklist counts from timeline.md."""
    text = path.read_text() if path.exists() else ""
    milestone = re.search(r"\*\*Next milestone: ([^*]+?)\.?\*\*", text)
    budget = re.search(r"^Budget: ([\d.]+) windows?", text, re.M)
    section = text.split("### Entry conditions", 1)[-1].split("\n#", 1)[0] if "### Entry conditions" in text else ""
    boxes = re.findall(r"^\s*- \[([ xX])\]", section, re.M)
    return {
        "milestone": milestone.group(1).strip() if milestone else None,
        "budget": float(budget.group(1)) if budget else None,
        "closed": sum(b in "xX" for b in boxes),
        "open": sum(b == " " for b in boxes),
    }


class Progress:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.data = json.loads(path.read_text()) if path.exists() else {}

    def save(self) -> None:
        self.path.write_text(json.dumps(self.data, indent=2))

    def start(self, status: dict) -> None:
        """At a shift start by the owner: a new milestone starts counting; the stall so far and the budget are accepted."""
        if self.data.get("milestone") != status["milestone"]:
            if self.data.get("milestone"):
                self.data.setdefault("history", []).append(
                    {"milestone": self.data["milestone"], "windows": len(self.data.get("windows", []))})
            self.data.update(milestone=status["milestone"], windows=[])
        self.data["closed"] = status["closed"]  # the owner accepts the checklist as it stands
        self.data["budget"] = status["budget"]
        self.data["progress_window"] = max(self.data["windows"], default=None)

    def record_cycle(self, windows: set[int], closed: int) -> None:
        """Count the windows the cycle ran in; note newly closed conditions."""
        self.data["windows"] = sorted(set(self.data["windows"]) | windows)
        if closed > self.data.get("closed", 0) and windows:
            self.data["progress_window"] = max(windows)
        self.data["closed"] = max(closed, self.data.get("closed", 0))

    def used(self) -> int:
        return len(self.data.get("windows", []))

    def stall_windows(self) -> int:
        """Finished windows with work since the last newly closed entry condition."""
        windows = self.data.get("windows", [])
        last, current = self.data.get("progress_window") or 0, max(windows, default=0)
        return sum(1 for w in windows if last < w < current)

    def line(self, status: dict) -> str:
        """One line for the cycle prompt."""
        if not status["milestone"]:
            return "No milestone in timeline.md: prepare a kickoff or re-plan meeting."
        n = status["closed"] + status["open"]
        budget = self.data.get("budget")
        s = (f"{status['milestone']}: {self.used()}"
             + (f" of {budget:g}" if budget else " (no budget set by the owner)")
             + f" windows used; {status['closed']} of {n} entry conditions closed; "
             f"{self.stall_windows()} window(s) without a closed condition.")
        if status["closed"] < self.data.get("closed", 0):
            s += (f" REOPENED: {self.data['closed'] - status['closed']} entry condition(s) were done and are no "
                  "longer ticked. Done is final: tick them again, or name the major finding or owner decision "
                  "that reopened them in their line.")
        if budget and self.used() > budget:
            s += " OVER BUDGET: prepare a re-plan meeting and stop with state 'meeting'."
        return s

    def stop_reason(self, status: dict) -> str | None:
        """Why the runner stops for the owner, or None."""
        if self.stall_windows() >= LIMITS["stall_windows"]:
            return (f"{status['milestone']}: {self.stall_windows()} windows with work but no entry "
                    "condition closed. Hold a re-plan meeting.")
        budget = self.data.get("budget")
        if budget and self.used() > LIMITS["overrun_stop"] * budget:
            return f"{status['milestone']}: {self.used()} windows used of {budget:g}. Hold a re-plan meeting."
        return None

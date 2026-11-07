"""Guard for the shift: blocks the actions that belong to the owner.

Runs as a PreToolUse hook on every tool call, including those of subagents.
It is a guard against mistakes, not a sandbox: Bash can still reach anything
the user account can reach. Branch protection on main is the real barrier.
"""

import re
import shlex
from pathlib import Path

from config import HERE, WORKDIR, WORKTREES

WRITE_ROOTS = [WORKDIR, WORKTREES, Path("/tmp")]
PROTECTED_BRANCHES = {"main", "master"}
PROTECTED_DIRS = [HERE, WORKDIR / ".claude" / "shift"]

APPROVED = re.compile(r"status:\s*['\"]?approved")
BASH_DENY = [
    (re.compile(r"\bgit\b.*\bpush\b.*(--all|--mirror|--delete|\s-d\b|\s\+\S)"), "push only named branches and tags, no bulk, delete or forced push"),
    (re.compile(r"\bgit\b.*\breset\b.*--hard"), "git reset --hard discards work"),
    (re.compile(r"\bgit\b.*\bclean\b.*-[a-z]*f"), "git clean -f deletes files"),
    (re.compile(r"\bgit\b.*\bbranch\b.*\s-D\b"), "force-deleting branches"),
    (re.compile(r"\bgit\b.*\b(push|merge|rebase|reset|checkout|switch)\b.*--force"), "forced git operation"),
    (re.compile(r"\bgit\b.*\btag\b.*-baseline"), "baseline tags follow the owner's gate go"),
    (re.compile(r"\bgh\s+(repo|secret|auth|release|ssh-key|gpg-key|ruleset|variable|workflow\s+(disable|enable))\b"), "repository settings belong to the owner"),
    (re.compile(r"\bgh\s+pr\s+(merge|review)\b.*\bmain\b"), "main belongs to the owner"),
    (re.compile(r"\bgh\s+pr\s+review\b.*--approve"), "approving belongs to the owner"),
    (re.compile(r"\bgh\s+(issue|pr|label)\s+delete\b"), "deleting issues, pull requests or labels"),
    (re.compile(r"\bgh\s+api\b.*(-X|--method)\s*(DELETE|PUT|PATCH)"), "changing the repository through the API"),
    (re.compile(r"\bgh\s+api\b.*\b(branches/[^ ]*/protection|collaborators|hooks|keys)\b"), "repository settings belong to the owner"),
    (re.compile(r"\bsudo\b"), "sudo"),
    (re.compile(r"\brm\s+-[a-z]*r[a-z]*f?\s+(/|~|\$HOME)(\s|$)"), "recursive delete of a root folder"),
]
GIT_BRANCH_CMDS = {"merge", "rebase", "reset", "checkout", "switch", "push", "commit"}


def _allowed_path(path: str) -> bool:
    p = Path(path).expanduser().resolve()
    if any(p.is_relative_to(d) for d in PROTECTED_DIRS):
        return False
    return any(p.is_relative_to(r) for r in WRITE_ROOTS)


def _touches_protected_branch(command: str) -> bool:
    try:
        tokens = shlex.split(command, posix=True)
    except ValueError:
        tokens = command.split()
    for i, tok in enumerate(tokens):
        if tok != "git":
            continue
        rest = tokens[i + 1 :]
        sub = next((t for t in rest if not t.startswith("-")), None)
        if sub in GIT_BRANCH_CMDS and PROTECTED_BRANCHES & set(rest):
            return True
    return False


def check(tool_name: str, tool_input: dict) -> str | None:
    """Return the reason to deny the call, or None to let it through."""
    if tool_name == "Bash":
        cmd = tool_input.get("command", "")
        for pattern, reason in BASH_DENY:
            if pattern.search(cmd):
                return reason
        if APPROVED.search(cmd):
            return "items become approved only after the owner's gate go, in the meeting"
        if _touches_protected_branch(cmd):
            return "main and master belong to the owner"
        if ".claude/shift" in cmd and re.search(r"(>|\btee\b|\bsed\s+-i|\brm\b|\bmv\b|\bcp\b)", cmd):
            return "the shift may not change itself"
        return None
    if tool_name in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
        path = tool_input.get("file_path") or tool_input.get("notebook_path") or ""
        if path and not _allowed_path(path):
            return f"writing outside the shift's worktree and the agents' worktrees: {path}"
        text = " ".join(str(tool_input.get(k, "")) for k in ("content", "new_string", "edits"))
        if APPROVED.search(text):
            return "items become approved only after the owner's gate go, in the meeting"
    return None


async def pre_tool_use(hook_input, tool_use_id, context):
    reason = check(hook_input.get("tool_name", ""), hook_input.get("tool_input") or {})
    if reason is None:
        return {}
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": f"Blocked in the shift: {reason}. "
            "If the work needs it, stop and report state 'blocked' for the owner.",
        }
    }

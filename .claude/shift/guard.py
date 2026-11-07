"""Guard for the shift: blocks the actions that belong to the owner.

Runs as a PreToolUse hook on every tool call, including those of subagents.
It is a guard against mistakes, not a sandbox: a script can still reach anything
the account can reach. Branch protection on main and a separate account for the
shift (README.md) are the real barriers.

A shell command is split into simple commands at ;, &&, ||, | and newlines, and
each one is checked on its own, so read-only commands next to a blocked word pass.
"""

import re
import shlex
import subprocess
from pathlib import Path

from config import HERE, WORKDIR, WORKTREES

WRITE_ROOTS = [WORKDIR, WORKTREES, Path("/tmp")]
PROTECTED = {"main", "master", "refs/heads/main", "refs/heads/master"}
SELF = ".claude/shift"
APPROVED = re.compile(r"status:\s*['\"]?approved")
SEPARATORS = re.compile(r"\|\||&&|;|\||\n")
REDIRECT = re.compile(r"(?<![0-9&])>>?\s*([^\s&]+)")
GIT_GLOBAL_WITH_ARG = {"-C", "-c", "--git-dir", "--work-tree", "--namespace"}
GH_READ = {"view", "list", "status", "diff", "checks", "download", "clone"}
TAG_READ = {"-l", "--list", "-v", "--verify", "--contains", "--points-at", "-n"}


def _tokens(segment: str) -> list[str]:
    try:
        return shlex.split(segment, posix=True)
    except ValueError:
        return segment.split()


def _push(rest: list[str]) -> str | None:
    opts = [a for a in rest if a.startswith("-")]
    short = "".join(o[1:] for o in opts if not o.startswith("--"))
    long = {o.split("=")[0] for o in opts if o.startswith("--")}
    if "f" in short or "d" in short or long & {
            "--force", "--force-with-lease", "--force-if-includes", "--delete", "--all", "--mirror", "--prune"}:
        return "push only named branches and tags, no forced, deleting or bulk push"
    for ref in [a for a in rest if not a.startswith("-")][1:]:  # the first is the remote
        if ref.startswith("+"):
            return "no forced refspec"
        src, colon, dst = ref.rpartition(":")
        if colon and not src:
            return "no deleting refspec"
        dst = dst if colon else ref
        if dst in PROTECTED:
            return "main belongs to the owner"
        if "baseline" in dst:
            return "baseline tags follow the owner's gate go"
    return None


def _git(args: list[str]) -> str | None:
    i = 0
    while i < len(args) and args[i].startswith("-"):  # global options before the subcommand
        i += 2 if args[i] in GIT_GLOBAL_WITH_ARG else 1
    if i >= len(args):
        return None
    sub, rest = args[i], args[i + 1 :]
    opts = [a for a in rest if a.startswith("-")]
    words = [a for a in rest if not a.startswith("-")]
    if sub == "push":
        return _push(rest)
    if sub in ("checkout", "switch") and PROTECTED & set(words):
        return "main belongs to the owner"
    if sub == "reset" and "--hard" in opts:
        return "git reset --hard discards work"
    if sub == "clean" and ("--force" in opts or any("f" in o for o in opts if not o.startswith("--"))):
        return "git clean -f deletes files"
    if sub == "branch" and ("-D" in opts or {"--delete", "--force"} <= set(opts)):
        return "force-deleting branches"
    if sub == "tag" and not TAG_READ & set(opts) and any("baseline" in w for w in words):
        return "baseline tags follow the owner's gate go"
    return None


def _pr_base(number: str) -> str | None:
    try:
        r = subprocess.run(["gh", "pr", "view", number, "--json", "baseRefName", "-q", ".baseRefName"],
                           cwd=WORKDIR, capture_output=True, text=True, timeout=30)
        return r.stdout.strip() if r.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def _gh(args: list[str]) -> str | None:
    if not args:
        return None
    group, sub = args[0], (args[1] if len(args) > 1 else "")
    if group in ("repo", "release", "workflow", "variable", "ruleset", "ssh-key", "gpg-key", "secret", "auth") \
            and sub not in GH_READ:
        return "repository settings and releases belong to the owner"
    if group in ("issue", "pr", "label") and sub == "delete":
        return "deleting issues, pull requests or labels"
    if group == "pr" and sub == "review" and ("--approve" in args or "-a" in args):
        return "approving belongs to the owner"
    if group == "pr" and sub == "merge":
        number = next((a for a in args[2:] if not a.startswith("-")), None)
        base = _pr_base(number) if number else None
        if base is None or base in PROTECTED or "--admin" in args:
            return "merging into main belongs to the owner (or the base branch could not be checked)"
    if group == "api":
        joined = " ".join(args)
        if re.search(r"(-X|--method)[ =]?(DELETE|PUT|PATCH)\b", joined, re.I):
            return "changing the repository through the API"
        if re.search(r"event=APPROVE|branches/[^ ]*/protection|/collaborators|/hooks|/keys|/rulesets", joined):
            return "repository settings and approvals belong to the owner"
    return None


def _segment(segment: str) -> str | None:
    args = _tokens(segment)
    if not args:
        return None
    cmd, rest = Path(args[0]).name, args[1:]
    if cmd == "sudo":
        return "sudo"
    if cmd == "git":
        return _git(rest)
    if cmd == "gh":
        return _gh(rest)
    if cmd == "plm" and rest[:1] == ["set"] and "status" in rest and "approved" in rest:
        return "items become approved only after the owner's gate go, in the meeting"
    if cmd == "rm" and any(o.startswith("-") and not o.startswith("--") and "r" in o.lower() for o in rest) and \
            any(a.rstrip("/") in ("", "~", "$HOME") for a in rest if not a.startswith("-")):
        return "recursive delete of a root folder"
    redirects = REDIRECT.findall(segment)
    edits = cmd in ("tee", "rm", "mv", "cp", "install", "truncate", "chmod") or \
        (cmd == "sed" and any(a.startswith("-i") for a in rest))
    targets = redirects + (rest if edits else [])
    if (redirects or edits) and any(SELF in t for t in targets):
        return "the shift may not change itself"
    if (redirects or edits) and APPROVED.search(segment):
        return "items become approved only after the owner's gate go, in the meeting"
    return None


def _allowed_path(path: str) -> bool:
    p = Path(path).expanduser().resolve()
    if p.is_relative_to(HERE) or f"/{SELF}/" in f"{p}/":
        return False
    return any(p.is_relative_to(r) for r in WRITE_ROOTS)


def check(tool_name: str, tool_input: dict) -> str | None:
    """Return the reason to deny the call, or None to let it through."""
    if tool_name == "Bash":
        for segment in SEPARATORS.split(tool_input.get("command", "")):
            reason = _segment(segment.strip())
            if reason:
                return reason
        return None
    if tool_name in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
        path = tool_input.get("file_path") or tool_input.get("notebook_path") or ""
        if path and not _allowed_path(path):
            return f"writing outside the shift's clone and the agents' worktrees, or into the shift itself: {path}"
        new = " ".join(str(tool_input.get(k, "")) for k in ("content", "new_string", "edits"))
        old = str(tool_input.get("old_string", ""))
        if tool_name == "Write" and path and Path(path).is_file():
            old = Path(path).read_text(errors="ignore")
        if APPROVED.search(new) and not APPROVED.search(old):
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

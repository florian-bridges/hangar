#!/usr/bin/env python3
"""Checks of the method that plm does not make; run by CI on every push and pull request.

    python3 scripts/check.py [repository]   # default: the repository holding this script

* owners: the owners allowed in schemas/meta.schema.json are the agents in
  .claude/agents/ plus chief-engineer, and the work-package form offers only those.
* requirements: a need (in a needs/ or stakeholder-needs/ folder) says "needs"
  and no "shall"; every other requirement has exactly one "shall"; no vague words.
* lengths: handover.md at most about one page, a meeting pack.md at most about two.

Exits 1 with one line per finding. Standard library only, so it runs anywhere.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
VAGUE = re.compile(r"\b(should|and/or|as far as possible|if possible|adequate|appropriate|sufficient(ly)?|etc)\b", re.I)
LIMITS = {"handover.md": 450, "pack.md": 1000}  # words: about one and two pages
SKIP = {".git", "node_modules", ".venv", ".claude"}


def field(text: str, key: str) -> str:
    """Value of a top-level YAML key, joined over its continuation lines (no YAML library needed)."""
    m = re.search(rf"^{key}:[ \t]*(.*(?:\n[ \t]+.*)*)", text, re.M)
    return " ".join(m.group(1).split()).strip("\"'>|- ") if m else ""


def owners() -> list[str]:
    out = []
    agents = {re.search(r"^name:\s*(\S+)", p.read_text(), re.M).group(1)
              for p in (ROOT / ".claude/agents").glob("*.md")} | {"chief-engineer"}
    schema = ROOT / "schemas/meta.schema.json"
    if schema.exists():
        allowed = set(json.loads(schema.read_text())["properties"]["owner"]["enum"])
        out += [f"schemas/meta.schema.json: owner {a} has no agent file" for a in sorted(allowed - agents)]
        out += [f"schemas/meta.schema.json: agent {a} is not an allowed owner" for a in sorted(agents - allowed)]
    form = ROOT / ".github/ISSUE_TEMPLATE/work-package.yml"
    if form.exists():
        m = re.search(r"options:\s*\[([^\]]*)\]", form.read_text())
        offered = {o.strip() for o in m.group(1).split(",")} if m else set()
        out += [f"{form.relative_to(ROOT)}: owner {o} has no agent file" for o in sorted(offered - agents)]
    return out


def files(pattern: str):
    for p in ROOT.rglob(pattern):
        if not SKIP & set(p.relative_to(ROOT).parts):
            yield p


def requirements() -> list[str]:
    out = []
    for p in files("*.yaml"):
        text = p.read_text(errors="ignore")
        if field(text, "type") != "requirement":
            continue
        rel, req = p.relative_to(ROOT), field(text, "text")
        name = f"{rel} ({field(text, 'id')})"
        if {"needs", "stakeholder-needs"} & set(rel.parts):
            if "shall" in req.lower().split() or "needs" not in req:
                out.append(f"{name}: a need reads '<stakeholder> needs …', without 'shall'")
        elif len(re.findall(r"\bshall\b", req)) != 1:
            out.append(f"{name}: exactly one 'shall' per requirement")
        if VAGUE.search(req):
            out.append(f"{name}: vague word '{VAGUE.search(req).group(0)}'")
    return out


def lengths() -> list[str]:
    out = []
    for name, limit in LIMITS.items():
        for p in files(name):
            words = len(p.read_text(errors="ignore").split())
            if words > limit:
                out.append(f"{p.relative_to(ROOT)}: {words} words, limit about {limit}")
    return out


def main() -> int:
    findings = owners() + requirements() + lengths()
    for f in findings:
        print(f)
    print(f"check: {len(findings)} finding(s)")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())

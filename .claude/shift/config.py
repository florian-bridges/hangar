"""Configuration of the shift, read from shift.toml and an optional, untracked shift.local.toml."""

import tomllib
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]  # the checkout that holds this folder
CFG = tomllib.loads((HERE / "shift.toml").read_text())
LOCAL = HERE / "shift.local.toml"  # per-host overrides, e.g. workdir = "." for a dedicated clone
if LOCAL.exists():
    local = tomllib.loads(LOCAL.read_text())
    CFG = {**CFG, **{k: v for k, v in local.items() if k != "limits"}, "limits": {**CFG["limits"], **local.get("limits", {})}}
CFG["name"] = CFG.get("name") or ROOT.name
CFG["workdir"] = CFG.get("workdir") or f"../{CFG['name']}-run"
CFG["worktrees"] = CFG.get("worktrees") or f"../{CFG['name']}-wt"
LIMITS = CFG["limits"]
WORKDIR = (ROOT / CFG["workdir"]).resolve()  # the shift's own clone on CFG["branch"], or ROOT itself
WORKTREES = (ROOT / CFG["worktrees"]).resolve()

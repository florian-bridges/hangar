"""Configuration of the shift, read from shift.toml."""

import tomllib
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]  # the owner's checkout that holds this folder
CFG = tomllib.loads((HERE / "shift.toml").read_text())
LIMITS = CFG["limits"]
WORKDIR = (ROOT / CFG["workdir"]).resolve()  # the shift's worktree on CFG["branch"]
WORKTREES = (ROOT / CFG["worktrees"]).resolve()

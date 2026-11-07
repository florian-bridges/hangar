#!/bin/sh
# Start the shift in its own worktree (shift.toml: workdir, branch).
set -e
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ]; then
  uv venv -q .venv --python 3.12
  uv pip install -q --python .venv/bin/python -r requirements.txt
fi
eval "$(.venv/bin/python -c 'import config as c; print(f"WORKDIR={c.WORKDIR} BRANCH={c.CFG[\"branch\"]}")')"
if [ ! -d "$WORKDIR" ]; then
  git -C ../.. fetch -q origin "$BRANCH"
  git -C ../.. worktree add "$WORKDIR" "$BRANCH"
fi
git -C "$WORKDIR" pull -q --ff-only origin "$BRANCH"
exec .venv/bin/python shift.py "$@"

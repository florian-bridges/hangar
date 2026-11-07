#!/bin/sh
# Start the shift in its own clone (shift.toml: workdir, branch).
set -e
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ]; then
  uv venv -q .venv --python 3.12
  uv pip install -q --python .venv/bin/python -r requirements.txt
fi
eval "$(.venv/bin/python -c 'import config as c; print(f"WORKDIR={c.WORKDIR} BRANCH={c.CFG[\"branch\"]}")')"
ROOT=$(cd ../.. && pwd)
if [ "$WORKDIR" = "$ROOT" ]; then   # this checkout is the shift's own clone (workdir = ".")
  git -C "$ROOT" checkout -q "$BRANCH"
elif [ ! -d "$WORKDIR" ]; then      # a separate clone, so the owner's checkout can stay on the same branch
  git clone -q --branch "$BRANCH" "$(git -C "$ROOT" remote get-url origin)" "$WORKDIR"
  git -C "$WORKDIR" lfs install --local >/dev/null 2>&1 || true
fi
git -C "$WORKDIR" pull -q --ff-only origin "$BRANCH"
exec .venv/bin/python shift.py "$@"

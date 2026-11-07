#!/bin/sh
# Start the shift in its own clone (shift.toml: workdir, branch).
set -e
cd "$(dirname "$0")"
want=$(sha256sum requirements.txt | cut -c1-16)
if [ ! -x .venv/bin/python ] || [ "$(cat .venv/.requirements 2>/dev/null)" != "$want" ]; then
  [ -x .venv/bin/python ] || uv venv -q .venv --python 3.12
  uv pip install -q --python .venv/bin/python -r requirements.txt
  echo "$want" > .venv/.requirements
fi
eval "$(.venv/bin/python -c 'import config as c; print("WORKDIR=%s BRANCH=%s NAME=%s" % (c.WORKDIR, c.CFG["branch"], c.CFG["name"]))')"
ROOT=$(cd ../.. && pwd -P)  # resolved like Python resolves WORKDIR
if [ "$WORKDIR" != "$ROOT" ] && [ ! -d "$WORKDIR" ]; then  # a separate clone, so the owner's checkout can stay on the branch
  git clone -q --branch "$BRANCH" "$(git -C "$ROOT" remote get-url origin)" "$WORKDIR"
fi
git -C "$WORKDIR" checkout -q "$BRANCH"   # stops here if the clone has uncommitted work
git -C "$WORKDIR" pull -q --ff-only origin "$BRANCH"
if command -v git-lfs >/dev/null; then git -C "$WORKDIR" lfs pull >/dev/null; fi
exec .venv/bin/python shift.py --project "$NAME" "$@"

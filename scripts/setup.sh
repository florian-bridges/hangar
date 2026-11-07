#!/bin/sh
# One-time setup of a new project made from the Hangar template. Run by the owner, from the repository root:
#   scripts/setup.sh              check the tools, install plm, create labels and the develop branch
#   scripts/setup.sh --protect    also protect main (pull request with the owner's approval, CI green)
# Then start Claude Code in the repository and run /meeting kickoff.
set -e
cd "$(dirname "$0")/.."

need() { command -v "$1" >/dev/null || { echo "missing: $1 ($2)"; missing=1; }; }
missing=0
need git "https://git-scm.com"
need git-lfs "https://git-lfs.com"
need node "Node.js >= 22.18, https://nodejs.org"
need npm "comes with Node.js"
need gh "GitHub CLI, https://cli.github.com, then: gh auth login"
need claude "Claude Code, https://claude.com/claude-code"
need uv "only for the shift, https://docs.astral.sh/uv"
[ "$missing" = 0 ] || exit 1

git lfs install --local >/dev/null
version=$(cat .plm-version)
if [ -z "$PLM_SKIP_INSTALL" ]; then
  echo "installing plm $version"
  npm install -g "github:florian-bridges/PLM#$version"
fi
plm validate

echo "creating labels"
label() { gh label create "$1" --color "$2" --description "$3" --force >/dev/null; }
label "type:work-package" 1d76db "Work package toward an entry condition"
label "type:backlog" c5def5 "Minor finding, remark or idea; not an entry condition"
label "needs-owner" d93f0b "Waits for the owner's answer"
label "meeting" 5319e7 "Prepared owner meeting"
label "blocked" b60205 "Cannot go on without help"
label "gate-condition" fbca04 "Condition of a go-with-conditions gate verdict"
label "won't do" ffffff "Stopped, with the reason in the issue"
for f in .claude/agents/*.md; do
  label "owner:$(basename "$f" .md)" ededed "Owned by $(basename "$f" .md)"
done
label "owner:chief-engineer" ededed "Owned by the chief engineer"

if ! git ls-remote --exit-code --heads origin develop >/dev/null; then
  echo "creating develop"
  git branch develop main 2>/dev/null || true
  git push -u origin develop
fi

if [ "$1" = "--protect" ]; then
  echo "protecting main"
  repo=$(gh repo view --json nameWithOwner -q .nameWithOwner)
  gh api -X PUT "repos/$repo/branches/main/protection" --input - >/dev/null <<'JSON'
{
  "required_status_checks": { "strict": false, "contexts": ["check"] },
  "enforce_admins": false,
  "required_pull_request_reviews": { "required_approving_review_count": 1, "require_code_owner_reviews": true },
  "restrictions": null
}
JSON
fi

echo "done. Next: claude, then /meeting kickoff"

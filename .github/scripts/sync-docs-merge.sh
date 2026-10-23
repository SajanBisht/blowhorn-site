#!/usr/bin/env bash
# Merge the docs-sync pull request once its site checks pass, then start
# the master site run that deploys the merged docs.
#
# Why not GitHub's own auto-merge: master has no branch protection, so
# auto-merge has no required checks to wait for and would merge at once —
# before the site run the sync started on the branch has even registered.
# That dispatched run is the only gate, so the merge waits for it here:
# watch the pull request's checks, and merge (squash) only when every one
# of them has passed. A failed check merges nothing: the check watch
# exits non-zero, this script stops, and the pull request stays open for
# a human.
#
# Why the second dispatch: the merge is made with github.token, and a
# push to master made by that token never starts push workflows, so
# site.yml would stay silent on the merge and nothing would deploy. A
# workflow_dispatch run started with the same token is allowed, and on
# master it deploys (site.yml's deploy job runs for any event that is not
# a pull request). The same trick as sync-docs-start-checks.sh, one ref
# later. Run it through make (see the docs-sync-merge target);
# sync-docs.yml calls the same target.
#
# Usage: sync-docs-merge.sh [BRANCH]  (default: docs-sync)
#
# Needs GH_TOKEN (github.token in CI) and, outside this repository,
# GH_REPO=owner/repo so gh knows which repository to act in.
set -euo pipefail
branch="${1:-docs-sync}"

read -r pr state <<< "$(gh pr view "$branch" --json number,state --jq '"\(.number) \(.state)"')"
if [ "$state" != "OPEN" ]; then
  echo "Sync pull request #$pr is $state, not OPEN; nothing to merge."
  exit 0
fi

# Wait for the dispatched site run to show up as a check on the pull
# request before watching anything. Waiting for just any check is not
# enough: the DCO check registers the instant the pull request opens and
# passes in about a second, and a check watch started then sees a
# complete, green list — the site check not yet on it — and merges past
# the very gate this script exists to enforce (seen live, 2026-10-23).
# The site check is site.yml's check job, named in that workflow.
site_check="Lint, build and check"
found=""
for _ in $(seq 1 30); do
  if gh pr checks "$pr" --json name --jq '.[].name' 2>/dev/null | grep -qx "$site_check"; then
    found=1
    break
  fi
  sleep 10
done
if [ -z "$found" ]; then
  echo "The site check '$site_check' never appeared on pull request #$pr; not merging."
  exit 1
fi

# Exits non-zero unless every check on the pull request passes.
gh pr checks "$pr" --watch --interval 10

gh pr merge "$pr" --squash

# The token's merge starts no push workflows (see header): start the
# site run on master that deploys the merged docs.
exec gh workflow run site.yml --ref master

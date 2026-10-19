#!/usr/bin/env bash
# After a public release, start sync-docs.yml at the product's release tag,
# so the published docs (the CLI reference included) match what shipped.
#
# A draft release starts nothing: it is published by hand after review, and
# the docs sync can be run then (Actions > Sync product docs).
#
# Inputs (environment): VERSION (v1.2.3, as resolve.sh validated it), DRAFT
# (true|false), GH_TOKEN (github.token in CI) and, outside this repository,
# GH_REPO=owner/repo.
set -euo pipefail
: "${VERSION:?VERSION is required}"
if [ "${DRAFT:-true}" != "false" ]; then
  echo "sync-docs: draft release; not starting the docs sync"
  exit 0
fi
ref="desktop-${VERSION}"
echo "sync-docs: starting sync-docs.yml at ${ref}"
exec gh workflow run sync-docs.yml -f ref="$ref"

#!/usr/bin/env bash
# Build the docs site and check its internal links with lychee (offline).
#
# Read the Docs serves the site under /en/latest/, and zensical's site_url
# puts that prefix into root-relative links. So the built site is copied to
# _linkcheck/en/latest/ before checking, to match the published layout.
#
# Usage: scripts/check_doc_links.sh [--stage-only] [extra lychee args]
#   --stage-only  build and stage the site, but skip lychee (CI runs lychee
#                 through lycheeverse/lychee-action instead).
# Needs lychee on PATH: https://lychee.cli.rs/installation/
set -euo pipefail

cd "$(dirname "$0")/.."
uv run --group docs zensical build
rm -rf _linkcheck
mkdir -p _linkcheck/en
cp -r site _linkcheck/en/latest

if [[ "${1:-}" == "--stage-only" ]]; then
  exit 0
fi

lychee --offline --no-progress \
  --root-dir "$PWD/_linkcheck" \
  --index-files index.html \
  "$@" \
  '_linkcheck/**/*.html'

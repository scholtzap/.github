#!/usr/bin/env bash
# Apply branch rulesets and squash-only auto-merge across scholtzap and 3BO-Track.
# Talks to GitHub through `gh api` (see apply-rulesets.py).
set -euo pipefail
cd "$(dirname "$0")/.."
python3 scripts/apply-rulesets.py "$@"

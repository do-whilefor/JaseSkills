#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
# Never remove knowledge/ or templates/. Only remove caches and stale generated selftest output.
find "$ROOT" -type d \( -name '__pycache__' -o -name '.pytest_cache' -o -name '.mypy_cache' -o -name '.ruff_cache' \) -prune -exec rm -rf {} +
find "$ROOT" -type f \( -name '*.pyc' -o -name '*.pyo' -o -name '.DS_Store' -o -name '*~' \) -delete
if [ -d "$ROOT/selftest/out" ]; then
  rm -rf "$ROOT/selftest/out"
fi
mkdir -p "$ROOT/selftest/.gitkeep-dir"
# keep legacy selftest directory present without stale evidence files
rmdir "$ROOT/selftest/.gitkeep-dir" 2>/dev/null || true
printf 'cleaned release artifacts under %s\n' "$ROOT"

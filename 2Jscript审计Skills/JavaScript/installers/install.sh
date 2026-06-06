#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
python3 scripts/install_and_env_check.py --root "$ROOT" --out reports/env-check || true
if command -v npm >/dev/null 2>&1; then
  npm install
  npx playwright install chromium || true
fi
python3 scripts/install_and_env_check.py --root "$ROOT" --out reports/env-check

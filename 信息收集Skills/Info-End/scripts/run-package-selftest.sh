#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
OUTDIR="${2:-selftest/out}"
SELFTEST_STEP_TIMEOUT="${SELFTEST_STEP_TIMEOUT:-45}"
python3 "${ROOT%/}/scripts/selftest-step-runner.py" --root "$ROOT" --outdir "$OUTDIR" --timeout "$SELFTEST_STEP_TIMEOUT"

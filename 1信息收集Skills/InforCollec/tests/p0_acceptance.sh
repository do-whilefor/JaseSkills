#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${1:-/tmp/info-end-p0-acceptance}"
rm -rf "$OUT"
node "$ROOT/scripts/js-ast-endpoint-extractor.mjs" "$ROOT/tests/fixtures/key_gap_app" --strict-ast > "$OUT.ast.jsonl"
"${PYTHON:-python3}" "$ROOT/info_end_run.py" --input "$ROOT/tests/fixtures/key_gap_app" --scope "$ROOT/tests/fixtures/key_gap_app" --output "$OUT" --max-files 300 --cve-db "$ROOT/tests/fixtures/key_gap_app/mock-cve-db.json" > "$OUT.run.json"
"${PYTHON:-python3}" "$ROOT/scripts/evidence-schema-validate.py" "$OUT/evidence-manifest.json" --kind evidence-manifest > "$OUT.schema.json"
"${PYTHON:-python3}" "$ROOT/quality/unified_quality_gate.py" --input "$ROOT/tests/fixtures/key_gap_app" --scope "$ROOT/tests/fixtures/key_gap_app" --manifest "$OUT/evidence-manifest.json" > "$OUT.quality.json"
"${PYTHON:-python3}" - <<PY
import json, pathlib
out=pathlib.Path('$OUT')
run=json.loads((out/'collection-run.json').read_text())
sv=json.loads((out/'schema-validation.json').read_text())
q=json.loads((out/'unified-quality-gate.json').read_text())
cov=next(g for g in q['gates'] if g['gate']=='coverage_gate')['coverage']
assert run['status']=='PASS'
assert sv['status']=='PASS'
assert q['status']=='PASS'
assert cov['skipped_reasons'].get('binary_file',0)>=1
assert cov['skipped_reasons'].get('large_file_over_2mb',0)>=1
assert cov['skipped_reasons'].get('symlink_skipped',0)>=1
print(json.dumps({'status':'PASS','schema_checks':len(sv['checks']),'skipped_reasons':cov['skipped_reasons'],'coverage':run['coverage']}, indent=2))
PY

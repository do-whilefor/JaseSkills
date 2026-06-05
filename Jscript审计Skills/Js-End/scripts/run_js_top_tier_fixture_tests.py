#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, sys, tempfile
from pathlib import Path
root=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve()
fixture=root/'fixtures/js-top-tier-samples/app'
out=root/'tests/js-top-tier-last-run'
out.mkdir(parents=True, exist_ok=True)
commands=[
    [sys.executable, str(root/'scripts/js_top_tier_collect.py'), '--root', str(fixture), '--out', str(out)],
    [sys.executable, str(root/'scripts/js_top_tier_analyze.py'), '--ledger', str(out/'js_asset_ledger.json'), '--out', str(out)],
    [sys.executable, str(root/'scripts/js_top_tier_report_generator.py'), '--report-dir', str(out)],
    [sys.executable, str(root/'scripts/js_top_tier_quality_gate.py'), '--report-dir', str(out)],
]
results=[]
for cmd in commands:
    p=subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    results.append({'cmd':' '.join(cmd), 'returncode':p.returncode, 'stdout':p.stdout[-4000:], 'stderr':p.stderr[-4000:]})
    if p.returncode != 0:
        break
ledger=json.loads((out/'js_asset_ledger.json').read_text(encoding='utf-8')) if (out/'js_asset_ledger.json').exists() else {}
analysis=json.loads((out/'js_analysis.json').read_text(encoding='utf-8')) if (out/'js_analysis.json').exists() else {}
gate=json.loads((out/'js_quality_gate.json').read_text(encoding='utf-8')) if (out/'js_quality_gate.json').exists() else {}
checks=[]
checks.append(('collects_js', ledger.get('stats',{}).get('javascript_assets',0) >= 2))
checks.append(('collects_sourcemap', ledger.get('stats',{}).get('sourcemaps',0) >= 1))
checks.append(('finds_graphql_or_ws', any(e.get('kind') in {'graphql_operation_candidate','websocket_candidate'} for e in ledger.get('evidence',[]))))
checks.append(('downgrades_without_dynamic', gate.get('decision') == 'not-top-tier'))
checks.append(('findings_candidate_only_without_backend', analysis.get('semantic_status') in {'candidate-only','ready'}))
ok=all(r['returncode']==0 for r in results) and all(v for _,v in checks)
summary={'ok':ok,'results':results,'checks':dict(checks),'out':str(out),'quality_gate':gate}
(root/'tests/js-top-tier-fixture-test-result.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(summary, ensure_ascii=False, indent=2))
raise SystemExit(0 if ok else 1)

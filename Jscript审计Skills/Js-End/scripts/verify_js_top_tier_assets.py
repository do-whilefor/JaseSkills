#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path
root=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve()
required=[
'15-js-top-tier-collection-analysis-audit/SKILL.md',
'scripts/js_top_tier_collect.py','scripts/js_top_tier_analyze.py','scripts/js_top_tier_quality_gate.py','scripts/run_js_top_tier_fixture_tests.py','scripts/verify_js_top_tier_assets.py',
'scripts/backends/js/babel_extract.mjs','scripts/backends/js/typescript_extract.mjs','scripts/js_runtime_evidence_bridge.py','scripts/js_role_tenant_diff.py','scripts/js_top_tier_report_generator.py',
'schemas/js-top-tier-ledger.schema.json','schemas/js-top-tier-finding.schema.json',
'templates/js-top-tier-report.md','knowledge/js-top-tier-audit-playbook.md',
'data/js_top_tier_collectors.json','data/js_top_tier_detectors.json','data/js_top_tier_quality_caps.json','data/js_top_tier_runtime_requirements.json',
'fixtures/js-top-tier-samples/app/index.html','fixtures/js-top-tier-samples/app/static/js/app.js','fixtures/js-top-tier-samples/app/static/js/app.js.map',
]
errors=[]
for r in required:
    if not (root/r).exists(): errors.append(f'missing: {r}')
for p in root.rglob('*'):
    if p.name == '__pycache__' or p.suffix == '.pyc' or p.name in {'.DS_Store','Thumbs.db'} or p.suffix in {'.tmp','.bak','.swp'}:
        errors.append(f'forbidden cache file: {p.relative_to(root)}')
print(json.dumps({'ok': not errors, 'errors': errors}, ensure_ascii=False, indent=2))
raise SystemExit(1 if errors else 0)

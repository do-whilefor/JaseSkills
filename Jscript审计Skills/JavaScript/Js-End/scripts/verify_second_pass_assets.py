#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path
root=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve()
required={
 '13-js-skills-second-pass-reverse-auditor/SKILL.md':1,
 'scripts/second_pass_reverse_audit.py':1,
 'scripts/verify_second_pass_assets.py':1,
 'schemas/second-pass-review.schema.json':1,
 'templates/second-pass-reverse-audit-report.md':1,
 'docs/SECOND_PASS_REVERSE_AUDIT.md':1,
 'knowledge/second-pass-js-audit-fidelity-rules.md':1,
 'data/second_pass_original_conclusion_checks.json':8,
 'data/second_pass_js_collection_points.json':30,
 'data/second_pass_js_audit_capabilities.json':20,
 'data/second_pass_severe_js_chains.json':25,
 'data/second_pass_unconventional_js_audit_points.json':40,
 'data/second_pass_score_rules.json':1,
 'fixtures/second-pass-negative/fake-ready-ast.json':1,
 'fixtures/second-pass-blocked/static-candidate-as-verified.json':1,
 'fixtures/second-pass-needs-review/doc-only-runtime-bridge.json':1,
}
errors=[]
for rel,min_count in required.items():
    p=root/rel
    if not p.exists():
        errors.append(f'missing: {rel}'); continue
    if p.suffix=='.json':
        data=json.loads(p.read_text(encoding='utf-8'))
        count=len(data) if isinstance(data,list) else 1
        if count < min_count:
            errors.append(f'too few entries: {rel} has {count}, need {min_count}')
    elif not p.read_text(encoding='utf-8', errors='ignore').strip():
        errors.append(f'empty: {rel}')
print(json.dumps({'ok':not errors,'errors':errors}, ensure_ascii=False, indent=2))
raise SystemExit(1 if errors else 0)

#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path
root=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve()
required={
 'data/js_collection_points.json':20,
 'data/js_audit_capabilities.json':30,
 'data/js_severe_vulnerability_chains.json':30,
 'data/info_js_linkage_matrix.json':10,
 'data/script_inventory_expected.json':15,
 'templates/extreme-skills-review-report.md':1,
 'schemas/extreme-review.schema.json':1,
 '12-js-skills-extreme-reviewer/SKILL.md':1,
 'knowledge/extreme-js-skills-review-checklist.md':1,
 'data/second_pass_js_collection_points.json':30,
 'data/second_pass_js_audit_capabilities.json':20,
 'data/second_pass_severe_js_chains.json':25,
 'data/second_pass_unconventional_js_audit_points.json':40,
 'scripts/second_pass_reverse_audit.py':1,
 '13-js-skills-second-pass-reverse-auditor/SKILL.md':1,
}

errors=[]
for rel,min_count in required.items():
    p=root/rel
    if not p.exists():
        errors.append(f'missing: {rel}'); continue
    if p.suffix=='.json':
        data=json.loads(p.read_text(encoding='utf-8'))
        count=len(data) if isinstance(data,list) else 1
        if count < min_count: errors.append(f'too few entries: {rel} has {count}, need {min_count}')
    elif not p.read_text(encoding='utf-8').strip():
        errors.append(f'empty: {rel}')
print(json.dumps({'ok':not errors,'errors':errors}, ensure_ascii=False, indent=2))
raise SystemExit(1 if errors else 0)

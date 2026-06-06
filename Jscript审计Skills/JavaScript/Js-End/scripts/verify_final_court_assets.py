#!/usr/bin/env python3
from __future__ import annotations
import json, sys, subprocess
from pathlib import Path
root = Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve()
required = [
 '14-js-skills-evidence-court/SKILL.md',
 'scripts/final_evidence_court_audit.py',
 'scripts/verify_final_court_assets.py',
 'schemas/final-evidence-court.schema.json',
 'templates/final-evidence-court-report.md',
 'docs/FINAL_EVIDENCE_COURT.md',
 'knowledge/final-evidence-court-rules.md',
 'data/final_court_prior_conclusion_trial.json',
 'data/final_court_js_collection_incidents.json',
 'data/final_court_pseudo_capabilities.json',
 'data/final_court_severe_miss_risks.json',
 'data/final_court_engineering_autopsy.json',
 'data/final_court_score_penalty_rules.json',
 'data/final_court_p0_nonnegotiable.json',
 'data/final_court_final_findings.json',
 'templates/final-evidence-court-report.md',
]
errors=[]
for rel in required:
    if not (root/rel).exists(): errors.append(f'missing: {rel}')
# cardinality checks
checks = {
 'data/final_court_js_collection_incidents.json':20,
 'data/final_court_pseudo_capabilities.json':10,
 'data/final_court_severe_miss_risks.json':30,
 'data/final_court_engineering_autopsy.json':10,
 'data/final_court_p0_nonnegotiable.json':10,
}
for rel, min_items in checks.items():
    if (root/rel).exists():
        try:
            data=json.loads((root/rel).read_text(encoding='utf-8'))
            if len(data) < min_items: errors.append(f'{rel}: expected >= {min_items}, got {len(data)}')
        except Exception as e:
            errors.append(f'{rel}: invalid json: {e}')
if not errors:
    proc=subprocess.run([sys.executable, str(root/'scripts/final_evidence_court_audit.py'), str(root)], text=True, capture_output=True)
    if proc.returncode != 0:
        errors.append('final_evidence_court_audit failed: ' + proc.stdout + proc.stderr)
print(json.dumps({'ok': not errors, 'errors': errors}, ensure_ascii=False, indent=2))
raise SystemExit(1 if errors else 0)

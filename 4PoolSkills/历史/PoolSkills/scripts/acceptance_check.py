#!/usr/bin/env python3
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
required_root = [
  'SKILL.md','README.md','CAPABILITY_MATRIX.md','SECURITY_AUDIT_WORKFLOW.md','QUALITY_GATE.md',
  'CANDIDATE_STATE_MACHINE.md','SECURITY_GRAPH_SCHEMA.json','VULNERABILITY_CHAIN_RULES.md','REPORT_GENERATION_CONTRACT.md','REVIEW_QUEUE.md','INSTALL_AND_VERIFY.md'
]
required_dirs = ['skills','schemas','tools','tests/fixtures','tests/replay','reports/templates','dashboard','rules','knowledge','vulnerability_templates','vulnerability_research_units','raw_original_kb_templates']
required_scripts = ['state_machine_validate.py','tool_health_score.py','adversarial_regression_runner.py','dashboard_status_generator.py','evidence_report_generator.py']
unit_files = ['README.md','STATIC_RULES.md','DYNAMIC_VALIDATION.md','NON_DESTRUCTIVE_BOUNDARY.md','FALSE_POSITIVE_FILTER.md','EVIDENCE_FIELDS.json','QUALITY_GATE.yaml','REPORT_TEMPLATE.md','TEST_CASES.md','FRAMEWORK_NOTES.md']
errors=[]
for f in required_root:
    if not (ROOT/f).exists(): errors.append(f'missing root file {f}')
for d in required_dirs:
    if not (ROOT/d).exists(): errors.append(f'missing directory {d}')
for f in required_scripts:
    if not (ROOT/'scripts'/f).exists(): errors.append(f'missing script {f}')
for skill in (ROOT/'skills').iterdir():
    if skill.is_dir() and (skill/'SKILL.md').exists() and not (skill/'EXECUTION_CONTRACT.md').exists(): errors.append(f'missing execution contract {skill.name}')
units=list((ROOT/'vulnerability_research_units').glob('*'))
if len(units) != 23: errors.append(f'expected 23 research units, found {len(units)}')
for u in units:
    for f in unit_files:
        if not (u/f).exists(): errors.append(f'missing {u.name}/{f}')
adv_path=ROOT/'tests/adversarial_regression_cases.json'
if adv_path.exists():
    adv=json.loads(adv_path.read_text(encoding='utf-8'))
    if len(adv.get('cases',[])) < 20: errors.append('adversarial cases < 20')
else:
    errors.append('missing tests/adversarial_regression_cases.json')
status='pass' if not errors else 'fail'
result={'status':status,'errors':errors,'research_unit_count':len(units)}
(ROOT/'outputs').mkdir(exist_ok=True)
(ROOT/'outputs/acceptance_result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(result, ensure_ascii=False, indent=2))
raise SystemExit(0 if not errors else 1)

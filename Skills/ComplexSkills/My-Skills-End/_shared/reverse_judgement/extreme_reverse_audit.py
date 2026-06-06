#!/usr/bin/env python3
from __future__ import annotations
import json, sys, re
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
SHARED = ROOT / '_shared'
RJ = SHARED / 'reverse_judgement'
ERRORS=[]

def load(rel):
    return json.loads((ROOT/rel).read_text(encoding='utf-8'))

def check(cond,msg):
    if not cond: ERRORS.append(msg)

def exists(rel):
    return bool(rel) and (ROOT/rel).exists()

def check_claim_traceability():
    data=load('_shared/reverse_judgement/evaluation_claim_traceability.json')
    required=data.get('mandatory_fields') or []
    check(len(data.get('claims',[]))>=15,'claim traceability must contain at least 15 corrected judgement items')
    for c in data.get('claims',[]):
        for f in required:
            check(f in c and c[f] not in ('',[],{}), f'claim {c.get("claim_id")} missing {f}')
        for f in ['concrete_file_path','repair_file','script_change','test_change']:
            val=c.get(f)
            if isinstance(val,str) and val.startswith('_shared/') or isinstance(val,str) and val.startswith('skills/') or isinstance(val,str) and val in {'SELFTEST_E2E_REPLAY_RESULT.json','SELFTEST_TOOL_HEALTH_RESULT.json','_shared/runs/playwright_local_capture_result_v41.json'}:
                check(exists(val), f'claim {c.get("claim_id")} references missing {f}: {val}')

def check_info_matrix():
    data=load('_shared/reverse_judgement/information_collection_coverage_matrix.json')
    items=data.get('items',[]); ids={i.get('id') for i in items}
    check(len(items)>=42, f'information matrix must cover >=42 sources, got {len(items)}')
    for prefix in [f'INFO{i:02d}' for i in range(1,43)]:
        check(any(str(x).startswith(prefix) for x in ids), f'information matrix missing {prefix}')
    for i in items:
        for key in ['responsible_skill','rule_file','output_field','manifest_field','test_file','expected_output','failure_judgement','quality_gate','priority']:
            check(i.get(key) not in (None,'',[],{}), f'info item {i.get("id")} missing {key}')
        for key in ['responsible_skill','rule_file','test_file']:
            check(exists(i.get(key)), f'info item {i.get("id")} missing file {key}: {i.get(key)}')

def check_js_matrix():
    data=load('_shared/reverse_judgement/js_audit_coverage_matrix.json')
    items=data.get('items',[]); ids={i.get('id') for i in items}
    check(len(items)>=44, f'JS matrix must cover >=44 audit points, got {len(items)}')
    for prefix in [f'JS{i:02d}' for i in range(1,45)]:
        check(any(str(x).startswith(prefix) for x in ids), f'JS matrix missing {prefix}')
    for i in items:
        for key in ['responsible_skill','ast_or_parser_requirement','rule_file','output_field','candidate_vulnerability_linkage','manifest_field','test_file','quality_gate','report_section']:
            check(i.get(key) not in (None,'',[],{}), f'js item {i.get("id")} missing {key}')
        for key in ['responsible_skill','rule_file','test_file']:
            check(exists(i.get(key)), f'js item {i.get("id")} missing file {key}: {i.get(key)}')

def check_vuln_matrix():
    data=load('_shared/reverse_judgement/vulnerability_coverage_matrix_23.json')
    items=data.get('items',[])
    check(len(items)==23, f'vulnerability matrix must cover exactly 23 classes, got {len(items)}')
    required=['template_id','vulnerability_type','trigger_condition','non_trigger_condition','static_evidence_required','dynamic_evidence_required','non_destructive_boundary','impact_proof','false_positive_exclusion','minimum_evidence_threshold','report_template','evidence_fields','quality_overlay','replay_fixtures','failure_handling','info_collection_linkage','js_audit_linkage','code_graph_linkage','manifest_linkage','quality_gate','final_conclusion']
    for i in items:
        for key in required:
            check(i.get(key) not in (None,'',[],{}), f'vuln {i.get("template_id")} missing {key}')
        for key in ['report_template','evidence_fields','quality_overlay']:
            check(exists(i.get(key)), f'vuln {i.get("template_id")} missing file {key}: {i.get(key)}')
        for name, rel in (i.get('replay_fixtures') or {}).items():
            check(exists(rel), f'vuln {i.get("template_id")} missing replay {name}: {rel}')

def check_controls():
    for rel, min_count in [('_shared/reverse_judgement/ai_hallucination_controls.json',15),('_shared/reverse_judgement/false_negative_controls.json',15),('_shared/reverse_judgement/false_positive_controls.json',15)]:
        d=load(rel); items=d.get('items',[]); check(len(items)>=min_count, f'{rel} must have >= {min_count} controls')
        for i in items:
            for key in ['risk_id','quality_gate']:
                check(i.get(key), f'{rel} item missing {key}')

def check_active_docs_reference_extreme_layer():
    for rel in ['SKILL.md','README_SYSTEM.md','CLAUDE.md','skills/10-regression-selftest-dashboard/SKILL.md','_shared/selftest/verify_system_integrity.py']:
        txt=(ROOT/rel).read_text(encoding='utf-8', errors='ignore')
        check('extreme_reverse_audit.py' in txt or 'reverse_judgement' in txt, f'{rel} must reference reverse judgement layer')

def main():
    check_claim_traceability(); check_info_matrix(); check_js_matrix(); check_vuln_matrix(); check_controls(); check_active_docs_reference_extreme_layer()
    result={'passed':not ERRORS,'errors':ERRORS,'summary':{'claim_count':len(load('_shared/reverse_judgement/evaluation_claim_traceability.json')['claims']),'info_count':len(load('_shared/reverse_judgement/information_collection_coverage_matrix.json')['items']),'js_count':len(load('_shared/reverse_judgement/js_audit_coverage_matrix.json')['items']),'vuln_count':len(load('_shared/reverse_judgement/vulnerability_coverage_matrix_23.json')['items'])}}
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 1 if ERRORS else 0
if __name__=='__main__':
    sys.exit(main())

#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import json, subprocess, sys
from _info_collect_lib import common_parser, parse_scope, enforce_scope, find_unredacted_secrets
ROOT=Path(__file__).resolve().parents[1]
REQUIRED={'authorization-scope','project-fingerprint','technology-stack','route-api-inventory','frontend-js','configuration-deployment','auth-role-tenant','hidden-information','dependency-surface','evidence-index'}
HIGH_VALUE={'frontend_hidden_api_literal','openapi_path_operation','postman_request','authentication_entry','authorization_middleware','tenant_boundary_signal','secret_name_signal','source_map_artifact','service_worker_cache_entry','dangerous_package_script','framework_route','auth_graph_edge','frontend_artifact_node','iac_cloud_asset','openapi_code_diff'}

def run_schema(path: Path) -> tuple[bool, list[str]]:
    proc=subprocess.run([sys.executable, str(ROOT/'scripts'/'evidence-schema-validate.py'), str(path), '--kind','evidence-manifest'], text=True, capture_output=True)
    if proc.returncode == 0: return True, []
    try:
        data=json.loads(proc.stdout); return False, data.get('errors', [proc.stdout+proc.stderr])
    except Exception:
        return False, [proc.stdout+proc.stderr]

def main():
    ap=common_parser('Strict information collection quality gate: schema, scope, redaction, section coverage and candidate evidence density.')
    ap.add_argument('--min-score',type=int,default=70)
    args=ap.parse_args(); path=Path(args.input).resolve(); scope=parse_scope(args.scope,path); ok,reason=enforce_scope(path,scope)
    if not ok: print(json.dumps({'status':'FAIL','score':0,'reason':reason},ensure_ascii=False)); return 2
    schema_ok,schema_errors=run_schema(path)
    data=json.loads(path.read_text(encoding='utf-8',errors='ignore'))
    items=data.get('items',[]) if isinstance(data,dict) else []
    sections={it.get('linked_report_section') for it in items if isinstance(it,dict)}
    missing=sorted(x for x in REQUIRED if x not in sections)
    secret_failures=[]
    bad_redaction=[]
    for i,it in enumerate(items):
        if not isinstance(it,dict): continue
        paths=find_unredacted_secrets(it.get('discovered_item_value_redacted'))
        if paths:
            secret_failures.append({'index':i,'evidence_id':it.get('evidence_id'),'paths':paths[:5]})
        if it.get('redaction_status') == 'not_sensitive_or_no_secret_literal' and paths:
            bad_redaction.append(i)
    review=sum(1 for it in items if isinstance(it,dict) and it.get('needs_human_review'))
    high=sum(1 for it in items if isinstance(it,dict) and it.get('discovered_item_type') in HIGH_VALUE)
    score=100
    score -= len(missing)*6
    if not schema_ok: score -= 30
    if secret_failures: score -= 50
    if bad_redaction: score -= 20
    if not high: score -= 8
    # Human review count is informational only; it never adds score.
    score=max(0,min(score,100))
    blockers=[]
    if not schema_ok: blockers.append('schema_validation_failed')
    if secret_failures: blockers.append('unredacted_secret_detected')
    if bad_redaction: blockers.append('redaction_status_contradiction')
    status='PASS' if score>=args.min_score and not blockers else 'FAIL'
    report={'schema_version':'info-quality-gate.v2','status':status,'score':score,'item_count':len(items),'missing_sections':missing,'schema_ok':schema_ok,'schema_errors':schema_errors[:20],'redaction_ok':not secret_failures,'secret_failures':secret_failures[:20],'redaction_status_errors':bad_redaction[:20],'human_review_items':review,'human_review_scoring':'informational_only_no_score_bonus','high_value_candidates':high,'blockers':blockers,'gate_note':'PASS means evidence quality is sufficient for next manual/security review, not that vulnerabilities are confirmed.'}
    out=args.output or '-'; text=json.dumps(report,ensure_ascii=False,indent=2)
    if out=='-': print(text)
    else: Path(out).write_text(text,encoding='utf-8')
    return 0 if status=='PASS' else 1
if __name__=='__main__': raise SystemExit(main())

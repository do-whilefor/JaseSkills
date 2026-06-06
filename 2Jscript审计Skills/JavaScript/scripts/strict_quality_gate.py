#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
VALID_STATUS = {"candidate","verified","false_positive","insufficient_evidence","not_reportable","not_deliverable"}
REQUIRED_TOP = ["id","title","type","severity","status","scope","code_evidence","dynamic_requests","dynamic_responses","reproduce_count","impact","false_positive_checks","fix"]
REQUIRED_VERIFIED = ["code_evidence","dynamic_requests","dynamic_responses","impact","false_positive_checks","accounts_used","fix"]
REPRO_FIELDS = ["time","request","response","account_role","target_resource","logs","code_location","conclusion"]
def nonempty(v):
    if v is None: return False
    if isinstance(v,str): return bool(v.strip())
    if isinstance(v,(list,tuple,dict)): return len(v)>0
    return bool(v)
def check(item):
    missing=[]
    for k in REQUIRED_TOP:
        if k not in item: missing.append(k)
    status=item.get('status')
    if status not in VALID_STATUS: missing.append('valid_status')
    if status=='verified':
        scope=item.get('scope') or {}
        if scope.get('authorized') is not True: missing.append('scope.authorized=true')
        if scope.get('non_destructive') is not True: missing.append('scope.non_destructive=true')
        if not nonempty(scope.get('target')): missing.append('scope.target')
        for k in REQUIRED_VERIFIED:
            if not nonempty(item.get(k)): missing.append(k)
        reps=item.get('reproductions') or []
        if int(item.get('reproduce_count') or 0)<3: missing.append('reproduce_count>=3')
        if len(reps)<3: missing.append('reproductions>=3')
        for i, r in enumerate(reps[:3],1):
            if not isinstance(r,dict): missing.append(f'reproduction_{i}_object'); continue
            for f in REPRO_FIELDS:
                if not nonempty(r.get(f)): missing.append(f'reproduction_{i}.{f}')
        if missing: return 'FAIL_DOWNGRADE_INSUFFICIENT_EVIDENCE', missing, 'insufficient_evidence'
    if status=='not_reportable' and not nonempty(item.get('not_reportable_reason')):
        return 'FAIL_MISSING_NOT_REPORTABLE_REASON',['not_reportable_reason'],'not_reportable'
    if status=='not_deliverable' and not nonempty(item.get('not_deliverable_reason')):
        return 'FAIL_MISSING_NOT_DELIVERABLE_REASON',['not_deliverable_reason'],'not_deliverable'
    return 'PASS' if not missing else 'PASS_WITH_WARNINGS', missing, status or 'not_deliverable'
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('manifest')
    args=ap.parse_args(); path=Path(args.manifest)
    items=[]
    if path.is_dir():
        for p in path.rglob('*.json'): items.append((p,json.loads(p.read_text(encoding='utf-8'))))
    else: items.append((path,json.loads(path.read_text(encoding='utf-8'))))
    rc=0
    for p,item in items:
        decision, miss, final=check(item)
        print(json.dumps({'file':str(p),'id':item.get('id'),'input_status':item.get('status'),'decision':decision,'final_status':final,'missing_or_warnings':miss}, ensure_ascii=False))
        if decision.startswith('FAIL'): rc=1
    return rc
if __name__=='__main__': raise SystemExit(main())

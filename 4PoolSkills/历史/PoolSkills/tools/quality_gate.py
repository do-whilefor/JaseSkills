#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
DYN_CONFIRMED='DYNAMIC_CONFIRMED'
PROMOTED_REQUIREMENTS=['has_code_evidence','has_runtime_evidence','has_negative_control','has_report_mapping','non_destructive']

def evaluate(candidates, evidence=None):
    ev_by_id={}
    if evidence:
        for f in evidence.get('findings',[]): ev_by_id[f.get('candidate_id')]=f
    findings=[]; overall='pass'
    for c in candidates.get('candidates',[]):
        cid=c.get('id','unknown'); input_status=c.get('status','candidate'); dyn=c.get('dynamic_state','STATIC_CANDIDATE')
        ev=ev_by_id.get(cid,{})
        ev_items=ev.get('evidence',[])
        has_code=bool(c.get('code_evidence')) or any(e.get('kind')=='source_line' for e in ev_items)
        has_runtime=bool(c.get('runtime_evidence') or c.get('dynamic_evidence')) or any(e.get('kind') in {'runtime','request_response','har','screenshot'} for e in ev_items)
        has_negative=bool(c.get('negative_controls'))
        has_report=bool(c.get('report_mapping'))
        nd=c.get('non_destructive') or {}
        non_destructive=nd.get('is_non_destructive') is True and nd.get('data_modified') is False
        hard=[]
        if not non_destructive: hard.append('non_destructive_boundary_missing_or_failed')
        if input_status in {'blocked','validation_blocked'} or dyn in {'DYNAMIC_BLOCKED','UNSAFE_TO_TEST'}:
            out='blocked'; level='none'; hard.append('validation_blocked_or_unsafe')
        elif dyn==DYN_CONFIRMED:
            if not has_code: hard.append('missing_code_evidence')
            if not has_runtime: hard.append('missing_runtime_evidence')
            if not has_negative: hard.append('missing_negative_control')
            if not has_report: hard.append('missing_report_mapping')
            out='promoted' if not hard else 'needs_review'
            level='confirmed' if out=='promoted' else 'inconclusive'
        else:
            hard.append('static_candidate_only')
            if not has_code: hard.append('missing_code_evidence')
            out='needs_review' if input_status!='blocked' else 'blocked'
            level='candidate' if out=='needs_review' else 'none'
        if hard and overall=='pass': overall='needs_review'
        if out=='blocked': overall='blocked' if overall!='needs_review' else overall
        findings.append({'candidate_id':cid,'input_status':input_status,'dynamic_state':dyn,'output_status':out,'hard_failures':hard,'allowed_report_level':level,'checks':{'has_code_evidence':has_code,'has_runtime_evidence':has_runtime,'has_negative_control':has_negative,'has_report_mapping':has_report,'non_destructive':non_destructive},'anti_hallucination':'static candidates cannot be reported as confirmed'})
    return {'schema_version':'quality-result-v1','overall_status':overall if findings else 'inconclusive','promotion_policy':{'promoted_requires':PROMOTED_REQUIREMENTS,'confirmed_requires_dynamic_state':DYN_CONFIRMED},'findings':findings}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--candidates',required=True); ap.add_argument('--evidence'); ap.add_argument('--out',required=True); ns=ap.parse_args()
    cand=json.loads(Path(ns.candidates).read_text(encoding='utf-8'))
    ev=json.loads(Path(ns.evidence).read_text(encoding='utf-8')) if ns.evidence else None
    data=evaluate(cand,ev); Path(ns.out).parent.mkdir(parents=True, exist_ok=True); Path(ns.out).write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'ok':True,'overall_status':data['overall_status'],'findings':len(data['findings'])}, ensure_ascii=False))
if __name__=='__main__': main()

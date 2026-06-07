#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
SAFE_PAYLOADS={'ssrf':'http://127.0.0.1/__non_destructive_probe__','sql_nosql_injection':'SAFE_QUOTE_TEST','command_injection':'echo SAFE_PROBE','path_traversal':'..%2FSAFE_NON_EXISTENT_FILE'}

def _route_path(f):
    routes=f.get('affected_routes') or []
    for r in routes:
        if r.get('path'): return r.get('path')
    return '/'

def _method(f):
    routes=f.get('affected_routes') or []
    for r in routes:
        if r.get('method'): return str(r.get('method')).upper()
    return 'GET'

def make_plan(f):
    det=f.get('detector_id','generic')
    payload=SAFE_PAYLOADS.get(det,'SAFE_NON_DESTRUCTIVE_VARIATION')
    path=_route_path(f); method=_method(f)
    return {
        'replay_plan_id':f.get('replay_plan_id','rp-'+f['finding_id']),
        'finding_id':f['finding_id'],
        'mode':'playwright_authorized_matrix_replay',
        'non_destructive':True,
        'payload_policy':'blocked if destructive_action_blocklist matches',
        'target_path':path,
        'steps':[
            {'id':'positive_static_context','action':'review_source_context','evidence_ref':(f.get('evidence_refs') or [None])[0]},
            {'id':'positive_open_route','action':'goto','url':path,'description':'open affected route or root within authorized target'},
            {'id':'trigger_lazy_load','action':'trigger_lazy_load','description':'scroll to trigger lazy-loaded chunks'},
            {'id':f.get('negative_test_id','negative'),'action':'negative_control','description':'same route/API with unauthorized role or different tenant must be denied','method':method,'path':path,'expected_status':403,'payload':payload},
            {'id':f.get('blocked_test_id','blocked'),'action':'blocked_control','description':'destructive payload variants are refused before execution','payload':'DROP TABLE must be blocked, not sent'}
        ],
        'required_evidence':['request','response','screenshot_or_dom','role','tenant','negative_control','blocked_control','sanitized_evidence_manifest']
    }

def convert(candidates_file):
    data=json.loads(Path(candidates_file).read_text(encoding='utf-8')); findings=data.get('findings') or data.get('candidates') or []
    return {'schema_version':'replay-plan-v1','plans':[make_plan(f) for f in findings],'policy':'Generated plans are non-destructive. Execution requires explicit authorized target_url, scope, and role/tenant matrix.'}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--candidates',required=True); ap.add_argument('--out',required=True); ns=ap.parse_args(); data=convert(ns.candidates); Path(ns.out).parent.mkdir(parents=True,exist_ok=True); Path(ns.out).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(json.dumps({'plans':len(data['plans'])},ensure_ascii=False))
if __name__=='__main__': main()

#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, hashlib
from pathlib import Path

def h(s): return hashlib.sha256(s.encode()).hexdigest()[:16]

def build(candidates_file, out_file):
    data=json.loads(Path(candidates_file).read_text(encoding='utf-8'))
    plans=[]
    for c in data.get('candidates',[]):
        route=c.get('route') or '/'
        method=(c.get('method') or 'GET').upper()
        cid=c.get('id')
        safe_method = method in {'GET','HEAD','OPTIONS'}
        plans.append({
            'id':'replay-'+h(cid or json.dumps(c,sort_keys=True)),
            'candidate_id':cid,
            'type':c.get('type'),
            'status':'validation_planned' if safe_method else 'needs_manual_non_destructive_design',
            'positive_control':{'actor':'authorized_owner_or_admin','method':method,'path':route,'expected':'baseline allowed response; capture status/body ownership fields'},
            'negative_control':{'actor':'lower_privilege_or_cross_tenant','method':method if safe_method else 'GET_OR_SAFE_DRYRUN_ONLY','path':route,'expected':'deny or no object leakage'},
            'blocked_control':{'actor':'out_of_scope_or_destructive','expected':'do not execute; mark blocked'},
            'evidence_required':['HAR','request_response_summary','screenshot_or_console_if_browser','role_tenant_matrix','object_owner_or_tenant_field'],
            'non_destructive_guard':{'allow_methods':['GET','HEAD','OPTIONS'],'mutating_methods_require':'explicit local test fixture and rollback plan'},
            'report_rule':'candidate remains needs_review unless positive and negative controls are both recorded'
        })
    out={'schema_version':'replay-plan-v1','source_candidates':candidates_file,'plans':plans,'policy':'non-destructive replay only; destructive payloads and third-party targets are blocked'}
    Path(out_file).parent.mkdir(parents=True,exist_ok=True); Path(out_file).write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'ok':True,'plans':len(plans)},ensure_ascii=False))

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--candidates',required=True); ap.add_argument('--out',required=True); ns=ap.parse_args(); build(ns.candidates,ns.out)
if __name__=='__main__': main()

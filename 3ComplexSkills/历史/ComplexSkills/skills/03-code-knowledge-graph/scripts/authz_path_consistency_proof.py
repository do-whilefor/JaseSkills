#!/usr/bin/env python3
"""Controller/service/repository authorization consistency proof builder."""
from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path
from typing import Any
ROOT=Path(__file__).resolve().parents[3]
AUTHZ=re.compile(r'authz|policy|permission|role|owner|tenant|guard|acl|rbac|preauthorize|authorize|can\(', re.I)
QUERY=re.compile(r'query|where|find|select|update|delete|repository|dao|model', re.I)

def load(p): return json.loads(Path(p).read_text(encoding='utf-8', errors='ignore'))
def eid(*p): return 'EVID-' + hashlib.sha256('|'.join(map(str,p)).encode()).hexdigest()[:16]

def build(cg: dict[str,Any]) -> dict[str,Any]:
    proofs=[]
    for i,ch in enumerate(cg.get('route_to_handler_chains') or []):
        route=ch.get('route') or {}; file=route.get('file')
        authz=ch.get('authz') or []; queries=ch.get('queries') or []; sinks=ch.get('sinks') or []; params=ch.get('parameters') or []
        layer_presence={'controller': bool(authz), 'service': False, 'repository': bool(queries)}
        # Heuristic layer proof from symbol/call names in same file and code graph query/model edges.
        blob=json.dumps(ch, ensure_ascii=False)
        service_authz=bool(re.search(r'service[^\n]{0,100}(authorize|permission|tenant|owner|role)|authorize[^\n]{0,100}service', blob, re.I))
        repo_tenant=bool(re.search(r'(where|filter|query)[^\n]{0,160}(tenant|owner|org|workspace|user_id)|tenant[^\n]{0,160}(where|filter|query)', blob, re.I))
        layer_presence['service']=service_authz
        layer_presence['repository']=layer_presence['repository'] and repo_tenant
        missing=[k for k,v in layer_presence.items() if not v]
        severity='needs_review' if missing and (sinks or params) else 'candidate'
        proofs.append({'proof_id':'AUTHZPATH-'+str(i+1),'evidence_id':eid(file, route.get('route'), i),'route':route,'file':file,'layers':layer_presence,'missing_layers':missing,'state':severity,'confirmed':False,'code_path_evidence':{'authz_boundaries':authz[:8],'queries':queries[:8],'sinks':sinks[:8],'parameters':params[:8]},'claim_policy':'Missing or present authz signals are proof obligations only; confirmed requires replay evidence and negative controls.'})
    return {'schema_version':'authz_path_consistency_proof_v1','proof_count':len(proofs),'proofs':proofs,'promotion_policy':'No controller/service/repository authz conclusion may be confirmed from signal-only proof.'}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--code-graph', required=True); ap.add_argument('--out'); ap.add_argument('--validate', action='store_true')
    a=ap.parse_args(); obj=build(load(a.code_graph))
    if a.validate:
        try:
            import jsonschema
            schema=load(ROOT/'schemas/authz_path_proof.schema.json'); errs=[e.message for e in jsonschema.Draft202012Validator(schema).iter_errors(obj)]
            if errs: obj['schema_errors']=errs
        except Exception as exc: obj['schema_errors']=[f'jsonschema_unavailable:{exc}']
    text=json.dumps(obj, ensure_ascii=False, indent=2)
    if a.out: Path(a.out).parent.mkdir(parents=True, exist_ok=True); Path(a.out).write_text(text+'\n', encoding='utf-8')
    else: print(text)
    return 0 if not obj.get('schema_errors') else 1
if __name__=='__main__': raise SystemExit(main())

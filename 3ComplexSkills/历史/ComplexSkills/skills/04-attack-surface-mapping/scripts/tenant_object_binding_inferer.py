#!/usr/bin/env python3
"""Infer tenant/object bindings from ORM/schema/model/query evidence."""
from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path
from typing import Any
ROOT=Path(__file__).resolve().parents[3]
TENANT=re.compile(r'(?i)(tenant_id|tenantId|org_id|orgId|organization_id|workspace_id|workspaceId|account_id|company_id|team_id)')
OWNER=re.compile(r'(?i)(owner_id|ownerId|user_id|userId|created_by|member_id|principal_id)')
MODEL=re.compile(r'(?i)(model|schema|entity|table|collection|struct|class)')
def load(p): return json.loads(Path(p).read_text(encoding='utf-8', errors='ignore'))
def eid(*p): return 'EVID-' + hashlib.sha256('|'.join(map(str,p)).encode()).hexdigest()[:16]
def build(cg):
    bindings=[]
    rows=(cg.get('models') or []) + (cg.get('queries') or []) + (cg.get('parameters') or []) + (cg.get('tenant_boundaries') or [])
    for i,r in enumerate(rows):
        blob=json.dumps(r, ensure_ascii=False)
        tf=TENANT.findall(blob); of=OWNER.findall(blob)
        if not tf and not of: continue
        kind='tenant_and_owner' if tf and of else 'tenant' if tf else 'owner'
        bindings.append({'binding_id':'TOB-'+str(len(bindings)+1),'evidence_id':eid(r.get('file'), r.get('line'), kind, i),'file':r.get('file'),'line':r.get('line'),'binding_kind':kind,'tenant_fields':sorted(set(tf)),'owner_fields':sorted(set(of)),'source_row':r,'confidence':'medium' if r.get('parser_confidence') in {'full_ast','ast_lite'} else 'low','confirmed':False,'required_proof':'Must be linked to executed role/tenant matrix and ORM query path before confirmed.'})
    return {'schema_version':'tenant_object_binding_inference_v1','binding_count':len(bindings),'bindings':bindings,'confidence_policy':'Inference is candidate evidence. Absence of binding does not prove isolation failure; presence does not prove enforcement.'}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--code-graph', required=True); ap.add_argument('--out'); ap.add_argument('--validate', action='store_true')
    a=ap.parse_args(); obj=build(load(a.code_graph))
    if a.validate:
        try:
            import jsonschema
            schema=load(ROOT/'schemas/tenant_object_binding.schema.json'); errs=[e.message for e in jsonschema.Draft202012Validator(schema).iter_errors(obj)]
            if errs: obj['schema_errors']=errs
        except Exception as exc: obj['schema_errors']=[f'jsonschema_unavailable:{exc}']
    text=json.dumps(obj, ensure_ascii=False, indent=2)
    if a.out: Path(a.out).parent.mkdir(parents=True, exist_ok=True); Path(a.out).write_text(text+'\n', encoding='utf-8')
    else: print(text)
    return 0 if not obj.get('schema_errors') else 1
if __name__=='__main__': raise SystemExit(main())

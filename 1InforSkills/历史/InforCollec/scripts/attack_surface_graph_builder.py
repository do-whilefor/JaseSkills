#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import json, re
from _info_collect_lib import common_parser, parse_scope, enforce_scope, stable_hash
PARAM_RE=re.compile(r'[:?&]([A-Za-z_][A-Za-z0-9_]{1,40})=|\{([A-Za-z_][A-Za-z0-9_]{1,40})\}|:([A-Za-z_][A-Za-z0-9_]{1,40})')
DATA_RE=re.compile(r'(?i)\b(user|account|tenant|organization|invoice|payment|file|document|order|project|workspace|session|token|secret|admin|role|permission)s?\b')
def load_manifest(path: Path):
    data=json.loads(path.read_text(encoding='utf-8', errors='ignore'))
    return data.get('items',[]) if isinstance(data,dict) else data

def node(nodes, typ, label, meta=None):
    nid=f'{typ}:{stable_hash(label)[:12]}'
    nodes.setdefault(nid, {'id':nid,'type':typ,'label':label,'meta':meta or {}})
    return nid

def valstr(v):
    return json.dumps(v,ensure_ascii=False,sort_keys=True,default=str)[:500]

def main():
    ap=common_parser('Build attack surface graph: Asset -> Endpoint -> Auth -> Role -> Tenant -> Parameter -> Data Object -> Sensitive Operation -> Evidence.')
    args=ap.parse_args(); manifest=Path(args.input).resolve(); scope=parse_scope(args.scope, manifest); ok,reason=enforce_scope(manifest, scope)
    if not ok: print(json.dumps({'status':'FAIL','reason':reason},ensure_ascii=False)); return 2
    items=load_manifest(manifest) if manifest.is_file() else []
    nodes={}; edges=[]
    for it in items:
        ev=node(nodes,'Evidence',it.get('evidence_id','unknown'),{'source_file':it.get('source_file'),'line':it.get('source_line_start')})
        asset=node(nodes,'Asset',it.get('source_file') or it.get('path') or 'unknown')
        edges.append({'from':asset,'to':ev,'relation':'has_evidence'})
        t=str(it.get('discovered_item_type','')); v=valstr(it.get('discovered_item_value_redacted',''))
        current=asset
        if any(k in t for k in ['route','endpoint','api','path','graphql','websocket','grpc','framework_route']):
            ep=node(nodes,'Endpoint',v or t); edges.append({'from':asset,'to':ep,'relation':'defines'}); edges.append({'from':ep,'to':ev,'relation':'supported_by'}); current=ep
            for pm in PARAM_RE.finditer(v):
                param=next(x for x in pm.groups() if x); pn=node(nodes,'Parameter',param); edges.append({'from':ep,'to':pn,'relation':'has_parameter'}); edges.append({'from':pn,'to':ev,'relation':'supported_by'})
        if any(k in t for k in ['auth','oauth','jwt','session','policy','guard']):
            a=node(nodes,'AuthPolicy',v or t); edges.append({'from':current,'to':a,'relation':'protected_or_mentioned_by'}); edges.append({'from':a,'to':ev,'relation':'supported_by'})
        if any(k in t for k in ['role','admin','permission','scope']):
            r=node(nodes,'RoleOrPermission',v or t); edges.append({'from':current,'to':r,'relation':'role_or_permission_signal'}); edges.append({'from':r,'to':ev,'relation':'supported_by'})
        if any(k in t for k in ['tenant','organization','owner','workspace','account']):
            ten=node(nodes,'TenantBoundary',v or t); edges.append({'from':current,'to':ten,'relation':'tenant_or_owner_signal'}); edges.append({'from':ten,'to':ev,'relation':'supported_by'})
        for dm in DATA_RE.finditer(v):
            d=node(nodes,'DataObject',dm.group(0).lower()); edges.append({'from':current,'to':d,'relation':'touches_data_object'}); edges.append({'from':d,'to':ev,'relation':'supported_by'})
        if any(k in t for k in ['secret','upload','file','command','sql','dependency','dangerous','bucket','cloud','iac']):
            op=node(nodes,'SensitiveOperation',v or t); edges.append({'from':current,'to':op,'relation':'contains_candidate'}); edges.append({'from':op,'to':ev,'relation':'supported_by'})
    graph={'schema_version':'attack-surface-graph.v2','input_manifest':str(manifest),'nodes':list(nodes.values()),'edges':edges,'quality_note':'Graph is evidence-derived and candidate-only until role/tenant/runtime validation.'}
    out=args.output or '-'; text=json.dumps(graph,ensure_ascii=False,indent=2)
    if out=='-': print(text)
    else: Path(out).write_text(text,encoding='utf-8')
    return 0
if __name__=='__main__': raise SystemExit(main())

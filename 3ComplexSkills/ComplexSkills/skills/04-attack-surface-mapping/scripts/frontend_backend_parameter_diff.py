#!/usr/bin/env python3
"""Frontend/backend parameter difference mapper.
Read-only. It compares backend accepted parameter signals with frontend API/client
signals. Differences are candidate obligations only, not vulnerabilities.
"""
from __future__ import annotations
import argparse, json, re, hashlib
from pathlib import Path
from typing import Any
SENSITIVE=re.compile(r'(?i)(tenant|org|workspace|owner|user_id|role|admin|scope|permission|status|state|price|amount|quantity|discount|coupon|redirect|url|uri|path|file|filename|template|command)')
QUERY_PARAM_RE=re.compile(r'[?&]([A-Za-z_][A-Za-z0-9_-]*)=')
BODY_FIELD_RE=re.compile(r'(?i)(?:JSON\.stringify\(|body\s*[:=]|data\s*[:=]|params\s*[:=])[^\n]{0,400}')
FIELD_RE=re.compile(r'["\']([A-Za-z_][A-Za-z0-9_-]{1,60})["\']\s*:')
def load(p: str|None)->Any:
    if not p: return {}
    path=Path(p)
    return json.loads(path.read_text(encoding='utf-8',errors='ignore')) if path.exists() else {}
def sha(s): return hashlib.sha256(s.encode()).hexdigest()[:16]
def backend_params(code:dict[str,Any])->list[dict[str,Any]]:
    out=[]
    for p in code.get('parameters') or []:
        name=str(p.get('name') or '').strip()
        if not name: continue
        out.append({'name':name,'binding_kind':p.get('binding_kind'),'file':p.get('file'),'line':p.get('line'),'sensitive':bool(p.get('sensitive') or SENSITIVE.search(name)),'source':'code_graph.parameters'})
    for chain in code.get('route_to_handler_chains') or []:
        route=(chain.get('route') or {}).get('route')
        for p in chain.get('parameters') or []:
            name=str(p.get('name') or '').strip()
            if name: out.append({'name':name,'route':route,'binding_kind':p.get('binding_kind'),'file':p.get('file'),'line':p.get('line'),'sensitive':bool(p.get('sensitive') or SENSITIVE.search(name)),'source':'route_to_handler_chain'})
    return out
def frontend_params(js:dict[str,Any])->list[dict[str,Any]]:
    out=[]
    for api in (js.get('api_clients') or []) + (js.get('endpoints') or []):
        text=json.dumps(api,ensure_ascii=False)
        route=api.get('target') or api.get('url') or api.get('path') or api.get('endpoint') or ''
        for m in QUERY_PARAM_RE.finditer(text): out.append({'name':m.group(1),'route':route,'file':api.get('file'),'line':api.get('line'),'source':'frontend_query'})
        for bm in BODY_FIELD_RE.finditer(text):
            for fm in FIELD_RE.finditer(bm.group(0)): out.append({'name':fm.group(1),'route':route,'file':api.get('file'),'line':api.get('line'),'source':'frontend_body'})
    for g in js.get('graphql') or []:
        text=json.dumps(g,ensure_ascii=False)
        for fm in FIELD_RE.finditer(text): out.append({'name':fm.group(1),'route':'/graphql','file':g.get('file'),'line':g.get('line'),'source':'frontend_graphql'})
    return out
def norm(n): return re.sub(r'[^a-z0-9]+','_',str(n).lower()).strip('_')
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--code-graph',required=True); ap.add_argument('--js-audit',required=True); ap.add_argument('--out',required=True); a=ap.parse_args()
    code=load(a.code_graph); js=load(a.js_audit); bp=backend_params(code); fp=frontend_params(js)
    fset={norm(x['name']) for x in fp if x.get('name')}; bset={norm(x['name']) for x in bp if x.get('name')}
    backend_only=[{**x,'diff_id':'PARAM-BACKEND-ONLY-'+sha(json.dumps(x,sort_keys=True,ensure_ascii=False)),'confirmation_policy':'backend-only parameter is candidate mass-assignment/hidden-parameter signal; dynamic backend acceptance proof required'} for x in bp if norm(x['name']) and norm(x['name']) not in fset]
    frontend_only=[{**x,'diff_id':'PARAM-FRONTEND-ONLY-'+sha(json.dumps(x,sort_keys=True,ensure_ascii=False)),'confirmation_policy':'frontend parameter without backend binding is not vulnerability; route mapping required'} for x in fp if norm(x['name']) and norm(x['name']) not in bset]
    result={'schema_version':'frontend_backend_parameter_diff_v1','backend_parameter_count':len(bp),'frontend_parameter_count':len(fp),'backend_only_count':len(backend_only),'frontend_only_count':len(frontend_only),'backend_parameters':bp,'frontend_parameters':fp,'backend_only_parameters':backend_only,'frontend_only_parameters':frontend_only,'sensitive_backend_only':[x for x in backend_only if x.get('sensitive')],'does_not_confirm':True,'claim_policy':'backend-only or frontend-only parameters are candidate signals only; confirmed requires non-destructive dynamic backend acceptance evidence and negative control'}
    out=Path(a.out); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(json.dumps({'ok':True,'backend_only':len(backend_only),'frontend_only':len(frontend_only)},ensure_ascii=False)); return 0
if __name__=='__main__': raise SystemExit(main())

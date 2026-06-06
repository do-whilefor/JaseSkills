#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any
from urllib.parse import urlparse, parse_qs

JS_SUFFIXES={'.js','.mjs','.cjs','.jsx','.ts','.tsx'}
BACKEND_SUFFIXES={'.js','.ts','.tsx','.py','.java','.php','.go','.rs','.rb','.cs'}
RISK_WORDS=re.compile(r'(tenant|org|owner|user|role|admin|permission|price|quota|balance|plan|status|state|force|debug|dryRun|override|redirect|callback|url|path|file|template|command|include|expand|fields|filter|sort)', re.I)
API_CALL_RE=re.compile(r'''(?P<client>fetch|axios(?:\.(?P<method>get|post|put|patch|delete|head|options))?|\w+Client\.(?P<cmet>get|post|put|patch|delete)|request)\s*\(\s*(?P<quote>[`"'])(?P<path>[^`"']{1,600})(?P=quote)(?P<tail>[^\)]{0,1200})\)''', re.I|re.S)
XHR_RE=re.compile(r'''\.open\s*\(\s*[`"'](?P<method>GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)[`"']\s*,\s*[`"'](?P<path>[^`"']{1,600})[`"']''', re.I|re.S)
ROUTE_RE=re.compile(r'''[`"'](?P<path>/(?:api|graphql|rpc|admin|internal|v\d+|tenant|org|project|user|payment|refund|export|download|upload|debug)[^`"']{0,500})[`"']''', re.I)
GQL_BODY_RE=re.compile(r'''(?:gql|graphql)\s*`(?P<body>[^`]{1,5000})`''', re.I|re.S)
GQL_OP_RE=re.compile(r'''(?P<kind>query|mutation|subscription)\s+(?P<name>[A-Za-z0-9_]+)?\s*(?:\((?P<vars>[^)]*)\))?\s*\{''', re.I|re.S)
WS_RE=re.compile(r'''new\s+WebSocket\s*\(\s*[`"'](?P<url>[^`"']+)[`"']''', re.I)
SSE_RE=re.compile(r'''new\s+EventSource\s*\(\s*[`"'](?P<url>[^`"']+)[`"']''', re.I)
JSON_RPC_RE=re.compile(r'''jsonrpc\s*[:=]\s*[`"']2\.0[`"'][\s\S]{0,800}?method\s*[:=]\s*[`"'](?P<method>[A-Za-z0-9_.:-]+)[`"']''', re.I)
KEY_RE=re.compile(r'''(?<![\w$])([A-Za-z_$][\w$]{1,80})\s*[:=]''')
TS_FIELD_RE=re.compile(r'''(?m)^\s*([A-Za-z_$][\w$]{1,80})\??\s*:\s*[^;,{]+[;,]?''')
PARAM_CALL_RE=re.compile(r'''(?:append|set|get)\s*\(\s*[`"']([A-Za-z_$][\w$.-]{1,80})[`"']''')
BACKEND_ROUTE_RE=re.compile(r'''(?:router|app|Route|routes|@(?:Get|Post|Put|Patch|Delete|RequestMapping))\s*(?:\.\s*(get|post|put|patch|delete)|\()\s*\(?\s*[`"']([^`"']{1,400})[`"']''', re.I)
BACKEND_FIELD_RE=re.compile(r'''(?:req\.body\.|body\[|request\.json\(|request\.form\[|params\.|query\.|@(?:Body|Query|Param)\(['"]?|\bfillable\s*=|\bpermit\(|\bvalidate\(|\binterface\s+|\btype\s+)[\s\S]{0,260}?['"]?([A-Za-z_$][\w$]{1,80})['"]?''', re.I)

@dataclass
class ApiRecord:
    api_id: str
    protocol: str
    method: str|None
    path: str
    baseURL: str|None
    call_file: str
    line: int|None
    call_function: str='unknown'
    call_component: str='unknown'
    route_page: str='unknown'
    trigger_condition: str='unknown'
    auth_required: str='unknown'
    possible_roles: list[str]=field(default_factory=list)
    request_headers: list[str]=field(default_factory=list)
    query_params: list[str]=field(default_factory=list)
    path_params: list[str]=field(default_factory=list)
    body_params: list[str]=field(default_factory=list)
    form_data_params: list[str]=field(default_factory=list)
    json_params: list[str]=field(default_factory=list)
    file_upload_fields: list[str]=field(default_factory=list)
    websocket_message_types: list[str]=field(default_factory=list)
    graphql_operationName: str|None=None
    graphql_variables: list[str]=field(default_factory=list)
    json_rpc_method: str|None=None
    param_sources: dict[str,list[str]]=field(default_factory=dict)
    hidden_param_candidates: list[str]=field(default_factory=list)
    high_risk_params: list[str]=field(default_factory=list)
    status: str='candidate-only'
    evidence: list[dict[str,Any]]=field(default_factory=list)

def read_text(p:Path)->str:
    return p.read_text(encoding='utf-8', errors='replace')

def line_no(text:str, idx:int)->int: return text.count('\n',0,idx)+1

def rel(p:Path, root:Path)->str:
    try: return str(p.resolve().relative_to(root.resolve())).replace('\\','/')
    except Exception: return str(p)

def uniq(xs):
    out=[]
    for x in xs:
        if x and x not in out: out.append(x)
    return out

def path_params(path:str)->list[str]:
    vals=[]
    vals += re.findall(r':([A-Za-z_$][\w$-]+)', path)
    vals += re.findall(r'\$\{\s*([A-Za-z_$][\w$.-]+)\s*\}', path)
    vals += re.findall(r'\{\s*([A-Za-z_$][\w$.-]+)\s*\}', path)
    return uniq(vals)

def query_params(path:str)->list[str]:
    try: return list(parse_qs(urlparse(path).query).keys())
    except Exception: return []

def infer_fields(blob:str)->list[str]:
    vals=[]
    vals += [m.group(1) for m in KEY_RE.finditer(blob)]
    vals += [m.group(1) for m in TS_FIELD_RE.finditer(blob)]
    vals += [m.group(1) for m in PARAM_CALL_RE.finditer(blob)]
    vals += re.findall(r'''\.append\s*\(\s*[`"']([A-Za-z_$][\w$.-]{1,80})[`"']''', blob)
    return uniq(vals)

def risk(xs:list[str])->list[str]: return [x for x in uniq(xs) if RISK_WORDS.search(x)]

def mk_record(idx:int, protocol:str, method:str|None, path:str, file:Path, root:Path, line:int, rule:str, snippet:str)->ApiRecord:
    rec=ApiRecord(f'API-{idx:05d}', protocol, method, path, None, rel(file,root), line)
    rec.query_params=query_params(path); rec.path_params=path_params(path)
    rec.evidence=[{'file':rel(file,root),'line':line,'rule':rule,'snippet':snippet[:260]}]
    return rec

def extract_file(file:Path, root:Path, start:int):
    text=read_text(file); records=[]; fields=infer_fields(text); idx=start
    for m in API_CALL_RE.finditer(text):
        method=(m.group('method') or m.group('cmet'))
        if m.group('client') == 'fetch':
            mm=re.search(r'''method\s*:\s*[`"']([A-Z]+)[`"']''', m.group('tail') or '', re.I)
            method=mm.group(1).upper() if mm else 'GET'
        elif method: method=method.upper()
        rec=mk_record(idx,'REST',method,m.group('path'),file,root,line_no(text,m.start()),'js.api.call',m.group(0))
        ctx=text[max(0,m.start()-700):m.end()+700]
        body=infer_fields(ctx)
        rec.body_params=body; rec.json_params=body; rec.hidden_param_candidates=risk(fields); rec.high_risk_params=risk(rec.query_params+rec.path_params+body+fields)
        rec.param_sources={'callsite_context':body,'file_schema_or_constants':fields}
        records.append(rec); idx+=1
    for m in XHR_RE.finditer(text):
        rec=mk_record(idx,'REST',m.group('method').upper(),m.group('path'),file,root,line_no(text,m.start()),'js.xhr.open',m.group(0))
        rec.hidden_param_candidates=risk(fields); rec.high_risk_params=risk(rec.query_params+rec.path_params+fields)
        records.append(rec); idx+=1
    for m in ROUTE_RE.finditer(text):
        if any(r.path == m.group('path') for r in records): continue
        rec=mk_record(idx,'REST',None,m.group('path'),file,root,line_no(text,m.start()),'js.route.string',m.group(0))
        rec.hidden_param_candidates=risk(fields); rec.high_risk_params=risk(rec.query_params+rec.path_params+fields)
        records.append(rec); idx+=1
    for m in WS_RE.finditer(text):
        rec=mk_record(idx,'WebSocket',None,m.group('url'),file,root,line_no(text,m.start()),'js.websocket',m.group(0))
        rec.websocket_message_types=uniq(re.findall(r'''(?:type|action|event)\s*[:=]\s*[`"']([A-Za-z0-9_.:-]+)[`"']''', text[max(0,m.start()-1200):m.end()+2500]))
        rec.hidden_param_candidates=risk(fields); rec.high_risk_params=risk(rec.websocket_message_types+fields)
        records.append(rec); idx+=1
    for m in SSE_RE.finditer(text):
        records.append(mk_record(idx,'SSE','GET',m.group('url'),file,root,line_no(text,m.start()),'js.sse',m.group(0))); idx+=1
    gql_bodies=[x.group('body') for x in GQL_BODY_RE.finditer(text)]
    for body in gql_bodies:
        gm=GQL_OP_RE.search(body)
        if not gm: continue
        vars_=uniq(re.findall(r'\$([A-Za-z_$][\w$]*)', gm.group('vars') or body))
        rec=mk_record(idx,'GraphQL','POST','/graphql',file,root,line_no(text,text.find(body[:30]) if body[:30] in text else 0),'js.graphql.operation',body)
        rec.graphql_operationName=gm.group('name'); rec.graphql_variables=vars_; rec.body_params=vars_; rec.json_params=vars_; rec.hidden_param_candidates=risk(fields); rec.high_risk_params=risk(vars_+fields)
        records.append(rec); idx+=1
    for m in JSON_RPC_RE.finditer(text):
        rec=mk_record(idx,'JSON-RPC','POST','unknown-json-rpc-endpoint',file,root,line_no(text,m.start()),'js.jsonrpc',m.group(0))
        rec.json_rpc_method=m.group('method'); rec.body_params=infer_fields(text[max(0,m.start()-500):m.end()+800]); rec.high_risk_params=risk(rec.body_params)
        records.append(rec); idx+=1
    return records, idx, {'file':rel(file,root),'frontend_fields':fields,'high_risk_fields':risk(fields)}

def load_ledger_assets(ledger_path:Path, fallback_root:Path)->tuple[list[Path],Path]:
    if not ledger_path.exists(): return [], fallback_root
    try: ledger=json.loads(ledger_path.read_text(encoding='utf-8'))
    except Exception: return [], fallback_root
    base=Path(ledger.get('root') or fallback_root).resolve()
    assets=[]
    for a in ledger.get('assets',[]):
        if a.get('kind') in {'javascript','service_worker'}:
            p=base/a.get('path','')
            if p.exists(): assets.append(p)
    return assets, base

def scan_har(har:Path)->dict[str,Any]:
    if not har.exists(): return {'status':'missing','observed_params':{},'requests':[]}
    try: obj=json.loads(har.read_text(encoding='utf-8', errors='replace'))
    except Exception as e: return {'status':'parse-error','error':str(e),'observed_params':{},'requests':[]}
    observed={}; reqs=[]
    for ent in obj.get('log',{}).get('entries',[]):
        req=ent.get('request',{}); url=req.get('url',''); params=[]
        for q in req.get('queryString',[]) or []: params.append(q.get('name'))
        post=req.get('postData',{}) or {}
        for q in post.get('params',[]) or []: params.append(q.get('name'))
        txt=post.get('text') or ''
        if txt.strip().startswith('{'):
            try:
                body=json.loads(txt)
                def walk(o,p=''):
                    if isinstance(o,dict):
                        for k,v in o.items(): params.append(p+k); walk(v,p+k+'.')
                    elif isinstance(o,list):
                        for v in o[:3]: walk(v,p)
                walk(body)
            except Exception: pass
        if url:
            observed[url]=uniq([p for p in params if p]); reqs.append({'method':req.get('method'),'url':url,'params':observed[url]})
    return {'status':'partial' if reqs else 'empty','observed_params':observed,'requests':reqs[:500]}

def scan_backend(root:Path)->dict[str,Any]:
    if not root.exists(): return {'status':'missing','backend_fields':[],'routes':[],'files':[]}
    fields=[]; routes=[]; files=[]
    for p in root.rglob('*'):
        if not p.is_file() or p.suffix.lower() not in BACKEND_SUFFIXES: continue
        text=read_text(p); rp=rel(p,root); files.append(rp)
        for m in BACKEND_FIELD_RE.finditer(text):
            fields.append({'field':m.group(1),'file':rp,'line':line_no(text,m.start()),'rule':'backend.accept.field.candidate'})
        for m in BACKEND_ROUTE_RE.finditer(text):
            routes.append({'method':(m.group(1) or 'unknown').upper(),'path':m.group(2),'file':rp,'line':line_no(text,m.start())})
    return {'status':'partial' if fields or routes else 'empty','backend_fields':fields[:5000],'routes':routes[:1000],'files':files[:1000]}

def main():
    ap=argparse.ArgumentParser(description='Build JS API and parameter model for hidden API/hidden parameter review')
    ap.add_argument('--root', default='.')
    ap.add_argument('--ledger', default='')
    ap.add_argument('--backend-root', default='')
    ap.add_argument('--har', default='')
    ap.add_argument('--out', default='reports/js-top-tier')
    args=ap.parse_args()
    root=Path(args.root).resolve(); out=Path(args.out).resolve(); out.mkdir(parents=True, exist_ok=True)
    assets=[]; asset_root=root
    if args.ledger: assets, asset_root=load_ledger_assets(Path(args.ledger).resolve(), root)
    if not assets: assets=[p for p in root.rglob('*') if p.is_file() and p.suffix.lower() in JS_SUFFIXES]; asset_root=root
    records=[]; summaries=[]; idx=1
    for p in sorted(set(assets)):
        recs, idx, summary=extract_file(p, asset_root, idx); records.extend(recs); summaries.append(summary)
    backend=scan_backend(Path(args.backend_root).resolve()) if args.backend_root else {'status':'missing','backend_fields':[],'routes':[],'files':[]}
    har=scan_har(Path(args.har).resolve()) if args.har else {'status':'missing','observed_params':{},'requests':[]}
    frontend=uniq([f for s in summaries for f in s.get('frontend_fields',[])])
    backend_fields=uniq([x.get('field') for x in backend.get('backend_fields',[])])
    traffic=uniq([p for vals in har.get('observed_params',{}).values() for p in vals])
    backend_only=uniq([f for f in backend_fields if f not in frontend and f not in traffic])
    model={'schema_version':'js-api-parameter-model/v1','status':'partial' if records else 'empty','downgrade':'candidate-only until backend acceptance and non-destructive role/tenant replay are proven','root':str(root),'api_count':len(records),'apis':[asdict(r) for r in records],'frontend_field_summary':{'fields':frontend,'high_risk_fields':risk(frontend),'files':summaries},'backend_model':backend,'traffic_model':har,'diff_summary':{'backend_only_fields':backend_only,'high_risk_backend_only_fields':risk(backend_only),'requires_dynamic_acceptance_test':bool(backend_only)},'required_next_steps':['run backend parameter diff','generate safe browser replay plan','perform role/tenant non-destructive validation before verified report']}
    (out/'js_api_parameter_model.json').write_text(json.dumps(model, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'ok':True,'out':str(out/'js_api_parameter_model.json'),'apis':len(records),'backend_status':backend.get('status'),'backend_only_fields':len(backend_only)}, ensure_ascii=False, indent=2))
if __name__=='__main__': main()

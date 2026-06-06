#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, re, zipfile
from pathlib import Path
from typing import Any
SECRET=re.compile(r'(?i)(authorization|cookie|token|secret|api[_-]?key|jwt|session|password)')

def sha(p: Path):
    h=hashlib.sha256();
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024), b''): h.update(b)
    return h.hexdigest()

def load_json(p: Path, default=None):
    try: return json.loads(p.read_text(encoding='utf-8'))
    except Exception: return default if default is not None else {}

def rel(p: Path, root: Path):
    try: return str(p.resolve().relative_to(root.resolve())).replace('\\','/')
    except Exception: return str(p)

def redact_headers(headers):
    if isinstance(headers, list):
        return [{**h, 'value':'<redacted>' if SECRET.search(str(h.get('name',''))) else h.get('value')} for h in headers]
    if isinstance(headers, dict):
        return {k:('<redacted>' if SECRET.search(k) else v) for k,v in headers.items()}
    return headers

def summarize_har(p: Path):
    obj=load_json(p,{})
    entries=obj.get('log',{}).get('entries',[]) if isinstance(obj,dict) else []
    out=[]
    for i,e in enumerate(entries[:2000]):
        req=e.get('request',{}) if isinstance(e,dict) else {}; res=e.get('response',{}) if isinstance(e,dict) else {}
        post=req.get('postData',{}) or {}
        out.append({'entry_id':f'{p.name}#{i}','method':req.get('method'),'url':req.get('url'),'status':res.get('status'),'request_headers':redact_headers(req.get('headers',[])[:80]),'response_headers':redact_headers(res.get('headers',[])[:80]),'has_post_data':bool(post),'post_mime':post.get('mimeType'),'response_content_mime':(res.get('content') or {}).get('mimeType'),'startedDateTime':e.get('startedDateTime')})
    return out

def summarize_trace(p: Path):
    try:
        with zipfile.ZipFile(p) as z:
            names=z.namelist()
        return {'entries':len(names),'has_network':any('network' in n.lower() or 'trace.network' in n.lower() for n in names),'has_screenshot':any(n.lower().endswith(('.png','.jpg','.jpeg','.webp')) or 'screenshot' in n.lower() for n in names),'sample':names[:50]}
    except Exception as e:
        return {'error':str(e)}

def main():
    ap=argparse.ArgumentParser(description='Build redacted evidence manifest from HAR/trace/screenshots/runtime outputs. No plan-only artifact is accepted as runtime proof.')
    ap.add_argument('--evidence-root', required=True)
    ap.add_argument('--out', default='reports/js-top-tier')
    ap.add_argument('--role-tenant-map', default='')
    args=ap.parse_args(); er=Path(args.evidence_root).resolve(); out=Path(args.out).resolve(); out.mkdir(parents=True, exist_ok=True)
    artifacts=[]; requests=[]; runtime_requirements={'har':False,'trace':False,'screenshots':False,'request_response':False,'role_tenant_mapping':False}
    for p in sorted(er.rglob('*')):
        if not p.is_file(): continue
        item={'path':rel(p,er),'absolute_path':str(p),'sha256':sha(p),'size':p.stat().st_size,'kind':'file'}
        low=p.name.lower()
        if low.endswith('.har'):
            item['kind']='har'; item['requests']=summarize_har(p); requests.extend(item['requests']); runtime_requirements['har']=True; runtime_requirements['request_response']=bool(item['requests'])
        elif low.endswith('.zip') and ('trace' in low or 'playwright' in low):
            item['kind']='playwright-trace'; item['trace_summary']=summarize_trace(p); runtime_requirements['trace']=True; runtime_requirements['screenshots']=runtime_requirements['screenshots'] or item['trace_summary'].get('has_screenshot',False)
        elif low.endswith(('.png','.jpg','.jpeg','.webp')):
            item['kind']='screenshot'; runtime_requirements['screenshots']=True
        elif low in {'role_tenant_matrix.json','role-tenant-matrix.json','runtime-role-tenant-map.json'}:
            item['kind']='role-tenant-map'; runtime_requirements['role_tenant_mapping']=True
        artifacts.append(item)
    if args.role_tenant_map and Path(args.role_tenant_map).exists():
        runtime_requirements['role_tenant_mapping']=True
        artifacts.append({'path':str(Path(args.role_tenant_map).resolve()),'kind':'role-tenant-map','sha256':sha(Path(args.role_tenant_map)),'size':Path(args.role_tenant_map).stat().st_size})
    status='ready' if all(runtime_requirements.values()) else ('partial' if any(runtime_requirements.values()) else 'missing')
    manifest={'schema_version':'js-evidence-manifest/v1','status':status,'evidence_root':str(er),'runtime_requirements':runtime_requirements,'artifacts':artifacts,'request_response_index':requests[:2000],'downgrade':'If status is not ready, browser replay / dynamic validation / verified vulnerability claims are blocked.'}
    (out/'js_evidence_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'ok':True,'status':status,'artifacts':len(artifacts),'requests':len(requests),'out':str(out/'js_evidence_manifest.json')}, ensure_ascii=False, indent=2))
if __name__=='__main__': main()

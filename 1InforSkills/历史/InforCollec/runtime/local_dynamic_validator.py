#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from _info_collect_lib import now_iso, stable_hash  # type: ignore

SAFE_METHODS={'GET','HEAD','OPTIONS'}
LOCAL_HOSTS={'127.0.0.1','localhost','::1','0.0.0.0'}

def is_local_url(url: str) -> bool:
    u=urllib.parse.urlparse(url)
    return u.scheme in {'http','https'} and (u.hostname in LOCAL_HOSTS or (u.hostname or '').endswith('.localhost'))

def norm(path: str) -> str:
    path=str(path or '/')
    path=urllib.parse.urlparse(path).path or path
    path=path.replace('{id}','1').replace(':id','1')
    return '/' + path.lstrip('/')

def load_manifest(manifest: Path) -> dict:
    return json.loads(manifest.read_text(encoding='utf-8', errors='ignore'))

def load_endpoints(manifest: Path) -> tuple[str, list[dict]]:
    data=load_manifest(manifest)
    scope_id='default-local-scope'
    out=[]
    for it in data.get('items',[]):
        if not scope_id and it.get('scope_id'):
            scope_id=str(it.get('scope_id'))
        if it.get('scope_id'):
            scope_id=str(it.get('scope_id'))
        v=it.get('discovered_item_value_redacted')
        if not isinstance(v, dict):
            continue
        route=v.get('route') or v.get('resolved_endpoint') or v.get('endpoint')
        method=str(v.get('method') or 'GET').upper()
        if route and method in SAFE_METHODS:
            out.append({'route':norm(route),'method':method,'source_evidence_id':it.get('evidence_id'),'source_file':it.get('source_file'),'line':it.get('source_line_start') or 1})
    return scope_id, out

def probe(base_url: str, endpoint: dict, timeout: int) -> dict:
    url=base_url.rstrip('/') + endpoint['route']
    req=urllib.request.Request(url, method=endpoint['method'])
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body=resp.read(512)
            return {'url':url,'method':endpoint['method'],'status_code':resp.status,'headers_sample':dict(list(resp.headers.items())[:12]),'body_hash':stable_hash(body.decode('utf-8','ignore')),'reachable':True}
    except urllib.error.HTTPError as e:
        return {'url':url,'method':endpoint['method'],'status_code':e.code,'headers_sample':dict(list(e.headers.items())[:12]),'body_hash':'', 'reachable': e.code < 500}
    except Exception as e:
        return {'url':url,'method':endpoint['method'],'error':type(e).__name__,'reachable':False}

def record_from_probe(ep: dict, result: dict) -> dict:
    captured = bool(result.get('reachable') and result.get('status_code') is not None)
    status_code = result.get('status_code')
    return {
        'role_context':'unspecified_local_probe',
        'tenant_context':'unspecified_local_probe',
        'url':str(result.get('url') or ''),
        'method':str(result.get('method') or ep.get('method') or 'GET'),
        'capture_status':'captured' if captured else 'failed',
        'request_sample':{'safe_method_only':True,'source_evidence_id':ep.get('source_evidence_id'),'route':ep.get('route')},
        'response_sample':{'status_code':status_code,'body_hash':result.get('body_hash') or '', 'headers_sample':result.get('headers_sample') or {}, 'error':result.get('error')},
        'screenshot':None,
        'har_entry':None,
        'safety':'local_loopback_only; safe HTTP methods only; no auth bypass; no third-party targets',
        'source_evidence_id':ep.get('source_evidence_id'),
        'source_file':ep.get('source_file') or 'runtime/local_dynamic_validator.py',
        'source_line_start':int(ep.get('line') or 1),
        'finding_status':'confirmed' if captured else 'candidate',
        'confidence':0.95 if captured else 0.45,
        'reason':'confirmed runtime evidence from authorized loopback probe' if captured else 'runtime probe failed or produced no HTTP status; remains candidate',
        'limitation':'Only safe-method loopback probing is performed; no destructive actions, no third-party targets, no auth bypass attempts.'
    }

def main() -> int:
    ap=argparse.ArgumentParser(description='Authorized local-only dynamic endpoint validator. Only probes loopback/local URLs and safe methods.')
    ap.add_argument('--manifest', required=True)
    ap.add_argument('--base-url', required=True, help='Must be http(s)://localhost or loopback')
    ap.add_argument('--output','-o', required=True)
    ap.add_argument('--timeout', type=int, default=3)
    ap.add_argument('--max-endpoints', type=int, default=50)
    args=ap.parse_args()
    run_id='runtime-'+stable_hash({'manifest':str(Path(args.manifest).resolve()),'base_url':args.base_url,'generated_at':now_iso()})[:16]
    if not is_local_url(args.base_url):
        report={'schema_version':'runtime-evidence.v1','run_id':run_id,'mode':'local_loopback_safe_probe','playwright_available':False,'scope_id':'default-local-scope','generated_at':now_iso(),'status':'FAIL','base_url':args.base_url,'reason':'base-url must be loopback/local only','records':[]}
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        return 2
    manifest=Path(args.manifest).resolve()
    scope_id, endpoints=load_endpoints(manifest)
    records=[]
    for ep in endpoints[:args.max_endpoints]:
        records.append(record_from_probe(ep, probe(args.base_url, ep, args.timeout)))
    report={'schema_version':'runtime-evidence.v1','run_id':run_id,'mode':'local_loopback_safe_probe','playwright_available':False,'scope_id':scope_id,'generated_at':now_iso(),'status':'PASS','base_url':args.base_url,'records':records}
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    return 0
if __name__=='__main__':
    raise SystemExit(main())

#!/usr/bin/env python3
"""Import Burp HAR, Playwright trace artifacts and storageState into evidence manifest.

This importer normalizes evidence. It does not perform browsing and cannot make a
candidate confirmed by itself.
"""
from __future__ import annotations
import argparse, json, zipfile, re
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

SECRET_HEADER_NAMES={'authorization','cookie','set-cookie','x-api-key','x-auth-token','proxy-authorization'}
SECRET_QUERY_KEYS={'token','access_token','refresh_token','api_key','apikey','key','secret','password','auth'}

def redact_header_value(name: str, value: str) -> str:
    return '<redacted>' if name.lower() in SECRET_HEADER_NAMES else str(value)

def redact_url(url: str) -> str:
    try:
        sp=urlsplit(url)
        q=[(k, '<redacted>' if k.lower() in SECRET_QUERY_KEYS else v) for k,v in parse_qsl(sp.query, keep_blank_values=True)]
        return urlunsplit((sp.scheme, sp.netloc, sp.path, urlencode(q), ''))
    except Exception:
        return '<unparseable_url_redacted>'

def load_json(p: Path) -> Any:
    try: return json.loads(p.read_text(encoding='utf-8', errors='ignore'))
    except Exception as exc: return {'_error':f'{exc.__class__.__name__}: {exc}', '_path':str(p)}

def import_har(path: str) -> list[dict[str,Any]]:
    p=Path(path); obj=load_json(p); entries=[]
    for e in (((obj or {}).get('log') or {}).get('entries') or []):
        req=e.get('request') or {}; res=e.get('response') or {}
        entries.append({
            'source':'burp_or_har','method':req.get('method'),'url':redact_url(req.get('url') or ''),'status':res.get('status'),
            'mimeType':(res.get('content') or {}).get('mimeType'),
            'request_headers':{h.get('name'):redact_header_value(h.get('name') or '', h.get('value') or '') for h in req.get('headers') or [] if h.get('name')},
            'response_headers':{h.get('name'):redact_header_value(h.get('name') or '', h.get('value') or '') for h in res.get('headers') or [] if h.get('name')},
            'request_body_size':(req.get('bodySize') or 0),'response_body_size':(res.get('bodySize') or 0),
            'startedDateTime':e.get('startedDateTime'),
            'evidence_file':str(p)
        })
    return entries

def import_storage(path: str) -> dict[str,Any]:
    p=Path(path); obj=load_json(p)
    return {
        'source':'playwright_storage_state','evidence_file':str(p),
        'cookies_count':len(obj.get('cookies') or []) if isinstance(obj, dict) else 0,
        'origins_count':len(obj.get('origins') or []) if isinstance(obj, dict) else 0,
        'origins':[{'origin':o.get('origin'), 'localStorage_keys':[i.get('name') for i in o.get('localStorage') or []]} for o in (obj.get('origins') or [])] if isinstance(obj, dict) else [],
        'raw_redacted': 'cookies values intentionally not copied into report output'
    }

def import_trace(path: str) -> dict[str,Any]:
    p=Path(path); result={'source':'playwright_trace','evidence_file':str(p),'events':0,'network_like_events':0,'screenshots':0,'console_like_events':0,'notes':[]}
    if p.is_dir():
        files=list(p.rglob('*'))
        result['screenshots']=sum(1 for f in files if f.suffix.lower() in {'.png','.jpg','.jpeg','webp'})
        for f in files:
            if f.suffix in {'.trace','.json','.jsonl'} and f.stat().st_size < 20_000_000:
                text=f.read_text(encoding='utf-8', errors='ignore')
                result['events'] += text.count('\n')
                result['network_like_events'] += len(re.findall(r'\b(request|response|resource)\b', text, re.I))
                result['console_like_events'] += len(re.findall(r'\bconsole\b', text, re.I))
    elif zipfile.is_zipfile(p):
        with zipfile.ZipFile(p) as z:
            names=z.namelist(); result['screenshots']=sum(1 for n in names if n.lower().endswith(('.png','.jpg','.jpeg','.webp')))
            for n in names:
                if n.endswith(('.trace','.json','.jsonl')):
                    data=z.read(n)[:20_000_000].decode('utf-8','ignore')
                    result['events'] += data.count('\n')
                    result['network_like_events'] += len(re.findall(r'\b(request|response|resource)\b', data, re.I))
                    result['console_like_events'] += len(re.findall(r'\bconsole\b', data, re.I))
    else:
        result['notes'].append('trace path is neither directory nor zip')
    return result

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--har', action='append', default=[])
    ap.add_argument('--playwright-trace', action='append', default=[])
    ap.add_argument('--storage-state', action='append', default=[])
    ap.add_argument('--candidate-id')
    ap.add_argument('--out', required=True)
    args=ap.parse_args()
    network=[]
    for h in args.har: network.extend(import_har(h))
    traces=[import_trace(t) for t in args.playwright_trace]
    storage=[import_storage(s) for s in args.storage_state]
    manifest={
        'schema_version':'evidence_manifest_v5_runtime_import_overlay',
        'candidate_id':args.candidate_id,
        'status':'imported_evidence_needs_quality_gate',
        'network_requests':network,
        'playwright_traces':traces,
        'storage_states':storage,
        'summary':{'har_files':len(args.har),'network_requests':len(network),'trace_files':len(traces),'storage_state_files':len(storage)},
        'claim_policy':'Imported artifacts are evidence inputs only; confirmed requires positive/negative tests and final claim guard.'
    }
    out=Path(args.out); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'ok':True,'out':str(out),'network_requests':len(network)},ensure_ascii=False))
if __name__=='__main__': main()

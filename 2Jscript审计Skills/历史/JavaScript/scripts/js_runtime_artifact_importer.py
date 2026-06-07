#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, hashlib, re, zipfile, urllib.parse
from pathlib import Path
from typing import Any
SECRET = re.compile(r'(?i)(authorization|cookie|token|secret|api[_-]?key|jwt|session|password)')
REQ_KINDS = {'har','playwright_trace','screenshot','dom_snapshot','console_log','role_tenant_matrix'}


def sha256(p: Path) -> str:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(1024*1024), b''):
            h.update(b)
    return h.hexdigest()


def rel(p: Path, root: Path) -> str:
    try: return p.resolve().relative_to(root.resolve()).as_posix()
    except Exception: return str(p)


def load_json(p: Path, default=None):
    try: return json.loads(p.read_text(encoding='utf-8'))
    except Exception: return default if default is not None else {}


def load_json_or_ndjson(p: Path):
    txt=p.read_text(encoding='utf-8', errors='replace')
    try:
        obj=json.loads(txt)
        if isinstance(obj, list): return obj
        if isinstance(obj, dict):
            for k in ('frames','messages','requests','items','events'):
                if isinstance(obj.get(k), list): return obj.get(k)
            return [obj]
    except Exception:
        rows=[]
        for line in txt.splitlines():
            line=line.strip()
            if not line: continue
            try: rows.append(json.loads(line))
            except Exception: rows.append({'raw': line[:2000]})
        return rows
    return []


def redact_value(name: str, value: Any):
    return '<redacted>' if SECRET.search(name or '') else value


def redact_url(url: Any):
    text=str(url or '')
    try:
        parsed=urllib.parse.urlsplit(text)
        pairs=urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
        if pairs:
            redacted_query=urllib.parse.urlencode([(k, '<redacted>' if SECRET.search(k) else v) for k,v in pairs], doseq=True)
            text=urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, redacted_query, parsed.fragment))
    except Exception:
        pass
    # Redact common credential assignments that appear outside normal query parsing.
    text=re.sub(r'(?i)(authorization|cookie|token|secret|api[_-]?key|jwt|session|password)(\s*[:=]\s*)[^&\s]+', r'\1\2<redacted>', text)
    return text


def redact_text(text: Any):
    value=str(text or '')
    # Preserve evidence that a body exists, but prevent common credential-bearing payloads from leaking.
    if SECRET.search(value):
        return '<redacted-sensitive-body>'
    return value


def redact_header_list(headers: Any):
    if isinstance(headers, dict):
        return [{'name':str(k),'value':redact_value(str(k), v)} for k,v in headers.items()]
    if not isinstance(headers, list): return []
    out=[]
    for h in headers:
        if not isinstance(h, dict): continue
        name=str(h.get('name',''))
        value=redact_value(name, h.get('value',''))
        out.append({'name':name,'value':value})
    return out


def parse_har(p: Path) -> dict[str,Any]:
    obj=load_json(p,{})
    entries=obj.get('log',{}).get('entries',[]) if isinstance(obj,dict) else []
    rr=[]; websocket=[]; graphql=[]; postmessage=[]
    for i,e in enumerate(entries):
        if not isinstance(e,dict): continue
        req=e.get('request',{}) or {}; res=e.get('response',{}) or {}
        url=redact_url(req.get('url','')); method=req.get('method','')
        post=req.get('postData') or {}
        post_text=redact_text(post.get('text','') if isinstance(post,dict) else str(post)[:4000])
        item={'index':i,'method':method,'url':url,'request_headers':redact_header_list(req.get('headers',[])),'response_status':res.get('status'),'response_headers':redact_header_list(res.get('headers',[])),'response_mime':(res.get('content') or {}).get('mimeType'),'has_request':bool(req),'has_response':bool(res),'post_data_preview':post_text[:1000]}
        rr.append(item)
        low=(url+' '+post_text).lower()
        if url.lower().startswith(('ws://','wss://')) or 'upgrade: websocket' in json.dumps(req.get('headers',[])).lower(): websocket.append(item)
        if '/graphql' in low or '"query"' in low or 'mutation ' in low or 'subscription ' in low: graphql.append(item)
        if 'postmessage' in low: postmessage.append(item)
    return {'request_response_count':len(rr),'request_response_index':rr[:5000],'graphql_entries':graphql[:500],'websocket_entries':websocket[:500],'postmessage_entries':postmessage[:500]}


def parse_request_index(p: Path):
    obj=load_json(p,{})
    reqs=obj.get('requests',[]) if isinstance(obj,dict) else []
    ress=obj.get('responses',[]) if isinstance(obj,dict) else []
    rr=[]; graphql=[]; websocket=[]; postmessage=[]
    for i,r in enumerate(reqs):
        if not isinstance(r,dict): continue
        raw_url=str(r.get('url',''))
        url=redact_url(raw_url); post=redact_text(r.get('postData','') or '')
        item={'index':i,'method':r.get('method'),'url':url,'request_headers':redact_header_list(r.get('headers',{})),'response_status':None,'response_headers':[],'response_mime':None,'has_request':True,'has_response':False,'role':r.get('role'),'tenant':r.get('tenant'),'post_data_preview':post[:1000]}
        # attach matching response by original URL, while storing only redacted URL evidence
        for s in ress:
            if isinstance(s,dict) and str(s.get('url','')) == raw_url:
                item.update({'response_status':s.get('status'),'response_headers':redact_header_list(s.get('headers',{})),'has_response':True}); break
        rr.append(item)
        low=(url+' '+post).lower()
        if url.lower().startswith(('ws://','wss://')): websocket.append(item)
        if '/graphql' in low or '"query"' in low or 'mutation ' in low or 'subscription ' in low: graphql.append(item)
        if 'postmessage' in low: postmessage.append(item)
    return {'request_response_count':len(rr),'request_response_index':rr,'graphql_entries':graphql,'websocket_entries':websocket,'postmessage_entries':postmessage}


def parse_trace(p: Path) -> dict[str,Any]:
    try:
        with zipfile.ZipFile(p) as z:
            names=z.namelist()
            has_network=any('network' in n.lower() or n.endswith('.network') for n in names)
            has_screenshot=any('screenshot' in n.lower() or n.lower().endswith(('.png','.jpg','.jpeg','.webp')) for n in names)
            has_dom=any('snapshot' in n.lower() or n.endswith('.trace') for n in names)
            return {'entries':len(names),'has_network':has_network,'has_screenshot':has_screenshot,'has_dom_snapshot_signal':has_dom,'sample':names[:50]}
    except Exception as e:
        return {'parse_error':str(e),'entries':0,'has_network':False,'has_screenshot':False,'has_dom_snapshot_signal':False}


def classify(p: Path) -> str:
    low=p.name.lower()
    if low.endswith('.har'): return 'har'
    if low.endswith('.zip') and ('trace' in low or 'playwright' in low): return 'playwright_trace'
    if low.endswith(('.png','.jpg','.jpeg','.webp')): return 'screenshot'
    if low.endswith(('.html','.dom','.snapshot')) and ('dom' in low or 'snapshot' in low): return 'dom_snapshot'
    if low in {'console.log','console.txt','browser-console.log'} or low.startswith('console-') or ('console' in low and low.endswith(('.log','.txt','.json'))): return 'console_log'
    if low in {'role_tenant_matrix.json','role-tenant-matrix.json','runtime-role-tenant-map.json'}: return 'role_tenant_matrix'
    if low.startswith('runtime-request-index') and low.endswith('.json'): return 'request_response_index'
    if low.startswith('graphql_frames') and low.endswith(('.json','.ndjson')): return 'graphql_frames'
    if low.startswith('websocket_frames') and low.endswith(('.json','.ndjson')): return 'websocket_frames'
    if low.startswith('postmessage_frames') and low.endswith(('.json','.ndjson')): return 'postmessage_frames'
    if low.endswith('.json') and 'authorization' in low: return 'authorization_result'
    return 'other'


def redact_any(name: str, value: Any):
    if SECRET.search(name or ''):
        return '<redacted>'
    if isinstance(value, dict):
        return {str(k): redact_any(str(k), v) for k, v in value.items()}
    if isinstance(value, list):
        return [redact_any(name, v) for v in value[:500]]
    if isinstance(value, str):
        # Protocol frame payloads often store secrets under generic keys such as payload/data.
        # Redact by both key name and credential-looking text, not only by the field name.
        return redact_text(redact_url(value))
    return value


def normalize_protocol_frames(kind: str, frames: list[Any], source_path: str):
    out=[]
    proto=kind.replace('_frames','')
    for i,f in enumerate(frames[:5000]):
        if not isinstance(f,dict):
            f={'raw':str(f)[:2000]}
        redacted={str(k): redact_any(str(k), v) for k,v in f.items()}
        out.append({'protocol':proto,'index':i,'source_path':source_path,'frame':redacted,'has_runtime_frame':True})
    return out


def main():
    ap=argparse.ArgumentParser(description='Import runtime artifacts: HAR, Playwright trace zip, screenshots, DOM snapshots, console logs, request/response indexes, GraphQL/WebSocket/postMessage frames, role/tenant matrix. This script validates imported evidence; it does not fabricate browser evidence.')
    ap.add_argument('--evidence-root', required=True)
    ap.add_argument('--out', default='reports/js-top-tier')
    ap.add_argument('--min-request-response', type=int, default=1)
    ap.add_argument('--require-authorized-target', action='store_true', help='fail if artifact-origin.json does not assert a non-fixture authorized target')
    args=ap.parse_args()
    root=Path(args.evidence_root).resolve(); out=Path(args.out).resolve(); out.mkdir(parents=True, exist_ok=True)
    origin=load_json(root/'artifact-origin.json', {}) if (root/'artifact-origin.json').exists() else {}
    origin_kind=str(origin.get('source_kind') or origin.get('kind') or '').lower()
    authorized=bool(origin.get('authorized_target') or origin.get('authorized_use')) and origin_kind not in {'fixture','sample','demo','synthetic','test_fixture'}
    artifacts=[]; rr=[]; protocol={'graphql':[],'websocket':[],'postmessage':[]}
    have={k:False for k in REQ_KINDS}
    for p in sorted(root.rglob('*')):
        if not p.is_file(): continue
        kind=classify(p)
        meta={'path':rel(p,root),'absolute_path':str(p),'kind':kind,'sha256':sha256(p),'size':p.stat().st_size}
        if kind=='har':
            h=parse_har(p); meta.update({k:v for k,v in h.items() if k!='request_response_index'}); rr.extend(h['request_response_index']); protocol['graphql'].extend(h['graphql_entries']); protocol['websocket'].extend(h['websocket_entries']); protocol['postmessage'].extend(h['postmessage_entries']); have['har']=True
        elif kind=='request_response_index':
            h=parse_request_index(p); meta.update({k:v for k,v in h.items() if k!='request_response_index'}); rr.extend(h['request_response_index']); protocol['graphql'].extend(h['graphql_entries']); protocol['websocket'].extend(h['websocket_entries']); protocol['postmessage'].extend(h['postmessage_entries'])
        elif kind=='playwright_trace':
            tr=parse_trace(p); meta['trace_summary']=tr; have['playwright_trace']=True; have['screenshot']=have['screenshot'] or tr.get('has_screenshot',False); have['dom_snapshot']=have['dom_snapshot'] or tr.get('has_dom_snapshot_signal',False)
        elif kind in {'graphql_frames','websocket_frames','postmessage_frames'}:
            frames=normalize_protocol_frames(kind, load_json_or_ndjson(p), rel(p,root))
            proto=kind.replace('_frames','')
            protocol[proto].extend(frames)
            meta['frame_count']=len(frames)
        elif kind in have:
            have[kind]=True
            if kind=='console_log':
                try: meta['console_preview']=p.read_text(encoding='utf-8', errors='replace')[:2000]
                except Exception: meta['console_preview']=''
            if kind=='role_tenant_matrix': meta['matrix_summary']=load_json(p,{})
        artifacts.append(meta)
    have['request_response']=len(rr) >= args.min_request_response
    ready_keys=['har','playwright_trace','screenshot','dom_snapshot','console_log','role_tenant_matrix','request_response']
    status='ready' if all(have.get(k) for k in ready_keys) else ('partial' if any(have.values()) or any(protocol.values()) else 'missing')
    if args.require_authorized_target and not authorized:
        status='blocked'
    result={'schema_version':'js-runtime-artifact-bundle/v1','status':status,'requirements':{k:bool(have.get(k)) for k in ready_keys},'authorized_target_import':authorized,'artifact_origin':origin,'evidence_root':str(root),'artifacts':artifacts,'request_response_index':rr[:5000],'protocol_runtime_evidence':protocol,'protocol_summary':{k:len(v) for k,v in protocol.items()},'promotion_blockers':[] if status=='ready' else [k for k in ready_keys if not have.get(k)] + ([] if authorized or not args.require_authorized_target else ['non_fixture_authorized_target_origin_missing']),'downgrade':'status must be ready and authorized_target_import true before runtime evidence can promote GraphQL/WebSocket/postMessage/authz findings.'}
    (out/'js_runtime_artifact_bundle.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    runtime={'schema_version':'js-runtime-evidence/v2','status':status,'requirements':{'har':have.get('har',False),'trace':have.get('playwright_trace',False),'screenshots':have.get('screenshot',False),'dom_snapshot':have.get('dom_snapshot',False),'console_log':have.get('console_log',False),'request_response':have.get('request_response',False),'role_tenant_mapping':have.get('role_tenant_matrix',False)},'authorized_target_import':authorized,'items':artifacts,'role_tenant_map':[a for a in artifacts if a['kind']=='role_tenant_matrix']}
    (out/'js_runtime_evidence.json').write_text(json.dumps(runtime, ensure_ascii=False, indent=2), encoding='utf-8')
    manifest={'schema_version':'js-evidence-manifest/v1','status':status,'evidence_root':str(root),'authorized_target_import':authorized,'artifact_origin':origin,'runtime_requirements':runtime['requirements'],'artifacts':artifacts,'request_response_index':rr[:5000],'protocol_runtime_evidence':protocol,'downgrade':'No ready manifest or no non-fixture authorized target origin means no confirmed runtime/dynamic claim.'}
    (out/'js_evidence_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'ok':status in {'ready','partial'},'status':status,'authorized_target_import':authorized,'requirements':result['requirements'],'protocol_summary':result['protocol_summary'],'artifacts':len(artifacts),'requests':len(rr),'out':str(out/'js_runtime_artifact_bundle.json')}, ensure_ascii=False, indent=2))
    raise SystemExit(0 if status in {'ready','partial'} else 1)

if __name__=='__main__':
    main()

#!/usr/bin/env python3
from __future__ import annotations
import argparse, base64, gzip, hashlib, json, mimetypes, os, re, sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urljoin

SCRIPT_SRC_RE = re.compile(r'<script\b[^>]*?\bsrc=["\']([^"\']+)["\'][^>]*>', re.I)
INLINE_SCRIPT_RE = re.compile(r'<script\b(?![^>]*?\bsrc=)[^>]*>(.*?)</script>', re.I|re.S)
LINK_MANIFEST_RE = re.compile(r'<link\b[^>]*?\brel=["\'][^"\']*(?:manifest|preload|modulepreload)[^"\']*["\'][^>]*?\bhref=["\']([^"\']+)["\'][^>]*>', re.I)
SOURCE_MAP_RE = re.compile(r'//#\s*sourceMappingURL=([^\s]+)')
DYNAMIC_IMPORT_RE = re.compile(r'\bimport\s*\(\s*[`"\']([^`"\']+)[`"\']\s*\)')
WORKER_RE = re.compile(r'\b(?:new\s+)?(?:Worker|SharedWorker)\s*\(\s*[`"\']([^`"\']+)[`"\']')
WASM_RE = re.compile(r'\b(?:WebAssembly\.(?:instantiate|instantiateStreaming)|\.wasm\b)|["\']([^"\']+\.wasm(?:\?[^"\']*)?)["\']')
FETCH_RE = re.compile(r'\b(?:fetch|axios\.(?:get|post|put|delete|patch)|XMLHttpRequest|\.open)\s*\(\s*[`"\']([^`"\']{1,500})[`"\']')
WS_RE = re.compile(r'\bnew\s+WebSocket\s*\(\s*[`"\']([^`"\']+)')
SSE_RE = re.compile(r'\bnew\s+EventSource\s*\(\s*[`"\']([^`"\']+)')
GRAPHQL_RE = re.compile(r'\b(query|mutation|subscription)\s+([A-Za-z0-9_]+)?\s*\([^`]*?\{|\b(gql|graphql)\s*`', re.I)
POSTMESSAGE_RE = re.compile(r'\.postMessage\s*\((.*?)\)', re.S)
STORAGE_RE = re.compile(r'\b(localStorage|sessionStorage|indexedDB|caches|CacheStorage)\b')
ENV_RE = re.compile(r'\b(NEXT_PUBLIC_[A-Z0-9_]+|VITE_[A-Z0-9_]+|REACT_APP_[A-Z0-9_]+|NUXT_PUBLIC_[A-Z0-9_]+)\b')
SECRET_RE = re.compile(r'(?i)\b(api[_-]?key|secret|token|jwt|firebase|supabase|s3|gcs|azure|client[_-]?id)\b.{0,80}')
ROUTE_RE = re.compile(r'["\'](/(?:admin|internal|api|graphql|refund|payment|tenant|org|debug|feature|v[0-9])[^"\']{0,240})["\']')

MANIFEST_NAMES = {
    'asset-manifest.json','build-manifest.json','routes-manifest.json','app-build-manifest.json','prerender-manifest.json',
    'precache-manifest.json','manifest.json','vite-manifest.json','.vite/manifest.json'
}
JS_SUFFIXES = {'.js','.mjs','.cjs','.jsx','.ts','.tsx'}
MAP_SUFFIXES = {'.map'}
HTML_SUFFIXES = {'.html','.htm'}

@dataclass
class Evidence:
    kind: str
    value: str
    file: str
    line: int | None = None
    status: str = 'candidate-only'
    rule_id: str = ''

@dataclass
class Asset:
    asset_id: str
    path: str
    kind: str
    source: str
    sha256: str | None
    size: int | None
    mime: str | None
    evidence: list[Evidence]
    related: dict[str, Any]


def sha256_file(p: Path) -> str:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024), b''):
            h.update(b)
    return h.hexdigest()

def rel(p: Path, root: Path) -> str:
    try: return str(p.resolve().relative_to(root.resolve())).replace('\\','/')
    except Exception: return str(p)

def read_text(p: Path) -> str:
    data=p.read_bytes()
    if data[:2] == b'\x1f\x8b':
        try: data = gzip.decompress(data)
        except Exception: pass
    for enc in ('utf-8','utf-8-sig','latin-1'):
        try: return data.decode(enc, errors='replace')
        except Exception: continue
    return data.decode('utf-8', errors='replace')

def line_no(text: str, idx: int) -> int:
    return text.count('\n', 0, idx)+1

def local_resolve(base: Path, ref: str, root: Path) -> Path | None:
    if re.match(r'^[a-z][a-z0-9+.-]*:', ref, re.I) or ref.startswith('//') or ref.startswith('data:'):
        return None
    q=ref.split('#',1)[0].split('?',1)[0]
    if not q: return None
    cand=(base.parent / q).resolve()
    try:
        cand.relative_to(root.resolve())
    except Exception:
        return None
    return cand if cand.exists() else None

def add_asset(assets: dict[str, Asset], p: Path, root: Path, kind: str, source: str, ev: Evidence | None = None, related: dict[str,Any] | None = None):
    key=str(p.resolve())
    evidence=[] if ev is None else [ev]
    if key not in assets:
        mime=mimetypes.guess_type(str(p))[0]
        assets[key]=Asset(hashlib.sha1(key.encode()).hexdigest()[:16], rel(p,root), kind, source, sha256_file(p) if p.exists() and p.is_file() else None, p.stat().st_size if p.exists() and p.is_file() else None, mime, evidence, related or {})
    else:
        if ev: assets[key].evidence.append(ev)
        if related: assets[key].related.update(related)

def extract_json_urls(obj: Any, out: list[str]):
    if isinstance(obj, dict):
        for k,v in obj.items():
            if isinstance(v, str) and (v.endswith(('.js','.mjs','.map','.wasm')) or '/static/' in v or '/_next/' in v or 'chunk' in v.lower()):
                out.append(v)
            else:
                extract_json_urls(v, out)
    elif isinstance(obj, list):
        for v in obj: extract_json_urls(v, out)

def parse_sourcemap(p: Path, root: Path) -> tuple[list[Evidence], dict[str,Any]]:
    ev=[]; related={'sources':[], 'has_sourcesContent':False, 'sourcesContent_leak_candidates':[]}
    try:
        obj=json.loads(read_text(p))
    except Exception as e:
        ev.append(Evidence('sourcemap_parse_error', str(e), rel(p,root), None, 'partial', 'sourcemap.parse'))
        return ev, related
    sources=obj.get('sources') or []
    related['sources'] = sources[:200]
    sc=obj.get('sourcesContent')
    related['has_sourcesContent'] = isinstance(sc, list)
    if isinstance(sc, list):
        for i, content in enumerate(sc[:200]):
            if not isinstance(content, str): continue
            for rgx, kind, rid in [(SECRET_RE,'secret_candidate','sourcemap.sourcesContent.secret'),(ROUTE_RE,'hidden_route','sourcemap.sourcesContent.route'),(GRAPHQL_RE,'graphql_operation','sourcemap.sourcesContent.graphql')]:
                for m in rgx.finditer(content[:200000]):
                    src = sources[i] if i < len(sources) else f'sourcesContent[{i}]'
                    ev.append(Evidence(kind, m.group(0)[:240], f'{rel(p,root)}::{src}', line_no(content,m.start()), 'candidate-only', rid))
                    related['sourcesContent_leak_candidates'].append({'source':src,'kind':kind,'value':m.group(0)[:160]})
    return ev, related

def parse_har(p: Path, root: Path, assets: dict[str, Asset], evidence: list[Evidence]):
    try:
        obj=json.loads(read_text(p))
    except Exception as e:
        evidence.append(Evidence('har_parse_error', str(e), rel(p,root), None, 'partial', 'har.parse'))
        return
    entries = obj.get('log',{}).get('entries',[]) if isinstance(obj,dict) else []
    for idx, ent in enumerate(entries):
        req=ent.get('request',{}) if isinstance(ent,dict) else {}
        res=ent.get('response',{}) if isinstance(ent,dict) else {}
        url=req.get('url','')
        ctype=';'.join([h.get('value','') for h in res.get('headers',[]) if h.get('name','').lower() == 'content-type'])
        if url.endswith(('.js','.mjs','.map','.wasm')) or 'javascript' in ctype or 'sourcemap' in ctype:
            evidence.append(Evidence('har_js_asset', url, rel(p,root), idx+1, 'partial', 'har.asset'))
        if '/graphql' in url or 'graphql' in ctype:
            evidence.append(Evidence('har_graphql', url, rel(p,root), idx+1, 'partial', 'har.graphql'))
        if url.startswith(('ws://','wss://')):
            evidence.append(Evidence('har_websocket', url, rel(p,root), idx+1, 'partial', 'har.websocket'))

def scan_js(p: Path, root: Path) -> tuple[list[Evidence], dict[str,Any]]:
    text=read_text(p)
    ev=[]; related={'source_map_url':None,'dynamic_imports':[],'workers':[],'wasm':[],'endpoints':[],'websockets':[],'sse':[],'graphql':False,'postmessage':False,'storage':False,'env_keys':[],'hidden_routes':[]}
    for name, rgx, kind, rid in [
        ('source_map_url', SOURCE_MAP_RE, 'source_map_reference', 'js.sourcemap.reference'),
        ('dynamic_imports', DYNAMIC_IMPORT_RE, 'dynamic_import', 'js.dynamic_import'),
        ('workers', WORKER_RE, 'worker_reference', 'js.worker.reference'),
        ('wasm', WASM_RE, 'wasm_reference', 'js.wasm.reference'),
        ('endpoints', FETCH_RE, 'endpoint_candidate', 'js.endpoint.fetch'),
        ('websockets', WS_RE, 'websocket_candidate', 'js.websocket'),
        ('sse', SSE_RE, 'sse_candidate', 'js.sse'),
        ('env_keys', ENV_RE, 'public_env_key', 'js.env.public'),
        ('hidden_routes', ROUTE_RE, 'hidden_route_candidate', 'js.route.hidden'),
    ]:
        for m in rgx.finditer(text):
            val = next((g for g in m.groups() if g), m.group(0)) if m.groups() else m.group(0)
            ev.append(Evidence(kind, str(val)[:500], rel(p,root), line_no(text,m.start()), 'candidate-only', rid))
            if name == 'source_map_url': related[name] = str(val)
            elif isinstance(related.get(name), list): related[name].append(str(val)[:500])
    for rgx, kind, rid in [(GRAPHQL_RE,'graphql_operation_candidate','js.graphql.operation'),(POSTMESSAGE_RE,'postmessage_candidate','js.postmessage'),(STORAGE_RE,'storage_candidate','js.storage'),(SECRET_RE,'secret_candidate','js.secret.candidate')]:
        for m in rgx.finditer(text):
            ev.append(Evidence(kind, m.group(0)[:500], rel(p,root), line_no(text,m.start()), 'candidate-only', rid))
            if 'graphql' in kind: related['graphql']=True
            if 'postmessage' in kind: related['postmessage']=True
            if 'storage' in kind: related['storage']=True
    return ev, related

def scan_html(p: Path, root: Path, assets: dict[str, Asset], evidence: list[Evidence]):
    text=read_text(p)
    for rgx, kind, rid in [(SCRIPT_SRC_RE,'html_script_src','html.script.src'),(LINK_MANIFEST_RE,'html_link_manifest','html.link.manifest')]:
        for m in rgx.finditer(text):
            ref=m.group(1)
            evidence.append(Evidence(kind, ref, rel(p,root), line_no(text,m.start()), 'candidate-only', rid))
            lp=local_resolve(p, ref, root)
            if lp and lp.is_file():
                akind='javascript' if lp.suffix.lower() in JS_SUFFIXES else ('manifest' if lp.suffix.lower()=='.json' else 'asset')
                add_asset(assets, lp, root, akind, kind, evidence[-1])
    for m in INLINE_SCRIPT_RE.finditer(text):
        content=m.group(1)
        if len(content.strip()) > 20:
            evidence.append(Evidence('inline_script', content[:300], rel(p,root), line_no(text,m.start()), 'candidate-only', 'html.script.inline'))

def scan_manifest(p: Path, root: Path, assets: dict[str, Asset], evidence: list[Evidence]):
    try: obj=json.loads(read_text(p))
    except Exception as e:
        evidence.append(Evidence('manifest_parse_error', str(e), rel(p,root), None, 'partial', 'manifest.parse'))
        return
    urls=[]; extract_json_urls(obj, urls)
    for u in urls:
        evidence.append(Evidence('manifest_asset_reference', u, rel(p,root), None, 'candidate-only', 'manifest.asset.reference'))
        lp=local_resolve(p,u,root)
        if lp and lp.is_file():
            kind='sourcemap' if lp.suffix.lower() in MAP_SUFFIXES else ('javascript' if lp.suffix.lower() in JS_SUFFIXES else 'asset')
            add_asset(assets, lp, root, kind, 'manifest', evidence[-1])

def collect(root: Path, out: Path) -> dict[str,Any]:
    assets: dict[str,Asset] = {}
    evidence: list[Evidence] = []
    all_files=[p for p in root.rglob('*') if p.is_file()]
    for p in all_files:
        low=p.name.lower(); suf=p.suffix.lower()
        if suf in JS_SUFFIXES:
            ev, related=scan_js(p, root)
            kind = 'service_worker' if (low in {'service-worker.js','sw.js','workbox-sw.js'} or '/sw/' in str(p).replace('\\','/')) else 'javascript'
            add_asset(assets,p,root,kind,'filesystem',None,related)
            assets[str(p.resolve())].evidence.extend(ev)
            evidence.extend(ev)
            sm=related.get('source_map_url')
            if sm:
                lp=local_resolve(p, sm, root)
                if lp and lp.is_file(): add_asset(assets,lp,root,'sourcemap','js_source_mapping_url',Evidence('source_map_reference',sm,rel(p,root),None,'candidate-only','js.sourcemap.reference'))
        elif suf in HTML_SUFFIXES:
            scan_html(p, root, assets, evidence)
        elif suf in MAP_SUFFIXES:
            ev, related=parse_sourcemap(p,root)
            add_asset(assets,p,root,'sourcemap','filesystem',None,related)
            assets[str(p.resolve())].evidence.extend(ev); evidence.extend(ev)
        elif low in MANIFEST_NAMES or low.endswith('-manifest.json') or '/.vite/' in str(p).replace('\\','/'):
            add_asset(assets,p,root,'manifest','filesystem')
            scan_manifest(p,root,assets,evidence)
        elif low.endswith('.har'):
            parse_har(p,root,assets,evidence)
        elif low in {'service-worker.js','sw.js','workbox-sw.js'} or '/sw/' in str(p).replace('\\','/'):
            ev, related=scan_js(p,root)
            add_asset(assets,p,root,'service_worker','filesystem',None,related)
            assets[str(p.resolve())].evidence.extend(ev); evidence.extend(ev)
        elif suf == '.wasm':
            add_asset(assets,p,root,'wasm','filesystem')
    stats={
        'javascript_assets': sum(1 for a in assets.values() if a.kind=='javascript'),
        'sourcemaps': sum(1 for a in assets.values() if a.kind=='sourcemap'),
        'manifests': sum(1 for a in assets.values() if a.kind=='manifest'),
        'service_workers': sum(1 for a in assets.values() if a.kind=='service_worker'),
        'wasm': sum(1 for a in assets.values() if a.kind=='wasm'),
        'evidence_items': len(evidence),
    }
    ledger={'schema_version':'js-top-tier-ledger/v1','root':str(root),'status':'partial','reason':'offline collection; dynamic role/tenant runtime capture not proven unless HAR/trace evidence is provided','stats':stats,'assets':[asdict(a) for a in assets.values()],'evidence':[asdict(e) for e in evidence]}
    out.mkdir(parents=True, exist_ok=True)
    (out/'js_asset_ledger.json').write_text(json.dumps(ledger, ensure_ascii=False, indent=2), encoding='utf-8')
    return ledger

def main():
    ap=argparse.ArgumentParser(description='Top-tier JS asset collector with strict evidence downgrade semantics')
    ap.add_argument('--root', default='.', help='authorized local source/build/HAR directory')
    ap.add_argument('--out', default='reports/js-top-tier')
    args=ap.parse_args()
    r=Path(args.root).resolve(); out=Path(args.out).resolve()
    if not r.exists():
        raise SystemExit(f'root not found: {r}')
    ledger=collect(r,out)
    print(json.dumps({'ok':True,'out':str(out/'js_asset_ledger.json'),'stats':ledger['stats'],'status':ledger['status']}, ensure_ascii=False, indent=2))
if __name__ == '__main__': main()

#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re, hashlib
from pathlib import Path
from _scope import iter_scoped_files, read_text_safe

TEXT_EXT = {'.html','.htm','.js','.jsx','.ts','.tsx','.mjs','.cjs','.vue','.json','.map'}
ENDPOINT_RE = re.compile(r'(?P<quote>["\'`])(?P<path>(?:(?:https?:)?//|wss?://|/)(?:api|admin|internal|graphql|socket|ws|v\d|download|upload|export|import|webhook|callback|oauth|saml|auth|tenant|org|workspace)[^"\'`\s<>{}]*)', re.I)
FETCH_RE = re.compile(r'\b(fetch|axios\.(?:get|post|put|patch|delete)|\$fetch|ky\.|superagent\.|request\(|graphqlRequest|client\.query|client\.mutate)\s*\(', re.I)
SCRIPT_RE = re.compile(r'<script[^>]+src=["\']([^"\']+)["\']', re.I)
SM_RE = re.compile(r'sourceMappingURL=([^\s*]+)')
GQL_RE = re.compile(r'\b(query|mutation|subscription)\s+([A-Za-z0-9_]+)?\s*[({]')
STORAGE_RE = re.compile(r'\b(localStorage|sessionStorage|indexedDB|document\.cookie|BroadcastChannel)\b')
POSTMSG_RE = re.compile(r'\bpostMessage\s*\(')
WS_RE = re.compile(r'\b(new\s+WebSocket|EventSource)\s*\(\s*["\'`]([^"\'`]+)')
SECRET_RE = re.compile(r'(?i)\b(api[_-]?key|secret|token|jwt|sentry_dsn|firebase|supabase|stripe|oauth|client_secret)[A-Za-z0-9_\-]*\s*[:=]\s*["\']([^"\']{8,})')
DOM_SINK_RE = re.compile(r'\b(innerHTML|outerHTML|insertAdjacentHTML|document\.write|eval|new Function|setTimeout|setInterval)\b')
SW_REGISTER_RE = re.compile(r'navigator\.serviceWorker\.register\s*\(\s*["\'`]([^"\'`]+)')
SW_FETCH_RE = re.compile(r'addEventListener\s*\(\s*["\']fetch["\']|event\.respondWith|caches\.match|cache\.put', re.I)
GUARD_RE = re.compile(r'\b(beforeEach|requireAuth|isAdmin|hasPermission|canActivate|routeGuard|permission|roles?|tenant|owner|featureFlag|flags?\.)\b', re.I)
PLATFORM_RE = re.compile(r'\b(contextBridge|ipcRenderer|ipcMain|remote|chrome\.runtime|browser\.runtime|content_scripts|manifest_version|wx\.request|my\.request|tt\.request|swan\.request)\b', re.I)
PARAM_RE = re.compile(r'(?P<key>[A-Za-z_$][A-Za-z0-9_$]{1,40})\s*:', re.M)
BASE_RE = re.compile(r'\b(baseURL|API_BASE|apiBase|NEXT_PUBLIC_[A-Z0-9_]+|VITE_[A-Z0-9_]+|REACT_APP_[A-Z0-9_]+)\s*[:=]\s*["\'`]([^"\'`]+)')
FEATURE_RE = re.compile(r'(?i)\b(featureFlag|feature_flags|experiment|abtest|preview|beta|debug|dryRun|trace|internal|adminOnly)\b')

def sha(s: str) -> str:
    return hashlib.sha256(s.encode('utf-8','ignore')).hexdigest()[:16]

def line_of(text: str, idx: int) -> int:
    return text.count('\n', 0, idx) + 1

def extract(root: str | Path):
    root = Path(root).resolve()
    out = {
        'schema_version':'js-asset-v1','source_root':str(root),'assets':[], 'endpoints':[],
        'graphql_operations':[], 'storage_uses':[], 'post_messages':[], 'secret_like_tokens':[],
        'dom_sinks':[], 'sourcemaps':[], 'service_workers':[], 'api_wrappers':[],
        'frontend_guards':[], 'platform_bridges':[], 'hidden_parameter_candidates':[],
        'base_urls':[], 'feature_flags':[], 'chunk_lineage':[],
        'policy':'candidate-only; backend correlation, auth/tenant matrix and dynamic evidence required before confirmation'
    }
    seen_assets=set(); seen_eps=set()
    for p in iter_scoped_files(root, 'js_artifact'):
        if p.suffix.lower() not in TEXT_EXT:
            continue
        try: text = read_text_safe(p, limit=8_000_000, redact=True)
        except Exception: continue
        rel = str(p.relative_to(root))
        suf=p.suffix.lower()
        if suf in {'.js','.jsx','.ts','.tsx','.mjs','.cjs','.vue'}:
            aid='js-'+sha(rel)
            if aid not in seen_assets:
                seen_assets.add(aid)
                out['assets'].append({'id':aid, 'kind':'javascript', 'path':rel, 'size':len(text), 'minified_hint': text.count('\n') < 3 and len(text) > 500, 'probable_chunk': bool(re.search(r'[.-][a-f0-9]{6,}\.', Path(rel).name, re.I))})
        if rel.lower().endswith(('asset-manifest.json','manifest.json','webpack-stats.json','build-manifest.json','react-loadable-manifest.json')):
            out['chunk_lineage'].append({'id':'chunk-'+sha(rel),'file':rel,'kind':'build_or_extension_manifest','review':'inspect chunk entrypoints, stale assets, extension permissions and content scripts'})
        for m in SCRIPT_RE.finditer(text):
            out['assets'].append({'id':'script-'+sha(rel+m.group(1)), 'kind':'script_tag', 'path':m.group(1), 'declared_in':rel, 'line':line_of(text,m.start()), 'external':m.group(1).startswith(('http','//'))})
        for m in ENDPOINT_RE.finditer(text):
            key=(rel,m.group('path'),m.start())
            if key not in seen_eps:
                seen_eps.add(key)
                path=m.group('path')
                out['endpoints'].append({'id':'ep-'+sha(rel+path+str(m.start())), 'path':path, 'file':rel, 'line':line_of(text,m.start()), 'evidence':'literal_endpoint', 'method_hint':'unknown', 'requires_backend_correlation':True})
        for m in FETCH_RE.finditer(text):
            out['api_wrappers'].append({'id':'wrap-'+sha(rel+str(m.start())), 'wrapper':m.group(1), 'file':rel, 'line':line_of(text,m.start()), 'requires_wrapper_resolution':True})
        for m in SM_RE.finditer(text):
            out['sourcemaps'].append({'id':'sm-'+sha(rel+m.group(1)), 'path':m.group(1), 'file':rel, 'line':line_of(text,m.start()), 'must_resolve_for_promoted_js_audit':True})
        for m in GQL_RE.finditer(text):
            out['graphql_operations'].append({'id':'gql-'+sha(rel+str(m.start())), 'operation_type':m.group(1), 'name':m.group(2) or '', 'file':rel, 'line':line_of(text,m.start()), 'authz_review_required':True})
        for m in STORAGE_RE.finditer(text):
            out['storage_uses'].append({'id':'storage-'+sha(rel+str(m.start())), 'api':m.group(1), 'file':rel, 'line':line_of(text,m.start())})
        for m in POSTMSG_RE.finditer(text):
            out['post_messages'].append({'id':'pm-'+sha(rel+str(m.start())), 'file':rel, 'line':line_of(text,m.start()), 'origin_validation_required':True})
        for m in WS_RE.finditer(text):
            out['endpoints'].append({'id':'ws-'+sha(rel+m.group(2)), 'path':m.group(2), 'file':rel, 'line':line_of(text,m.start()), 'evidence':'websocket_or_sse', 'requires_message_type_matrix':True})
        for m in SECRET_RE.finditer(text):
            out['secret_like_tokens'].append({'id':'sec-'+sha(rel+str(m.start())), 'kind':m.group(1), 'file':rel, 'line':line_of(text,m.start()), 'redacted_value_hash':sha(m.group(2)), 'value':'<REDACTED>'})
        for m in DOM_SINK_RE.finditer(text):
            out['dom_sinks'].append({'id':'dom-'+sha(rel+str(m.start())), 'sink':m.group(1), 'file':rel, 'line':line_of(text,m.start())})
        for m in SW_REGISTER_RE.finditer(text):
            out['service_workers'].append({'id':'sw-'+sha(rel+m.group(1)), 'path':m.group(1), 'declared_in':rel, 'line':line_of(text,m.start()), 'cache_route_review_required':True})
        if SW_FETCH_RE.search(text) or Path(rel).name.lower().startswith('service-worker'):
            out['service_workers'].append({'id':'sw-file-'+sha(rel), 'path':rel, 'declared_in':rel, 'line':1, 'cache_route_review_required':True})
        for m in GUARD_RE.finditer(text):
            out['frontend_guards'].append({'id':'guard-'+sha(rel+str(m.start())), 'signal':m.group(1), 'file':rel, 'line':line_of(text,m.start()), 'cannot_prove_backend_authz':True})
        for m in PLATFORM_RE.finditer(text):
            out['platform_bridges'].append({'id':'bridge-'+sha(rel+str(m.start())), 'signal':m.group(1), 'file':rel, 'line':line_of(text,m.start()), 'boundary_review_required':True})
        for m in BASE_RE.finditer(text):
            out['base_urls'].append({'id':'base-'+sha(rel+str(m.start())), 'name':m.group(1), 'value':m.group(2), 'file':rel, 'line':line_of(text,m.start())})
        for m in FEATURE_RE.finditer(text):
            out['feature_flags'].append({'id':'flag-'+sha(rel+str(m.start())), 'signal':m.group(1), 'file':rel, 'line':line_of(text,m.start())})
        # Conservative hidden-param candidates from object literals close to request wrappers.
        if FETCH_RE.search(text):
            for m in PARAM_RE.finditer(text):
                key=m.group('key')
                if key.lower() in {'headers','body','params','data','method','url','query','role','tenantid','orgid','workspaceid','userid','ownerid','admin','debug','dryrun','trace','preview'}:
                    out['hidden_parameter_candidates'].append({'id':'param-'+sha(rel+key+str(m.start())), 'name':key, 'file':rel, 'line':line_of(text,m.start()), 'reason':'request-adjacent object key; compare frontend schema to backend DTO/model'})
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('root')
    ap.add_argument('--out', required=True)
    ns=ap.parse_args()
    data=extract(ns.root)
    Path(ns.out).parent.mkdir(parents=True, exist_ok=True)
    Path(ns.out).write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'ok':True,'endpoints':len(data['endpoints']),'assets':len(data['assets']),'sourcemaps':len(data['sourcemaps']),'graphql':len(data['graphql_operations']),'service_workers':len(data['service_workers'])}, ensure_ascii=False))
if __name__=='__main__': main()

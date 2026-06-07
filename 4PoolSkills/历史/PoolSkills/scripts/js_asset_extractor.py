#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,re,hashlib
from pathlib import Path
SCRIPT=re.compile(r"<script[^>]+src=['\"]([^'\"]+)['\"]",re.I)
SM=re.compile(r"sourceMappingURL=([^\s*]+)")
EP=re.compile(r"(?:(?:https?:)?//[^'\"\s]+|/(?:api|graphql|v\d|admin|internal|webhook)[A-Za-z0-9_./:{}?=&%-]*)")
SEC=re.compile(r"(?i)(api[_-]?key|token|secret|bucket|access[_-]?key|sentry_dsn|supabase|firebase)\s*[:=]\s*['\"][^'\"]{6,}")
GUARD=re.compile(r"(?i)(beforeEach|isAdmin|hasPermission|requireAuth|canActivate|routeGuard|featureFlag|permissions?|roles?)")
WRAP=re.compile(r"(?i)(axios\.create|interceptors\.|fetch\(|request\(|graphql\(|gql`|new WebSocket|EventSource|postMessage|addEventListener\(['\"]message)")
PLATFORM=re.compile(r"(?i)(contextBridge|ipcRenderer|chrome\.runtime|browser\.runtime|content_scripts|manifest_version|wx\.request|my\.request|tt\.request|swan\.request)")
def sha(p):
    try: return hashlib.sha256(p.read_bytes()).hexdigest()[:16]
    except Exception: return None

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('project'); ap.add_argument('--out',default='outputs/js_assets.json'); a=ap.parse_args(); r=Path(a.project).resolve()
    out={'schema_version':'js-asset-inventory-v3','script_references':[],'local_js_files':[],'chunk_lineage':[],'sourcemaps':[],'endpoints':[],'secret_candidates':[],'frontend_guards':[],'api_wrappers':[],'platform_bridges':[],'policy':'candidate only until backend mapping, impact and dynamic evidence exist'}
    for p in r.rglob('*'):
        if any(x in p.parts for x in ['.git','node_modules','vendor']): continue
        if not p.is_file() or p.stat().st_size>2000000: continue
        rel=str(p.relative_to(r)); suf=p.suffix.lower()
        if suf not in ['.html','.htm','.vue','.js','.mjs','.cjs','.ts','.jsx','.tsx','.json']: continue
        txt=p.read_text(encoding='utf-8',errors='ignore')
        if suf in ['.html','.htm','.vue','.jsx','.tsx']:
            for m in SCRIPT.finditer(txt): out['script_references'].append({'from':rel,'src':m.group(1),'is_cdn_or_external':m.group(1).startswith(('http','//'))})
        if suf in ['.js','.mjs','.cjs','.ts','.jsx','.tsx','.vue']:
            out['local_js_files'].append({'file':rel,'sha256_16':sha(p),'size':p.stat().st_size,'probable_chunk':bool(re.search(r'[.-][a-f0-9]{6,}\.',p.name,re.I))})
            for m in SM.finditer(txt): out['sourcemaps'].append({'file':rel,'sourceMappingURL':m.group(1)})
            for m in EP.finditer(txt): out['endpoints'].append({'file':rel,'endpoint':m.group(0)[:250],'line':txt[:m.start()].count('\n')+1})
            for m in SEC.finditer(txt): out['secret_candidates'].append({'file':rel,'line':txt[:m.start()].count('\n')+1,'pattern':m.group(1),'candidate_only':True,'handling':'redact_value'})
            for m in GUARD.finditer(txt): out['frontend_guards'].append({'file':rel,'line':txt[:m.start()].count('\n')+1,'signal':m.group(1)})
            for m in WRAP.finditer(txt): out['api_wrappers'].append({'file':rel,'line':txt[:m.start()].count('\n')+1,'signal':m.group(1),'requires_backend_correlation':True})
            for m in PLATFORM.finditer(txt): out['platform_bridges'].append({'file':rel,'line':txt[:m.start()].count('\n')+1,'signal':m.group(1),'boundary_review_required':True})
        if rel.lower().endswith(('asset-manifest.json','manifest.json','webpack-stats.json','build-manifest.json','react-loadable-manifest.json')):
            out['chunk_lineage'].append({'file':rel,'kind':'build_or_extension_manifest','summary':'inspect chunk entrypoints, extension permissions, content scripts, and stale assets'})
    Path(a.out).parent.mkdir(parents=True,exist_ok=True); Path(a.out).write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__': main()

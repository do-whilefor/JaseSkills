#!/usr/bin/env python3
"""Authorized JS asset collector and static audit candidate extractor.

It is intentionally non-invasive: it reads local files only, never downloads
remote assets, never validates secrets, and never turns candidates into
confirmed findings. Output is JSONL suitable for evidence manifests and QG.
"""
from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path
from typing import Iterable

SKIP_DIRS={'.git','node_modules','vendor','__pycache__','.venv','venv','.next/cache','dist-info','target','build/cache'}
TEXT_EXTS={'.html','.htm','.js','.mjs','.cjs','.jsx','.ts','.tsx','.vue','.svelte','.json','.map','.css'}
SCRIPT_SRC=re.compile(r'<script\b[^>]*\bsrc=["\']([^"\']+)["\'][^>]*>', re.I)
INLINE_SCRIPT=re.compile(r'<script\b(?![^>]*\bsrc=)[^>]*>(.*?)</script>', re.I|re.S)
LINK_REL=re.compile(r'<link\b[^>]*\b(?:rel|as)=["\']([^"\']+)["\'][^>]*\bhref=["\']([^"\']+)["\'][^>]*>', re.I)
NEXT_DATA=re.compile(r'<script\b[^>]*\bid=["\']__NEXT_DATA__["\'][^>]*>(.*?)</script>', re.I|re.S)
NUXT_DATA=re.compile(r'window\.__NUXT__|__NUXT_DATA__', re.I)
SOURCEMAP=re.compile(r'[#@]\s*sourceMappingURL\s*=\s*([^\s*]+)')
DYNAMIC_IMPORT=re.compile(r'\bimport\s*\(\s*([`"\'])(.*?)\1\s*\)', re.S)
REQUIRE_ENSURE=re.compile(r'\brequire\.ensure\s*\(')
FETCH_CALL=re.compile(r'\b(fetch|axios(?:\.[a-z]+)?|XMLHttpRequest|WebSocket|EventSource|graphql|gql|ApolloClient|Relay|urql)\b', re.I)
URL_LITERAL=re.compile(r'([`"\'])(?P<url>(?:https?://[^`"\']+)|(?:/[A-Za-z0-9_./{}:$?&=%+\-#]{2,}))\1')
GRAPHQL_OP=re.compile(r'\b(query|mutation|subscription)\s+([A-Za-z0-9_]+)?\s*\(', re.I)
AUTH_HINT=re.compile(r'\b(Authorization|Bearer|X-CSRF|csrf|withCredentials|credentials|api[_-]?key|refresh[_-]?token|access[_-]?token)\b', re.I)
PARAM_SOURCE=re.compile(r'\b(location|URLSearchParams|localStorage|sessionStorage|indexedDB|postMessage|document\.cookie|FormData|route\.params|params\.|query\.)\b', re.I)
DANGEROUS_SINK=re.compile(r'\b(eval|Function|innerHTML|dangerouslySetInnerHTML|document\.write|child_process|exec\(|spawn\(|open\(|readFile|writeFile|template|redirect|callback|objectKey|bucket|tenantId|userId|roleId)\b', re.I)
BUNDLER_SIGS={
  'webpack':[r'__webpack_require__', r'webpackJsonp', r'webpackChunk'],
  'vite':[r'vite/preload-helper', r'import\.meta\.env', r'/@vite/'],
  'rollup':[r'rollup', r'System\.register'],
  'parcel':[r'parcelRequire'],
  'next':[r'__NEXT_DATA__', r'/_next/static/', r'build-manifest\.json'],
  'nuxt':[r'__NUXT__', r'_nuxt/'],
  'angular':[r'ng-version', r'ɵɵdefineComponent'],
  'react':[r'React\.createElement', r'jsx-runtime'],
  'vue':[r'Vue\.createApp', r'__VUE__'],
  'remix':[r'__remixContext', r'manifest-[A-Z0-9a-z]']
}
EDGE_FILES={'asset-manifest.json','build-manifest.json','manifest.json','service-worker.js','sw.js','workbox-', 'precache-manifest'}

def sha(s:str)->str: return hashlib.sha256(s.encode()).hexdigest()
def skip(p:Path)->bool: return any(part in SKIP_DIRS for part in p.parts)
def line_of(text:str, offset:int)->int: return text.count('\n',0,offset)+1
def redact(v:str)->str:
    v=str(v).strip()
    v=re.sub(r'(eyJ[A-Za-z0-9_.-]{20,})', lambda m:m.group(1)[:3]+'****'+m.group(1)[-3:], v)
    v=re.sub(r'(?i)(token|secret|api[_-]?key|password|session|cookie)=([^&\s]+)', r'\1=****', v)
    if len(v)>220: return v[:100]+'…'+v[-40:]
    return v

def emit(kind:str, path:Path, root:Path, text:str, offset:int, value:object, extra:dict|None=None)->dict:
    rel=str(path.relative_to(root))
    item={
        'asset_id':'JS-'+sha(f'{rel}:{kind}:{line_of(text,offset)}:{value}')[:12],
        'type':kind,
        'source_file':rel,
        'line':line_of(text,offset),
        'value':value,
        'evidence_status':'static_candidate_needs_dynamic_validation',
        'dynamic_status':'not_validated',
        'redaction_status':'redacted_or_metadata_only'
    }
    if extra: item.update(extra)
    return item

def scan_file(path:Path, root:Path)->Iterable[dict]:
    try: text=path.read_text(encoding='utf-8', errors='ignore')
    except Exception: return []
    out=[]; lower_name=path.name.lower(); suffix=path.suffix.lower()
    if suffix in {'.html','.htm','.vue','.svelte'}:
        for m in SCRIPT_SRC.finditer(text): out.append(emit('html_script_src',path,root,text,m.start(),redact(m.group(1))))
        for m in INLINE_SCRIPT.finditer(text): out.append(emit('inline_script',path,root,text,m.start(),{'sha256':sha(m.group(1)),'length':len(m.group(1))}))
        for m in LINK_REL.finditer(text):
            rel=m.group(1).lower(); href=m.group(2)
            if any(x in rel for x in ['manifest','preload','prefetch','script','modulepreload']): out.append(emit('html_link_asset',path,root,text,m.start(),{'rel':rel,'href':redact(href)}))
        for m in NEXT_DATA.finditer(text): out.append(emit('next_data',path,root,text,m.start(),{'sha256':sha(m.group(1)),'length':len(m.group(1))}))
    if any(k in lower_name for k in EDGE_FILES) or lower_name.endswith('.webmanifest'):
        out.append(emit('edge_manifest_or_worker_file',path,root,text,0,lower_name))
    for name,pats in BUNDLER_SIGS.items():
        if any(re.search(p,text,re.I) for p in pats): out.append(emit('bundler_or_framework_signature',path,root,text,0,name))
    if NUXT_DATA.search(text): out.append(emit('nuxt_payload_hint',path,root,text,0,'nuxt payload/global data'))
    for m in SOURCEMAP.finditer(text): out.append(emit('sourcemap_hint',path,root,text,m.start(),redact(m.group(1))))
    for m in DYNAMIC_IMPORT.finditer(text): out.append(emit('dynamic_import_chunk',path,root,text,m.start(),redact(m.group(2))))
    for m in REQUIRE_ENSURE.finditer(text): out.append(emit('require_ensure_chunk',path,root,text,m.start(),'require.ensure'))
    for m in URL_LITERAL.finditer(text):
        url=m.group('url')
        if len(url)>2: out.append(emit('url_or_endpoint_literal',path,root,text,m.start(),redact(url)))
    for m in FETCH_CALL.finditer(text): out.append(emit('request_wrapper_hint',path,root,text,m.start(),m.group(1)))
    for m in GRAPHQL_OP.finditer(text): out.append(emit('graphql_operation_hint',path,root,text,m.start(),{'operation':m.group(1),'name':m.group(2)}))
    for m in AUTH_HINT.finditer(text): out.append(emit('auth_material_flow_hint',path,root,text,m.start(),m.group(1)))
    for m in PARAM_SOURCE.finditer(text): out.append(emit('parameter_source_hint',path,root,text,m.start(),m.group(1)))
    for m in DANGEROUS_SINK.finditer(text): out.append(emit('source_sink_candidate_hint',path,root,text,m.start(),m.group(1)))
    return out

def main()->int:
    ap=argparse.ArgumentParser(description='Collect JS/static frontend candidates from an authorized local project.')
    ap.add_argument('root')
    ap.add_argument('-o','--output',default='js-asset-candidates.jsonl')
    ap.add_argument('--max-bytes',type=int,default=3_000_000)
    args=ap.parse_args(); root=Path(args.root).resolve(); count=0
    with Path(args.output).open('w',encoding='utf-8') as wf:
        for p in sorted(root.rglob('*')):
            if skip(p) or not p.is_file() or p.suffix.lower() not in TEXT_EXTS: continue
            try:
                if p.stat().st_size>args.max_bytes: continue
            except Exception: continue
            for item in scan_file(p,root):
                wf.write(json.dumps(item,ensure_ascii=False)+'\n'); count+=1
    print(f'wrote {count} JS/static candidates to {args.output}')
    return 0
if __name__=='__main__': raise SystemExit(main())

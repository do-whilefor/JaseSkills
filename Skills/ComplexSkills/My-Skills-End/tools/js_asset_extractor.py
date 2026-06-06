#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re, hashlib
from pathlib import Path
SCRIPT_RE = re.compile(r'<script[^>]+src=["\']([^"\']+)["\']', re.I)
ENDPOINT_RE = re.compile(r'''(?P<q>["'`])(?P<val>(?:https?://[^"'`\s]+|wss?://[^"'`\s]+|/(?:api|graphql|v\d|admin|internal|webhook|ws|sse)[^"'`\s<>]*))(?P=q)''')
GRAPHQL_RE = re.compile(r'\b(query|mutation|subscription)\s+[A-Za-z0-9_]+|/graphql\b', re.I)
STORAGE_RE = re.compile(r'\b(localStorage|sessionStorage|indexedDB|document\.cookie|cookieStore)\b')
POSTMESSAGE_RE = re.compile(r'\b(postMessage|addEventListener\(["\']message["\'])')
SOURCEMAP_RE = re.compile(r'//#\s*sourceMappingURL=([^\s]+)|([A-Za-z0-9._/-]+\.map)')
SECRET_RE = re.compile(r'\b(?:api[_-]?key|secret|token|jwt|sentry_dsn|firebase|supabase|stripe)[A-Za-z0-9_\-]*\b\s*[:=]\s*["\']([^"\']{8,})["\']', re.I)
SERVICE_WORKER_RE = re.compile(r'\bserviceWorker\.register\(["\']([^"\']+)["\']')
def sha256(p: Path):
    try: return hashlib.sha256(p.read_bytes()).hexdigest()
    except Exception: return None
def line_no(text, pos): return text.count('\n', 0, pos) + 1
def rel(root, p):
    try: return str(p.relative_to(root))
    except Exception: return str(p)
def extract(root: Path):
    root = root.resolve(); result={'schema_version':'js_asset_v1','parser_mode':'regex_candidate_not_ast','root':str(root),'assets':[],'endpoints':[],'source_maps':[],'graphql':[],'storage':[],'post_message':[],'secret_like':[],'service_workers':[],'warnings':['Deterministic local candidate extraction, not full Babel/TypeScript AST analysis.']}
    files=[p for p in root.rglob('*') if p.is_file() and p.suffix.lower() in {'.html','.htm','.js','.jsx','.ts','.tsx','.mjs','.cjs'}]
    for p in sorted(files):
        text=p.read_text(encoding='utf-8', errors='ignore'); src={'path':rel(root,p),'sha256':sha256(p)}; kind='html' if p.suffix.lower() in {'.html','.htm'} else 'javascript'
        result['assets'].append({'path':src['path'],'kind':kind,'sha256':src['sha256']})
        if kind == 'html':
            for m in SCRIPT_RE.finditer(text): result['assets'].append({'path':m.group(1),'kind':'script_reference','source':{'path':src['path'],'line':line_no(text,m.start())}})
        for m in ENDPOINT_RE.finditer(text):
            val=m.group('val'); k='websocket' if val.startswith(('ws://','wss://')) or '/ws' in val else ('graphql' if 'graphql' in val.lower() else 'http_api')
            result['endpoints'].append({'value':val,'kind':k,'source':{'path':src['path'],'line':line_no(text,m.start())}})
        for m in GRAPHQL_RE.finditer(text): result['graphql'].append({'value':m.group(0)[:160],'source':{'path':src['path'],'line':line_no(text,m.start())}})
        for m in STORAGE_RE.finditer(text): result['storage'].append({'api':m.group(1),'source':{'path':src['path'],'line':line_no(text,m.start())}})
        for m in POSTMESSAGE_RE.finditer(text): result['post_message'].append({'api':m.group(1),'source':{'path':src['path'],'line':line_no(text,m.start())}})
        for m in SOURCEMAP_RE.finditer(text): result['source_maps'].append({'value':m.group(1) or m.group(2),'source':{'path':src['path'],'line':line_no(text,m.start())}})
        for m in SERVICE_WORKER_RE.finditer(text): result['service_workers'].append({'value':m.group(1),'source':{'path':src['path'],'line':line_no(text,m.start())}})
        for m in SECRET_RE.finditer(text): result['secret_like'].append({'kind':'secret_like_candidate','redacted_value':'<redacted>','source':{'path':src['path'],'line':line_no(text,m.start())},'reporting_policy':'candidate_only_until_impact_verified'})
    return result
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('root'); ap.add_argument('--out'); args=ap.parse_args(); res=extract(Path(args.root)); txt=json.dumps(res,ensure_ascii=False,indent=2)
    if args.out: Path(args.out).parent.mkdir(parents=True, exist_ok=True); Path(args.out).write_text(txt+'\n', encoding='utf-8')
    print(txt)
if __name__=='__main__': main()

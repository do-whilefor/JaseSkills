#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,re
from pathlib import Path
SKIP={'.git','node_modules','vendor','target','dist','build','.next','coverage','outputs'}
ROUTE_PATTERNS=[
 ('express_koa_fastify', re.compile(r"(?:app|router|server)\.(get|post|put|patch|delete|head|options|all)\s*\(\s*['\"]([^'\"]+)",re.I), ['.js','.ts','.jsx','.tsx']),
 ('nestjs_controller', re.compile(r"@(Get|Post|Put|Patch|Delete|Options|Head|All)\s*\(\s*['\"]?([^'\")]+)?['\"]?\s*\)",re.I), ['.ts','.js']),
 ('next_route_handler', re.compile(r"export\s+(?:async\s+)?function\s+(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s*\(",re.I), ['.js','.ts','.tsx']),
 ('django_path', re.compile(r"(?:path|re_path)\s*\(\s*r?['\"]([^'\"]+)['\"]\s*,\s*([A-Za-z_][A-Za-z0-9_\.]*)",re.I), ['.py']),
 ('fastapi', re.compile(r"@(?:app|router)\.(get|post|put|patch|delete|head|options)\s*\(\s*['\"]([^'\"]+)",re.I), ['.py']),
 ('spring', re.compile(r"@(GetMapping|PostMapping|PutMapping|PatchMapping|DeleteMapping|RequestMapping)\s*(?:\(\s*(?:value\s*=\s*|path\s*=\s*)?['\"]([^'\"]*)['\"])?",re.I), ['.java','.kt']),
 ('laravel', re.compile(r"Route::(?:middleware\s*\([^)]*\)\s*->\s*)?(get|post|put|patch|delete|any|match)\s*\(\s*['\"]([^'\"]+)",re.I), ['.php']),
 ('rails', re.compile(r"\b(get|post|put|patch|delete|match)\s+['\"]([^'\"]+)['\"]",re.I), ['.rb']),
 ('go_gin_fiber_chi', re.compile(r"\.(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS|HandleFunc|Handle)\s*\(\s*\"([^\"]+)\"",re.I), ['.go']),
 ('rust_axum_actix', re.compile(r"(?:\.route\s*\(\s*\"([^\"]+)\"\s*,\s*(get|post|put|patch|delete|any)\s*\(|#\[(get|post|put|patch|delete)\(\s*\"([^\"]+)\"\s*\)\])",re.I), ['.rs']),
]
SIGNALS=['openapi','swagger','graphql','websocket','socket.io','grpc','proto3','sse','eventsource','webhook','cron','queue','worker','bullmq','sidekiq','celery','rq','resque']

def method_route(framework, match, rel):
    g=match.groups()
    if framework=='django_path': return 'ANY','/'+g[0].lstrip('/'), g[1]
    if framework=='next_route_handler':
        route='/' + rel.replace('app/','').replace('pages/api/','').rsplit('.',1)[0]
        route=re.sub(r'/route$', '', route)
        if route.startswith('/api/') is False and rel.startswith('app/api/'): route='/api/'+route.lstrip('/')
        return g[0].upper(), normalize_route(route), g[0]
    if framework=='spring': return ({'GetMapping':'GET','PostMapping':'POST','PutMapping':'PUT','PatchMapping':'PATCH','DeleteMapping':'DELETE'}.get(g[0], 'ANY')), (g[1] or '/'), None
    if framework=='rust_axum_actix':
        route = g[0] or g[3] or '/'; method=(g[1] or g[2] or 'ANY').upper(); return method, route, None
    return g[0].upper(), g[1], None

def normalize_route(route):
    route = route or '/'
    route = re.sub(r'<(?:[A-Za-z_][A-Za-z0-9_]*:)?([A-Za-z_][A-Za-z0-9_]*)>', r'{\1}', route)
    route = re.sub(r'\[([A-Za-z_][A-Za-z0-9_]*)\]', r'{\1}', route)
    return '/' + route.lstrip('/')

def params(route):
    r=normalize_route(route or '')
    return sorted(set(re.findall(r':([A-Za-z_][A-Za-z0-9_]*)', r) + re.findall(r'\{([A-Za-z_][A-Za-z0-9_]*)\}', r)))

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('project'); ap.add_argument('--out',default='outputs/attack_surface.json'); a=ap.parse_args(); root=Path(a.project).resolve()
    routes=[]; docs=[]; non_http=[]
    for p in root.rglob('*'):
        if any(x in p.parts for x in SKIP) or not p.is_file(): continue
        rel=str(p.relative_to(root)); suf=p.suffix.lower()
        if suf not in {'.js','.ts','.tsx','.jsx','.py','.java','.kt','.php','.rb','.go','.rs','.json','.yml','.yaml','.proto','.md','.html','.vue'}: continue
        try: txt=p.read_text(encoding='utf-8', errors='ignore')
        except Exception: continue
        low=(txt+'\n'+rel).lower(); sig=[x for x in SIGNALS if x in low]
        if sig: docs.append({'file':rel,'signals':sig,'line':1})
        if any(x in low for x in ['cron','queue','worker','consumer','@scheduled','sidekiq','celery','bullmq']): non_http.append({'file':rel,'signals':[x for x in ['cron','queue','worker','consumer','scheduled'] if x in low]})
        for fw,rx,exts in ROUTE_PATTERNS:
            if suf not in exts: continue
            for m in rx.finditer(txt):
                meth, route, handler = method_route(fw,m,rel)
                routes.append({'framework_hint':fw,'file':rel,'line':txt[:m.start()].count('\n')+1,'method':meth,'route':normalize_route(route or '/'), 'handler_hint':handler, 'parameters':params(route or ''), 'source':'route_extractor_v2'})
        if rel.startswith('pages/api/') and suf in ['.js','.ts','.jsx','.tsx'] and re.search(r'export\s+default\s+(?:async\s+)?function|module\.exports\s*=', txt):
            route='/' + rel.replace('pages/api/','api/').rsplit('.',1)[0]
            routes.append({'framework_hint':'next_pages_api','file':rel,'line':1,'method':'ANY','route':normalize_route(route), 'handler_hint':'default_handler', 'parameters':params(route), 'source':'route_extractor_v2'})
    out={'schema_version':'attack-surface-v2','project':str(root),'routes':routes,'api_docs_and_realtime_signals':docs,'non_http_entrypoints':non_http,'policy':'candidate inventory only; never confirm vulnerabilities from routes alone'}
    Path(a.out).parent.mkdir(parents=True,exist_ok=True); Path(a.out).write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__': main()

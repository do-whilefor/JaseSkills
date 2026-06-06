#!/usr/bin/env python3
"""Semantic graph builder for authorized local code review.

This is a dependency-light extractor that builds a route/source/guard/sink graph
from local project files. It does not execute target code and it does not send
network traffic. Its purpose is to create evidence-backed review input for later
browser/API replay, not to confirm vulnerabilities by itself.
"""
from __future__ import annotations
import argparse, json, re, hashlib
from pathlib import Path
from typing import Any, Iterable

LANG_EXT = {
    '.js':'javascript','.jsx':'javascript','.ts':'typescript','.tsx':'typescript',
    '.py':'python','.java':'java','.php':'php','.go':'go','.rs':'rust','.rb':'ruby',
    '.yml':'yaml','.yaml':'yaml','.json':'json','.md':'markdown','.sh':'shell',
    '.ps1':'powershell','.tf':'terraform','.sql':'sql','.xml':'xml','.gradle':'gradle'
}
HTTP_METHODS = ['get','post','put','patch','delete','options','head','all']
SINK_PATTERNS = {
    'command_execution': [r'child_process\.(exec|execFile|spawn)', r'\bexec\s*\(', r'\bsystem\s*\(', r'Runtime\.getRuntime\(\)\.exec', r'ProcessBuilder\s*\(', r'os\.system\s*\(', r'subprocess\.(Popen|run|call)', r'\bshell_exec\s*\('],
    'file_read': [r'fs\.readFile', r'readFileSync', r'open\s*\(', r'Files\.read', r'Storage::get', r'file_get_contents\s*\('],
    'file_write': [r'fs\.writeFile', r'writeFileSync', r'Files\.write', r'Storage::put', r'move_uploaded_file\s*\('],
    'sql_raw': [r'\braw\s*\(', r'\bquery\s*\(', r'createNativeQuery', r'DB::(select|statement|raw)', r'cursor\.execute\s*\('],
    'ssrf_fetch': [r'fetch\s*\(', r'axios\.', r'requests\.(get|post|put)', r'RestTemplate', r'HttpClient', r'GuzzleHttp'],
    'template_render': [r'render_template\s*\(', r'res\.render\s*\(', r'TemplateEngine', r'view\s*\('],
    'deserialization': [r'pickle\.loads?', r'yaml\.load\s*\(', r'ObjectInputStream', r'unserialize\s*\(', r'JSON\.parse\s*\('],
    'jwt_session': [r'jwt\.', r'jsonwebtoken', r'createToken', r'parseClaims', r'Session', r'cookie'],
    'graphql_ws': [r'GraphQL', r'graphql', r'WebSocket', r'EventSource', r'SseEmitter'],
}
SOURCE_PATTERNS = [r'req\.(body|query|params|headers|cookies)', r'request\.(GET|POST|args|form|json|headers|cookies)', r'@RequestParam', r'@PathVariable', r'@RequestBody', r'\$_(GET|POST|REQUEST|COOKIE|FILES)', r'Input::', r'Request\$request']
GUARD_PATTERNS = [r'auth', r'authorize', r'permission', r'policy', r'guard', r'tenant', r'role', r'admin', r'@PreAuthorize', r'@RolesAllowed', r'Depends\(', r'middleware\(']

SKIP_DIRS = {'.git','node_modules','vendor','dist','build','.next','target','.venv','venv','__pycache__','.idea','.vscode'}
TEXT_EXT = set(LANG_EXT) | {'.env','.example','.conf','.ini','.properties','.dockerfile'}


def sha1(s: str) -> str:
    return hashlib.sha1(s.encode('utf-8', errors='ignore')).hexdigest()[:12]

def iter_files(base: Path, max_bytes: int=1_500_000) -> Iterable[Path]:
    for p in base.rglob('*'):
        if not p.is_file():
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        if p.stat().st_size > max_bytes:
            continue
        if p.suffix.lower() in TEXT_EXT or p.name in {'Dockerfile','Makefile','Procfile','package.json','composer.json','pom.xml','build.gradle','settings.gradle'}:
            yield p

def rel(base: Path, p: Path) -> str:
    try: return str(p.relative_to(base)).replace('\\','/')
    except Exception: return str(p)

def line_no(text: str, idx: int) -> int:
    return text.count('\n', 0, idx) + 1

def context_lines(text: str, idx: int, span: int=180) -> str:
    return text[max(0, idx-span): idx+span].replace('\n',' ')[:360]


def add_route(routes: list[dict[str, Any]], base: Path, p: Path, framework: str, method: str, path: str, idx: int, snippet: str, handler: str|None=None):
    routes.append({
        'id': f"route:{framework}:{method.upper()}:{path}:{rel(base,p)}:{line_no(snippet if False else '',0)}:{len(routes)}",
        'framework': framework,
        'method': method.upper(),
        'path': path,
        'handler': handler or 'unknown',
        'file': rel(base,p),
        'line': line_no(p.read_text(encoding='utf-8', errors='ignore'), idx),
        'evidence': context_lines(p.read_text(encoding='utf-8', errors='ignore'), idx),
        'status': 'static_extracted_needs_dynamic_replay'
    })

def extract_express(base: Path, p: Path, text: str, routes: list[dict[str,Any]]):
    pat = re.compile(r'\b(?:app|router|server)\.(get|post|put|patch|delete|options|head|all|use)\s*\(\s*[`\'\"]([^`\'\"]+)[`\'\"](?P<rest>[^\n;]*)', re.I)
    for m in pat.finditer(text):
        method=m.group(1); path=m.group(2); rest=m.group('rest')[:160]
        add_route(routes,base,p,'express',method,path,m.start(),text,rest.strip())

def next_route_from_file(base: Path, p: Path, text: str, routes: list[dict[str,Any]]):
    r=rel(base,p)
    path=None
    if '/pages/api/' in '/' + r:
        path='/' + r.split('pages/api/',1)[1]
        path=re.sub(r'\.(js|jsx|ts|tsx)$','',path)
        path=path.replace('/index','').replace('[',':').replace(']','')
        methods=['ANY']
    elif '/app/' in '/' + r and p.name.lower() in {'route.js','route.ts'}:
        path='/' + r.split('/app/',1)[1].rsplit('/route.',1)[0]
        path=path.replace('/page','').replace('[',':').replace(']','')
        methods=[m.group(1) for m in re.finditer(r'export\s+(?:async\s+)?function\s+(GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD)\b', text)] or ['ANY']
    else:
        return
    for method in methods:
        add_route(routes,base,p,'nextjs',method,path,0,text,'file-system-route')

def extract_django(base: Path, p: Path, text: str, routes: list[dict[str,Any]]):
    pat=re.compile(r'\b(?:path|re_path)\s*\(\s*[rRuUbBfF]*[\'\"]([^\'\"]+)[\'\"]\s*,\s*([^,\)]+)', re.S)
    for m in pat.finditer(text):
        add_route(routes,base,p,'django','ANY','/'+m.group(1).lstrip('/'),m.start(),text,m.group(2).strip()[:120])

def extract_fastapi(base: Path, p: Path, text: str, routes: list[dict[str,Any]]):
    pat=re.compile(r'@(?:app|router)\.(get|post|put|patch|delete|options|head|api_route)\s*\(\s*[rRuUbBfF]*[\'\"]([^\'\"]+)[\'\"](?P<rest>[^\n]*)', re.I)
    for m in pat.finditer(text):
        add_route(routes,base,p,'fastapi',m.group(1),m.group(2),m.start(),text,m.group('rest')[:160])

def extract_spring(base: Path, p: Path, text: str, routes: list[dict[str,Any]]):
    class_base=''
    cm=re.search(r'@RequestMapping\s*\(\s*(?:value\s*=\s*)?[\'\"]([^\'\"]+)[\'\"]', text)
    if cm and text.find('class', cm.end(), cm.end()+500) != -1:
        class_base=cm.group(1).rstrip('/')
    pat=re.compile(r'@(GetMapping|PostMapping|PutMapping|PatchMapping|DeleteMapping|RequestMapping)\s*(?:\(\s*(?:value\s*=\s*)?[\'\"]([^\'\"]*)[\'\"]|\()', re.I)
    map_method={'GetMapping':'GET','PostMapping':'POST','PutMapping':'PUT','PatchMapping':'PATCH','DeleteMapping':'DELETE','RequestMapping':'ANY'}
    for m in pat.finditer(text):
        method=map_method.get(m.group(1), 'ANY')
        path=(class_base + '/' + (m.group(2) or '').lstrip('/')).replace('//','/') or '/'
        add_route(routes,base,p,'spring',method,path,m.start(),text,'annotation-mapping')

def extract_laravel(base: Path, p: Path, text: str, routes: list[dict[str,Any]]):
    pat=re.compile(r'Route::(get|post|put|patch|delete|options|any|match|resource)\s*\(\s*(?:\[[^\]]+\]\s*,\s*)?[\'\"]([^\'\"]+)[\'\"](?P<rest>[^;]*)', re.S|re.I)
    for m in pat.finditer(text):
        add_route(routes,base,p,'laravel',m.group(1),'/'+m.group(2).lstrip('/'),m.start(),text,m.group('rest')[:160].replace('\n',' '))

def extract_sources_sinks_guards(base: Path, p: Path, text: str):
    sources=[]; sinks=[]; guards=[]
    for pat in SOURCE_PATTERNS:
        for m in re.finditer(pat, text, re.I):
            sources.append({'file':rel(base,p),'line':line_no(text,m.start()),'pattern':pat,'evidence':context_lines(text,m.start())})
    for kind, pats in SINK_PATTERNS.items():
        for pat in pats:
            for m in re.finditer(pat, text, re.I):
                sinks.append({'kind':kind,'file':rel(base,p),'line':line_no(text,m.start()),'pattern':pat,'evidence':context_lines(text,m.start()),'status':'sink_needs_trace_to_source_and_guard'})
    for pat in GUARD_PATTERNS:
        for m in re.finditer(pat, text, re.I):
            guards.append({'file':rel(base,p),'line':line_no(text,m.start()),'pattern':pat,'evidence':context_lines(text,m.start())})
    return sources,sinks,guards

def detect_frameworks(files: list[Path], base: Path) -> dict[str,Any]:
    hints={}
    names={rel(base,p):p.name for p in files}
    for p in files:
        r=rel(base,p); name=p.name.lower()
        try: text=p.read_text(encoding='utf-8', errors='ignore')[:200000]
        except Exception: text=''
        def hit(k, evidence): hints.setdefault(k,[]).append({'file':r,'evidence':evidence})
        if name=='package.json':
            if 'express' in text: hit('express','package.json dependency express')
            if 'next' in text: hit('nextjs','package.json dependency next')
            if '@nestjs/' in text: hit('nestjs','package.json dependency @nestjs')
            if 'fastify' in text: hit('fastify','package.json dependency fastify')
        if name in {'urls.py','settings.py'} or 'django.urls' in text: hit('django','django urls/settings/import')
        if 'FastAPI(' in text or 'APIRouter(' in text: hit('fastapi','FastAPI/APIRouter construction')
        if '@SpringBootApplication' in text or '@RestController' in text: hit('spring','Spring annotation')
        if name=='composer.json' and 'laravel/framework' in text: hit('laravel','composer laravel/framework')
        if '/routes/' in '/' + r and p.suffix=='.php' and 'Route::' in text: hit('laravel','Laravel routes file')
    return hints

def build(project: str, framework_filter: str|None=None) -> dict[str,Any]:
    base=Path(project).resolve()
    files=list(iter_files(base))
    routes=[]; sources=[]; sinks=[]; guards=[]; languages={}; errors=[]
    for p in files:
        languages[LANG_EXT.get(p.suffix.lower(), p.name)] = languages.get(LANG_EXT.get(p.suffix.lower(), p.name),0)+1
        try: text=p.read_text(encoding='utf-8', errors='ignore')
        except Exception as exc:
            errors.append({'file':rel(base,p),'error':str(exc)}); continue
        fw = framework_filter
        if fw in {None,'express'} and p.suffix.lower() in {'.js','.ts','.jsx','.tsx'}: extract_express(base,p,text,routes)
        if fw in {None,'nextjs'} and p.suffix.lower() in {'.js','.ts','.jsx','.tsx'}: next_route_from_file(base,p,text,routes)
        if fw in {None,'django'} and p.suffix.lower()=='.py': extract_django(base,p,text,routes)
        if fw in {None,'fastapi'} and p.suffix.lower()=='.py': extract_fastapi(base,p,text,routes)
        if fw in {None,'spring'} and p.suffix.lower()=='.java': extract_spring(base,p,text,routes)
        if fw in {None,'laravel'} and p.suffix.lower()=='.php': extract_laravel(base,p,text,routes)
        so,si,gu=extract_sources_sinks_guards(base,p,text)
        sources.extend(so); sinks.extend(si); guards.extend(gu)
    route_edges=[]
    for r in routes:
        same_file_guards=[g for g in guards if g['file']==r['file'] and abs(g['line']-r['line']) < 80]
        same_file_sinks=[s for s in sinks if s['file']==r['file']]
        same_file_sources=[s for s in sources if s['file']==r['file']]
        r['guard_hints']=same_file_guards[:12]
        r['sink_hints']=same_file_sinks[:12]
        r['source_hints']=same_file_sources[:12]
        r['risk_needles']=sorted({s['kind'] for s in same_file_sinks})
        if not same_file_guards:
            r['review_flags']=['guard_not_found_near_route']
        else:
            r['review_flags']=[]
    return {
        'schema_version':'semantic_graph_v1',
        'project_root':str(base),
        'framework_filter':framework_filter or 'auto_all',
        'files_scanned':len(files),
        'languages':languages,
        'framework_hints':detect_frameworks(files,base),
        'routes':routes,
        'sources':sources,
        'sinks':sinks,
        'guards':guards,
        'edges':route_edges,
        'coverage':{
            'route_count':len(routes),'source_count':len(sources),'sink_count':len(sinks),'guard_hint_count':len(guards),
            'status':'static_semantic_extraction_only_dynamic_replay_required_for_confirmed'
        },
        'errors':errors[:200],
        'claim_policy':'This graph is evidence for candidate discovery only; it cannot confirm vulnerabilities without browser/API replay, positive/negative tests and quality gate.'
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('project', help='authorized local project directory')
    ap.add_argument('--framework', choices=['express','nextjs','django','fastapi','spring','laravel'])
    ap.add_argument('--out', required=True)
    args=ap.parse_args()
    result=build(args.project,args.framework)
    out=Path(args.out); out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'ok':True,'out':str(out),'routes':len(result['routes']),'sinks':len(result['sinks']),'sources':len(result['sources'])},ensure_ascii=False))
if __name__=='__main__': main()

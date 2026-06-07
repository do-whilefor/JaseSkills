#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import os
import sys
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'scripts'
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from _info_collect_lib import (  # type: ignore
    PATH_RE,
    ROUTE_RE,
    URL_RE,
    common_parser,
    dry_run_report,
    enforce_scope,
    evidence,
    iter_scoped_files,
    line_no,
    output_report,
    parse_scope,
    read_text,
    scan_inventory,
    stable_hash,
)

HTTP_METHODS = {'get','post','put','patch','delete','options','head'}
PARAM_NAME_RE = re.compile(r'(?i)\b(req\.(?:query|body|params|headers|cookies)\.([A-Za-z0-9_$-]+)|request\.(?:GET|POST|data|args|headers|cookies)\.get\(["\']([^"\']+)|["\']([A-Za-z0-9_$-]+)["\']\s*:\s*(?:Joi\.|z\.|body\(|query\(|param\(|header\(|cookie\())')
HIDDEN_PARAM_RE = re.compile(r'(?i)\b(debug|preview|draft|include|expand|fields|filter|sort|page|limit|offset|tenantId|orgId|organizationId|workspaceId|accountId|projectId|userId|role|admin|impersonate|bypass|internal|feature[_-]?flag)\b')
WS_EVENT_RE = re.compile(r"(?i)(?:\.on|\.emit|send|subscribe|publish|channel)\s*\(\s*[`\"']([A-Za-z0-9_.:\-/]+)[`\"']")
GQL_OP_RE = re.compile(r'\b(query|mutation|subscription)\s+([A-Za-z_][A-Za-z0-9_]*)')
GQL_SCHEMA_RE = re.compile(r'\b(type|interface|input|enum|scalar|union)\s+([A-Za-z_][A-Za-z0-9_]*)')
SECRET_NAME_RE = re.compile(r'(?i)(password|passwd|secret|token|api[_-]?key|client[_-]?secret|private[_-]?key|webhook[_-]?secret|jwt|cookie|session)')
CI_NAMES = {'.github', '.gitlab-ci.yml', 'Jenkinsfile', 'azure-pipelines.yml', 'circle.yml', '.circleci', 'bitbucket-pipelines.yml'}
IAC_SUFFIXES = {'.tf', '.tfvars'}
IAC_NAMES = {'Dockerfile', 'docker-compose.yml', 'docker-compose.yaml', 'compose.yml', 'compose.yaml', 'Chart.yaml', 'values.yaml', 'kustomization.yaml'}
DOC_SUFFIXES = {'.md', '.rst', '.txt', '.adoc'}
CONFIG_SUFFIXES = {'.env', '.ini', '.conf', '.config', '.properties', '.yaml', '.yml', '.toml', '.json', '.xml'}
DEPENDENCY_FILES = {'package.json','package-lock.json','pnpm-lock.yaml','yarn.lock','requirements.txt','pyproject.toml','poetry.lock','Pipfile','Pipfile.lock','pom.xml','build.gradle','gradle.lockfile','composer.json','composer.lock','Gemfile','Gemfile.lock','go.mod','go.sum','Cargo.toml','Cargo.lock','packages.lock.json'}
DOC_ROUTE_HINT_RE = re.compile(r'(?i)\b(?:GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD)\s+(/(?:api|admin|internal|graphql|v[0-9]|auth|oauth|callback|webhook|debug|health|metrics|socket|ws|rpc|files|upload|download)[A-Za-z0-9_./{}:\-?=&%]*)')


def _source_type(path: Path) -> str:
    name = path.name.lower()
    if path.suffix.lower() in {'.js','.jsx','.ts','.tsx','.mjs','.cjs','.map'}:
        return 'frontend_or_js_artifact'
    if path.suffix.lower() in {'.graphql','.gql','.proto'}:
        return 'api_schema'
    if path.suffix.lower() in DOC_SUFFIXES:
        return 'documentation'
    if name in DEPENDENCY_FILES:
        return 'dependency_manifest'
    if path.suffix.lower() in IAC_SUFFIXES or path.name in IAC_NAMES:
        return 'iac_or_deployment'
    return 'source'


def iter_authorized(args):
    root = Path(args.input).resolve()
    scope = parse_scope(args.scope, root)
    ok, reason = enforce_scope(root, scope)
    if args.dry_run:
        return root, scope, ok, reason, []
    if not ok:
        return root, scope, ok, reason, []
    files = list(iter_scoped_files(root, scope, args.max_files, args.timeout, args.scan_profile, args.follow_symlinks)) if root.is_dir() else [root]
    return root, scope, ok, reason, files


def out_of_scope_item(name: str, root: Path, reason: str):
    base = root.parent if root.parent.exists() else Path('/')
    return evidence(name, root, base, 'out_of_scope_blocked', {'path': str(root), 'reason': reason}, 1, confidence=1.0, severity_hint='blocker', needs_review=True, linked_report_section='authorization-scope', reason='scope gate blocked input path', limitation='collector did not scan because input is outside allowed scope')


def add_item(items: list[dict], name: str, path: Path, root: Path, typ: str, value: Any, line: int = 1, confidence: float = 0.6, section: str = 'evidence-index', needs_review: bool = False, source_type: str | None = None, **kw: Any) -> None:
    items.append(evidence(
        name,
        path,
        root,
        typ,
        value,
        line,
        confidence=confidence,
        needs_review=needs_review,
        linked_report_section=section,
        source_type=source_type or _source_type(path),
        reason=kw.pop('reason', f'{typ} collected from authorized local file'),
        reproduction_command=kw.pop('reproduction_command', f"python collectors/{name}.py --input {root} --scope {root} --output out/{name}.json"),
        limitation=kw.pop('limitation', 'static local analysis; dynamic exposure, reachability, role and tenant behavior remain candidate-only unless separately validated'),
        **kw,
    ))




def _route_auth_from_text(txt: str) -> tuple[str, str, list[str]]:
    mids=re.findall(r'\b([A-Za-z_][A-Za-z0-9_]*(?:Auth|Guard|Policy|Middleware|Permission|Role|Tenant|Jwt|Session)[A-Za-z0-9_]*)\b', txt)
    low=txt.lower()
    authn='present' if any(x in low for x in ['auth','jwt','session','passport','guard','login_required','before_action']) else 'not_identified'
    authz='present' if any(x in low for x in ['role','permission','policy','can?','authorize','tenant','workspace','org']) else 'not_identified'
    return authn, authz, sorted(set(mids))[:12]

def _normalize_framework_route(route: str) -> str:
    route=(route or '').strip().strip('`"\'')
    if not route.startswith('/') and not route.startswith('http'):
        route='/' + route
    route=re.sub(r'//+', '/', route)
    return route

def _join_routes(base: str, sub: str) -> str:
    base=_normalize_framework_route(base) if base else ''
    sub=_normalize_framework_route(sub) if sub else ''
    if base in {'','/'}: return sub or '/'
    if sub in {'','/'}: return base
    return re.sub(r'//+', '/', base.rstrip('/') + '/' + sub.lstrip('/'))

def _add_framework_endpoint(items, name, p, root, method, route, framework, handler, line, snippet='', confidence=.86, scope_id=''):
    authn, authz, middleware=_route_auth_from_text(snippet + ' ' + (handler or ''))
    add_item(items, name, p, root, 'endpoint', {
        'method': method.upper(), 'route': _normalize_framework_route(route), 'framework': framework,
        'handler': handler or 'inline_or_unresolved', 'middleware': middleware or ['not_identified'],
        'authn': authn, 'authz': authz,
        'extraction': 'framework_specific_static_extractor'
    }, line, confidence, 'route-api-inventory', endpoint_relevance='high', auth_relevance='medium' if authn=='present' else 'low', role_relevance='medium' if authz=='present' else 'low', tenant_relevance='medium' if 'tenant' in snippet.lower() else 'low', scope_id=scope_id, reason=f'{framework} route pattern gives structured method/route/handler evidence', limitation='framework-specific static extractor; runtime reachability and effective middleware execution still require authorized validation')

def _collect_framework_routes(items, name: str, p: Path, root: Path, text: str, scope_id: str) -> None:
    for m in re.finditer(r'''(?sx)\b(?:app|router|server|fastify|blueprint)\s*\.\s*(get|post|put|patch|delete|options|head|use)\s*\(\s*([`"'])([^`"']+)\2\s*(?:,\s*([^\n;]{0,500}))?''', text):
        args=m.group(4) or ''
        ids=re.findall(r'\b([A-Za-z_$][A-Za-z0-9_$]*)\b', args)
        handler=ids[-1] if ids else 'inline_handler'
        _add_framework_endpoint(items,name,p,root,m.group(1),m.group(3),'express_or_fastify',handler,line_no(text,m.group(0)),m.group(0)+args,.87,scope_id)
    for m in re.finditer(r'''(?sx)@(?:app|router|blueprint)\.(get|post|put|patch|delete|options|head|route)\s*\(\s*([`"'])([^`"']+)\2([^\n]*)\)\s*(?:\n\s*@[\w.()'",\s]+)*\n\s*(?:async\s+)?def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(([^)]*)\)''', text):
        method='GET' if m.group(1).lower()=='route' else m.group(1).upper()
        _add_framework_endpoint(items,name,p,root,method,m.group(3),'fastapi_or_flask',m.group(5),line_no(text,m.group(0)),m.group(0)+' '+m.group(6),.9,scope_id)
    controller_base=''
    cm=re.search(r'''@Controller\s*\(\s*([`"'])([^`"']*)\1\s*\)''', text)
    if cm: controller_base=cm.group(2)
    nest_map={'Get':'GET','Post':'POST','Put':'PUT','Patch':'PATCH','Delete':'DELETE','Options':'OPTIONS','Head':'HEAD','All':'ALL'}
    for m in re.finditer(r'''(?sx)@(Get|Post|Put|Patch|Delete|Options|Head|All)\s*\(\s*(?:(['"`])([^'"`]*)\2)?\s*\)\s*(?:\n\s*@(UseGuards|Roles|Permissions|SetMetadata)[^\n]*){0,8}\s*\n\s*(?:public|private|protected|async\s+|\s)*([A-Za-z_][A-Za-z0-9_]*)\s*\(''', text):
        _add_framework_endpoint(items,name,p,root,nest_map[m.group(1)],_join_routes(controller_base,m.group(3) or ''),'nestjs',m.group(5),line_no(text,m.group(0)),m.group(0),.9,scope_id)
    base=''
    bm=re.search(r'''@(RequestMapping)\s*\(\s*(?:value\s*=\s*)?([`"'])([^`"']+)\2''', text)
    if bm and re.search(r'\bclass\s+[A-Za-z_]', text[bm.end():bm.end()+500]): base=bm.group(3)
    spring_map={'GetMapping':'GET','PostMapping':'POST','PutMapping':'PUT','PatchMapping':'PATCH','DeleteMapping':'DELETE','RequestMapping':'REQUEST'}
    for m in re.finditer(r'''(?sx)@(GetMapping|PostMapping|PutMapping|PatchMapping|DeleteMapping|RequestMapping)\s*\(\s*(?:(?:value|path)\s*=\s*)?([`"'])([^`"']+)\2[^)]*\)\s*(?:\n\s*@[A-Za-z0-9_().,'"\s]+)*\n\s*(?:public|private|protected)?\s*[A-Za-z0-9_<>, ?]+\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(''', text):
        snippet=m.group(0)
        method=spring_map[m.group(1)]
        if method=='REQUEST':
            mm=re.search(r'method\s*=\s*RequestMethod\.([A-Z]+)', snippet); method=mm.group(1) if mm else 'REQUEST'
        _add_framework_endpoint(items,name,p,root,method,_join_routes(base,m.group(3)),'spring_boot',m.group(4),line_no(text,m.group(0)),snippet,.9,scope_id)
    for m in re.finditer(r'''(?sx)Route::(get|post|put|patch|delete|options|any|match)\s*\(\s*([`"'])([^`"']+)\2\s*,\s*([^;\n]+)(?:\n|;)''', text):
        h=m.group(4).strip()[:160]
        mw=' '.join(re.findall(r'->middleware\s*\(([^)]*)\)', text[m.start():m.start()+400]))
        _add_framework_endpoint(items,name,p,root,m.group(1),m.group(3),'laravel',h,line_no(text,m.group(0)),m.group(0)+' '+mw,.88,scope_id)
    for m in re.finditer(r'''(?m)^\s*(get|post|put|patch|delete|match)\s+['"]([^'"]+)['"]\s*(?:,\s*to:\s*['"]([^'"]+)['"])?''', text):
        _add_framework_endpoint(items,name,p,root,m.group(1),m.group(2),'rails',m.group(3) or 'rails_route_handler',line_no(text,m.group(0)),m.group(0),.86,scope_id)
    for m in re.finditer(r'''(?sx)\b([A-Za-z_][A-Za-z0-9_]*)\.(GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD|Any|Handle)\s*\(\s*([`"'])([^`"']+)\3\s*,\s*([^\n;)]+)''', text):
        _add_framework_endpoint(items,name,p,root,m.group(2),m.group(4),'gin_echo_fiber',m.group(5).strip()[:120],line_no(text,m.group(0)),m.group(0),.86,scope_id)

def collect_routes(name: str, root: Path, scope: dict, files: list[Path]) -> list[dict]:
    items: list[dict] = []
    for p in files:
        text = read_text(p)
        low = p.name.lower()
        if low.endswith('.json'):
            try:
                data = json.loads(text)
                if isinstance(data, dict) and ('openapi' in data or 'swagger' in data):
                    for route, methods in (data.get('paths') or {}).items():
                        if isinstance(methods, dict):
                            for method, spec in methods.items():
                                if method.lower() in HTTP_METHODS:
                                    add_item(items, name, p, root, 'endpoint', {'method': method.upper(), 'route': route, 'source': 'openapi', 'parameters': sorted((spec or {}).get('parameters', []), key=lambda x: json.dumps(x, sort_keys=True)) if isinstance(spec, dict) else []}, 1, .92, 'route-api-inventory', endpoint_relevance='high', scope_id=scope['scope_id'], reason='OpenAPI path operation provides structured method and route evidence', limitation='OpenAPI may be stale; correlate with code and runtime before confirmed status')
                if isinstance(data, dict) and ('item' in data and 'info' in data):
                    def rec(arr):
                        for it in arr or []:
                            if isinstance(it, dict) and 'item' in it:
                                rec(it.get('item'))
                            elif isinstance(it, dict):
                                req = it.get('request') or {}; url=req.get('url')
                                raw=url.get('raw') if isinstance(url, dict) else url
                                if raw:
                                    add_item(items, name, p, root, 'endpoint', {'method': req.get('method','GET'), 'route': raw, 'source': 'postman'}, 1, .84, 'route-api-inventory', True, endpoint_relevance='high', scope_id=scope['scope_id'], reason='Postman collection contains request definition', limitation='Collection request requires code/runtime correlation before confirmed status')
                    rec(data.get('item'))
            except Exception:
                pass
        if low.endswith(('.graphql','.gql')):
            for m in GQL_SCHEMA_RE.finditer(text):
                add_item(items, name, p, root, 'graphql_schema_symbol', {'kind': m.group(1), 'name': m.group(2)}, line_no(text, m.group(0)), .86, 'route-api-inventory', endpoint_relevance='medium', scope_id=scope['scope_id'])
        if low.endswith('.proto'):
            for m in re.finditer(r'\bservice\s+([A-Za-z_][A-Za-z0-9_]*)|\brpc\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(', text):
                add_item(items, name, p, root, 'grpc_service_or_rpc', {'service_or_rpc': m.group(1) or m.group(2)}, line_no(text, m.group(0)), .86, 'route-api-inventory', endpoint_relevance='high', scope_id=scope['scope_id'])
        _collect_framework_routes(items, name, p, root, text, scope['scope_id'])
        for m in ROUTE_RE.finditer(text):
            method = (m.group(1) or m.group(3) or 'ROUTE').upper(); route = m.group(2) or m.group(4) or m.group(5)
            add_item(items, name, p, root, 'endpoint', {'method': method, 'route': route, 'handler_evidence': 'inline route declaration', 'authn': 'unknown', 'authz': 'unknown', 'middleware': 'unknown'}, line_no(text, m.group(0)), .72, 'route-api-inventory', endpoint_relevance='high', scope_id=scope['scope_id'], limitation='route declaration extracted statically; handler/middleware/auth fields need framework-specific correlation')
        for m in PATH_RE.finditer(text):
            add_item(items, name, p, root, 'endpoint_candidate_literal', {'route': m.group(0), 'method': 'UNKNOWN'}, line_no(text, m.group(0)), .55, 'route-api-inventory', True, endpoint_relevance='medium', scope_id=scope['scope_id'], limitation='literal path candidate; may be documentation, test data, dead code or generated code')
    return items




def _rel(root: Path, p: Path) -> str:
    try: return str(p.resolve().relative_to(root.resolve())).replace('\\','/')
    except Exception: return str(p)

def _load_sourcemap_index(root: Path, files: list[Path]) -> dict[str, dict]:
    out={}
    for p in files:
        if not p.name.lower().endswith('.map'): continue
        try:
            data=json.loads(read_text(p)); sources=data.get('sources') or []
            out[p.name[:-4]]={'map_file':_rel(root,p),'sources':sources[:200], 'sources_count':len(sources)}
        except Exception:
            continue
    return out

def _extract_js_callgraph_items(items, name: str, root: Path, p: Path, text: str, scope_id: str, sourcemaps: dict[str,dict]) -> None:
    constants={}
    for m in re.finditer(r'''(?m)\b(?:const|let|var)\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*=\s*([`"'])([^`"']*)\2''', text):
        constants[m.group(1)]=m.group(3)
    imports=[]
    for m in re.finditer(r'''(?m)^\s*import\s+(?:\{([^}]+)\}|([A-Za-z_$][A-Za-z0-9_$]*)|\*\s+as\s+([A-Za-z_$][A-Za-z0-9_$]*))?\s*(?:from\s*)?([`"'])([^`"']+)\4''', text):
        names=[]
        if m.group(1): names=[x.strip().split(' as ')[-1] for x in m.group(1).split(',')]
        elif m.group(2) or m.group(3): names=[m.group(2) or m.group(3)]
        imports.append({'names':names,'from':m.group(5)})
        add_item(items,name,p,root,'js_import_edge',{'imported':names,'from':m.group(5)},line_no(text,m.group(0)),.72,'frontend-js',False,scope_id=scope_id,reason='ES module import edge collected for frontend callgraph',limitation='Static import edge only; bundler alias resolution may be incomplete')
    clients={}
    for m in re.finditer(r'''(?s)\b(?:const|let|var)\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*=\s*axios\.create\s*\(\s*\{(.{0,800}?)\}\s*\)''', text):
        body=m.group(2); bm=re.search(r'''baseURL\s*:\s*([`"'])([^`"']+)\1|baseURL\s*:\s*([A-Za-z_$][A-Za-z0-9_$]*)''', body)
        base=(bm.group(2) if bm and bm.group(2) else constants.get(bm.group(3), '') if bm else '')
        clients[m.group(1)]=base
        add_item(items,name,p,root,'js_http_client_wrapper',{'client':m.group(1),'baseURL':base,'wrapper':'axios.create'},line_no(text,m.group(0)),.86,'frontend-js',False,endpoint_relevance='medium',scope_id=scope_id,reason='axios.create wrapper and baseURL resolved from local JS',limitation='Environment variables and runtime interceptors may alter final URL')
    wrappers={}
    for m in re.finditer(r'''(?s)\b(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*\(([^)]*)\)\s*\{(.{0,1200}?)\}''', text):
        fname=m.group(1); body=m.group(3)
        if any(x in body for x in ['fetch(', 'axios', '.get(', '.post(', '.request(']):
            wrappers[fname]=body
            add_item(items,name,p,root,'js_api_wrapper_function',{'function':fname,'imports':imports[:10],'body_hash':stable_hash(body)},line_no(text,m.group(0)),.76,'frontend-js',True,endpoint_relevance='medium',scope_id=scope_id,reason='Function body calls fetch/axios/client method and is treated as API wrapper candidate',limitation='Wrapper semantics are approximated; verify in AST/callgraph review')
    api_calls=[]
    call_patterns=[
        ('fetch', r'''\bfetch\s*\(\s*([`"'])([^`"']+)\1'''),
        ('axios_method', r'''\b([A-Za-z_$][A-Za-z0-9_$]*)\.(get|post|put|patch|delete|head|options)\s*\(\s*([`"'])([^`"']+)\3'''),
        ('wrapper_call', r'''\b([A-Za-z_$][A-Za-z0-9_$]*)\s*\(\s*([`"'])(/(?:api|admin|internal|graphql|auth|oauth|callback|webhook|v[0-9])[^`"']*)\2'''),
    ]
    for sink, pat in call_patterns:
        for m in re.finditer(pat, text):
            method='UNKNOWN'; endpoint=''; base=''; callee=sink
            if sink=='fetch': endpoint=m.group(2); method='REQUEST'
            elif sink=='axios_method':
                callee=m.group(1); method=m.group(2).upper(); endpoint=m.group(4); base=clients.get(callee,'')
            else:
                callee=m.group(1); endpoint=m.group(3); method='WRAPPER'; base=''
                if callee not in wrappers and not any(callee in im.get('names',[]) for im in imports):
                    continue
            if not base and callee.lower().startswith('api') and endpoint.startswith('/') and not endpoint.startswith('/api'):
                base='/api'
            resolved=(base.rstrip('/') + '/' + endpoint.lstrip('/')) if base else endpoint
            sm=sourcemaps.get(p.name) or sourcemaps.get(p.name + '.map') or {}
            val={'sink':sink,'callee':callee,'method':method,'endpoint':endpoint,'resolved_endpoint':resolved,'baseURL':base,'wrapper_known':callee in wrappers,'import_edges':imports[:10],'chunk_lineage':{'file':_rel(root,p),'sourcemap':sm}}
            add_item(items,name,p,root,'js_callgraph_api_call',val,line_no(text,m.group(0)),.84 if sink!='wrapper_call' or callee in wrappers else .7,'frontend-js',True,endpoint_relevance='high',scope_id=scope_id,reason='Frontend API call extracted with wrapper/baseURL/import/chunk lineage context',limitation='Static callgraph; dynamic string construction, runtime baseURL and interceptors may change final endpoint')
            api_calls.append(val)
    if api_calls:
        add_item(items,name,p,root,'js_callgraph_summary',{'api_call_count':len(api_calls),'wrappers':sorted(wrappers),'clients':clients,'imports':imports[:20]},1,.82,'frontend-js',True,endpoint_relevance='high',scope_id=scope_id,reason='Per-file frontend callgraph summary generated from local JS',limitation='Summary is static and must be correlated with backend endpoints')

def _run_node_js_ast(root: Path) -> list[dict]:
    """Run the optional Node AST extractor without inheriting pipes.

    Some Windows and constrained pytest runners can stall when a nested Node
    process inherits stdout/stderr pipes from a parent Python subprocess. Writing
    JSONL to a temporary file and waiting on the process handle avoids pipe EOF
    deadlocks while preserving AST extraction when Node and parser deps exist.
    """
    script = ROOT / 'scripts' / 'js-ast-endpoint-extractor.mjs'
    if os.environ.get('INFO_END_PIPELINE_NO_NODE_AST') == '1':
        return []
    if not script.exists():
        return []
    import tempfile
    tmp_name = ''
    try:
        with tempfile.NamedTemporaryFile(prefix='info_end_js_ast_', suffix='.jsonl', delete=False) as tmp:
            tmp_name = tmp.name
        cmd = ['node', str(script), str(root), '-o', tmp_name]
        kwargs = {'stdin': subprocess.DEVNULL, 'stdout': subprocess.DEVNULL, 'stderr': subprocess.DEVNULL, 'close_fds': True}
        if os.name == 'nt':
            kwargs['creationflags'] = getattr(subprocess, 'CREATE_NEW_PROCESS_GROUP', 0)
        else:
            kwargs['start_new_session'] = True
        proc = subprocess.Popen(cmd, **kwargs)
        try:
            rc = proc.wait(timeout=30)
        except subprocess.TimeoutExpired:
            try:
                proc.kill()
            except Exception:
                pass
            try:
                proc.wait(timeout=3)
            except Exception:
                pass
            return []
        rows = []
        if rc == 0 and tmp_name:
            for line in Path(tmp_name).read_text(encoding='utf-8', errors='ignore').splitlines():
                try:
                    rows.append(json.loads(line))
                except Exception:
                    pass
        return rows
    except Exception:
        return []
    finally:
        if tmp_name:
            try:
                Path(tmp_name).unlink(missing_ok=True)
            except Exception:
                pass

def collect_js_assets(name: str, root: Path, scope: dict, files: list[Path]) -> list[dict]:
    items: list[dict] = []
    sourcemaps = _load_sourcemap_index(root, files)
    for row in _run_node_js_ast(root):
        sf = row.get('source_file') or 'unknown'
        p0 = root / sf if sf != 'unknown' else root
        add_item(items, name, p0, root, 'js_ast_endpoint_candidate', row, int(row.get('line') or 1), .84, 'frontend-js', True, endpoint_relevance='high', auth_relevance='medium' if row.get('auth_context') else 'low', tenant_relevance='medium' if row.get('tenant_context') else 'low', scope_id=scope['scope_id'], reason='Node JS AST extractor produced endpoint candidate with sink/function evidence', limitation=row.get('limitation') or 'AST/fallback candidate; requires backend/runtime correlation')
    js_files = [p for p in files if p.suffix.lower() in {'.js','.jsx','.ts','.tsx','.mjs','.cjs','.map','.json','.html'} or 'service-worker' in p.name.lower() or 'manifest' in p.name.lower()]
    for p in js_files:
        text = read_text(p)
        if p.suffix.lower() in {'.js','.jsx','.ts','.tsx','.mjs','.cjs'}:
            _extract_js_callgraph_items(items, name, root, p, text, scope['scope_id'], sourcemaps)
        low = p.name.lower()
        if low.endswith('.map'):
            add_item(items, name, p, root, 'source_map_artifact', {'file': p.name, 'hash': stable_hash(text)}, 1, .96, 'frontend-js', True, data_sensitivity='medium', scope_id=scope['scope_id'], reason='source map artifact exists inside authorized local project', limitation='source maps reveal original paths but do not prove endpoint reachability')
            try:
                data=json.loads(text)
                for src in (data.get('sources') or [])[:500]:
                    add_item(items, name, p, root, 'sourcemap_original_path', src, 1, .9, 'frontend-js', True, data_sensitivity='medium', scope_id=scope['scope_id'])
            except Exception:
                add_item(items, name, p, root, 'sourcemap_parse_limitation', {'file': p.name, 'reason': 'json parse failed'}, 1, .4, 'frontend-js', True, scope_id=scope['scope_id'], limitation='source map was detected but could not be parsed as JSON')
        if 'service-worker' in low or low in {'sw.js','workbox.js'}:
            for m in re.finditer(r'(?i)(precache|addAll|registerRoute|cacheName|url:)\s*[^\n]{0,180}', text):
                add_item(items, name, p, root, 'service_worker_cache_entry', m.group(0), line_no(text, m.group(0)), .74, 'frontend-js', True, endpoint_relevance='medium', scope_id=scope['scope_id'], limitation='service worker cache reference may be a cached asset rather than a callable API')
        if 'manifest' in low or low.endswith('.html'):
            for m in PATH_RE.finditer(text):
                add_item(items, name, p, root, 'manifest_or_html_hidden_path', m.group(0), line_no(text, m.group(0)), .64, 'frontend-js', True, endpoint_relevance='medium', scope_id=scope['scope_id'])
        for m in re.finditer(r'\bimport\s*\(\s*[`\"\']([^`\"\']+)[`\"\']\s*\)', text):
            add_item(items, name, p, root, 'dynamic_import_chunk', m.group(1), line_no(text, m.group(0)), .76, 'frontend-js', False, scope_id=scope['scope_id'])
        for m in PATH_RE.finditer(text):
            add_item(items, name, p, root, 'frontend_api_literal', m.group(0), line_no(text, m.group(0)), .58, 'frontend-js', True, endpoint_relevance='medium', scope_id=scope['scope_id'], limitation='regex literal extraction; run js-ast-endpoint-extractor for wrapper/baseURL correlation')
        for m in URL_RE.finditer(text):
            add_item(items, name, p, root, 'frontend_url_or_callback', m.group(0), line_no(text, m.group(0)), .58, 'frontend-js', True, endpoint_relevance='medium', scope_id=scope['scope_id'])
        for m in GQL_OP_RE.finditer(text):
            add_item(items, name, p, root, 'graphql_operation_in_frontend', {'type': m.group(1), 'name': m.group(2)}, line_no(text, m.group(0)), .74, 'frontend-js', False, endpoint_relevance='medium', scope_id=scope['scope_id'])
        for m in re.finditer(r'(?i)\b(feature[_-]?flag|experiment|ab[_-]?test|enable[A-Z][A-Za-z0-9_]*|is[A-Z][A-Za-z0-9_]*(?:Enabled|Active)|permission|role|tenant)\b', text):
            add_item(items, name, p, root, 'frontend_flag_or_permission_signal', m.group(0), line_no(text, m.group(0)), .56, 'frontend-js', True, auth_relevance='medium', role_relevance='medium', tenant_relevance='medium', scope_id=scope['scope_id'])
    return items


def collect_config(name: str, root: Path, scope: dict, files: list[Path]) -> list[dict]:
    items: list[dict] = []
    for p in files:
        text=read_text(p)
        low=p.name.lower()
        is_config = p.name.startswith('.env') or p.suffix.lower() in CONFIG_SUFFIXES or p.name in IAC_NAMES or 'nginx' in low or 'apache' in low or 'caddy' in low
        if not is_config: continue
        add_item(items, name, p, root, 'config_file', {'file': str(p.relative_to(root)) if p.is_relative_to(root) else p.name}, 1, .78, 'configuration-deployment', False, scope_id=scope['scope_id'])
        for key in re.finditer(r'(?im)^\s*([A-Z0-9_./-]{2,80}|[a-zA-Z0-9_.-]{2,80})\s*[:=]\s*([^#\n]{1,300})', text):
            k=key.group(1); v=key.group(2).strip()
            typ='secret_name_signal' if SECRET_NAME_RE.search(k) else 'config_key'
            add_item(items, name, p, root, typ, {'key': k, 'value': v if typ!='secret_name_signal' else '<redacted-by-evidence-helper>'}, line_no(text,key.group(0)), .72 if typ=='config_key' else .88, 'configuration-deployment', typ=='secret_name_signal', data_sensitivity='high' if typ=='secret_name_signal' else 'low', scope_id=scope['scope_id'], limitation='secret values are intentionally not printed; verify rotation and exposure manually if real secret existed')
        for m in re.finditer(r'(?i)\b(cors|csp|content-security-policy|rate[_-]?limit|cookie|session|oauth|saml|oidc|redirect_uri|callback|webhook|queue|redis|postgres|mysql|mongodb|s3|bucket|storage|debug|staging|local|test)\b', text):
            add_item(items, name, p, root, 'security_relevant_config_signal', m.group(0), line_no(text,m.group(0)), .58, 'configuration-deployment', True, scope_id=scope['scope_id'])
    return items




def _load_local_cve_db(cve_db: str | None) -> dict:
    if not cve_db:
        cve_db=os.environ.get('INFO_END_CVE_DB')
    if not cve_db: return {}
    try:
        data=json.loads(Path(cve_db).read_text(encoding='utf-8', errors='ignore'))
    except Exception:
        return {}
    out={}
    if isinstance(data, dict):
        for k,v in data.items(): out[str(k).lower()]=v
    elif isinstance(data, list):
        for row in data:
            if isinstance(row, dict):
                key=f"{row.get('manager','')}:{row.get('name','')}".lower(); out[key]=row
    return out

def _dep_key(manager: str, name_: str) -> str:
    return f'{manager}:{name_}'.lower()

def _maybe_add_verified_dep_advisory(items, name, p, root, dep_name, manager, version, section, scope_id, db):
    rec=db.get(_dep_key(manager, dep_name)) or db.get(dep_name.lower())
    if not rec: return
    cves=rec.get('cves') or ([rec.get('cve')] if rec.get('cve') else [])
    add_item(items,name,p,root,'verified_dependency_advisory',{'manager':manager,'section':section,'name':dep_name,'version':version,'advisory':rec,'verification_status':'verified','verification_source':'local_cve_db','needs_online_verification':False,'cves':cves},1,.9,'dependency-surface',True,scope_id=scope_id,verification_status='verified',verification_source='local_cve_db',needs_online_verification=False,reason='Dependency advisory matched explicitly supplied local verification database; no network lookup was performed',limitation='Local database may be stale or mock data; reproduce by passing --cve-db and reviewing the database entry')

def collect_dependencies(name: str, root: Path, scope: dict, files: list[Path], cve_db: str | None = None, allow_online_verification: bool = False) -> list[dict]:
    items: list[dict]=[]
    local_db=_load_local_cve_db(cve_db)
    for p in files:
        if p.name not in DEPENDENCY_FILES: continue
        text=read_text(p)
        add_item(items, name, p, root, 'package_manager_file', p.name, 1, .86, 'dependency-surface', False, scope_id=scope['scope_id'])
        if p.name == 'package.json':
            try:
                data=json.loads(text)
                regs=[]
                if isinstance(data.get('publishConfig'), dict) and data['publishConfig'].get('registry'): regs.append(data['publishConfig'].get('registry'))
                if regs:
                    add_item(items,name,p,root,'private_registry_config',{'registries':regs},1,.78,'dependency-surface',True,scope_id=scope['scope_id'],reason='package.json registry configuration collected',limitation='Registry reachability and ownership are not checked offline')
                for sec in ['dependencies','devDependencies','peerDependencies','optionalDependencies']:
                    for dep, ver in (data.get(sec) or {}).items():
                        risk='needs_online_verification'
                        if isinstance(ver,str) and (ver.startswith('git+') or ver.startswith('http') or 'github:' in ver): risk='git_or_url_dependency_needs_review'
                        if isinstance(ver,str) and re.match(r'^[*xX]|latest$', ver): risk='unpinned_dependency_needs_review'
                        add_item(items, name, p, root, 'dependency', {'manager':'npm','section':sec,'name':dep,'version':ver,'risk_status':risk,'needs_online_verification':True}, 1, .72, 'dependency-surface', True, scope_id=scope['scope_id'], needs_online_verification=True, limitation='Offline dependency inventory; CVE/deprecation/typosquat checks require explicit local DB or authorized online verification')
                        _maybe_add_verified_dep_advisory(items,name,p,root,dep,'npm',ver,sec,scope['scope_id'],local_db)
                for script, cmd in (data.get('scripts') or {}).items():
                    typ='package_script' if script not in {'preinstall','install','postinstall','prepare'} else 'dangerous_package_script'
                    add_item(items, name, p, root, typ, {'script':script,'command':cmd}, 1, .76 if typ=='package_script' else .88, 'dependency-surface', typ=='dangerous_package_script', scope_id=scope['scope_id'])
            except Exception:
                pass
        elif p.name in {'requirements.txt','pyproject.toml','pom.xml','build.gradle','composer.json','Gemfile','go.mod','Cargo.toml'}:
            manager={'requirements.txt':'pypi','pyproject.toml':'pypi','pom.xml':'maven','build.gradle':'maven','composer.json':'composer','Gemfile':'rubygems','go.mod':'go','Cargo.toml':'cargo'}.get(p.name,'unknown')
            for line_idx, line in enumerate(text.splitlines(), 1):
                stripped=line.strip()
                if re.search(r'(?i)(github\.com|git\+|http://|https://|version|require|package|module|^\s*[A-Za-z0-9_.-]+[=<>~])', line):
                    dep_name=(re.split(r'[=<>~\s"\']+', stripped.strip('"\'')) or [''])[0]
                    add_item(items, name, p, root, 'dependency_or_registry_signal', {'manager':manager,'raw':stripped[:300],'risk_status':'needs_online_verification'}, line_idx, .56, 'dependency-surface', True, scope_id=scope['scope_id'], needs_online_verification=True, limitation='Generic dependency signal; exact package semantics depend on package manager')
                    if dep_name: _maybe_add_verified_dep_advisory(items,name,p,root,dep_name,manager,'unknown','unknown',scope['scope_id'],local_db)
        else:
            add_item(items, name, p, root, 'lock_file_present', {'file': p.name, 'risk_status':'needs_online_verification','needs_online_verification':True}, 1, .82, 'dependency-surface', True, scope_id=scope['scope_id'], needs_online_verification=True)
    if not local_db:
        add_item(items,name,root,root,'dependency_online_verification_not_performed',{'reason':'no --cve-db supplied and no network verification performed','policy':'do not invent CVE/deprecation/typosquat claims'},1,.98,'dependency-surface',False,scope_id=scope['scope_id'],reason='Dependency collector ran offline and did not report verified CVEs',limitation='Provide --cve-db with explicit authorization to generate verified_dependency_advisory evidence')
    return items

def collect_docs(name: str, root: Path, scope: dict, files: list[Path]) -> list[dict]:
    items=[]
    for p in files:
        if p.suffix.lower() not in DOC_SUFFIXES and p.name.lower() not in {'openapi.json','swagger.json'}: continue
        text=read_text(p)
        add_item(items, name, p, root, 'documentation_file', {'file': p.name}, 1, .72, 'docs-tests-history', False, scope_id=scope['scope_id'])
        for m in DOC_ROUTE_HINT_RE.finditer(text):
            add_item(items, name, p, root, 'documented_endpoint', {'method': m.group(0).split()[0].upper(), 'route': m.group(1)}, line_no(text,m.group(0)), .7, 'docs-tests-history', True, endpoint_relevance='medium', scope_id=scope['scope_id'], limitation='documentation may be stale; correlate with code and runtime')
        for m in re.finditer(r'(?i)\b(TODO|FIXME|deprecated|legacy|sample credential|example password|mock|fixture|seed|migration|changelog|release|error example)\b', text):
            add_item(items, name, p, root, 'docs_history_signal', m.group(0), line_no(text,m.group(0)), .55, 'docs-tests-history', True, scope_id=scope['scope_id'])
    return items


def collect_ci_cd(name: str, root: Path, scope: dict, files: list[Path]) -> list[dict]:
    items=[]
    for p in files:
        rel = str(p.relative_to(root)).replace('\\','/') if p.is_relative_to(root) else p.name
        if not ('.github/workflows/' in rel or '.gitlab-ci' in p.name or p.name in CI_NAMES or 'jenkinsfile' == p.name.lower() or '.circleci/' in rel):
            continue
        text=read_text(p)
        add_item(items, name, p, root, 'ci_cd_file', rel, 1, .88, 'configuration-deployment', False, scope_id=scope['scope_id'])
        for m in re.finditer(r'(?i)\b(secrets\.|env:|permissions:|uses:|docker build|kubectl|helm|terraform|aws |gcloud |az |deploy|artifact|cache|upload-artifact|download-artifact)\b', text):
            add_item(items, name, p, root, 'ci_cd_security_signal', m.group(0), line_no(text,m.group(0)), .62, 'configuration-deployment', True, scope_id=scope['scope_id'], limitation='CI/CD signal is local static evidence; cloud/runner state is not verified')
    return items


def collect_iac(name: str, root: Path, scope: dict, files: list[Path]) -> list[dict]:
    items=[]
    for p in files:
        text=read_text(p)
        rel=str(p.relative_to(root)).replace('\\','/') if p.is_relative_to(root) else p.name
        if not (p.suffix.lower() in IAC_SUFFIXES or p.name in IAC_NAMES or any(x in rel.lower() for x in ['kubernetes','k8s','deployment','ingress','service','helm','values.yaml'])):
            continue
        add_item(items, name, p, root, 'iac_or_container_file', p.name, 1, .82, 'configuration-deployment', False, scope_id=scope['scope_id'])
        graph={'file':rel,'resources':[],'edges':[],'images':[],'ports':[],'hosts':[],'secret_refs':[],'service_accounts':[]}
        if p.name == 'Dockerfile':
            for m in re.finditer(r'(?im)^\s*FROM\s+([^\s]+)|^\s*EXPOSE\s+(.+)|^\s*ENV\s+([A-Za-z_][A-Za-z0-9_]*)', text):
                if m.group(1): graph['images'].append(m.group(1)); typ='docker_base_image'; val={'image':m.group(1)}
                elif m.group(2): graph['ports'].append(m.group(2)); typ='docker_exposed_port'; val={'ports':m.group(2).split()}
                else: typ='docker_env_key'; val={'key':m.group(3)}
                add_item(items,name,p,root,typ,val,line_no(text,m.group(0)),.82,'configuration-deployment',True,scope_id=scope['scope_id'],reason='Dockerfile instruction parsed into structured IaC evidence',limitation='Dockerfile evidence does not prove deployed runtime state')
        if p.suffix.lower() in {'.yaml','.yml'} or p.name in {'docker-compose.yml','docker-compose.yaml','compose.yml','compose.yaml','values.yaml','Chart.yaml'}:
            kind=None; current_name=None
            for idx,line in enumerate(text.splitlines(),1):
                km=re.match(r'\s*kind:\s*([A-Za-z0-9_.-]+)', line)
                nm=re.match(r'\s*name:\s*([A-Za-z0-9_.-]+)', line)
                im=re.match(r'\s*image:\s*([^\s#]+)', line)
                pm=re.match(r'\s*-?\s*(?:containerPort|targetPort|port):\s*([0-9]+)', line)
                hm=re.match(r'\s*host:\s*([^\s#]+)', line)
                sm=re.search(r'(secretKeyRef|secretRef|secretName):\s*([A-Za-z0-9_.-]+)?', line)
                sam=re.match(r'\s*serviceAccountName:\s*([A-Za-z0-9_.-]+)', line)
                if km: kind=km.group(1); graph['resources'].append({'kind':kind,'name':current_name})
                if nm: current_name=nm.group(1); graph['resources'].append({'kind':kind,'name':current_name})
                if im: graph['images'].append(im.group(1))
                if pm: graph['ports'].append(pm.group(1))
                if hm: graph['hosts'].append(hm.group(1))
                if sm: graph['secret_refs'].append({'line':idx,'type':sm.group(1),'name':sm.group(2) or '<inline-or-next-line>'})
                if sam: graph['service_accounts'].append(sam.group(1))
        if p.suffix.lower() in {'.tf','.tfvars'}:
            for m in re.finditer(r'''(?s)\b(resource|data|provider|module)\s+"([^"]+)"(?:\s+"([^"]+)")?\s*\{(.{0,2000}?)\}''', text):
                block={'block_type':m.group(1),'resource_type':m.group(2),'name':m.group(3),'line':line_no(text,m.group(0))}
                graph['resources'].append(block)
                for hm in re.finditer(r'(?im)\b(bucket|name|domain|host|security_group|subnet_id|vpc_id|role|policy)\s*=\s*(["\'][^"\']+["\']|[^\n#]+)', m.group(4)):
                    graph['edges'].append({'from':block,'property':hm.group(1),'value_hash':stable_hash(hm.group(2))[:12]})
                add_item(items,name,p,root,'terraform_resource',block,block['line'],.86,'configuration-deployment',True,scope_id=scope['scope_id'],reason='Terraform block parsed into structured resource evidence',limitation='Terraform state/cloud reality is not queried')
        if any(graph[k] for k in ['resources','images','ports','hosts','secret_refs','service_accounts','edges']):
            add_item(items,name,p,root,'iac_resource_graph',graph,1,.84,'configuration-deployment',True,scope_id=scope['scope_id'],reason='Structured IaC resource graph built from local manifests',limitation='Static manifest graph; rendered Helm templates and live cluster/cloud state are not verified')
        for m in re.finditer(r'(?i)\b(resource\s+"[^"]+"|provider\s+"[^"]+"|image:|FROM\s+[^\s]+|ports?:|ingress|host:|secretKeyRef|configMapRef|env:|volumeMounts|serviceAccount|iam|bucket|security_group|namespace|replicas)\b', text):
            add_item(items, name, p, root, 'iac_cloud_or_runtime_signal', m.group(0), line_no(text,m.group(0)), .62, 'configuration-deployment', True, scope_id=scope['scope_id'], limitation='IaC signal is from local manifests; cloud reality is not queried')
    return items

def collect_graphql(name: str, root: Path, scope: dict, files: list[Path]) -> list[dict]:
    items=[]
    for p in files:
        if p.suffix.lower() not in {'.graphql','.gql','.js','.ts','.jsx','.tsx','.json'}: continue
        text=read_text(p)
        for m in GQL_SCHEMA_RE.finditer(text):
            add_item(items, name, p, root, 'graphql_schema_symbol', {'kind':m.group(1),'name':m.group(2)}, line_no(text,m.group(0)), .84, 'route-api-inventory', False, endpoint_relevance='medium', scope_id=scope['scope_id'])
        for m in GQL_OP_RE.finditer(text):
            add_item(items, name, p, root, 'graphql_operation', {'type':m.group(1),'name':m.group(2)}, line_no(text,m.group(0)), .76, 'route-api-inventory', True, endpoint_relevance='medium', scope_id=scope['scope_id'])
        if re.search(r'(?i)introspection|__schema|__type', text):
            add_item(items, name, p, root, 'graphql_introspection_artifact_signal', {'file': p.name}, 1, .68, 'hidden-information', True, endpoint_relevance='medium', scope_id=scope['scope_id'])
    return items


def collect_websocket(name: str, root: Path, scope: dict, files: list[Path]) -> list[dict]:
    items=[]
    for p in files:
        text=read_text(p)
        for m in re.finditer(r'(?i)(new\s+WebSocket\s*\(|socket\.io|ws://|wss://|@SubscribeMessage|ServerWebSocket|websocket)', text):
            add_item(items, name, p, root, 'websocket_stack_signal', m.group(0), line_no(text,m.group(0)), .68, 'route-api-inventory', True, endpoint_relevance='medium', scope_id=scope['scope_id'])
        for m in WS_EVENT_RE.finditer(text):
            add_item(items, name, p, root, 'websocket_event', m.group(1), line_no(text,m.group(0)), .64, 'route-api-inventory', True, endpoint_relevance='medium', scope_id=scope['scope_id'])
    return items


def collect_sourcemaps(name: str, root: Path, scope: dict, files: list[Path]) -> list[dict]:
    items=[]
    for p in files:
        if not p.name.lower().endswith('.map'): continue
        text=read_text(p)
        add_item(items, name, p, root, 'source_map_artifact', {'file': p.name, 'hash': stable_hash(text)}, 1, .96, 'frontend-js', True, data_sensitivity='medium', scope_id=scope['scope_id'])
        try:
            data=json.loads(text)
            for src in (data.get('sources') or [])[:1000]:
                add_item(items, name, p, root, 'source_map_original_source', src, 1, .9, 'frontend-js', True, data_sensitivity='medium', scope_id=scope['scope_id'])
            for content in (data.get('sourcesContent') or [])[:100]:
                for m in PATH_RE.finditer(content):
                    add_item(items, name, p, root, 'source_map_deleted_or_hidden_api_candidate', m.group(0), line_no(content,m.group(0)), .6, 'hidden-information', True, endpoint_relevance='medium', scope_id=scope['scope_id'], limitation='endpoint came from sourcemap source content; may be deleted, stale or dead code')
        except Exception:
            add_item(items, name, p, root, 'source_map_parse_limitation', {'file': p.name}, 1, .4, 'frontend-js', True, scope_id=scope['scope_id'])
    return items




def _route_contexts_for_binding(text: str) -> list[dict]:
    ctx=[]
    for m in ROUTE_RE.finditer(text):
        route=m.group(2) or m.group(4) or m.group(5) or ''
        method=(m.group(1) or m.group(3) or 'ROUTE').upper()
        ctx.append({'line':line_no(text,m.group(0)),'route':route,'method':method,'raw':m.group(0)})
    for m in re.finditer(r'''(?sx)@(?:app|router|blueprint)\.(get|post|put|patch|delete|options|head|route)\s*\(\s*([`"'])([^`"']+)\1''', text):
        ctx.append({'line':line_no(text,m.group(0)),'route':m.group(2),'method':m.group(1).upper(),'raw':m.group(0)})
    for m in re.finditer(r'''(?sx)Route::(get|post|put|patch|delete|options|any|match)\s*\(\s*([`"'])([^`"']+)\2''', text):
        ctx.append({'line':line_no(text,m.group(0)),'route':m.group(3),'method':m.group(1).upper(),'raw':m.group(0)})
    return sorted(ctx, key=lambda x:x['line'])

def _bind_to_route(route_ctx: list[dict], line: int) -> dict:
    prev=[r for r in route_ctx if r['line'] <= line]
    if not prev: return {'binding_status':'unbound','route':None,'method':None,'distance_lines':None}
    best=prev[-1]; dist=line-best['line']
    return {'binding_status':'bound_candidate' if dist <= 120 else 'weak_file_level_binding','route':best['route'],'method':best['method'],'distance_lines':dist,'route_line':best['line']}

def _collect_schema_and_model_params(items, name: str, p: Path, root: Path, text: str, route_ctx: list[dict], scope_id: str) -> None:
    for m in re.finditer(r'''(?s)\b(?:class|interface|type)\s+([A-Za-z_][A-Za-z0-9_]*(?:Dto|DTO|Request|Input|Payload|Schema)?)\b[^\{]*\{(.{0,2000}?)\}''', text):
        block=m.group(2); cname=m.group(1)
        for fm in re.finditer(r'''(?m)\b([A-Za-z_][A-Za-z0-9_]*(?:Id|ID|_id|tenant|org|workspace|account|project|role|debug|preview|draft|include|expand|filter|sort|limit|offset)?)\s*(?:[:=]|\?)''', block):
            ln=line_no(text, fm.group(0))
            add_item(items,name,p,root,'parameter',{'name':fm.group(1),'source':'dto_or_typescript_schema','schema_or_model':cname,'route_binding':_bind_to_route(route_ctx,ln)},ln,.74,'parameter-dataflow',True,endpoint_relevance='medium',tenant_relevance='medium' if re.search(r'(?i)tenant|org|workspace|account|project',fm.group(1)) else 'low',role_relevance='medium' if 'role' in fm.group(1).lower() else 'low',scope_id=scope_id,reason='DTO/schema field extracted and bound to nearest route context when available',limitation='Binding is lexical proximity; full type flow requires language-specific AST/dataflow')
    for m in re.finditer(r'''(?im)(?:fillable\s*=\s*\[([^\]]+)\]|\b@Column\b|\bColumn\s*\(|models\.[A-Za-z]+Field\(|db\.Column\()''', text):
        raw=m.group(0); ln=line_no(text,raw)
        names=re.findall(r'''["']([A-Za-z_][A-Za-z0-9_]*(?:Id|ID|_id|tenant|org|workspace|account|project|role|admin|is[A-Z][A-Za-z0-9_]*)?)["']''', raw) or re.findall(r'\b([A-Za-z_][A-Za-z0-9_]*(?:Id|ID|_id|tenant|org|workspace|account|project|role|admin))\b', raw)
        add_item(items,name,p,root,'orm_or_mass_assignment_field',{'fields':sorted(set(names)),'source':'orm_or_fillable','route_binding':_bind_to_route(route_ctx,ln)},ln,.68,'parameter-dataflow',True,tenant_relevance='medium' if re.search(r'(?i)tenant|org|workspace|account|project',raw) else 'low',role_relevance='medium' if re.search(r'(?i)role|admin',raw) else 'low',scope_id=scope_id,reason='ORM or mass-assignment field signal collected',limitation='Field presence alone does not prove mass assignment exploitability')

def collect_hidden_parameters(name: str, root: Path, scope: dict, files: list[Path]) -> list[dict]:
    items=[]
    for p in files:
        text=read_text(p)
        route_ctx=_route_contexts_for_binding(text)
        _collect_schema_and_model_params(items, name, p, root, text, route_ctx, scope['scope_id'])
        for m in PARAM_NAME_RE.finditer(text):
            param = next((g for g in m.groups()[1:] if g), m.group(0))
            ln=line_no(text,m.group(0))
            add_item(items, name, p, root, 'parameter', {'name': param, 'source': 'handler/schema/validator/static', 'route_binding': _bind_to_route(route_ctx, ln)}, ln, .70, 'parameter-dataflow', True, endpoint_relevance='medium', tenant_relevance='medium' if re.search(r'(?i)tenant|org|workspace|account|project|userId',param) else 'low', role_relevance='medium' if re.search(r'(?i)role|admin|permission',param) else 'low', scope_id=scope['scope_id'], reason='Handler/schema/validator parameter collected and bound to nearest route context', limitation='Route binding is static lexical proximity; runtime request parsing may differ')
        for m in HIDDEN_PARAM_RE.finditer(text):
            ln=line_no(text,m.group(0))
            add_item(items, name, p, root, 'hidden_or_authorization_parameter_signal', {'name':m.group(0),'route_binding':_bind_to_route(route_ctx,ln)}, ln, .56, 'parameter-dataflow', True, auth_relevance='medium', tenant_relevance='medium', role_relevance='medium', scope_id=scope['scope_id'], reason='Hidden/authorization-relevant parameter term appears in local source evidence', limitation='Keyword signal only; verify source/sink, trust boundary and role behavior')
    return items


COLLECTORS = {
    'route_collector': collect_routes,
    'js_asset_collector': collect_js_assets,
    'config_collector': collect_config,
    'dependency_collector': collect_dependencies,
    'docs_collector': collect_docs,
    'ci_cd_collector': collect_ci_cd,
    'iac_collector': collect_iac,
    'graphql_collector': collect_graphql,
    'websocket_collector': collect_websocket,
    'sourcemap_collector': collect_sourcemaps,
    'hidden_parameter_collector': collect_hidden_parameters,
}


def run_collector(collector_name: str) -> int:
    ap = common_parser(f'{collector_name}: authorized local-only information collector')
    args = ap.parse_args()
    root, scope, ok, reason, files = iter_authorized(args)
    if args.dry_run:
        return dry_run_report(args, collector_name, root, scope)
    if not ok:
        return output_report(args, collector_name, [out_of_scope_item(collector_name, root, reason)], {'scope_check':'FAIL'}) or 2
    if collector_name == 'dependency_collector':
        items = collect_dependencies(collector_name, root, scope, files, cve_db=getattr(args,'cve_db',None), allow_online_verification=getattr(args,'allow_online_verification',False))
    else:
        items = COLLECTORS[collector_name](collector_name, root, scope, files)
    inv = scan_inventory(root, scope, args.max_files, args.timeout, args.scan_profile, args.follow_symlinks) if root.is_dir() else {'analyzed_files':1,'skipped_files':0,'skipped_reasons':{},'skipped_file_sample':[]}
    coverage = {
        **inv,
        'collector': collector_name,
        'scope_id': scope['scope_id'],
        'candidate_items': len(items),
        'limitations': ['static local analysis', 'no network verification unless explicit local --cve-db was supplied', 'confirmed status requires manual/runtime evidence']
    }
    return output_report(args, collector_name, items, {'coverage': coverage})

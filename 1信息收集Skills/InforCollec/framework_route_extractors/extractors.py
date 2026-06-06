from __future__ import annotations
import re
from pathlib import Path
from typing import Any

def _ln(text: str, needle: str) -> int:
    idx=text.find(needle)
    return 1 if idx < 0 else text[:idx].count('\n')+1

def _add(out, framework, method, path, source, line, handler='', confidence=.75, meta=None):
    out.append({'framework':framework,'method':method.upper() if method else 'ROUTE','path':path or '/', 'handler':handler, 'source_file':str(source), 'line':line, 'confidence':confidence, 'meta':meta or {}})

def extract_framework_routes(path: Path, root: Path, text: str) -> list[dict[str,Any]]:
    out=[]
    try: rel=str(path.relative_to(root)).replace('\\','/')
    except Exception: rel=str(path)
    for m in re.finditer(r"""(?x)(?:app|router|server|fastify)\s*\.\s*(get|post|put|patch|delete|options|head|all|use)\s*\(\s*[`"']([^`"']+)""", text):
        _add(out,'Express/Fastify',m.group(1),m.group(2),path,_ln(text,m.group(0)),confidence=.78)
    if re.search(r'(^|/)(pages/api|app/api)/', rel):
        route='/' + re.sub(r'^(?:src/)?(?:pages/|app/)?api/', 'api/', rel)
        route=re.sub(r'/(route|index)\.(js|jsx|ts|tsx)$','',route)
        route=re.sub(r'\.(js|jsx|ts|tsx)$','',route)
        route=route.replace('[','{').replace(']','}')
        methods=sorted(set(re.findall(r'export\s+async\s+function\s+(GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD)\b', text))) or ['ROUTE']
        for method in methods: _add(out,'Next.js',method,route,path,1,confidence=.82,meta={'route_source':'filesystem'})
    prefixes=[m.group(1) or '' for m in re.finditer(r"""@Controller\s*\(\s*[`"']?([^`"')]*)""", text)] or ['']
    for m in re.finditer(r"""@(Get|Post|Put|Patch|Delete|Options|Head|All)\s*\(\s*[`"']?([^`"')]*)""", text):
        for pref in prefixes:
            route='/' + '/'.join(x.strip('/') for x in [pref,m.group(2)] if x is not None and x!='')
            _add(out,'NestJS',m.group(1),route,path,_ln(text,m.group(0)),confidence=.82)
    prefixes=[m.group(1) for m in re.finditer(r"""APIRouter\s*\([^)]*prefix\s*=\s*[`"']([^`"']+)""", text)] or ['']
    for m in re.finditer(r"""@(app|router)\s*\.\s*(get|post|put|patch|delete|options|head|websocket)\s*\(\s*[`"']([^`"']+)""", text):
        pfx='' if m.group(1)=='app' else (prefixes[0] if prefixes else '')
        route='/' + '/'.join(x.strip('/') for x in [pfx,m.group(3)] if x)
        _add(out,'FastAPI',m.group(2),route,path,_ln(text,m.group(0)),confidence=.86)
    for m in re.finditer(r"""(?x)\b(?:path|re_path)\s*\(\s*[rRuUbBfF]*[`"']([^`"']+)""", text):
        _add(out,'Django','ROUTE','/'+m.group(1).strip('/'),path,_ln(text,m.group(0)),confidence=.76)
    prefixes=[]
    for m in re.finditer(r"""@RequestMapping\s*\(\s*(?:value\s*=\s*)?[`"']?([^`"',)]*)""", text): prefixes.append(m.group(1) or '')
    prefixes=prefixes[:1] or ['']
    smap={'GetMapping':'GET','PostMapping':'POST','PutMapping':'PUT','DeleteMapping':'DELETE','PatchMapping':'PATCH','RequestMapping':'ROUTE'}
    for m in re.finditer(r"""@(GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping|RequestMapping)\s*\(\s*(?:value\s*=\s*)?[`"']?([^`"',)]*)""", text):
        for pref in prefixes:
            route='/' + '/'.join(x.strip('/') for x in [pref,m.group(2)] if x)
            _add(out,'Spring',smap.get(m.group(1),'ROUTE'),route,path,_ln(text,m.group(0)),confidence=.78)
    for m in re.finditer(r"""Route::(get|post|put|patch|delete|options|any|match)\s*\(\s*[`"']([^`"']+)""", text):
        _add(out,'Laravel',m.group(1),m.group(2),path,_ln(text,m.group(0)),confidence=.86)
    for m in re.finditer(r"""(?x)(?:r|router|engine|mux)\s*\.\s*(GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD|HandleFunc|Handle)\s*\(\s*[`"']([^`"']+)""", text):
        _add(out,'Go',m.group(1).replace('HandleFunc','ROUTE').replace('Handle','ROUTE'),m.group(2),path,_ln(text,m.group(0)),confidence=.76)
    for m in re.finditer(r"""http\.HandleFunc\s*\(\s*[`"']([^`"']+)""", text):
        _add(out,'Go','ROUTE',m.group(1),path,_ln(text,m.group(0)),confidence=.72)
    for m in re.finditer(r"""#\[(get|post|put|patch|delete)\s*\(\s*[`"']([^`"']+)""", text):
        _add(out,'Rust',m.group(1),m.group(2),path,_ln(text,m.group(0)),confidence=.82)
    for m in re.finditer(r"""\.route\s*\(\s*[`"']([^`"']+)\s*[`"']\s*,\s*(get|post|put|patch|delete|any)\s*\(""", text):
        _add(out,'Rust',m.group(2),m.group(1),path,_ln(text,m.group(0)),confidence=.76)
    seen=set(); uniq=[]
    for r in out:
        key=(r['framework'],r['method'],r['path'],r['source_file'],r['line'])
        if key not in seen: seen.add(key); uniq.append(r)
    return uniq

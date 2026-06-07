#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re, hashlib
from pathlib import Path
from _scope import iter_scoped_files, read_text_safe
EXTS={'.js','.ts','.jsx','.tsx','.py','.java','.kt','.php','.go','.rs','.rb'}
PATTERNS=[
 ('express', re.compile(r'\b(?:app|router|server)\.(get|post|put|patch|delete|head|options|all)\s*\(\s*["\']([^"\']+)')),
 ('nestjs', re.compile(r'@(Get|Post|Put|Patch|Delete|Options|Head|All)\s*\(\s*["\']?([^"\')]+)?["\']?\s*\)')),
 ('fastapi', re.compile(r'@(?:app|router)\.(get|post|put|patch|delete|head|options)\s*\(\s*["\']([^"\']+)')),
 ('django', re.compile(r'\b(?:path|re_path)\s*\(\s*r?["\']([^"\']+)["\']')),
 ('spring', re.compile(r'@(GetMapping|PostMapping|PutMapping|PatchMapping|DeleteMapping|RequestMapping)\s*(?:\(\s*(?:value\s*=\s*|path\s*=\s*)?["\']([^"\']*)["\'])?')),
 ('laravel', re.compile(r'Route::(?:middleware\s*\([^)]*\)\s*->\s*)?(get|post|put|patch|delete|any|match)\s*\(\s*["\']([^"\']+)')),
 ('go', re.compile(r'\.(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS|HandleFunc|Handle)\s*\(\s*["\']([^"\']+)')),
 ('rust', re.compile(r'(?:\.route\s*\(\s*["\']([^"\']+)["\']\s*,\s*(get|post|put|patch|delete|any)\s*\(|#\[(get|post|put|patch|delete)\(\s*["\']([^"\']+)["\']\s*\)\])')),
 ('rails', re.compile(r'\b(get|post|put|patch|delete|match)\s+["\']([^"\']+)')),
]
AUTHN_RE=re.compile(r'\b(authenticate|requireAuth|login_required|Depends\s*\(|@PreAuthorize|can\(|authorize|middleware\(["\']auth|Jwt|Guard|passport|session|current_user)', re.I)
AUTHZ_RE=re.compile(r'\b(role|permission|tenant|organization|workspace|owner|isAdmin|authorize|policy|scope|RBAC|ABAC|@Roles|@Can)', re.I)
MIDDLEWARE_RE=re.compile(r'\b(requireAuth|requireOwner|middleware\([^)]*\)|Depends\([^)]*\)|@PreAuthorize\([^)]*\)|@Roles\([^)]*\)|can\([^)]*\)|authorize\([^)]*\))', re.I)
PARAM_RE=re.compile(r'[:{<\[]([A-Za-z_][A-Za-z0-9_]*)[>\]}]?')

def sid(s): return hashlib.sha256(s.encode()).hexdigest()[:16]
def line_of(t,i): return t.count('\n',0,i)+1

def norm(path):
    path=path or '/'
    path=re.sub(r'<(?:[A-Za-z_][A-Za-z0-9_]*:)?([A-Za-z_][A-Za-z0-9_]*)>', r'{\1}', path)
    path=re.sub(r'\[([A-Za-z_][A-Za-z0-9_]*)\]', r'{\1}', path)
    return '/' + path.lstrip('/')

def method_path(fw,m,rel):
    g=m.groups()
    if fw=='django': return 'ANY', norm(g[0])
    if fw=='spring':
        meth={'GetMapping':'GET','PostMapping':'POST','PutMapping':'PUT','PatchMapping':'PATCH','DeleteMapping':'DELETE'}.get(g[0], 'ANY')
        return meth, norm(g[1] or '/')
    if fw=='rust':
        return (g[1] or g[2] or 'ANY').upper(), norm(g[0] or g[3] or '/')
    if fw=='nestjs': return g[0].upper(), norm(g[1] or '/')
    return g[0].upper(), norm(g[1])

def extract(root):
    root=Path(root).resolve(); routes=[]
    for p in iter_scoped_files(root, 'source'):
        if p.suffix.lower() not in EXTS: continue
        try: text=read_text_safe(p, limit=4_000_000, redact=True)
        except Exception: continue
        rel=str(p.relative_to(root))
        for fw,rx in PATTERNS:
            for m in rx.finditer(text):
                method,path=method_path(fw,m,rel)
                start=max(0,m.start()-500); end=min(len(text),m.end()+800); ctx=text[start:end]
                middlewares=sorted(set(x.group(1)[:160] for x in MIDDLEWARE_RE.finditer(ctx)))
                params=sorted(set(PARAM_RE.findall(path)))
                routes.append({'id':'route-'+sid(rel+path+str(m.start())),'framework':fw,'method':method,'path':path,'file':rel,'line':line_of(text,m.start()),'handler':'unknown','authn_hint':'present' if AUTHN_RE.search(ctx) else 'missing_or_unknown','authz_hint':'present' if AUTHZ_RE.search(ctx) else 'missing_or_unknown','middlewares':middlewares,'parameters':params,'source':'route_extractor_regex_candidate','confirmation_policy':'route candidate; AST semantic graph preferred when available'})
        # Next.js file-system route fallback.
        if rel.startswith(('pages/api/','app/api/')) and p.suffix.lower() in {'.js','.jsx','.ts','.tsx'}:
            path='/' + re.sub(r'\.(js|jsx|ts|tsx)$','',rel)
            path=path.replace('pages/api/','api/').replace('app/api/','api/').replace('/route','')
            for meth in sorted(set(x.upper() for x in re.findall(r'export\s+(?:async\s+)?function\s+(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s*\(', text, re.I)) or ['ANY']):
                routes.append({'id':'route-'+sid(rel+path+meth),'framework':'nextjs_file_route','method':meth,'path':norm(path),'file':rel,'line':1,'handler':'file_system_route','authn_hint':'present' if AUTHN_RE.search(text[:2000]) else 'missing_or_unknown','authz_hint':'present' if AUTHZ_RE.search(text[:2000]) else 'missing_or_unknown','middlewares':[],'parameters':sorted(set(PARAM_RE.findall(path))),'source':'nextjs_file_route_candidate','confirmation_policy':'candidate until executed or AST-confirmed'})
    return {'schema_version':'route-inventory-v1','source_root':str(root),'routes':routes,'policy':'routes are candidates until linked to handler/auth graph and dynamic evidence'}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('root'); ap.add_argument('--out', required=True); ns=ap.parse_args()
    data=extract(ns.root); Path(ns.out).parent.mkdir(parents=True, exist_ok=True); Path(ns.out).write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'ok':True,'routes':len(data['routes'])}, ensure_ascii=False))
if __name__=='__main__': main()

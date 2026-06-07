#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.scope_guard import iter_scoped_files, load_scope, read_text_scoped

ROUTE_PATTERNS = [
 ('express', re.compile(r"(?P<router>app|router)\.(?P<method>get|post|put|patch|delete|all)\s*\(\s*['\"](?P<path>[^'\"]+)['\"]\s*,(?P<rest>[^\n;]*)", re.I)),
 ('fastapi', re.compile(r"@(?P<router>app|router)\.(?P<method>get|post|put|patch|delete)\s*\(\s*['\"](?P<path>[^'\"]+)['\"]", re.I)),
 ('flask', re.compile(r"@(?P<router>app|bp)\.route\s*\(\s*['\"](?P<path>[^'\"]+)['\"](?:.*?methods\s*=\s*\[(?P<methods>[^\]]+)\])?", re.I)),
 ('spring', re.compile(r"@(?P<method>GetMapping|PostMapping|PutMapping|PatchMapping|DeleteMapping|RequestMapping)\s*\(\s*(?:value\s*=\s*)?['\"](?P<path>[^'\"]+)['\"]", re.I)),
 ('nestjs', re.compile(r"@(?P<method>Get|Post|Put|Patch|Delete|All)\s*\(\s*['\"](?P<path>[^'\"]*)['\"]", re.I)),
 ('rails', re.compile(r"(?P<method>get|post|put|patch|delete)\s+['\"](?P<path>[^'\"]+)['\"](?:\s*,\s*to:\s*['\"](?P<handler>[^'\"]+)['\"])?", re.I)),
 ('laravel', re.compile(r"Route::(?P<method>get|post|put|patch|delete|any)\s*\(\s*['\"](?P<path>[^'\"]+)['\"]\s*,\s*(?P<handler>[^\)]*)", re.I)),
 ('gin', re.compile(r"(?P<router>r|router|group)\.(?P<method>GET|POST|PUT|PATCH|DELETE|Any)\s*\(\s*['\"](?P<path>[^'\"]+)['\"]\s*,\s*(?P<handler>[^\)]+)", re.I)),
 ('django', re.compile(r"path\s*\(\s*['\"](?P<path>[^'\"]+)['\"]\s*,\s*(?P<handler>[A-Za-z0-9_\.]+)", re.I)),
]
AUTH_HINTS = re.compile(r'auth|jwt|guard|permission|role|policy|authorize|login_required|middleware|Depends\(', re.I)

def route_id(method, path, file, line):
    return 'route-' + hashlib.sha256(f'{method}:{path}:{file}:{line}'.encode()).hexdigest()[:14]

def _line_no(text, pos): return text[:pos].count('\n') + 1

def collect(root: str | Path, scope_file: str | None = None) -> dict:
    root=Path(root).resolve(); scope=load_scope(root, scope_file); routes=[]
    for p in iter_scoped_files(root, scope):
        if p.suffix.lower() not in {'.py','.js','.ts','.tsx','.jsx','.java','.kt','.php','.rb','.go','.rs'}: continue
        text,_=read_text_scoped(p, root, scope, limit=1_000_000)
        rel=str(p.relative_to(root))
        lines=text.splitlines()
        for fw,rx in ROUTE_PATTERNS:
            for m in rx.finditer(text):
                method=(m.groupdict().get('method') or 'GET').upper().replace('MAPPING','')
                if method == 'REQUEST': method='ANY'
                if method == 'ANY': method='ANY'
                methods=m.groupdict().get('methods')
                if methods:
                    method=','.join(re.findall(r'[A-Z]+', methods.upper())) or method
                path=m.groupdict().get('path') or '/'
                line=_line_no(text,m.start())
                context='\n'.join(lines[max(0,line-5):min(len(lines),line+5)])
                auth='present' if AUTH_HINTS.search(context) else 'unknown'
                handler=m.groupdict().get('handler') or ''
                routes.append({'route_id':route_id(method,path,rel,line),'framework':fw,'method':method,'path':path,'handler':handler.strip()[:200] or 'unknown','file':rel,'line':line,'middleware':'present' if 'middleware' in context.lower() else 'unknown','authn':auth,'authz':'present' if re.search(r'role|permission|policy|authorize|guard|can\(',context,re.I) else 'unknown','evidence':[{'file':rel,'line':line,'summary':context.strip()[:500]}]})
    return {'schema_version':'route-inventory-v2','root':str(root),'routes':routes,'counts':{'routes':len(routes)}}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('root'); ap.add_argument('--scope-file'); ap.add_argument('--out',required=True); ns=ap.parse_args()
    data=collect(ns.root, ns.scope_file); Path(ns.out).parent.mkdir(parents=True,exist_ok=True); Path(ns.out).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(json.dumps(data['counts'],ensure_ascii=False))
if __name__=='__main__': main()

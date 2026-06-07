#!/usr/bin/env python3
from __future__ import annotations
import ast, json, re, sys
from pathlib import Path
file = Path(sys.argv[1]) if len(sys.argv) > 1 else None
if not file or not file.exists():
    print(json.dumps({'status':'failed','plugin':'python_security_graph','backend':'python_ast','real_ast':False,'error':'missing input file','nodes':[],'edges':[]})); raise SystemExit(0)
code = file.read_text(encoding='utf-8', errors='ignore')
nodes=[]; edges=[]; seen=set(); seene=set()
def add(t, id, **kw):
    if id not in seen:
        seen.add(id); nodes.append({'id':id,'type':t,'file':str(file),'ast_backend':'python_ast','real_ast':True,**kw})
    return id
def edge(a,b,t,**kw):
    k=(a,b,t)
    if k not in seene:
        seene.add(k); edges.append({'from':a,'to':b,'type':t,'ast_backend':'python_ast','real_ast':True,**kw})
def unparse(n):
    try: return ast.unparse(n)
    except Exception: return ''
def deco_texts(node): return [unparse(d) for d in getattr(node,'decorator_list',[]) or []]
def route_from_deco(d):
    dl=d.lower(); method=None
    for m in ['get','post','put','patch','delete','route']:
        if re.search(r'(\.|@|\b)'+m+r'\s*\(', dl): method = 'GET' if m=='route' else m.upper()
    path='/'
    mm=re.search(r"['\"]([^'\"]+)['\"]", d)
    if mm: path=mm.group(1)
    return method, path
class Visitor(ast.NodeVisitor):
    def __init__(self): self.stack=[add('module', str(file), path=str(file))]
    @property
    def parent(self): return self.stack[-1]
    def visit_FunctionDef(self,node): self._func(node)
    def visit_AsyncFunctionDef(self,node): self._func(node)
    def _func(self,node):
        decs=deco_texts(node); fid=add('function', f'{file}:function:{node.name}:{node.lineno}', name=node.name, line=node.lineno)
        pushed=fid
        for d in decs:
            method,path=route_from_deco(d)
            if method:
                rid=add('route', f'{file}:{method}:{path}:{node.lineno}', method=method, route=path, line=node.lineno)
                hid=add('handler', f'{file}:handler:{node.name}:{node.lineno}', name=node.name, line=node.lineno)
                edge(rid,hid,'ROUTE_TO_HANDLER')
                pushed=hid
            if re.search(r'login_required|permission_required|Depends|Security|Auth|jwt|role|tenant', d, re.I):
                gid=add('guard', f'{file}:{node.name}:guard:{abs(hash(d))}', decorator=d, line=node.lineno)
                edge(pushed,gid,'USES_MIDDLEWARE'); edge(gid, add('authn', f'{file}:{node.name}:authn', line=node.lineno), 'ENFORCES_AUTHN')
        self.stack.append(pushed)
        self.generic_visit(node)
        self.stack.pop()
    def visit_Assign(self,node):
        txt=unparse(node)
        for pattern, source in [(r'request\.args\.get\(["\']([^"\']+)', 'query'),(r'request\.form\.get\(["\']([^"\']+)', 'body'),(r'request\.json\.get\(["\']([^"\']+)', 'json'),(r'request\.GET\.get\(["\']([^"\']+)', 'query'),(r'request\.POST\.get\(["\']([^"\']+)', 'body')]:
            for m in re.finditer(pattern, txt):
                sid=add('source', f'{file}:{node.lineno}:source:{source}:{m.group(1)}', name=m.group(1), source=source, line=node.lineno)
                edge(self.parent, sid, 'READS_PARAMETER')
        self.generic_visit(node)
    def visit_Call(self,node):
        fn=unparse(node.func); line=getattr(node,'lineno',0)
        sink_kind=None
        if fn in {'eval','exec'}: sink_kind='code_execution'
        elif fn in {'open','pathlib.Path.open'} or fn.endswith('.open'): sink_kind='file_access'
        elif fn in {'os.system','subprocess.run','subprocess.Popen','subprocess.call'} or fn.startswith('subprocess.'): sink_kind='command_execution'
        elif fn in {'pickle.loads','yaml.load'}: sink_kind='deserialization'
        elif re.search(r'requests\.(get|post|put|delete)|httpx\.(get|post|put|delete)|urllib\.request\.urlopen', fn): sink_kind='server_side_request'
        elif re.search(r'\.execute|\.raw|raw_query|find\(', fn): sink_kind='database_query'
        if sink_kind:
            sid=add('sink', f'{file}:{line}:sink:{fn}', name=fn, sink_kind=sink_kind, line=line)
            edge(self.parent, sid, 'REACHES_SINK')
        # FastAPI/Django request and security dependencies inside arguments.
        txt=unparse(node)
        for m in re.finditer(r'(tenantId|tenant_id|orgId|org_id|workspaceId|projectId|ownerId|userId|role|admin|debug|dryRun)', txt):
            pid=add('parameter', f'{file}:{line}:param:{m.group(1)}', name=m.group(1), source='ast_identifier', line=line)
            edge(self.parent, pid, 'READS_PARAMETER')
        self.generic_visit(node)
try:
    tree=ast.parse(code)
    Visitor().visit(tree)
    print(json.dumps({'status':'ready','plugin':'python_security_graph','backend':'python_ast','real_ast':True,'file':str(file),'nodes':nodes,'edges':edges,'quality':{'node_types':sorted({n['type'] for n in nodes}),'edge_types':sorted({e['type'] for e in edges})}}, ensure_ascii=False, indent=2))
except Exception as e:
    print(json.dumps({'status':'failed','plugin':'python_security_graph','backend':'python_ast','real_ast':False,'file':str(file),'error':str(e),'nodes':[],'edges':[]}, ensure_ascii=False, indent=2))

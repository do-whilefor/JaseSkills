#!/usr/bin/env python3
import ast, json, sys, pathlib, re
file = pathlib.Path(sys.argv[1]) if len(sys.argv)>1 else None
if not file or not file.exists():
    print(json.dumps({'status':'failed','plugin':'python_ast_libcst','error':'missing input file','nodes':[],'edges':[]})); raise SystemExit(0)
code = file.read_text(encoding='utf-8', errors='ignore')
nodes=[]; edges=[]
def add(t, id, **kw):
    nodes.append({'id':id,'type':t,'file':str(file),**kw}); return id
try: tree=ast.parse(code)
except Exception as e:
    print(json.dumps({'status':'failed','plugin':'python_ast_libcst','error':str(e),'nodes':[],'edges':[]})); raise SystemExit(0)
class V(ast.NodeVisitor):
    def visit_FunctionDef(self,node):
        decs=[]
        for d in node.decorator_list:
            try: decs.append(ast.unparse(d))
            except Exception: decs.append('')
        for d in decs:
            if any(x in d.lower() for x in ['route','get(','post(','put(','patch(','delete(']):
                method='GET'
                for m in ['post','put','patch','delete','get']:
                    if m in d.lower(): method=m.upper()
                route='/'
                mm=re.search(r"[\(,]\s*['\"]([^'\"]+)['\"]", d)
                if mm: route=mm.group(1)
                rid=add('route',f'{file}:{method} {route}',method=method,route=route,line=node.lineno)
                hid=add('handler',f'{file}:{node.name}',name=node.name,line=node.lineno)
                edges.append({'from':rid,'to':hid,'type':'ROUTE_TO_HANDLER'})
                if any('permission' in x.lower() or 'login_required' in x.lower() or 'auth' in x.lower() or 'depends' in x.lower() for x in decs):
                    gid=add('guard',f'{file}:{node.name}:decorator_guard',decorators=decs)
                    edges.append({'from':rid,'to':gid,'type':'USES_MIDDLEWARE'})
                    edges.append({'from':gid,'to':add('authn',f'{file}:{node.name}:authn'), 'type':'ENFORCES_AUTHN'})
        self.generic_visit(node)
    def visit_Call(self,node):
        fname=''
        try: fname=ast.unparse(node.func)
        except Exception: pass
        if any(s in fname for s in ['open','subprocess','os.system','eval','exec','pickle.loads','yaml.load','requests.get','httpx.get']):
            add('sink',f'{file}:{getattr(node,"lineno",0)}:{fname}',name=fname,line=getattr(node,'lineno',0))
        self.generic_visit(node)
V().visit(tree)
print(json.dumps({'status':'ready','plugin':'python_ast_libcst','file':str(file),'nodes':nodes,'edges':edges}, ensure_ascii=False, indent=2))

#!/usr/bin/env python3
"""Security graph extractor v3 for local authorized repositories.

Read-only. Builds a schema-valid security_graph_v3 while retaining legacy arrays
used by downstream skills. Full AST readiness is runtime-probed; builtin AST-lite
parsers are explicitly marked and never claimed as full semantic parsers.
"""
from __future__ import annotations
import argparse, ast, hashlib, json, os, re, shutil, subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[3]
PLUGIN_DIR=Path(__file__).with_name('parser_plugins')
REGISTRY=PLUGIN_DIR/'PARSER_PLUGIN_REGISTRY.json'
SKIP_DIRS={'.git','node_modules','vendor','__pycache__','.venv','dist-info','target','build','.next','.nuxt'}
LANG_EXT={'.py':'python','.js':'javascript','.jsx':'javascript','.ts':'typescript','.tsx':'typescript','.mjs':'javascript','.cjs':'javascript','.java':'java','.go':'go','.rs':'rust','.php':'php','.rb':'ruby'}

ROUTE_PATTERNS=[
 ('js_express', re.compile(r"\b(?:app|router)\.(get|post|put|patch|delete|options|head)\(\s*['\"]([^'\"]+)",re.I), lambda m:(m.group(1).upper(),m.group(2))),
 ('java_spring', re.compile(r"@(Get|Post|Put|Patch|Delete|Request)Mapping\s*(?:\(\s*(?:value\s*=\s*)?['\"]([^'\"]+)|\(\s*path\s*=\s*['\"]([^'\"]+))",re.I), lambda m:((m.group(1).replace('Request','') or 'ANY').upper(),m.group(2) or m.group(3) or '/')),
 ('go_router', re.compile(r"\.(GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD)\(\s*['\"]([^'\"]+)",re.I), lambda m:(m.group(1).upper(),m.group(2))),
 ('php_laravel', re.compile(r"Route::(get|post|put|patch|delete|options|any)\(\s*['\"]([^'\"]+)",re.I), lambda m:(m.group(1).upper(),m.group(2))),
 ('ruby_rails', re.compile(r"\b(get|post|put|patch|delete|resources|resource)\s+['\"]?([^'\"\s,]+)",re.I), lambda m:(m.group(1).upper(),m.group(2))),
 ('rust_route', re.compile(r"route\(\s*['\"]([^'\"]+)['\"]\s*,\s*(get|post|put|patch|delete|any)",re.I), lambda m:(m.group(2).upper(),m.group(1))),
 ('fastapi_flask', re.compile(r"@(?:app|router)\.(get|post|put|patch|delete|options|head)\(\s*['\"]([^'\"]+)",re.I), lambda m:(m.group(1).upper(),m.group(2))),
]
IMPORT_PATTERNS={
 'java': re.compile(r"^\s*import\s+([A-Za-z0-9_.*]+);",re.M),
 'php': re.compile(r"^\s*use\s+([^;]+);",re.M),
 'go': re.compile(r"import\s+(?:\((.*?)\)|\"([^\"]+)\")",re.S),
 'rust': re.compile(r"^\s*use\s+([^;]+);",re.M),
 'ruby': re.compile(r"^\s*require(?:_relative)?\s+['\"]([^'\"]+)",re.M),
 'javascript': re.compile(r"(?:import\s+(?:[^'\"]+\s+from\s+)?|require\()\s*['\"]([^'\"]+)",re.M),
 'typescript': re.compile(r"(?:import\s+(?:[^'\"]+\s+from\s+)?|require\()\s*['\"]([^'\"]+)",re.M),
}
SYMBOL_PATTERNS={
 'java': [(re.compile(r"\bclass\s+([A-Za-z0-9_]+)"),'class'),(re.compile(r"(?:public|private|protected)?\s*(?:static\s+)?[A-Za-z0-9_<>,.?]+\s+([A-Za-z0-9_]+)\s*\([^;{}]*\)\s*\{"),'function')],
 'php': [(re.compile(r"\bclass\s+([A-Za-z0-9_]+)"),'class'),(re.compile(r"\bfunction\s+([A-Za-z0-9_]+)\s*\("),'function')],
 'go': [(re.compile(r"\bfunc\s+(?:\([^)]*\)\s*)?([A-Za-z0-9_]+)\s*\("),'function'),(re.compile(r"\btype\s+([A-Za-z0-9_]+)\s+struct"),'class')],
 'rust': [(re.compile(r"\bfn\s+([A-Za-z0-9_]+)\s*\("),'function'),(re.compile(r"\bstruct\s+([A-Za-z0-9_]+)"),'class')],
 'ruby': [(re.compile(r"\bclass\s+([A-Za-z0-9_:]+)"),'class'),(re.compile(r"\bdef\s+([A-Za-z0-9_!?=]+)"),'function')],
}
CALL_RE=re.compile(r"\b([A-Za-z_][A-Za-z0-9_.:]*)(?:\.|::)?([A-Za-z_][A-Za-z0-9_!?=]*)\s*\(")
API_RE=re.compile(r"\b(?:fetch|axios\.(?:get|post|put|patch|delete)|requests\.|httpx\.|RestTemplate|WebClient|http\.Get|Net::HTTP|curl_exec)\s*\(?\s*([`'\"][^`'\"]+)?",re.I)
AUTHZ_RE=re.compile(r"(canActivate|authorize|permission|policy|guard|rbac|abac|acl|role|isAdmin|hasPermission|requireRole|@PreAuthorize|before_action|authenticate_user)",re.I)
TENANT_RE=re.compile(r"(tenant_id|tenantId|org_id|orgId|workspace_id|workspaceId|organization|company_id|team_id|owner_id|user_id|account_id)",re.I)
MIDDLEWARE_RE=re.compile(r"(middleware|interceptor|before_action|beforeEach|use\(|Depends\(|@UseGuards|@PreAuthorize|HandlerFunc)",re.I)

PARAMETER_PATTERNS=[
 ('express_query', re.compile(r"req\.query\.([A-Za-z0-9_]+)|req\.query\[['\"]([^'\"]+)", re.I), 'query'),
 ('express_body', re.compile(r"req\.body\.([A-Za-z0-9_]+)|req\.body\[['\"]([^'\"]+)", re.I), 'body'),
 ('express_path', re.compile(r"req\.params\.([A-Za-z0-9_]+)|req\.params\[['\"]([^'\"]+)", re.I), 'path'),
 ('header', re.compile(r"(?:req\.headers\[['\"]([^'\"]+)|getHeader\(['\"]([^'\"]+)|@RequestHeader\(['\"]?([^'\")]+))", re.I), 'header'),
 ('cookie', re.compile(r"(?:req\.cookies\.([A-Za-z0-9_]+)|@CookieValue\(['\"]?([^'\")]+)|request\.cookies\.get\(['\"]([^'\"]+))", re.I), 'cookie'),
 ('python_query', re.compile(r"request\.(?:args|GET)\.get\(['\"]([^'\"]+)|Query\(", re.I), 'query'),
 ('python_body', re.compile(r"request\.(?:json|form|POST|get_json)|Body\(", re.I), 'body'),
 ('python_file', re.compile(r"request\.(?:files|FILES)|UploadFile|File\(", re.I), 'multipart'),
 ('java_param', re.compile(r"@(RequestParam|PathVariable|RequestBody|RequestHeader|CookieValue)(?:\([^)]*\))?\s+[^,;)]+\s+([A-Za-z0-9_]+)", re.I), 'java_binding'),
 ('php_param', re.compile(r"\$request->(?:input|query|post|file|header|cookie)\(['\"]([^'\"]+)", re.I), 'php_request'),
 ('go_param', re.compile(r"\.(?:Query|PostForm|Param|GetHeader|Cookie|FormFile)\(['\"]([^'\"]+)", re.I), 'go_request'),
 ('rails_param', re.compile(r"params\[['\"]([^'\"]+)['\"]\]", re.I), 'rails_params'),
]
VALIDATOR_RE=re.compile(r"(validate|validator|schema|zod|joi|yup|pydantic|serializer|StrongParameters|permit\(|FormRequest|@Valid|BindingResult|ShouldBind|binding|dry-validation)", re.I)
MODEL_RE=re.compile(r"\b(class\s+[A-Za-z0-9_]+\((?:BaseModel|Model)|interface\s+[A-Za-z0-9_]+|type\s+[A-Za-z0-9_]+\s+struct|Schema\(|Entity\(|@Entity|ActiveRecord|Eloquent|Prisma)", re.I)
QUERY_RE=re.compile(r"(findOne|findById|where\(|filter\(|select\(|update\(|delete\(|insert\(|save\(|create\(|raw\(|queryRaw|execute\(|aggregate\(|collection\.)", re.I)
RESPONSE_RE=re.compile(r"(return\s+(?:jsonify|JSONResponse|Response|render|redirect)|res\.(?:json|send|download|redirect|status)|JsonResponse|HttpResponse|return\s+ResponseEntity|ctx\.JSON|render\s+json:)", re.I)
SENSITIVE_FIELD_RE=re.compile(r"(tenant|org|workspace|owner|user_id|role|admin|scope|permission|status|state|price|amount|quantity|discount|coupon|redirect|url|uri|path|file|filename|template|command)", re.I)

SINKS={
 'command_execution': re.compile(r"\b(?:exec|spawn|system|popen|subprocess\.|child_process|shell_exec|passthru|ProcessBuilder|Command::new)\b",re.I),
 'file_operation': re.compile(r"\b(?:open|readFile|writeFile|createReadStream|createWriteStream|sendfile|FileInputStream|Files\.read|Files\.write|File\.read|File\.write|fs::read|fs::write)\s*\(",re.I),
 'network_request': re.compile(r"\b(?:requests\.|httpx\.|fetch\(|axios\.|RestTemplate|WebClient|http\.Get|Net::HTTP|curl_exec|reqwest::)",re.I),
 'database_query': re.compile(r"\b(?:raw\(|execute\(|query\(|queryRaw|sequelize\.query|EntityManager\.createQuery|DB::raw|whereRaw|find_by_sql|ActiveRecord::Base\.connection\.execute)"),
 'template_render': re.compile(r"\b(?:render_template|render\(|Template\(|compile\(|ejs\.render|twig|handlebars|mustache|erb|haml)\b",re.I),
 'deserialization': re.compile(r"\b(?:deserialize|unserialize|pickle\.load|yaml\.load|ObjectInputStream|readObject|Marshal\.load|JSON\.parse|serde_json::from_str)\b",re.I),
 'upload': re.compile(r"\b(?:upload|multipart|unzip|extract|ZipInputStream|plugin|loader|extension)\b",re.I),
}

def sha16(s:str)->str: return hashlib.sha256(s.encode('utf-8','ignore')).hexdigest()[:16]
def line_of(text:str,pos:int)->int: return text[:pos].count('\n')+1
def safe_read(p:Path)->str:
    try: return p.read_text(encoding='utf-8',errors='ignore')
    except Exception: return ''
def skip(path:Path)->bool: return any(part in SKIP_DIRS for part in path.parts)
def os_env():
    env=os.environ.copy(); env['PYTHONDONTWRITEBYTECODE']='1'; return env

def node_id(kind:str,*parts:Any)->str: return f"{kind}:"+sha16('|'.join(map(str,parts)))

def add_node(nodes:dict[str,dict], kind:str, label:str, **props)->str:
    nid=props.pop('id', None) or node_id(kind,label,props.get('file',''),props.get('line',''))
    nodes.setdefault(nid, {'id':nid,'type':kind,'label':label,'properties':props})
    return nid

def add_edge(edges:list, src:str, dst:str, typ:str, **props):
    if src and dst: edges.append({'from':src,'to':dst,'type':typ,'properties':props})

class PyVisitor(ast.NodeVisitor):
    def __init__(self,file:str):
        self.file=file; self.imports=[]; self.symbols=[]; self.calls=[]; self.routes=[]; self.authz=[]; self.tenant=[]; self.middleware=[]; self.edges=[]
    def visit_Import(self,node):
        for n in node.names: self.imports.append({'file':self.file,'module':n.name,'line':node.lineno,'parser':'python_ast','parser_confidence':'full_ast'})
    def visit_ImportFrom(self,node):
        self.imports.append({'file':self.file,'module':node.module or '', 'names':[n.name for n in node.names], 'line':node.lineno,'parser':'python_ast','parser_confidence':'full_ast'})
    def visit_FunctionDef(self,node):
        self.symbols.append({'file':self.file,'type':'function','name':node.name,'line':node.lineno,'parser':'python_ast','parser_confidence':'full_ast'})
        for dec in node.decorator_list:
            try: txt=ast.unparse(dec)
            except Exception: txt=''
            for _,rx,getter in [p for p in ROUTE_PATTERNS if p[0]=='fastapi_flask']:
                m=rx.search('@'+txt if not txt.startswith('@') else txt)
                if m:
                    method,route=getter(m); r={'file':self.file,'method':method,'route':route,'handler':node.name,'line':node.lineno,'parser':'python_ast','parser_confidence':'full_ast'}
                    self.routes.append(r)
            if AUTHZ_RE.search(txt): self.authz.append({'file':self.file,'line':node.lineno,'symbol':node.name,'snippet_hash':sha16(txt),'parser':'python_ast','parser_confidence':'full_ast'})
            if MIDDLEWARE_RE.search(txt): self.middleware.append({'file':self.file,'line':node.lineno,'symbol':node.name,'snippet_hash':sha16(txt),'parser':'python_ast','parser_confidence':'full_ast'})
        self.generic_visit(node)
    def visit_AsyncFunctionDef(self,node): self.visit_FunctionDef(node)
    def visit_ClassDef(self,node):
        self.symbols.append({'file':self.file,'type':'class','name':node.name,'line':node.lineno,'parser':'python_ast','parser_confidence':'full_ast'}); self.generic_visit(node)
    def visit_Call(self,node):
        try: name=ast.unparse(node.func)
        except Exception: name=''
        self.calls.append({'file':self.file,'callee':name,'line':getattr(node,'lineno',0),'parser':'python_ast','parser_confidence':'full_ast'})
        if AUTHZ_RE.search(name): self.authz.append({'file':self.file,'line':getattr(node,'lineno',0),'callee':name,'parser':'python_ast','parser_confidence':'full_ast'})
        self.generic_visit(node)
    def visit_Name(self,node):
        if TENANT_RE.search(node.id): self.tenant.append({'file':self.file,'line':getattr(node,'lineno',0),'identifier':node.id,'parser':'python_ast','parser_confidence':'full_ast'})

def run_ts_plugin(root:Path)->dict[str,Any]:
    if os.environ.get('SKIP_OPTIONAL_AST_PLUGIN')=='1': return {'ready':False,'backend':'typescript_compiler_api','reason':'skipped_by_SKIP_OPTIONAL_AST_PLUGIN_for_fast_replay'}
    node=shutil.which('node'); script=PLUGIN_DIR/'js_ts_ast_bridge.js'
    if not node or not script.exists(): return {'ready':False,'backend':'typescript_compiler_api','reason':'node or bridge missing'}
    try:
        cp=subprocess.run([node,str(script),str(root)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=45,env=os_env())
        data=json.loads(cp.stdout or '{}')
        if cp.returncode!=0 and data.get('ready') is not False: data={'ready':False,'backend':'typescript_compiler_api','reason':cp.stderr[:400]}
        return data
    except Exception as exc: return {'ready':False,'backend':'typescript_compiler_api','reason':str(exc)}

def plugin_status(root:Path)->dict[str,Any]:
    reg=json.loads(REGISTRY.read_text(encoding='utf-8')) if REGISTRY.exists() else {'plugins':[]}
    statuses=[]
    for p in reg.get('plugins',[]):
        cmd=p.get('required_command')
        command_found=True if not cmd else bool(shutil.which(cmd))
        ready=bool(p.get('runtime_probe',{}).get('ready')) if p.get('runtime_probe') else (p.get('type','').startswith('builtin') and command_found)
        if p.get('type','').startswith('optional'): ready=False
        statuses.append({**p,'command_found':command_found,'ready':ready,'claim_verified':ready})
    ts=run_ts_plugin(root)
    for s in statuses:
        if s.get('backend')=='typescript_compiler_api':
            s['ready']=bool(ts.get('ready')); s['claim_verified']=bool(ts.get('ready')); s['runtime_reason']=ts.get('reason') or ts.get('error','')
    return {'registry_schema':reg.get('schema_version'),'claim_policy':reg.get('claim_policy'),'statuses':statuses,'typescript_ast_result':ts}

def scan_imports(rel,text,lang):
    rows=[]; rx=IMPORT_PATTERNS.get(lang)
    if not rx: return rows
    for m in rx.finditer(text):
        val=m.group(1) or ''
        if lang=='go' and '\n' in val:
            for q in re.finditer(r'"([^"]+)"',val): rows.append({'file':rel,'module':q.group(1),'line':line_of(text,m.start()+q.start()),'parser':f'{lang}_ast_lite','parser_confidence':'ast_lite'})
        else: rows.append({'file':rel,'module':val.strip(),'line':line_of(text,m.start()),'parser':f'{lang}_ast_lite','parser_confidence':'ast_lite'})
    return rows

def scan_text(rel:str,text:str,suffix:str,lang:str)->dict[str,list]:
    routes=[]; api=[]; sinks=[]; authz=[]; tenant=[]; middleware=[]; calls=[]; symbols=[]; imports=scan_imports(rel,text,lang); parameters=[]; validators=[]; models=[]; queries=[]; responses=[]
    for source,rgx,getter in ROUTE_PATTERNS:
        for m in rgx.finditer(text):
            method,route=getter(m); routes.append({'file':rel,'method':method or 'ANY','route':route,'line':line_of(text,m.start()),'parser':f'{lang}_ast_lite' if lang in {'java','php','go','rust','ruby'} else 'heuristic_candidate','parser_confidence':'ast_lite' if lang in {'java','php','go','rust','ruby'} else 'heuristic_candidate','source':source})
    for rx,typ in SYMBOL_PATTERNS.get(lang,[]):
        for m in rx.finditer(text): symbols.append({'file':rel,'type':typ,'name':m.group(1),'line':line_of(text,m.start()),'parser':f'{lang}_ast_lite','parser_confidence':'ast_lite'})
    for m in CALL_RE.finditer(text):
        calls.append({'file':rel,'callee':'.'.join([x for x in m.groups() if x]),'line':line_of(text,m.start()),'parser':f'{lang}_ast_lite' if lang in {'java','php','go','rust','ruby'} else 'heuristic_candidate','parser_confidence':'ast_lite' if lang in {'java','php','go','rust','ruby'} else 'heuristic_candidate'})
    for m in API_RE.finditer(text): api.append({'file':rel,'target':(m.group(1) or '').strip('`"\''),'line':line_of(text,m.start()),'parser':'heuristic_candidate','parser_confidence':'candidate'})
    for name,rx in SINKS.items():
        for m in rx.finditer(text): sinks.append({'file':rel,'sink_type':name,'line':line_of(text,m.start()),'snippet_hash':sha16(text[m.start():m.start()+160]),'parser':f'{lang}_ast_lite' if lang in {'java','php','go','rust','ruby'} else 'heuristic_candidate','parser_confidence':'ast_lite' if lang in {'java','php','go','rust','ruby'} else 'candidate'})
    for m in AUTHZ_RE.finditer(text): authz.append({'file':rel,'line':line_of(text,m.start()),'signal':m.group(1),'parser':'semantic_signal','parser_confidence':'signal'})
    for m in TENANT_RE.finditer(text): tenant.append({'file':rel,'line':line_of(text,m.start()),'field':m.group(1),'parser':'semantic_signal','parser_confidence':'signal'})
    for m in MIDDLEWARE_RE.finditer(text): middleware.append({'file':rel,'line':line_of(text,m.start()),'signal':m.group(1),'parser':'semantic_signal','parser_confidence':'signal'})
    for pname, prx, pkind in PARAMETER_PATTERNS:
        for m in prx.finditer(text):
            groups=[g for g in m.groups() if g]
            name=(groups[-1] if groups else m.group(0))[:100]
            parameters.append({'file':rel,'name':name,'binding_kind':pkind,'line':line_of(text,m.start()),'parser':'semantic_parameter_signal','parser_confidence':'candidate','sensitive':bool(SENSITIVE_FIELD_RE.search(name or m.group(0)))})
    for m in VALIDATOR_RE.finditer(text): validators.append({'file':rel,'validator':m.group(1),'line':line_of(text,m.start()),'parser':'semantic_signal','parser_confidence':'signal'})
    for m in MODEL_RE.finditer(text): models.append({'file':rel,'model_signal':m.group(0)[:120],'line':line_of(text,m.start()),'parser':'semantic_signal','parser_confidence':'signal'})
    for m in QUERY_RE.finditer(text): queries.append({'file':rel,'query_signal':m.group(1),'line':line_of(text,m.start()),'parser':'semantic_signal','parser_confidence':'signal'})
    for m in RESPONSE_RE.finditer(text): responses.append({'file':rel,'response_signal':m.group(1)[:120],'line':line_of(text,m.start()),'parser':'semantic_signal','parser_confidence':'signal'})
    return {'routes':routes,'api_clients':api,'sinks':sinks,'authz_boundaries':authz,'tenant_boundaries':tenant,'middleware_boundaries':middleware,'calls':calls,'symbols':symbols,'imports':imports,'parameters':parameters,'validators':validators,'models':models,'queries':queries,'responses':responses}

def merge_ts(out,ts):
    if not ts.get('ready'): return
    for k in ['routes','imports','exports','dynamic_imports','calls','api_clients','authz_boundaries','tenant_boundaries','sinks','edges','parameters','validators','models','queries','responses']:
        out.setdefault(k,[]).extend(ts.get(k) or [])
    for f in ts.get('functions') or []: out.setdefault('symbols',[]).append({'file':f.get('file'),'type':'function','name':f.get('name'),'line':f.get('line'),'parser':'typescript_ast','parser_confidence':'full_ast'})
    for c in ts.get('classes') or []: out.setdefault('symbols',[]).append({'file':c.get('file'),'type':'class','name':c.get('name'),'line':c.get('line'),'parser':'typescript_ast','parser_confidence':'full_ast'})

def dedupe(items:list[dict])->list[dict]:
    seen=set(); res=[]
    for x in items:
        key=json.dumps(x,sort_keys=True,ensure_ascii=False)
        if key not in seen: seen.add(key); res.append(x)
    return res

def build_schema_graph(out:dict[str,Any])->None:
    nodes={}; edges=[]
    file_nodes={}
    for f in out.get('files',[]): file_nodes[f['path']]=add_node(nodes,'file',f['path'],**f)
    symbol_nodes=[]
    for s in out.get('symbols',[]):
        sid=add_node(nodes,'function' if s.get('type')=='function' else 'class',s.get('name','symbol'),**s); symbol_nodes.append((s,sid));
        if s.get('file') in file_nodes: add_edge(edges,file_nodes[s['file']],sid,'calls',parser=s.get('parser'),relationship='file_contains_symbol')
    route_nodes=[]
    for r in out.get('routes',[]):
        rid=add_node(nodes,'route',f"{r.get('method','ANY')} {r.get('route')}",**r); route_nodes.append((r,rid))
        if r.get('file') in file_nodes: add_edge(edges,file_nodes[r['file']],rid,'handles',parser=r.get('parser'),parser_confidence=r.get('parser_confidence'))
    for b in out.get('authz_boundaries',[]):
        bid=add_node(nodes,'guard',b.get('signal') or b.get('symbol') or b.get('callee') or 'authz_boundary',**b)
        if b.get('file') in file_nodes: add_edge(edges,file_nodes[b['file']],bid,'guards',parser=b.get('parser'))
    for b in out.get('middleware_boundaries',[]):
        bid=add_node(nodes,'middleware',b.get('signal') or b.get('symbol') or 'middleware',**b)
        if b.get('file') in file_nodes: add_edge(edges,file_nodes[b['file']],bid,'validates',parser=b.get('parser'))
    for b in out.get('tenant_boundaries',[]):
        bid=add_node(nodes,'trust_boundary',b.get('field') or b.get('identifier') or 'tenant_boundary',**b)
        if b.get('file') in file_nodes: add_edge(edges,file_nodes[b['file']],bid,'crosses_boundary',parser=b.get('parser'))
    for s in out.get('sinks',[]):
        typ=s.get('sink_type','sink'); stype={'command_execution':'command_execution','file_operation':'file_operation','network_request':'network_request','database_query':'database_query','template_render':'template_render','deserialization':'deserialization','upload':'upload'}.get(typ,'sink')
        sid=add_node(nodes,stype,typ,**s)
        if s.get('file') in file_nodes: add_edge(edges,file_nodes[s['file']],sid,'flows_to',parser=s.get('parser'),parser_confidence=s.get('parser_confidence'))
    for a in out.get('api_clients',[]):
        aid=add_node(nodes,'network_request',a.get('target') or 'api_client',**a)
        if a.get('file') in file_nodes: add_edge(edges,file_nodes[a['file']],aid,'maps_to_frontend',parser=a.get('parser'))
    for param in out.get('parameters',[]):
        pid=add_node(nodes,'parameter',param.get('name') or 'parameter',**param)
        if param.get('file') in file_nodes: add_edge(edges,file_nodes[param['file']],pid,'accepts_parameter',parser=param.get('parser'),sensitive=param.get('sensitive'))
    for val in out.get('validators',[]):
        vid=add_node(nodes,'validator',val.get('validator') or 'validator',**val)
        if val.get('file') in file_nodes: add_edge(edges,file_nodes[val['file']],vid,'validates',parser=val.get('parser'))
    for model in out.get('models',[]):
        mid=add_node(nodes,'model',model.get('model_signal') or 'model',**model)
        if model.get('file') in file_nodes: add_edge(edges,file_nodes[model['file']],mid,'maps_to_model',parser=model.get('parser'))
    for q in out.get('queries',[]):
        qid=add_node(nodes,'query',q.get('query_signal') or 'query',**q)
        if q.get('file') in file_nodes: add_edge(edges,file_nodes[q['file']],qid,'executes_query',parser=q.get('parser'))
    for resp in out.get('responses',[]):
        rid=add_node(nodes,'response',resp.get('response_signal') or 'response',**resp)
        if resp.get('file') in file_nodes: add_edge(edges,file_nodes[resp['file']],rid,'returns_response',parser=resp.get('parser'))
    for r,rid in route_nodes:
        for s in out.get('sinks',[]):
            if r.get('file')==s.get('file'):
                sid=add_node(nodes,{'command_execution':'command_execution','file_operation':'file_operation','network_request':'network_request','database_query':'database_query','template_render':'template_render','deserialization':'deserialization','upload':'upload'}.get(s.get('sink_type'),'sink'),s.get('sink_type','sink'),**s)
                add_edge(edges,rid,sid,'flows_to',same_file_candidate=True,confirmation_policy='requires code review and dynamic evidence')
    # Deduplicate edges by full JSON.
    seen=set(); uniq=[]
    for e in edges:
        key=json.dumps(e,sort_keys=True,ensure_ascii=False)
        if key not in seen: seen.add(key); uniq.append(e)
    out['nodes']=list(nodes.values()); out['edges']=uniq
    out['metadata']={'project_path':out['root'],'generated_at':datetime.now(timezone.utc).isoformat(),'scope':'local_authorized_read_only','extractor':'advanced_code_graph_extractor.py','parser_backends':out.get('parser_backends',{})}
    out['provenance']={'claim_policy':'full AST readiness must be runtime-probed; ast_lite and heuristic nodes are candidates only','node_id_policy':'type + sha256(label,file,line,properties)[:16]','edge_id_policy':'deduped by JSON content','schema':'_shared/security_graph/SECURITY_GRAPH_SCHEMA.json'}

def extract(root:Path)->dict[str,Any]:
    root=root.resolve(); ps=plugin_status(root)
    out={'schema_version':'security_graph_v3','root':str(root),'extractor':'advanced_code_graph_extractor.py','non_destructive':True,'capabilities':{'schema_valid_nodes_edges':True,'pluginized_parser_backends':True,'python_ast':True,'java_php_go_rust_ruby_ast_lite':True,'external_parsers_runtime_checked':True,'heuristic_fallback_marked_candidate_only':True},'parser_backends':ps,'files':[],'imports':[],'exports':[],'symbols':[],'calls':[],'routes':[],'api_clients':[],'sinks':[],'authz_boundaries':[],'tenant_boundaries':[],'middleware_boundaries':[],'source_sink_paths':[],'frontend_backend_map_inputs':[],'parameters':[],'validators':[],'models':[],'queries':[],'responses':[],'route_to_handler_chains':[],'warnings':[]}
    for p in sorted(root.rglob('*')):
        if not p.is_file() or skip(p): continue
        suf=p.suffix.lower(); lang=LANG_EXT.get(suf)
        if not lang: continue
        rel=str(p.relative_to(root)); text=safe_read(p)
        out['files'].append({'path':rel,'language':lang,'suffix':suf,'size':len(text)})
        if suf=='.py':
            try:
                tree=ast.parse(text,filename=rel); v=PyVisitor(rel); v.visit(tree)
                out['imports']+=v.imports; out['symbols']+=v.symbols; out['calls']+=v.calls; out['routes']+=v.routes; out['authz_boundaries']+=v.authz; out['tenant_boundaries']+=v.tenant; out['middleware_boundaries']+=v.middleware
            except SyntaxError as e: out['warnings'].append(f'python_ast_failed {rel}: {e}')
        scan=scan_text(rel,text,suf,lang)
        for k,v in scan.items(): out.setdefault(k,[]); out[k]+=v
    merge_ts(out, ps.get('typescript_ast_result') or {})
    for k in ['imports','exports','symbols','calls','routes','api_clients','sinks','authz_boundaries','tenant_boundaries','middleware_boundaries','parameters','validators','models','queries','responses']:
        out[k]=dedupe(out.get(k,[]))
    for r in out['routes']:
        same_file = lambda arr: [x for x in arr if x.get('file') == r.get('file')]
        out['route_to_handler_chains'].append({
            'route': r,
            'handler': r.get('handler') or 'unresolved_handler_requires_parser_backend',
            'middleware': same_file(out.get('middleware_boundaries', [])),
            'authn': [x for x in same_file(out.get('authz_boundaries', [])) if re.search('auth|login|session|jwt', json.dumps(x), re.I)],
            'authz': same_file(out.get('authz_boundaries', [])),
            'validators': same_file(out.get('validators', [])),
            'parameters': same_file(out.get('parameters', [])),
            'models': same_file(out.get('models', [])),
            'queries': same_file(out.get('queries', [])),
            'sinks': same_file(out.get('sinks', [])),
            'responses': same_file(out.get('responses', [])),
            'evidence': {'file': r.get('file'), 'line': r.get('line'), 'parser_confidence': r.get('parser_confidence')},
            'claim_policy': 'Route→Handler→Middleware→AuthN→AuthZ→Validator→Parameter→Model→Query→Sink→Response candidate graph; dynamic evidence required for confirmed findings'
        })
        for s in out['sinks']:
            if r.get('file')==s.get('file'):
                out['source_sink_paths'].append({'route':r,'sink':s,'edge_type':'same_file_candidate','confirmation_policy':'candidate only; requires non-destructive dynamic evidence and negative control'})
        for b in out['authz_boundaries']+out['tenant_boundaries']+out['middleware_boundaries']:
            if r.get('file')==b.get('file'):
                out.setdefault('route_boundary_paths',[]).append({'route':r,'boundary':b,'confirmation_policy':'guard presence does not prove authorization correctness'})
    for a in out['api_clients']: out['frontend_backend_map_inputs'].append({'api_client':a,'backend_route_match_required':True,'quality_gate':'unmapped_frontend_api_cannot_confirm'})
    build_schema_graph(out)
    out['edge_count']=len(out['edges']); out['node_count']=len(out['nodes']); out['route_count']=len(out['routes']); out['sink_count']=len(out['sinks']); out['parameter_count']=len(out.get('parameters',[])); out['route_chain_count']=len(out.get('route_to_handler_chains',[]))
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('root'); ap.add_argument('-o','--output'); ap.add_argument('--check-plugins',action='store_true')
    args=ap.parse_args(); data=plugin_status(Path(args.root).resolve()) if args.check_plugins else extract(Path(args.root))
    text=json.dumps(data,ensure_ascii=False,indent=2)
    if args.output: Path(args.output).parent.mkdir(parents=True,exist_ok=True); Path(args.output).write_text(text+'\n',encoding='utf-8')
    else: print(text)
if __name__=='__main__': main()

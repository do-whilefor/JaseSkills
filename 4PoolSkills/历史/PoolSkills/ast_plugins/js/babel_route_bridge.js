#!/usr/bin/env node
'use strict';
const fs = require('fs');
const path = require('path');
function emit(obj){ console.log(JSON.stringify(obj, null, 2)); }
function fail(msg, file){ emit({schema_version:'phase4-security-graph-v2', status:'missing', plugin:'babel_js', file, error:String(msg), nodes:[], edges:[]}); process.exit(0); }
function fallbackScan(file, reason){
  const code = fs.readFileSync(file, 'utf8');
  const nodes=[]; const edges=[]; const seen=new Set();
  function addNode(type,id,props={}){ const k=type+'|'+id; if(!seen.has(k)){seen.add(k); nodes.push({id,type,file,...props});} return id; }
  function addEdge(from,to,type){ if(from&&to) edges.push({from,to,type}); }
  const routeRx=/(?:app|router|server)\.(get|post|put|patch|delete|head|options|all)\s*\(\s*['\"]([^'\"]+)['\"]([\s\S]{0,250})/ig;
  let m;
  while((m=routeRx.exec(code))){
    const method=m[1].toUpperCase(), route=m[2]; const line=code.slice(0,m.index).split('\n').length;
    const rid=addNode('route', `${file}:${method} ${route}`, {method, route, framework_hint:'regex_fallback', line});
    const hid=addNode('handler', `${file}:handler:${m.index}`, {name:'regex_handler', line}); addEdge(rid,hid,'ROUTE_TO_HANDLER');
    if(/auth|session|jwt|token/i.test(m[3])) addEdge(hid, addNode('authn', `${hid}:authn`, {name:'regex_authn_signal'}), 'ENFORCES_AUTHN');
    if(/admin|role|permission|tenant|policy|guard/i.test(m[3])) addEdge(hid, addNode('authz', `${hid}:authz`, {name:'regex_authz_signal'}), 'ENFORCES_AUTHZ');
    (route.match(/[:{<]([A-Za-z_][A-Za-z0-9_]*)/g)||[]).forEach(tok=>{ const name=tok.replace(/^[:{<]/,'').replace(/[}>]$/,''); addEdge(rid, addNode('parameter', `${rid}:param:${name}`, {name}), 'READS_PARAMETER'); });
  }
  const clientRx=/(fetch|axios\.(?:get|post|put|patch|delete)|api\.(?:get|post|put|patch|delete)|client\.(?:get|post|put|patch|delete))\s*\(\s*['\"]([^'\"]+)['\"]/ig;
  while((m=clientRx.exec(code))){ const method=(m[1].split('.')[1]||'GET').toUpperCase(); const id=addNode('api_client', `${file}:${method} ${m[2]}:${m.index}`, {method,url:m[2],client:m[1]}); addEdge(addNode('module', `${file}:module`, {path:file}), id, 'DECLARES_API_CLIENT'); }
  const gqlRx=/(gql`|graphql\s*\()/ig; while((m=gqlRx.exec(code))){ const id=addNode('graphql_operation', `${file}:graphql:${m.index}`, {operation:'regex_graphql_signal'}); addEdge(addNode('module', `${file}:module`, {path:file}), id, 'DECLARES_GRAPHQL_OPERATION'); }
  emit({schema_version:'phase4-security-graph-v2', status:'degraded', plugin:'babel_js', parser_mode:'regex_fallback', fallback_reason:reason, candidate_status:'needs_review', degraded_reason:'missing Babel parser/traverse; regex fallback cannot confirm vulnerabilities', file, nodes, edges, capabilities:['regex_fallback_routes','api_client_strings','graphql_signal']}); process.exit(0);
}
let parser, traverse;
const file = process.argv[2];
if (!file || !fs.existsSync(file)) fail('missing input file', file || null);
try {
  parser = require('@babel/parser');
  traverse = require('@babel/traverse').default;
} catch (e) { fallbackScan(file, 'missing @babel/parser or @babel/traverse: ' + e.message); }
const code = fs.readFileSync(file, 'utf8');
let ast;
try {
  ast = parser.parse(code, {
    sourceType: 'unambiguous',
    allowReturnOutsideFunction: true,
    plugins: [
      'typescript','jsx','decorators-legacy','classProperties','classPrivateProperties',
      'dynamicImport','importMeta','objectRestSpread','optionalChaining','nullishCoalescingOperator',
      'topLevelAwait'
    ]
  });
} catch (e) { fail('parse error: ' + e.message, file); }
const nodes=[]; const edges=[]; const seen=new Set();
function loc(node){ return node && node.loc ? {line: node.loc.start.line, column: node.loc.start.column} : {}; }
function addNode(type, id, props={}){
  const key=type+'|'+id;
  if(!seen.has(key)){ seen.add(key); nodes.push({id, type, file, ...props}); }
  return id;
}
function addEdge(from,to,type,props={}){ if(from && to) edges.push({from,to,type,...props}); }
function str(n){
  if(!n) return null;
  if(n.type==='StringLiteral' || n.type==='Literal') return String(n.value);
  if(n.type==='TemplateLiteral' && n.expressions.length===0) return n.quasis[0].value.cooked;
  if(n.type==='Identifier') return n.name;
  if(n.type==='MemberExpression') return str(n.object)+'.'+str(n.property);
  return null;
}
function calleeName(c){
  if(!c) return '';
  if(c.type==='Identifier') return c.name;
  if(c.type==='MemberExpression') return (calleeName(c.object)||'') + '.' + (str(c.property)||'');
  return '';
}
function fnName(n, fallback){ return n && (n.id?.name || n.key?.name || n.name) || fallback; }
const httpMethods = new Set(['get','post','put','patch','delete','head','options','all','use']);
const jsHttpClients = new Set(['fetch','axios','request','got','ky','superagent']);
function maybeAuthNodes(handlerId, name, node){
  const txt=(name||'') + ' ' + code.slice(node.start || 0, Math.min(code.length, (node.end||node.start||0)+400));
  if(/auth|login|session|jwt|token|passport|requireUser|ensureUser/i.test(txt)) addEdge(handlerId, addNode('authn', `${handlerId}:authn`, {name:'authn_signal'}), 'ENFORCES_AUTHN');
  if(/role|permission|policy|authorize|can\(|guard|admin|tenant|owner|rbac|abac/i.test(txt)) addEdge(handlerId, addNode('authz', `${handlerId}:authz`, {name:'authz_signal'}), 'ENFORCES_AUTHZ');
}
function addBackendRoute(method, route, node, handlerNode, framework='express_like'){
  const rid = addNode('route', `${file}:${method.toUpperCase()} ${route}`, {method:method.toUpperCase(), route, framework_hint:framework, ...loc(node)});
  const args = node.arguments || [];
  args.slice(1).forEach((arg, idx)=>{
    const isLast = idx === args.slice(1).length-1;
    const name = fnName(arg, arg.type==='ArrowFunctionExpression'?'inline_handler':`middleware_${idx}`);
    const kind = isLast ? 'handler' : 'middleware';
    const id = addNode(kind, `${file}:${name}:${node.start}:${idx}`, {name, ...loc(arg)});
    addEdge(rid, id, kind==='handler' ? 'ROUTE_TO_HANDLER' : 'USES_MIDDLEWARE');
    maybeAuthNodes(id, name, arg);
  });
  if(args.length===1 && handlerNode){
    const hid=addNode('handler', `${file}:${handlerNode}:${node.start}`, {name:handlerNode, ...loc(node)});
    addEdge(rid,hid,'ROUTE_TO_HANDLER'); maybeAuthNodes(hid, handlerNode, node);
  }
  (route.match(/[:{<]([A-Za-z_][A-Za-z0-9_]*)/g)||[]).forEach(tok=>{
    const name=tok.replace(/^[:{<]/,'').replace(/[}>]$/,'');
    addEdge(rid, addNode('parameter', `${rid}:param:${name}`, {name}), 'READS_PARAMETER');
  });
}
function addClientEndpoint(method, url, node, client='fetch'){
  const id = addNode('api_client', `${file}:${client}:${method.toUpperCase()} ${url}:${node.start}`, {method:method.toUpperCase(), url, client, ...loc(node)});
  addEdge(addNode('module', `${file}:module`, {path:file}), id, 'DECLARES_API_CLIENT');
  if(/\b(id|user|org|tenant|project|invoice|order|file|admin|role|permission)\b/i.test(url)){
    const obj=(url.match(/\b(user|org|tenant|project|invoice|order|file|admin|role|permission)s?\b/i)||[])[1] || 'business_object';
    addEdge(id, addNode('asset', `${file}:asset:${obj}`, {name:obj}), 'ACCESSES_ASSET');
  }
}
function objectPropValue(obj, keys){
  if(!obj || obj.type!=='ObjectExpression') return null;
  for(const p of obj.properties||[]){
    const k=str(p.key); if(keys.includes(k)) return str(p.value);
  }
  return null;
}
traverse(ast, {
  ImportDeclaration(p){
    const src=str(p.node.source); if(src){ addEdge(addNode('module', `${file}:module`, {path:file}), addNode('module', `${file}:import:${src}`, {imported:src}), 'IMPORTS'); }
  },
  ExportNamedDeclaration(p){
    // Next.js / Remix / route-handler method exports: export async function GET(req) {}
    const d=p.node.declaration;
    if(d && d.type==='FunctionDeclaration' && /^(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)$/.test(d.id?.name||'')){
      addBackendRoute(d.id.name, path.basename(file), d, d.id.name, 'next_route_handler');
    }
  },
  CallExpression(p){
    const n=p.node; const c=n.callee; const cname=calleeName(c);
    if(c && c.type==='MemberExpression'){
      const method=String(c.property?.name || c.property?.value || '').toLowerCase();
      if(httpMethods.has(method)){
        const route=str(n.arguments[0]);
        if(route && /^\//.test(route) && !/axios|fetch|request|got|ky|superagent/i.test(cname)) addBackendRoute(method, route, n, null, 'express_koa_fastify_nest_like');
      }
      // axios instance and request wrappers
      if(/\b(axios|client|api|request|http)\b/i.test(cname)){
        const m = httpMethods.has(method) ? method : (method==='request' ? (objectPropValue(n.arguments[0], ['method']) || 'GET') : null);
        const url = str(n.arguments[0]) || objectPropValue(n.arguments[0], ['url','path','endpoint']);
        if(m && url && /^\//.test(url)) addClientEndpoint(m, url, n, cname);
      }
    }
    if(c && c.type==='Identifier'){
      if(c.name==='fetch'){
        const url=str(n.arguments[0]);
        const m=objectPropValue(n.arguments[1], ['method']) || 'GET';
        if(url) addClientEndpoint(m, url, n, 'fetch');
      }
      if(c.name==='gql' || c.name==='graphql'){
        const q=str(n.arguments[0]);
        const id=addNode('graphql_operation', `${file}:graphql:${n.start}`, {operation:q ? q.slice(0,120) : 'unknown', ...loc(n)});
        addEdge(addNode('module', `${file}:module`, {path:file}), id, 'DECLARES_GRAPHQL_OPERATION');
      }
      if(c.name==='require'){
        const src=str(n.arguments[0]); if(src) addEdge(addNode('module', `${file}:module`, {path:file}), addNode('module', `${file}:require:${src}`, {imported:src}), 'IMPORTS');
      }
    }
    if(c && c.type==='Import'){
      const src=str(n.arguments[0]); if(src) addEdge(addNode('module', `${file}:module`, {path:file}), addNode('module', `${file}:dynamic_import:${src}`, {imported:src, dynamic:true}), 'DYNAMIC_IMPORTS');
    }
  },
  ObjectExpression(p){
    const route=objectPropValue(p.node, ['path','route']);
    const component=objectPropValue(p.node, ['component','name']);
    if(route && /^\//.test(route)){
      const rid=addNode('frontend_route', `${file}:frontend_route:${route}:${p.node.start}`, {route, component, framework_hint:'react_vue_angular_router', ...loc(p.node)});
      addEdge(addNode('module', `${file}:module`, {path:file}), rid, 'DECLARES_FRONTEND_ROUTE');
    }
  },
  TaggedTemplateExpression(p){
    const tag=calleeName(p.node.tag);
    if(/gql|graphql/i.test(tag)){
      const raw=(p.node.quasi.quasis||[]).map(q=>q.value.cooked).join('${}');
      const id=addNode('graphql_operation', `${file}:graphql:${p.node.start}`, {operation:raw.slice(0,160), ...loc(p.node)});
      addEdge(addNode('module', `${file}:module`, {path:file}), id, 'DECLARES_GRAPHQL_OPERATION');
    }
  }
});
emit({schema_version:'phase4-security-graph-v2', status:'ready', plugin:'babel_js', file, nodes, edges, capabilities:['express_like_routes','next_route_handlers','api_client_wrappers','fetch_axios_request','graphql_operations','dynamic_imports','frontend_routes','authn_authz_signals']});

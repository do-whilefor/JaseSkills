#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
function emit(obj){ console.log(JSON.stringify(obj, null, 2)); }
function fail(msg){ emit({status:'missing', plugin:'typescript_security_graph', backend:'typescript_compiler_api', real_ast:false, error:msg, nodes:[], edges:[]}); process.exit(0); }
let ts; try { ts = require('typescript'); } catch(e){ fail('missing typescript module: '+e.message); }
const file = process.argv[2];
if (!file || !fs.existsSync(file)) fail('missing input file');
const code = fs.readFileSync(file, 'utf8');
const ext = path.extname(file).toLowerCase();
const scriptKind = ext === '.tsx' ? ts.ScriptKind.TSX : ext === '.jsx' ? ts.ScriptKind.JSX : ext === '.ts' ? ts.ScriptKind.TS : ts.ScriptKind.JS;
const sf = ts.createSourceFile(file, code, ts.ScriptTarget.Latest, true, scriptKind);
const nodes=[]; const edges=[]; const seenNodes=new Set(); const seenEdges=new Set();
function loc(n){ const p=sf.getLineAndCharacterOfPosition(n.getStart(sf)); return {line:p.line+1, column:p.character+1}; }
function clean(s){ return String(s||'').replace(/^['"`]|['"`]$/g,''); }
function text(n){ try { return n.getText(sf); } catch(e) { return ''; } }
function node(type, id, props={}){ if(!seenNodes.has(id)){ seenNodes.add(id); nodes.push({id, type, file, ast_backend:'typescript_compiler_api', real_ast:true, ...props}); } return id; }
function edge(from,to,type,props={}){ const id=from+'|'+type+'|'+to; if(!seenEdges.has(id)){ seenEdges.add(id); edges.push({from,to,type, ast_backend:'typescript_compiler_api', real_ast:true, ...props}); } }
function strLit(n){
  if(!n) return null;
  if(ts.isStringLiteral(n) || ts.isNoSubstitutionTemplateLiteral(n)) return n.text;
  if(ts.isTemplateExpression(n)) return n.getText(sf);
  if(ts.isIdentifier(n)) return '${'+n.text+'}';
  return clean(text(n));
}
function propName(n){
  if(!n) return '';
  if(ts.isIdentifier(n)) return n.text;
  if(ts.isStringLiteral(n) || ts.isNumericLiteral(n)) return n.text;
  return clean(text(n));
}
function calleeName(expr){
  if(!expr) return '';
  if(ts.isIdentifier(expr)) return expr.text;
  if(ts.isPropertyAccessExpression(expr)) return calleeName(expr.expression)+'.'+expr.name.text;
  if(ts.isElementAccessExpression(expr)) return calleeName(expr.expression)+'['+text(expr.argumentExpression)+']';
  return text(expr);
}
function objectKeys(n){
  const out=[];
  if(n && ts.isObjectLiteralExpression(n)){
    for(const p of n.properties){
      if(ts.isPropertyAssignment(p)) out.push(propName(p.name));
      if(ts.isShorthandPropertyAssignment(p)) out.push(propName(p.name));
      if(ts.isSpreadAssignment(p)) out.push('...spread');
    }
  }
  return out;
}
function methodFromCall(name){
  const lower=name.toLowerCase();
  for(const m of ['get','post','put','patch','delete','head','options']){
    if(lower.endsWith('.'+m) || lower === m) return m.toUpperCase();
  }
  return null;
}
function routePathFromNextFile(){
  let normalized = file.replace(/\\/g,'/');
  let idx = normalized.indexOf('/app/api/');
  if(idx >= 0){
    let r = normalized.slice(idx + '/app/api'.length).replace(/\/route\.[jt]sx?$/,'');
    return r || '/';
  }
  idx = normalized.indexOf('/pages/api/');
  if(idx >= 0){
    let r = normalized.slice(idx + '/pages/api'.length).replace(/\.[jt]sx?$/,'');
    return r || '/';
  }
  return null;
}
function addParam(parentId, name, source, n){
  if(!name) return;
  const l=loc(n); const pid=node('parameter', `${parentId}:param:${source}:${name}`, {name, source, line:l.line, column:l.column});
  edge(parentId, pid, 'READS_PARAMETER', {source});
}
function scanRequestParam(parentId, n){
  const t=text(n);
  const patterns=[
    [/req\.query\.([A-Za-z0-9_$]+)/g,'query'],[/req\.params\.([A-Za-z0-9_$]+)/g,'path'],[/req\.body\.([A-Za-z0-9_$]+)/g,'body'],
    [/request\.query\.([A-Za-z0-9_$]+)/g,'query'],[/request\.params\.([A-Za-z0-9_$]+)/g,'path'],[/request\.body\.([A-Za-z0-9_$]+)/g,'body'],
    [/searchParams\.get\(['"`]([^'"`]+)['"`]\)/g,'query'],[/\.get\(['"`]([^'"`]+)['"`]\)/g,'getter']
  ];
  for(const [re,src] of patterns){ let m; while((m=re.exec(t)) !== null) addParam(parentId, m[1], src, n); }
}
function scanGraphQL(parentId, content, n){
  if(!content) return;
  const re=/(query|mutation|subscription)\s+([A-Za-z0-9_]+)?/g; let m;
  while((m=re.exec(content)) !== null){
    const l=loc(n); const gid=node('graphql_operation', `${file}:${l.line}:graphql:${m[1]}:${m[2]||'anonymous'}`, {operation:m[1], name:m[2]||'anonymous', line:l.line});
    edge(parentId, gid, 'DECLARES_GRAPHQL_OPERATION');
  }
}
function scanStorage(parentId, n){
  const t=text(n); const l=loc(n);
  const storageKinds=['localStorage','sessionStorage','indexedDB'];
  for(const k of storageKinds){
    if(t.includes(k)){
      const sid=node('browser_storage', `${file}:${l.line}:${k}`, {name:k, line:l.line, access:text(n).slice(0,240)});
      edge(parentId, sid, 'TOUCHES_BROWSER_STORAGE');
    }
  }
}
function addApiCall(call, parentId){
  const name=calleeName(call.expression); const args=Array.from(call.arguments || []); const l=loc(call);
  let url=null, method=null, headers=[], bodyParams=[], queryParams=[], pathParams=[];
  if(name === 'fetch' || name.endsWith('.fetch')){
    url=strLit(args[0]); method='GET';
    if(args[1] && ts.isObjectLiteralExpression(args[1])){
      for(const p of args[1].properties){
        if(ts.isPropertyAssignment(p)){
          const key=propName(p.name).toLowerCase();
          if(key === 'method') method=(strLit(p.initializer)||'GET').toUpperCase();
          if(key === 'headers') headers=objectKeys(p.initializer);
          if(key === 'body') bodyParams=objectKeys(p.initializer).concat((text(p.initializer).match(/[A-Za-z0-9_$]+/g)||[]).filter(x=>/id|tenant|org|role|user|owner|admin|debug|dryRun|preview|trace/i.test(x)));
        }
      }
    }
  } else if(/axios|ky|superagent|graphql|apollo|urql|client|api|request/i.test(name)){
    method = methodFromCall(name) || 'CALL'; url=strLit(args[0]);
    if(args[1]) bodyParams=objectKeys(args[1]);
    if(args[2] && ts.isObjectLiteralExpression(args[2])){
      for(const p of args[2].properties){ if(ts.isPropertyAssignment(p) && propName(p.name).toLowerCase()==='headers') headers=objectKeys(p.initializer); }
    }
  } else if(name === 'WebSocket' || name.endsWith('.WebSocket')){
    method='WEBSOCKET'; url=strLit(args[0]);
  }
  if(!url && method !== 'WEBSOCKET') return;
  const aid=node('api_call', `${file}:${l.line}:${method}:${url||name}`, {method, url:url||name, callee:name, line:l.line, column:l.column, headers, body_params:[...new Set(bodyParams)].filter(Boolean)});
  edge(parentId, aid, 'EMITS_REQUEST');
  const urlStr=String(url||'');
  for(const m of urlStr.matchAll(/[:{]([A-Za-z0-9_$]+)[}]?/g)) pathParams.push(m[1]);
  for(const m of urlStr.matchAll(/[?&]([A-Za-z0-9_$]+)=/g)) queryParams.push(m[1]);
  [...new Set(headers)].forEach(h=>{ const hid=node('header', `${aid}:header:${h}`, {name:h}); edge(aid,hid,'USES_HEADER'); });
  [...new Set(bodyParams)].filter(Boolean).forEach(p=>{ const pid=node('parameter', `${aid}:body:${p}`, {name:p, source:'body'}); edge(aid,pid,'SENDS_PARAMETER'); });
  [...new Set(queryParams)].forEach(p=>{ const pid=node('parameter', `${aid}:query:${p}`, {name:p, source:'query'}); edge(aid,pid,'SENDS_PARAMETER'); });
  [...new Set(pathParams)].forEach(p=>{ const pid=node('parameter', `${aid}:path:${p}`, {name:p, source:'path'}); edge(aid,pid,'SENDS_PARAMETER'); });
  scanGraphQL(aid, text(call), call);
}
function scanRoute(nodeDecl, name, decorators=[]){
  const l=loc(nodeDecl); let rid=null, route=null, method=null, framework=null;
  if(/^(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)$/.test(name)){
    method=name; route=routePathFromNextFile() || '/'; framework='next_route_handler';
  }
  for(const d of decorators){
    const dt=text(d); const m=dt.match(/@(Get|Post|Put|Patch|Delete|All)\s*\(([^)]*)\)/);
    if(m){ method=m[1].toUpperCase(); route=clean(m[2]||'/'); framework='nestjs'; }
  }
  if(!rid && method){
    rid=node('route', `${file}:${method}:${route}:${l.line}`, {method, route, framework, line:l.line, column:l.column});
    const hid=node('handler', `${file}:handler:${name}:${l.line}`, {name, line:l.line, column:l.column});
    edge(rid, hid, 'ROUTE_TO_HANDLER');
    for(const d of decorators){ const dt=text(d); if(/UseGuards|AuthGuard|Roles|Permissions|RequireAuth|auth/i.test(dt)){ const gid=node('guard', `${file}:${name}:guard:${dt.slice(0,80)}`, {decorator:dt}); edge(rid,gid,'USES_MIDDLEWARE'); edge(gid,node('authn',`${file}:${name}:authn`,{}),'ENFORCES_AUTHN'); } }
    scanRequestParam(rid, nodeDecl);
    return hid;
  }
  return null;
}
function currentOwner(stack){ return stack.length ? stack[stack.length-1] : node('module', file, {path:file}); }
const stack=[];
function walk(n){
  let ownerPushed=false;
  if(ts.isSourceFile(n)) { stack.push(node('module', file, {path:file})); ownerPushed=true; }
  if(ts.isFunctionDeclaration(n) && n.name){
    const h=scanRoute(n, n.name.text, Array.from(n.decorators||[]));
    stack.push(h || node('function', `${file}:function:${n.name.text}:${loc(n).line}`, {name:n.name.text, line:loc(n).line})); ownerPushed=true;
  }
  if(ts.isMethodDeclaration(n)){
    const nm=propName(n.name); const h=scanRoute(n, nm, Array.from(n.decorators||[]));
    stack.push(h || node('function', `${file}:method:${nm}:${loc(n).line}`, {name:nm, line:loc(n).line})); ownerPushed=true;
  }
  if(ts.isVariableDeclaration(n) && n.name && (ts.isArrowFunction(n.initializer)||ts.isFunctionExpression(n.initializer))){
    const nm=propName(n.name); stack.push(node('function', `${file}:function:${nm}:${loc(n).line}`, {name:nm, line:loc(n).line})); ownerPushed=true;
  }
  if(ts.isCallExpression(n)){
    const parent=currentOwner(stack); addApiCall(n, parent); scanStorage(parent, n);
    const cname=calleeName(n.expression);
    if(cname==='import' || cname.endsWith('.import')){
      const target=strLit((n.arguments||[])[0]); const iid=node('dynamic_import', `${file}:${loc(n).line}:import:${target}`, {target, line:loc(n).line}); edge(parent,iid,'DYNAMIC_IMPORTS');
    }
    if(/serviceWorker\.register/.test(cname)){
      const target=strLit((n.arguments||[])[0]); const sw=node('service_worker_registration', `${file}:${loc(n).line}:serviceWorker:${target}`, {target, line:loc(n).line}); edge(parent,sw,'REGISTERS_SERVICE_WORKER');
    }
    if(/postMessage|BroadcastChannel|MessageChannel|MessagePort/.test(cname)){
      const mb=node('message_boundary', `${file}:${loc(n).line}:${cname}`, {callee:cname, line:loc(n).line}); edge(parent,mb,'CROSSES_MESSAGE_BOUNDARY');
    }
  }
  if(ts.isNewExpression(n)){
    const name=calleeName(n.expression); const parent=currentOwner(stack);
    if(name==='WebSocket') addApiCall(n, parent);
    if(/BroadcastChannel|MessageChannel/.test(name)){ const mb=node('message_boundary', `${file}:${loc(n).line}:${name}`, {callee:name, line:loc(n).line}); edge(parent,mb,'CROSSES_MESSAGE_BOUNDARY'); }
  }
  if(ts.isStringLiteral(n) || ts.isNoSubstitutionTemplateLiteral(n)) scanGraphQL(currentOwner(stack), n.text, n);
  ts.forEachChild(n, walk);
  if(ownerPushed) stack.pop();
}
walk(sf);
const nodeTypes=[...new Set(nodes.map(n=>n.type))]; const edgeTypes=[...new Set(edges.map(e=>e.type))];
emit({status:'ready', plugin:'typescript_security_graph', backend:'typescript_compiler_api', real_ast:true, file, nodes, edges, quality:{node_types:nodeTypes, edge_types:edgeTypes, has_api_call:nodeTypes.includes('api_call'), has_security_graph:edges.length>0}});

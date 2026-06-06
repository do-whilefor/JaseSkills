#!/usr/bin/env node
// TypeScript Compiler API semantic extraction backend. Default AST backend.
// It emits static call graph, simple interprocedural taint validation candidates, protocol clues and source/sink paths.
import fs from 'node:fs';
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
let ts;
try { ts = require('typescript'); } catch(e) { console.error('missing typescript'); process.exit(2); }
const file = process.argv[2];
const code = fs.readFileSync(file, 'utf8');
const kind = file.endsWith('.tsx') ? ts.ScriptKind.TSX : file.endsWith('.jsx') ? ts.ScriptKind.JSX : file.endsWith('.ts') ? ts.ScriptKind.TS : ts.ScriptKind.JS;
const sf = ts.createSourceFile(file, code, ts.ScriptTarget.Latest, true, kind);
const SOURCE_RE = /\b(location\.(hash|search|href)|document\.cookie|localStorage|sessionStorage|message\.data|event\.data|ev\.data|URLSearchParams|document\.URL|document\.referrer)\b/;
const SINK_RE = /\b(innerHTML|outerHTML|insertAdjacentHTML|document\.write|eval|Function|window\.open|location\.href|dangerouslySetInnerHTML|srcdoc)\b/;
const MAX_PATHS = 240;
const out = {status:'ready', backend:'typescript', backend_role:'default_ast_backend', file, imports: [], dynamicImports: [], calls: [], callGraphEdges: [], interproceduralCallEdges: [], propertyAccess: [], assignments: [], variableDeclarations: [], strings: [], endpoints: [], routes: [], interfaces: [], enums: [], graphql: [], websocket: [], postmessage: [], sources: [], sinks: [], authzTenantSignals: [], functionDefinitions: [], functionSinkParams: [], sourceSinkPaths: [], dataflowCandidates: [], taintSummary: {variables:0, direct_paths:0, interprocedural_paths:0}};
function line(n){ return sf.getLineAndCharacterOfPosition(n.getStart(sf)).line + 1; }
function text(n){ return n ? n.getText(sf).slice(0,2000) : ''; }
function name(n){
  if (!n) return '';
  if (ts.isIdentifier(n) || ts.isPrivateIdentifier(n)) return n.text;
  if (ts.isStringLiteral(n) || ts.isNoSubstitutionTemplateLiteral(n)) return n.text;
  if (ts.isPropertyAccessExpression(n)) return name(n.expression)+'.'+name(n.name);
  if (ts.isElementAccessExpression(n)) return name(n.expression)+'['+name(n.argumentExpression)+']';
  if (ts.isCallExpression(n)) return name(n.expression)+'()';
  return text(n).slice(0,160);
}
function functionName(n){
  if (n.name) return name(n.name);
  if (ts.isVariableDeclaration(n.parent) && n.parent.name) return name(n.parent.name);
  if (ts.isPropertyAssignment(n.parent) && n.parent.name) return name(n.parent.name);
  return 'anonymous@'+line(n);
}
function stringText(n){
  if (!n) return '';
  if (ts.isStringLiteral(n) || ts.isNoSubstitutionTemplateLiteral(n)) return n.text;
  if (ts.isTemplateExpression(n)) return n.head.text + n.templateSpans.map(s=>'${}'+s.literal.text).join('');
  if (ts.isBinaryExpression(n) && n.operatorToken.kind === ts.SyntaxKind.PlusToken) return stringText(n.left) + stringText(n.right);
  return '';
}
function endpointLike(value){ return typeof value === 'string' && (/^\/(api|admin|internal|graphql|tenant|org|refund|payment|ws|vnc|websockify)/.test(value) || /^https?:/.test(value) || /^wss?:/.test(value)); }
function routeLike(value){ return typeof value === 'string' && /^\/(admin|internal|debug|tenant|org|payment|refund|api|graphql|settings|users|orders|vnc|app)/.test(value); }
function pushEndpoint(n, kind, value, method='UNKNOWN', callee='') { if (endpointLike(value)) out.endpoints.push({line:line(n), kind, value, method, callee}); }
function pushRoute(n, kind, value){ if (routeLike(value)) out.routes.push({line:line(n), kind, value}); }
function containsSource(raw){ return SOURCE_RE.test(raw); }
function containsSink(raw){ return SINK_RE.test(raw); }
function paramNames(n){ return Array.from(n.parameters || []).map(p=>name(p.name)).filter(Boolean); }
function findFunctionRecord(fn){ return out.functionDefinitions.find(f => f.name === fn); }

function visit(n, fnStack=[]){
  let stack=fnStack;
  if (ts.isFunctionDeclaration(n) || ts.isMethodDeclaration(n) || ts.isArrowFunction(n) || ts.isFunctionExpression(n)) {
    let nm = functionName(n);
    const params=paramNames(n);
    out.functionDefinitions.push({name:nm, line:line(n), params, parent_function:fnStack[fnStack.length-1] || '<top>'});
    stack=[...fnStack, nm];
  }
  const current=stack[stack.length-1] || '<top>';
  if (ts.isImportDeclaration(n) && n.moduleSpecifier) out.imports.push({line:line(n), source:text(n.moduleSpecifier).replace(/^[`'"]|[`'"]$/g,'')});
  if (ts.isVariableDeclaration(n)) {
    const target=name(n.name); const src=text(n.initializer).slice(0,1000);
    out.variableDeclarations.push({line:line(n), target, source:src, function_scope:current, source_tainted:containsSource(src)});
  }
  if (ts.isCallExpression(n)) {
    const callee=name(n.expression); const args=Array.from(n.arguments || []).map(a=>text(a).slice(0,1000)); const first=stringText(n.arguments && n.arguments[0]);
    out.calls.push({line:line(n), callee, args, function_scope:current});
    out.callGraphEdges.push({from:current, to:callee, line:line(n), status:'ast-call-edge'});
    if (current !== '<top>') out.interproceduralCallEdges.push({caller:current, callee, line:line(n), args, status:'ast-interprocedural-call-edge'});
    if (/^(fetch|axios(\.|$)|XMLHttpRequest|request|get|post|put|patch|del|apiClient|client\.)/.test(callee)) {
      let method='UNKNOWN'; const m=callee.match(/\.(get|post|put|patch|delete)$/i); if (m) method=m[1].toUpperCase();
      const joined=args.join(' '); const mm=joined.match(/method\s*:\s*['"]([A-Z]+)['"]/i); if (mm) method=mm[1].toUpperCase();
      pushEndpoint(n,'network-call',first,method,callee);
    }
    if (callee === 'import') out.dynamicImports.push({line:line(n), source:first});
    if (/postMessage$/.test(callee)) out.postmessage.push({line:line(n), kind:'postMessage-call', target:text(n).slice(0,800)});
    if (/addEventListener$/.test(callee) && first === 'message') out.postmessage.push({line:line(n), kind:'message-handler', target:text(n).slice(0,800)});
  }
  if (ts.isNewExpression(n) && name(n.expression)==='WebSocket') { const v=stringText(n.arguments && n.arguments[0]); out.websocket.push({line:line(n), url:v}); pushEndpoint(n,'websocket',v,'WS','WebSocket'); }
  if (ts.isPropertyAccessExpression(n)) out.propertyAccess.push({line:line(n), value:name(n)});
  if (ts.isBinaryExpression(n) && n.operatorToken.kind === ts.SyntaxKind.EqualsToken) out.assignments.push({line:line(n), target:name(n.left), source:text(n.right).slice(0,1000), function_scope:current, source_tainted:containsSource(text(n.right))});
  if (ts.isStringLiteral(n) || ts.isNoSubstitutionTemplateLiteral(n)) { out.strings.push({line:line(n), value:n.text}); pushEndpoint(n,'string-literal', n.text); pushRoute(n,'string-literal', n.text); }
  if (ts.isTaggedTemplateExpression(n) && /gql|graphql/i.test(name(n.tag))) out.graphql.push({line:line(n), kind:'tagged-template', text:text(n.template).slice(0,1500)});
  if ((ts.isNoSubstitutionTemplateLiteral(n) || ts.isTemplateExpression(n)) && /\b(query|mutation|subscription)\b/.test(text(n))) out.graphql.push({line:line(n), kind:'template-operation', text:text(n).slice(0,1500)});
  if (ts.isInterfaceDeclaration(n)) out.interfaces.push({line:line(n), name:n.name.text, fields:n.members.map(m=>m.name ? text(m.name) : '').filter(Boolean)});
  if (ts.isEnumDeclaration(n)) out.enums.push({line:line(n), name:n.name.text, members:n.members.map(m=>text(m.name))});
  const raw=text(n);
  if (containsSource(raw)) out.sources.push({line:line(n), value:raw.slice(0,500), ast_kind:ts.SyntaxKind[n.kind], function_scope:current});
  if (containsSink(raw)) out.sinks.push({line:line(n), value:raw.slice(0,500), ast_kind:ts.SyntaxKind[n.kind], function_scope:current});
  if (/\b(role|permission|rbac|tenant|orgId|workspaceId|isAdmin|can[A-Z][A-Za-z0-9_]*|featureFlag|experiment|beta|preview)\b/.test(raw)) out.authzTenantSignals.push({line:line(n), value:raw.slice(0,500), ast_kind:ts.SyntaxKind[n.kind], function_scope:current});
  ts.forEachChild(n, child => visit(child, stack));
}
visit(sf);

// Function sink params: detect function parameters used in sink-bearing expression/body.
for (const fn of out.functionDefinitions) {
  const fnSinks = out.sinks.filter(s => s.function_scope === fn.name);
  for (const param of fn.params || []) {
    for (const sk of fnSinks) {
      if (new RegExp('\\b'+param.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')+'\\b').test(sk.value)) {
        out.functionSinkParams.push({function:fn.name, param, sink_line:sk.line, sink_value:sk.value, status:'ast-param-to-sink'});
      }
    }
  }
}

// Variable taint from declarations and assignments.
const taintedVars = new Map();
for (const d of [...out.variableDeclarations, ...out.assignments]) {
  if (d.source_tainted) taintedVars.set(d.target, {line:d.line, source:d.source, function_scope:d.function_scope});
}
let changed=true;
while (changed) {
  changed=false;
  for (const d of [...out.variableDeclarations, ...out.assignments]) {
    if (taintedVars.has(d.target)) continue;
    for (const [v,info] of taintedVars.entries()) {
      if (new RegExp('\\b'+v.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')+'\\b').test(d.source || '')) {
        taintedVars.set(d.target, {line:info.line, source:info.source, via:d.target, function_scope:d.function_scope}); changed=true; break;
      }
    }
  }
}
out.taintSummary.variables=taintedVars.size;
for (const [v,info] of taintedVars.entries()) out.dataflowCandidates.push({line:info.line, target:v, source:info.source, status:'ast-tainted-variable', function_scope:info.function_scope});

// Direct source/sink proximity remains candidate.
for (const s of out.sources) for (const t of out.sinks) if (out.sourceSinkPaths.length < MAX_PATHS && Math.abs(s.line-t.line) <= 50) { out.sourceSinkPaths.push({source_line:s.line, sink_line:t.line, status:'ast-proximity-candidate', reason:'same file AST source/sink proximity; not full DFG', source_function:s.function_scope, sink_function:t.function_scope}); out.taintSummary.direct_paths++; }

// Interprocedural path: tainted argument passed to a function parameter that reaches a sink.
for (const call of out.calls) {
  const sinks = out.functionSinkParams.filter(x => x.function === call.callee || call.callee.endsWith('.'+x.function));
  if (!sinks.length) continue;
  call.args.forEach((arg, idx) => {
    let taint=null;
    if (containsSource(arg)) taint={line:call.line, source:arg, mode:'direct-source-argument'};
    if (!taint) {
      for (const [v,info] of taintedVars.entries()) {
        if (new RegExp('\\b'+v.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')+'\\b').test(arg)) { taint={...info, mode:'tainted-variable-argument', variable:v}; break; }
      }
    }
    if (!taint) return;
    for (const sink of sinks) {
      const fn=findFunctionRecord(sink.function); const paramIndex=(fn?.params || []).indexOf(sink.param);
      if (paramIndex === idx || paramIndex < 0) {
        if (out.sourceSinkPaths.length < MAX_PATHS) out.sourceSinkPaths.push({source_line:taint.line, sink_line:sink.sink_line, call_line:call.line, status:'validated-interprocedural-ast-path', reason:'AST call argument maps tainted source/variable into callee parameter used by sink; still static, not runtime confirmed', source:taint.source, sink:sink.sink_value, caller:call.function_scope, callee:call.callee, param:sink.param});
        out.taintSummary.interprocedural_paths++;
      }
    }
  });
}
console.log(JSON.stringify(out));

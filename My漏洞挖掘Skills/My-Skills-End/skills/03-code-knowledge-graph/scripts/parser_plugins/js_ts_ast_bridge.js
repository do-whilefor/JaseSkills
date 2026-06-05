#!/usr/bin/env node
// Optional read-only TypeScript Compiler API bridge for code graph v2.
const fs = require('fs');
const path = require('path');
let ts;
try { ts = require('typescript'); } catch (e) { console.log(JSON.stringify({ready:false, backend:'typescript_compiler_api', reason:'typescript package not resolvable'})); process.exit(0); }
const root = path.resolve(process.argv[2] || '.');
const EXT = new Set(['.js','.jsx','.ts','.tsx','.mjs','.cjs']);
const out = {ready:true, backend:'typescript_compiler_api', routes:[], imports:[], exports:[], dynamic_imports:[], calls:[], functions:[], classes:[], api_clients:[], authz_boundaries:[], tenant_boundaries:[], sinks:[], edges:[]};
function skip(rel){ return rel.split(path.sep).some(x => ['node_modules','.git','vendor','__pycache__','.venv'].includes(x)); }
function walk(dir){ for (const name of fs.readdirSync(dir)) { const p=path.join(dir,name); const rel=path.relative(root,p); if (skip(rel)) continue; const st=fs.statSync(p); if (st.isDirectory()) walk(p); else if (EXT.has(path.extname(p))) parse(p, rel); } }
function lineOf(sf,node){ return sf.getLineAndCharacterOfPosition(node.getStart(sf)).line + 1; }
function snippet(sf,node){ return node.getText(sf).slice(0,160); }
function parse(p, rel){
  const text=fs.readFileSync(p,'utf8'); const sf=ts.createSourceFile(rel,text,ts.ScriptTarget.Latest,true,ts.ScriptKind.TSX);
  const localFuncs = new Set();
  function visit(node){
    if (ts.isImportDeclaration(node) && node.moduleSpecifier) out.imports.push({file:rel,module:node.moduleSpecifier.text,line:lineOf(sf,node),parser:'typescript_ast'});
    if (ts.isExportDeclaration(node) && node.moduleSpecifier) out.exports.push({file:rel,module:node.moduleSpecifier.text,line:lineOf(sf,node),parser:'typescript_ast'});
    if ((ts.isFunctionDeclaration(node) || ts.isMethodDeclaration(node)) && node.name) { const n=node.name.getText(sf); localFuncs.add(n); out.functions.push({file:rel,name:n,line:lineOf(sf,node),parser:'typescript_ast'}); }
    if (ts.isClassDeclaration(node) && node.name) out.classes.push({file:rel,name:node.name.text,line:lineOf(sf,node),parser:'typescript_ast'});
    if (ts.isCallExpression(node)) {
      const expr=node.expression.getText(sf); const args=node.arguments || []; const first=args[0]; const s=snippet(sf,node); const line=lineOf(sf,node);
      out.calls.push({file:rel,callee:expr,line,parser:'typescript_ast'});
      if (expr === 'import' && first && ts.isStringLiteralLike(first)) out.dynamic_imports.push({file:rel,module:first.text,line,parser:'typescript_ast'});
      if (/^(app|router)\.(get|post|put|patch|delete|options|head)$/.test(expr) && first && ts.isStringLiteralLike(first)) {
        const method=expr.split('.')[1].toUpperCase(); const handler=args[1] ? args[1].getText(sf).slice(0,80) : '';
        out.routes.push({file:rel,method,route:first.text,handler,line,parser:'typescript_ast'});
        out.edges.push({from:`route:${method} ${first.text}`,to:`handler:${handler}`,type:'route_to_handler',file:rel,parser:'typescript_ast'});
      }
      if (/^(fetch|request|axios\.(get|post|put|patch|delete)|client\.(get|post|put|patch|delete)|api\.(get|post|put|patch|delete))$/.test(expr)) out.api_clients.push({file:rel,client:expr,target:first ? first.getText(sf).slice(0,160) : '',line,parser:'typescript_ast'});
      if (/can\(|hasPermission|authorize|requireRole|isAdmin|guard|policy|acl|rbac|abac/i.test(s)) out.authz_boundaries.push({file:rel,line,snippet:s,parser:'typescript_ast'});
      if (/tenant|orgId|organization|workspaceId|tenant_id|org_id/i.test(s)) out.tenant_boundaries.push({file:rel,line,snippet:s,parser:'typescript_ast'});
      if (/exec|spawn|eval|Function|readFile|writeFile|createReadStream|createWriteStream|sequelize\.query|queryRaw|raw\(/i.test(s)) out.sinks.push({file:rel,line,sink_type:'js_ts_security_sink',snippet:s,parser:'typescript_ast'});
    }
    ts.forEachChild(node, visit);
  }
  visit(sf);
}
try { walk(root); } catch (e) { out.ready=false; out.reason=String(e && e.stack || e); }
console.log(JSON.stringify(out, null, 2));

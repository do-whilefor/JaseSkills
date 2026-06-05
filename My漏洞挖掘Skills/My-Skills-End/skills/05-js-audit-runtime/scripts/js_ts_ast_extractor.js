#!/usr/bin/env node
// Optional TypeScript Compiler API extractor. Read-only local analysis only.
const fs = require('fs');
const path = require('path');
let ts;
try { ts = require('typescript'); } catch (e) { console.log(JSON.stringify({ready:false, error:'typescript package not resolvable'})); process.exit(0); }
const root = path.resolve(process.argv[2] || '.');
const JS_EXT = new Set(['.js','.jsx','.ts','.tsx','.mjs','.cjs']);
const out = {ready:true, backend:'typescript_compiler_api', files:[], imports:[], exports:[], dynamic_imports:[], api_clients:[], graphql:[], post_message:[], realtime:[], functions:[]};
function walk(dir){
  for (const name of fs.readdirSync(dir)) {
    const p = path.join(dir,name); const rel = path.relative(root,p);
    if (rel.split(path.sep).some(x => ['node_modules','.git','vendor','__pycache__'].includes(x))) continue;
    const st = fs.statSync(p); if (st.isDirectory()) walk(p); else if (JS_EXT.has(path.extname(p))) parseFile(p, rel);
  }
}
function lineOf(sf,node){ return sf.getLineAndCharacterOfPosition(node.getStart(sf)).line + 1; }
function textOf(sf,node){ return node.getText(sf).slice(0,120); }
function parseFile(p, rel){
  const text = fs.readFileSync(p,'utf8'); const sf = ts.createSourceFile(rel, text, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
  out.files.push({file:rel, ast:true, size:text.length});
  function visit(node){
    if (ts.isImportDeclaration(node) && node.moduleSpecifier) out.imports.push({file:rel,module:node.moduleSpecifier.text,line:lineOf(sf,node),source:'typescript_ast'});
    if (ts.isExportDeclaration(node) && node.moduleSpecifier) out.exports.push({file:rel,module:node.moduleSpecifier.text,line:lineOf(sf,node),source:'typescript_ast'});
    if (ts.isFunctionDeclaration(node) && node.name) out.functions.push({file:rel,name:node.name.text,line:lineOf(sf,node),source:'typescript_ast'});
    if (ts.isCallExpression(node)) {
      const expr = node.expression.getText(sf);
      if (expr === 'import' && node.arguments[0] && ts.isStringLiteralLike(node.arguments[0])) out.dynamic_imports.push({file:rel,module:node.arguments[0].text,line:lineOf(sf,node),source:'typescript_ast'});
      if (expr === 'fetch' || expr.startsWith('axios.') || expr === 'request') {
        const a=node.arguments[0]; out.api_clients.push({file:rel,client:expr,target:a?textOf(sf,a):'',line:lineOf(sf,node),source:'typescript_ast'});
      }
      if (expr === 'postMessage' || textOf(sf,node).includes('addEventListener')) out.post_message.push({file:rel,line:lineOf(sf,node),source:'typescript_ast'});
    }
    if (ts.isNewExpression(node)) {
      const expr=node.expression.getText(sf); if (expr === 'WebSocket' || expr === 'EventSource') out.realtime.push({file:rel,type:expr,line:lineOf(sf,node),source:'typescript_ast'});
    }
    if (ts.isTaggedTemplateExpression(node) && node.tag.getText(sf).includes('gql')) out.graphql.push({file:rel,line:lineOf(sf,node),source:'typescript_ast',operation_or_fragment:'gql_template'});
    ts.forEachChild(node, visit);
  }
  visit(sf);
}
try { walk(root); } catch (e) { out.error = String(e && e.stack || e); }
console.log(JSON.stringify(out, null, 2));

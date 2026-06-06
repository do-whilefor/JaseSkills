#!/usr/bin/env node
// Optional @babel/parser extractor. It exits successfully with ready=false when the package is unavailable.
const fs = require('fs');
const path = require('path');
let parser, traverse;
try { parser = require('@babel/parser'); } catch (e) { console.log(JSON.stringify({ready:false, backend:'babel_parser', reason:'@babel/parser package not resolvable'})); process.exit(0); }
try { traverse = require('@babel/traverse').default; } catch (e) { traverse = null; }
const root = path.resolve(process.argv[2] || '.');
const EXT = new Set(['.js','.jsx','.ts','.tsx','.mjs','.cjs']);
const out = {ready:true, backend:'babel_parser', files:[], imports:[], exports:[], dynamic_imports:[], api_clients:[], routes:[], wrapper_apis:[], graphql:[], websocket:[]};
function skip(rel){return rel.split(path.sep).some(x=>['node_modules','.git','vendor','__pycache__','.venv','dist','.next'].includes(x));}
function walk(d){for(const name of fs.readdirSync(d)){const p=path.join(d,name);const rel=path.relative(root,p); if(skip(rel)) continue; const st=fs.statSync(p); if(st.isDirectory()) walk(p); else if(EXT.has(path.extname(p))) parseFile(p,rel);}}
function loc(n){return (n && n.loc && n.loc.start && n.loc.start.line) || 1;}
function calleeName(c){ if(!c) return ''; if(c.type==='Identifier') return c.name; if(c.type==='MemberExpression') return calleeName(c.object)+'.'+calleeName(c.property); if(c.type==='ThisExpression') return 'this'; return c.type; }
function lit(n){ return n && (n.type==='StringLiteral' || n.type==='Literal') ? n.value : ''; }
function parseFile(p,rel){
 const src=fs.readFileSync(p,'utf8'); let ast; try{ast=parser.parse(src,{sourceType:'unambiguous',plugins:['typescript','jsx','dynamicImport','decorators-legacy','classProperties']});}catch(e){out.files.push({file:rel,parse_error:String(e.message||e)});return;}
 out.files.push({file:rel,ast:true,size:src.length});
 const visit={
  ImportDeclaration(x){out.imports.push({file:rel,module:x.node.source.value,line:loc(x.node),parser:'babel_parser'});},
  ExportNamedDeclaration(x){if(x.node.source) out.exports.push({file:rel,module:x.node.source.value,line:loc(x.node),parser:'babel_parser'});},
  CallExpression(x){const n=x.node; const name=calleeName(n.callee); const a=n.arguments||[]; const first=a[0]; const line=loc(n);
    if((name==='import' || (n.callee && n.callee.type==='Import')) && lit(first)) out.dynamic_imports.push({file:rel,module:lit(first),line,parser:'babel_parser'});
    if(/^(fetch|axios\.(get|post|put|patch|delete)|request|client\.(get|post|put|patch|delete)|api\.(get|post|put|patch|delete))$/.test(name)) out.api_clients.push({file:rel,client:name,target:lit(first) || (first?src.slice(first.start,first.end).slice(0,160):''),line,parser:'babel_parser'});
    if(/^(app|router)\.(get|post|put|patch|delete|options|head)$/.test(name) && lit(first)) out.routes.push({file:rel,method:name.split('.')[1].toUpperCase(),route:lit(first),line,parser:'babel_parser'});
    if(/graphql|gql|Apollo|urql/i.test(name) || /query\s*\{|mutation\s*\{|subscription\s*\{/.test(src.slice(n.start,n.end))) out.graphql.push({file:rel,line,client:name,parser:'babel_parser'});
    if(/WebSocket|socket\.emit|socket\.on|send\(/.test(name)) out.websocket.push({file:rel,line,client:name,parser:'babel_parser'});
  },
  FunctionDeclaration(x){ const body=src.slice(x.node.start,x.node.end); if(/fetch\(|axios\.|request\(/.test(body) && x.node.id) out.wrapper_apis.push({file:rel,name:x.node.id.name,line:loc(x.node),wraps:'network_client',parser:'babel_parser'}); }
 };
 if(traverse) traverse(ast, visit);
}
try { walk(root); } catch(e) { out.ready=false; out.reason=String(e && e.stack || e); }
console.log(JSON.stringify(out,null,2));

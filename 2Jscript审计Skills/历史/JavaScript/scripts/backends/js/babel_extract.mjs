#!/usr/bin/env node
// Optional AST backend. ESM-safe: no CommonJS `require` in .mjs.
import fs from 'node:fs';
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
let parser;
try { parser = require('@babel/parser'); } catch (e) { console.error('missing @babel/parser'); process.exit(2); }
const file = process.argv[2];
const code = fs.readFileSync(file, 'utf8');
let ast;
try {
  ast = parser.parse(code, {sourceType: 'unambiguous', plugins: ['typescript','jsx','dynamicImport','classProperties','decorators-legacy','optionalChaining','nullishCoalescingOperator']});
} catch (e) {
  console.error(e.message); process.exit(3);
}
const out = {status:'ready', backend:'babel', file, imports: [], calls: [], memberWrites: [], strings: [], endpoints: [], dynamicImports: [], graphql: [], websocket: []};
function loc(n){ return n && n.loc ? n.loc.start.line : null; }
function nameOf(n){
  if (!n) return '';
  if (n.type === 'Identifier') return n.name;
  if (n.type === 'StringLiteral') return n.value;
  if (n.type === 'TemplateLiteral') return n.quasis.map(q=>q.value.cooked || '').join('${}');
  if (n.type === 'MemberExpression') return nameOf(n.object)+'.'+nameOf(n.property);
  if (n.type === 'CallExpression') return nameOf(n.callee)+'()';
  return n.type;
}
function stringValue(n){
  if (!n) return '';
  if (n.type === 'StringLiteral') return n.value;
  if (n.type === 'TemplateLiteral') return n.quasis.map(q=>q.value.cooked || '').join('${}');
  if (n.type === 'BinaryExpression' && n.operator === '+') return stringValue(n.left) + stringValue(n.right);
  return '';
}
function pushEndpoint(n, kind, value){
  if (typeof value === 'string' && (/^\/(api|admin|internal|graphql|tenant|org|refund|payment|ws)/.test(value) || /^wss?:/.test(value))) out.endpoints.push({line:loc(n), kind, value});
}
function walk(n){
  if (!n || typeof n !== 'object') return;
  if (n.type === 'ImportDeclaration') out.imports.push({line: loc(n), source: n.source && n.source.value});
  if (n.type === 'ImportExpression') { const v=stringValue(n.source); out.dynamicImports.push({line:loc(n), source:v}); }
  if (n.type === 'CallExpression') {
    const callee = nameOf(n.callee);
    out.calls.push({line: loc(n), callee});
    if (/^(fetch|axios|get|post|put|patch|del|request|apiClient)/.test(callee)) pushEndpoint(n, 'network-call', stringValue(n.arguments && n.arguments[0]));
    if (callee === 'gql' || callee.endsWith('.gql')) out.graphql.push({line:loc(n), text:stringValue(n.arguments && n.arguments[0]).slice(0,500)});
  }
  if (n.type === 'NewExpression' && nameOf(n.callee) === 'WebSocket') {
    const v=stringValue(n.arguments && n.arguments[0]); out.websocket.push({line:loc(n), url:v}); pushEndpoint(n,'websocket',v);
  }
  if (n.type === 'AssignmentExpression' && n.left && n.left.type === 'MemberExpression') out.memberWrites.push({line: loc(n), target: nameOf(n.left)});
  if (n.type === 'StringLiteral') pushEndpoint(n, 'string-literal', n.value);
  if (n.type === 'TemplateLiteral') pushEndpoint(n, 'template-literal', stringValue(n));
  for (const k of Object.keys(n)) {
    if (['loc','start','end','extra'].includes(k)) continue;
    const v = n[k];
    if (Array.isArray(v)) v.forEach(walk); else walk(v);
  }
}
walk(ast.program);
console.log(JSON.stringify(out));

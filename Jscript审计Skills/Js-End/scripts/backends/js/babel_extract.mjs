#!/usr/bin/env node
// Optional AST backend. It is only ready when @babel/parser is installed in the local runtime.
const fs = require('fs');
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
const out = {file, imports: [], calls: [], memberWrites: [], strings: []};
function loc(n){ return n && n.loc ? n.loc.start.line : null; }
function nameOf(n){
  if (!n) return '';
  if (n.type === 'Identifier') return n.name;
  if (n.type === 'StringLiteral') return n.value;
  if (n.type === 'MemberExpression') return nameOf(n.object)+'.'+nameOf(n.property);
  if (n.type === 'CallExpression') return nameOf(n.callee)+'()';
  return n.type;
}
function walk(n){
  if (!n || typeof n !== 'object') return;
  if (n.type === 'ImportDeclaration') out.imports.push({line: loc(n), source: n.source && n.source.value});
  if (n.type === 'CallExpression') out.calls.push({line: loc(n), callee: nameOf(n.callee)});
  if (n.type === 'AssignmentExpression' && n.left && n.left.type === 'MemberExpression') out.memberWrites.push({line: loc(n), target: nameOf(n.left)});
  if (n.type === 'StringLiteral' && typeof n.value === 'string' && /^\/(api|admin|internal|graphql|tenant|org|refund|payment)/.test(n.value)) out.strings.push({line: loc(n), value: n.value});
  for (const k of Object.keys(n)) {
    if (['loc','start','end','extra'].includes(k)) continue;
    const v = n[k];
    if (Array.isArray(v)) v.forEach(walk); else walk(v);
  }
}
walk(ast.program);
console.log(JSON.stringify(out));

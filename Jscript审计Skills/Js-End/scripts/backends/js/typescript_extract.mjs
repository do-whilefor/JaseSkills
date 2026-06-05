#!/usr/bin/env node
// Optional TypeScript Compiler API backend. Ready only when `typescript` is installed locally.
const fs = require('fs');
let ts;
try { ts = require('typescript'); } catch(e) { console.error('missing typescript'); process.exit(2); }
const file = process.argv[2];
const code = fs.readFileSync(file, 'utf8');
const kind = file.endsWith('.tsx') ? ts.ScriptKind.TSX : file.endsWith('.jsx') ? ts.ScriptKind.JSX : file.endsWith('.ts') ? ts.ScriptKind.TS : ts.ScriptKind.JS;
const sf = ts.createSourceFile(file, code, ts.ScriptTarget.Latest, true, kind);
const out = {file, imports: [], calls: [], propertyAccess: [], strings: []};
function line(n){ return sf.getLineAndCharacterOfPosition(n.getStart(sf)).line + 1; }
function text(n){ return n.getText(sf).slice(0,240); }
function visit(n){
  if (ts.isImportDeclaration(n) && n.moduleSpecifier) out.imports.push({line:line(n), source:text(n.moduleSpecifier).replace(/^['"]|['"]$/g,'')});
  if (ts.isCallExpression(n)) out.calls.push({line:line(n), callee:text(n.expression)});
  if (ts.isPropertyAccessExpression(n)) out.propertyAccess.push({line:line(n), value:text(n)});
  if (ts.isStringLiteral(n) && /^\/(api|admin|internal|graphql|tenant|org|refund|payment)/.test(n.text)) out.strings.push({line:line(n), value:n.text});
  ts.forEachChild(n, visit);
}
visit(sf);
console.log(JSON.stringify(out));

#!/usr/bin/env node
const fs = require('fs');
let ts;
try { ts = require('typescript'); } catch (e) {
  console.error('typescript module missing');
  process.exit(2);
}
const file = process.argv[2];
const source = fs.readFileSync(file, 'utf8');
const sf = ts.createSourceFile(file, source, ts.ScriptTarget.Latest, true, file.endsWith('.tsx') ? ts.ScriptKind.TSX : ts.ScriptKind.TS);
const lineOf = (node) => sf.getLineAndCharacterOfPosition(node.getStart(sf)).line + 1;
function nameOf(node) {
  if (node.name && node.name.getText) return node.name.getText(sf);
  const text = node.getText(sf).slice(0, 200);
  const m = text.match(/([A-Za-z_$][A-Za-z0-9_$]*)\s*\(/);
  return m ? m[1] : '<anonymous>';
}
const out = {status:'parsed', parser:'typescript.compiler_api', functions:[], classes:[], calls:[], imports:[], errors:[]};
function walk(node) {
  if (ts.isFunctionDeclaration(node) || ts.isMethodDeclaration(node) || ts.isArrowFunction(node) || ts.isFunctionExpression(node)) {
    out.functions.push({name:nameOf(node), line:lineOf(node), end_line:sf.getLineAndCharacterOfPosition(node.end).line+1, kind:ts.SyntaxKind[node.kind]});
  }
  if (ts.isClassDeclaration(node)) out.classes.push({name:nameOf(node), line:lineOf(node), end_line:sf.getLineAndCharacterOfPosition(node.end).line+1, kind:'ClassDeclaration'});
  if (ts.isCallExpression(node)) out.calls.push({name:node.expression.getText(sf).slice(0,200), line:lineOf(node), kind:'CallExpression'});
  if (ts.isImportDeclaration(node)) out.imports.push({name:node.moduleSpecifier.getText(sf).replace(/^['"]|['"]$/g,''), line:lineOf(node), kind:'ImportDeclaration'});
  ts.forEachChild(node, walk);
}
walk(sf);
console.log(JSON.stringify(out));

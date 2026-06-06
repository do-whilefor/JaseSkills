#!/usr/bin/env node
// Optional TypeScript Compiler API backend. ESM-safe: no CommonJS `require` in .mjs.
import fs from 'node:fs';
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
let ts;
try { ts = require('typescript'); } catch(e) { console.error('missing typescript'); process.exit(2); }
const file = process.argv[2];
const code = fs.readFileSync(file, 'utf8');
const kind = file.endsWith('.tsx') ? ts.ScriptKind.TSX : file.endsWith('.jsx') ? ts.ScriptKind.JSX : file.endsWith('.ts') ? ts.ScriptKind.TS : ts.ScriptKind.JS;
const sf = ts.createSourceFile(file, code, ts.ScriptTarget.Latest, true, kind);
const out = {status:'ready', backend:'typescript', file, imports: [], calls: [], propertyAccess: [], strings: [], endpoints: [], interfaces: [], enums: []};
function line(n){ return sf.getLineAndCharacterOfPosition(n.getStart(sf)).line + 1; }
function text(n){ return n.getText(sf).slice(0,500); }
function stringText(n){
  if (!n) return '';
  if (ts.isStringLiteral(n) || ts.isNoSubstitutionTemplateLiteral(n)) return n.text;
  if (ts.isTemplateExpression(n)) return n.head.text + n.templateSpans.map(s=>'${}'+s.literal.text).join('');
  if (ts.isBinaryExpression(n) && n.operatorToken.kind === ts.SyntaxKind.PlusToken) return stringText(n.left) + stringText(n.right);
  return '';
}
function endpoint(n, kind, value){ if (value && (/^\/(api|admin|internal|graphql|tenant|org|refund|payment|ws)/.test(value) || /^wss?:/.test(value))) out.endpoints.push({line:line(n), kind, value}); }
function visit(n){
  if (ts.isImportDeclaration(n) && n.moduleSpecifier) out.imports.push({line:line(n), source:text(n.moduleSpecifier).replace(/^['"]|['"]$/g,'')});
  if (ts.isCallExpression(n)) {
    const callee=text(n.expression); out.calls.push({line:line(n), callee});
    if (/^(fetch|axios|get|post|put|patch|del|request|apiClient)/.test(callee)) endpoint(n,'network-call',stringText(n.arguments[0]));
  }
  if (ts.isNewExpression(n) && text(n.expression)==='WebSocket') endpoint(n,'websocket',stringText(n.arguments && n.arguments[0]));
  if (ts.isPropertyAccessExpression(n)) out.propertyAccess.push({line:line(n), value:text(n)});
  if (ts.isStringLiteral(n) || ts.isNoSubstitutionTemplateLiteral(n)) endpoint(n,'string-literal', n.text);
  if (ts.isInterfaceDeclaration(n)) out.interfaces.push({line:line(n), name:n.name.text, fields:n.members.map(m=>m.name ? text(m.name) : '').filter(Boolean)});
  if (ts.isEnumDeclaration(n)) out.enums.push({line:line(n), name:n.name.text, members:n.members.map(m=>text(m.name))});
  ts.forEachChild(n, visit);
}
visit(sf);
console.log(JSON.stringify(out));

#!/usr/bin/env node
/*
 * Authorized local-only JS endpoint extractor.
 * Uses @babel/parser when available and performs a small AST walk for CallExpression/NewExpression.
 * If parser is unavailable it falls back to lexical extraction and marks every record accordingly.
 * Candidate output is not a confirmed vulnerability finding.
 */
import fs from 'fs';
import path from 'path';
import { createRequire } from 'module';
const require = createRequire(import.meta.url);

function parseArgs(argv) {
  const args = { root: null, out: '-', strictAst: false, includeHtml: true };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === '-o' || a === '--out') args.out = argv[++i];
    else if (a === '--strict-ast') args.strictAst = true;
    else if (a === '--no-html') args.includeHtml = false;
    else if (!args.root) args.root = a;
  }
  if (!args.root) {
    console.error('usage: node scripts/js-ast-endpoint-extractor.mjs <project-root> [-o out.jsonl] [--strict-ast]');
    process.exit(2);
  }
  return args;
}

function tryLoadBabelParser() {
  try { return require('@babel/parser'); } catch (_) { return null; }
}

function walk(root, acc = []) {
  for (const name of fs.readdirSync(root, { withFileTypes: true })) {
    const p = path.join(root, name.name);
    if (name.isDirectory()) {
      if (['node_modules', '.git', 'dist', 'build', '.next', '.nuxt', 'coverage', '.pytest_cache'].includes(name.name)) continue;
      walk(p, acc);
    } else if (/\.(mjs|cjs|js|jsx|ts|tsx|vue|svelte|html)$/i.test(name.name)) {
      acc.push(p);
    }
  }
  return acc;
}

function lineOf(content, index) { return content.slice(0, index).split(/\r?\n/).length; }
function locLine(node, fallbackContent, fallbackIndex) { return node?.loc?.start?.line || lineOf(fallbackContent, fallbackIndex || 0); }
function simpleHash(s) { let h = 2166136261; for (let i = 0; i < s.length; i++) h = Math.imul(h ^ s.charCodeAt(i), 16777619); return ('00000000' + (h >>> 0).toString(16)).slice(-8); }

function detectContexts(snippet) {
  const auth = [], tenant = [];
  if (/Authorization|Bearer|csrf|xsrf|cookie|credentials\s*:/i.test(snippet)) auth.push('auth_material_or_header_reference');
  if (/localStorage|sessionStorage|IndexedDB|idb|getItem\(/i.test(snippet)) auth.push('browser_storage_token_source');
  if (/tenant|orgId|organization|workspace|accountId|projectId/i.test(snippet)) tenant.push('tenant_or_org_identifier_reference');
  if (/admin|role|permission|isAdmin|can\(/i.test(snippet)) auth.push('role_or_permission_reference');
  return { auth_context: auth, tenant_context: tenant };
}

function enclosingFunction(content, index) {
  const prefix = content.slice(Math.max(0, index - 2500), index);
  const patterns = [
    /function\s+([A-Za-z0-9_$]+)\s*\([^)]*\)\s*\{[^{}]*$/s,
    /(?:const|let|var)\s+([A-Za-z0-9_$]+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>[^{}]*$/s,
    /([A-Za-z0-9_$]+)\s*\([^)]*\)\s*\{[^{}]*$/s
  ];
  for (const re of patterns) { const m = prefix.match(re); if (m) return m[1]; }
  return null;
}

function literalValue(node, constants = {}) {
  if (!node) return null;
  if (node.type === 'StringLiteral' || node.type === 'Literal') return String(node.value);
  if (node.type === 'TemplateLiteral') {
    let parts = [];
    for (let i = 0; i < node.quasis.length; i++) {
      parts.push(node.quasis[i].value.cooked || node.quasis[i].value.raw || '');
      if (i < node.expressions.length) {
        const expr = node.expressions[i];
        if (expr.type === 'Identifier' && constants[expr.name]) parts.push(constants[expr.name]);
        else parts.push('${' + (expr.name || expr.type) + '}');
      }
    }
    return parts.join('');
  }
  if (node.type === 'Identifier' && constants[node.name]) return constants[node.name];
  if (node.type === 'BinaryExpression' && node.operator === '+') {
    const l = literalValue(node.left, constants), r = literalValue(node.right, constants);
    if (l !== null && r !== null) return l + r;
  }
  return null;
}

function memberName(node) {
  if (!node) return '';
  if (node.type === 'Identifier') return node.name;
  if (node.type === 'ThisExpression') return 'this';
  if (node.type === 'MemberExpression' || node.type === 'OptionalMemberExpression') {
    return memberName(node.object) + '.' + memberName(node.property);
  }
  return node.type || '';
}

function collectConstants(ast) {
  const constants = {};
  const axiosInstances = {};
  function visit(n) {
    if (!n || typeof n !== 'object') return;
    if (n.type === 'VariableDeclarator' && n.id?.type === 'Identifier') {
      const v = literalValue(n.init, constants);
      if (typeof v === 'string') constants[n.id.name] = v;
      if (n.init?.type === 'CallExpression' && memberName(n.init.callee) === 'axios.create') {
        const obj = n.init.arguments?.[0];
        if (obj?.type === 'ObjectExpression') {
          for (const prop of obj.properties || []) {
            const k = prop.key?.name || prop.key?.value;
            if (k === 'baseURL') axiosInstances[n.id.name] = literalValue(prop.value, constants) || '';
          }
        }
      }
    }
    for (const k of Object.keys(n)) {
      if (['loc','start','end'].includes(k)) continue;
      const v = n[k];
      if (Array.isArray(v)) v.forEach(visit); else if (v && typeof v === 'object') visit(v);
    }
  }
  visit(ast);
  return { constants, axiosInstances };
}

function recordCandidate({ rel, content, node, endpoint, method=null, sink, parserMode, functionName=null, confidence=0.82, idx=null }) {
  const start = node?.start ?? idx ?? 0;
  const snippet = content.slice(Math.max(0, start - 300), Math.min(content.length, start + 700));
  const ctx = detectContexts(snippet);
  return {
    type: 'js_ast_endpoint_candidate', backend: parserMode.startsWith('babel') ? 'babel_parser_ast_walk' : 'lexical_fallback', parser_mode: parserMode,
    source_file: rel, line: locLine(node, content, start), function_name: functionName || enclosingFunction(content, start),
    ast_node_type: node?.type || null, sink_type: sink, method, endpoint,
    auth_context: ctx.auth_context, tenant_context: ctx.tenant_context,
    evidence: { snippet_hash: simpleHash(snippet), snippet_preview: snippet.replace(/\s+/g, ' ').slice(0, 240), ast_node_type: node?.type || null },
    confidence, review_status: 'needs_review', limitation: parserMode === 'lexical_fallback' ? 'lexical fallback; verify wrapper/baseURL/source-map manually' : 'AST candidate; still requires auth/tenant replay before reportability'
  };
}

function extractAst(ast, content, rel) {
  const { constants, axiosInstances } = collectConstants(ast);
  const out = [];
  const fnStack = [];
  function currentFn(){ return fnStack.length ? fnStack[fnStack.length-1] : null; }
  function visit(n, parent=null) {
    if (!n || typeof n !== 'object') return;
    let pushed = false;
    if (['FunctionDeclaration','FunctionExpression','ArrowFunctionExpression','ObjectMethod','ClassMethod'].includes(n.type)) {
      fnStack.push(n.id?.name || parent?.id?.name || parent?.key?.name || null); pushed = true;
    }
    if (n.type === 'CallExpression' || n.type === 'OptionalCallExpression') {
      const callee = memberName(n.callee);
      const args = n.arguments || [];
      let endpoint = null, method = null, sink = null;
      if (callee.endsWith('fetch')) { endpoint = literalValue(args[0], constants); sink = 'fetch'; }
      else if (callee === 'axios' || callee.endsWith('.request')) { endpoint = literalValue(args[0], constants); sink = 'axios'; }
      else if (/\.open$/.test(callee) && args.length >= 2) { method = literalValue(args[0], constants); endpoint = literalValue(args[1], constants); sink = 'xhr_open'; }
      else if (/\.ajax$/.test(callee) && args[0]?.type === 'ObjectExpression') {
        sink = 'jquery_ajax';
        for (const p of args[0].properties || []) if ((p.key?.name || p.key?.value) === 'url') endpoint = literalValue(p.value, constants);
      } else {
        const m = callee.match(/^([A-Za-z0-9_$]+)\.(get|post|put|patch|delete|head|options)$/i);
        if (m) { method = m[2].toUpperCase(); endpoint = literalValue(args[0], constants); sink = 'axios_method_or_client_method'; if (axiosInstances[m[1]]) endpoint = axiosInstances[m[1]] + (endpoint || ''); }
      }
      if (endpoint) out.push(recordCandidate({ rel, content, node:n, endpoint, method, sink, parserMode:'babel_ast_walk', functionName:currentFn(), confidence:0.86 }));
    }
    if (n.type === 'NewExpression') {
      const callee = memberName(n.callee); const endpoint = literalValue(n.arguments?.[0], constants);
      if (endpoint && /WebSocket$/.test(callee)) out.push(recordCandidate({ rel, content, node:n, endpoint, sink:'websocket', parserMode:'babel_ast_walk', functionName:currentFn(), confidence:0.86 }));
      if (endpoint && /EventSource$/.test(callee)) out.push(recordCandidate({ rel, content, node:n, endpoint, sink:'eventsource', parserMode:'babel_ast_walk', functionName:currentFn(), confidence:0.86 }));
    }
    if (n.type === 'TaggedTemplateExpression') {
      const tag = memberName(n.tag); if (/gql|graphql/i.test(tag)) {
        const endpoint = literalValue(n.quasi, constants) || 'graphql_document';
        out.push(recordCandidate({ rel, content, node:n, endpoint, method:'GRAPHQL_DOCUMENT', sink:'graphql_literal', parserMode:'babel_ast_walk', functionName:currentFn(), confidence:0.70 }));
      }
    }
    for (const k of Object.keys(n)) { if (['loc','start','end'].includes(k)) continue; const v=n[k]; if (Array.isArray(v)) v.forEach(x=>visit(x,n)); else if (v && typeof v==='object') visit(v,n); }
    if (pushed) fnStack.pop();
  }
  visit(ast);
  return out;
}

function extractLexical(content, file, rel) {
  const out = [];
  const patterns = [
    { sink: 'fetch', re: /\bfetch\s*\(\s*([`'\"])([^`'\"]{1,500})\1/gi },
    { sink: 'axios', re: /\baxios(?:\.[a-z]+)?\s*\(\s*([`'\"])([^`'\"]{1,500})\1/gi },
    { sink: 'axios_method', re: /\baxios\.(get|post|put|patch|delete|head|options)\s*\(\s*([`'\"])([^`'\"]{1,500})\2/gi },
    { sink: 'xhr_open', re: /\.open\s*\(\s*([`'\"])(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\1\s*,\s*([`'\"])([^`'\"]{1,500})\3/gi },
    { sink: 'jquery_ajax', re: /\$\.ajax\s*\(\s*\{[\s\S]{0,400}?url\s*:\s*([`'\"])([^`'\"]{1,500})\1/gi },
    { sink: 'graphql_literal', re: /\b(query|mutation|subscription)\s+([A-Za-z0-9_]+)\s*[({]/g },
    { sink: 'websocket', re: /new\s+WebSocket\s*\(\s*([`'\"])([^`'\"]{1,500})\1/gi },
    { sink: 'eventsource', re: /new\s+EventSource\s*\(\s*([`'\"])([^`'\"]{1,500})\1/gi },
    { sink: 'grpc_web', re: /new\s+[A-Za-z0-9_$]*Client\s*\(\s*([`'\"])([^`'\"]{1,500})\1/gi }
  ];
  for (const p of patterns) {
    let m; while ((m = p.re.exec(content))) {
      let endpoint=null, method=null;
      if (p.sink === 'axios_method') { method=m[1].toUpperCase(); endpoint=m[3]; }
      else if (p.sink === 'xhr_open') { method=m[2].toUpperCase(); endpoint=m[4]; }
      else if (p.sink === 'graphql_literal') { method='GRAPHQL_'+m[1].toUpperCase(); endpoint=m[2]; }
      else { endpoint=m[2] || m[4] || m[1]; }
      out.push(recordCandidate({ rel, content, node:null, endpoint, method, sink:p.sink, parserMode:'lexical_fallback', idx:m.index, confidence:p.sink==='graphql_literal'?0.55:0.72 }));
    }
  }
  return out;
}

function parseWithBabel(parser, content) {
  return parser.parse(content, { sourceType:'unambiguous', plugins:['typescript','jsx','decorators-legacy','classProperties','dynamicImport'], errorRecovery:true, ranges:false });
}

function main() {
  const args=parseArgs(process.argv); const root=path.resolve(args.root); const parser=tryLoadBabelParser();
  if (args.strictAst && !parser) { console.error('strict AST requested but @babel/parser is not installed'); process.exit(3); }
  const records=[];
  for (const file of walk(root)) {
    const content=fs.readFileSync(file,'utf8'); const rel=path.relative(root,file).replace(/\\/g,'/');
    if (parser && !/\.html$/i.test(file)) {
      try { const ast=parseWithBabel(parser, content); records.push(...extractAst(ast, content, rel)); continue; }
      catch (e) { if (args.strictAst) { console.error(`AST parse failed for ${rel}: ${e.message}`); process.exit(4); } }
    }
    if (args.strictAst) continue;
    records.push(...extractLexical(content, file, rel));
  }
  const data=records.map(r=>JSON.stringify(r)).join('\n') + (records.length?'\n':'');
  if(args.out==='-') process.stdout.write(data); else fs.writeFileSync(args.out,data);
  console.error(`wrote ${records.length} JS endpoint candidates`);
}
main();

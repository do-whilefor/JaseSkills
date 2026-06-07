#!/usr/bin/env python3
"""Build a conservative local code graph for authorized audit candidates.

This is an evidence builder, not a vulnerability confirmer. It uses Python AST where
available and safe lexical recognizers for other languages. Output is JSON with
nodes/edges plus explicit parser_mode so downstream gates cannot confuse fallback
regex with true semantic analysis.
"""
from __future__ import annotations
import argparse, ast, json, re
from pathlib import Path
from typing import Any, Dict, List

SKIP_DIRS = {'.git','node_modules','dist','build','.next','.nuxt','coverage','__pycache__'}
PY_ROUTE_DECORATORS = {'route','get','post','put','patch','delete','head','options'}
JS_ROUTE_RE = re.compile(r"\b(?:router|app)\.(get|post|put|patch|delete|head|options|use)\s*\(\s*['\"]([^'\"]+)", re.I)
JAVA_ROUTE_RE = re.compile(r"@(GetMapping|PostMapping|PutMapping|PatchMapping|DeleteMapping|RequestMapping)\s*(?:\(\s*(?:value\s*=\s*)?['\"]([^'\"]+)['\"])?", re.I)
PHP_ROUTE_RE = re.compile(r"Route::(get|post|put|patch|delete|any)\s*\(\s*['\"]([^'\"]+)", re.I)
GO_ROUTE_RE = re.compile(r"\b(?:router|r|mux)\.(GET|POST|PUT|PATCH|DELETE|HandleFunc|Handle)\s*\(\s*['\"]([^'\"]+)", re.I)
RUST_ROUTE_RE = re.compile(r"#\[(get|post|put|patch|delete)\(\s*['\"]([^'\"]+)['\"]\s*\)\]", re.I)
SINK_RE = re.compile(r"\b(exec|spawn|system|popen|eval|Function|subprocess|os\.system|open\(|readFile|writeFile|query\(|findOne\(|requests\.|fetch\(|axios\.)", re.I)
AUTH_RE = re.compile(r"auth|jwt|session|permission|role|guard|policy|csrf|login_required|require_user|isAuthenticated|authorize", re.I)
TENANT_RE = re.compile(r"tenant|orgId|organization|workspace|accountId|projectId|ownerId", re.I)


def walk(root: Path):
    for p in root.rglob('*'):
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        if p.is_file() and p.suffix.lower() in {'.py','.js','.ts','.tsx','.jsx','.java','.php','.go','.rs','.rb'}:
            yield p


def add_node(nodes: List[Dict[str,Any]], **kw):
    kw.setdefault('id', f"N{len(nodes)+1:05d}")
    nodes.append(kw)
    return kw['id']


def parse_python(path: Path, root: Path, nodes, edges):
    rel = str(path.relative_to(root)).replace('\\','/')
    text = path.read_text(errors='ignore')
    try:
        tree = ast.parse(text)
        mode = 'python_ast'
    except SyntaxError:
        tree = None
        mode = 'python_ast_failed'
    if tree is None:
        return
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            fn_id = add_node(nodes, type='function', language='python', name=node.name, source_file=rel, line=node.lineno, parser_mode=mode)
            for dec in node.decorator_list:
                dec_txt = ast.unparse(dec) if hasattr(ast, 'unparse') else ''
                if any(f'.{m}' in dec_txt or dec_txt.endswith(m) for m in PY_ROUTE_DECORATORS):
                    path_lit = None
                    method = None
                    for m in PY_ROUTE_DECORATORS:
                        if f'.{m}' in dec_txt.lower() or dec_txt.lower().endswith(m): method = m.upper()
                    for child in ast.walk(dec):
                        if isinstance(child, ast.Constant) and isinstance(child.value, str) and child.value.startswith('/'):
                            path_lit = child.value
                            break
                    route_id = add_node(nodes, type='route', language='python', method=method, path=path_lit, source_file=rel, line=getattr(dec, 'lineno', node.lineno), parser_mode=mode)
                    edges.append({'from': route_id, 'to': fn_id, 'type': 'route_to_handler'})
            for child in ast.walk(node):
                if isinstance(child, ast.Call):
                    call = ast.unparse(child.func) if hasattr(ast,'unparse') else ''
                    if SINK_RE.search(call):
                        sink_id = add_node(nodes, type='sink', language='python', sink=call, source_file=rel, line=getattr(child,'lineno',node.lineno), parser_mode=mode)
                        edges.append({'from': fn_id, 'to': sink_id, 'type': 'handler_to_sink'})
                    if AUTH_RE.search(call):
                        auth_id = add_node(nodes, type='auth_reference', language='python', name=call, source_file=rel, line=getattr(child,'lineno',node.lineno), parser_mode=mode)
                        edges.append({'from': fn_id, 'to': auth_id, 'type': 'handler_to_auth_reference'})


def parse_lexical(path: Path, root: Path, nodes, edges):
    rel = str(path.relative_to(root)).replace('\\','/')
    text = path.read_text(errors='ignore')
    ext = path.suffix.lower()
    route_patterns = []
    lang = ext.lstrip('.')
    if ext in {'.js','.jsx','.ts','.tsx'}: route_patterns = [('js_lexical', JS_ROUTE_RE)]
    elif ext == '.java': route_patterns = [('java_annotation_lexical', JAVA_ROUTE_RE)]
    elif ext == '.php': route_patterns = [('php_route_lexical', PHP_ROUTE_RE)]
    elif ext == '.go': route_patterns = [('go_route_lexical', GO_ROUTE_RE)]
    elif ext == '.rs': route_patterns = [('rust_route_lexical', RUST_ROUTE_RE)]
    for mode, rx in route_patterns:
        for m in rx.finditer(text):
            line = text[:m.start()].count('\n') + 1
            method, pth = (m.group(1).upper(), m.group(2) if len(m.groups()) >= 2 else None)
            route_id = add_node(nodes, type='route', language=lang, method=method, path=pth, source_file=rel, line=line, parser_mode=mode)
            snippet = text[m.start():m.start()+500]
            if AUTH_RE.search(snippet):
                auth_id = add_node(nodes, type='auth_reference', language=lang, name='nearby_auth_keyword', source_file=rel, line=line, parser_mode=mode)
                edges.append({'from': route_id, 'to': auth_id, 'type': 'route_to_auth_reference'})
            if TENANT_RE.search(snippet):
                ten_id = add_node(nodes, type='tenant_reference', language=lang, name='nearby_tenant_keyword', source_file=rel, line=line, parser_mode=mode)
                edges.append({'from': route_id, 'to': ten_id, 'type': 'route_to_tenant_reference'})
    for m in SINK_RE.finditer(text):
        line = text[:m.start()].count('\n') + 1
        add_node(nodes, type='sink', language=lang, sink=m.group(1), source_file=rel, line=line, parser_mode='sink_lexical')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('root')
    ap.add_argument('-o','--out', default='-')
    args = ap.parse_args()
    root = Path(args.root).resolve()
    nodes, edges = [], []
    for p in walk(root):
        if p.suffix.lower() == '.py':
            parse_python(p, root, nodes, edges)
        parse_lexical(p, root, nodes, edges)
    graph = {'schema_version':'codegraph.v1','project_root':str(root),'nodes':nodes,'edges':edges,'summary':{'node_count':len(nodes),'edge_count':len(edges)}}
    data = json.dumps(graph, ensure_ascii=False, indent=2)
    if args.out == '-': print(data)
    else: Path(args.out).write_text(data, encoding='utf-8')
    print(f"wrote code graph nodes={len(nodes)} edges={len(edges)}", file=__import__('sys').stderr)

if __name__ == '__main__': main()

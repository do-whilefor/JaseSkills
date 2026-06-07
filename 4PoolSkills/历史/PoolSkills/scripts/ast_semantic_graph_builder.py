#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, shutil, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
SKIP = {'.git','node_modules','vendor','dist','build','.next','coverage','outputs','__pycache__','.venv','venv'}
LANG = {
    '.py': ('python_security_graph', [sys.executable, str(ROOT/'ast_plugins/python/python_security_graph_bridge.py')]),
    '.js': ('typescript_security_graph', ['node', str(ROOT/'ast_plugins/js/typescript_security_graph_bridge.js')]),
    '.jsx': ('typescript_security_graph', ['node', str(ROOT/'ast_plugins/js/typescript_security_graph_bridge.js')]),
    '.mjs': ('typescript_security_graph', ['node', str(ROOT/'ast_plugins/js/typescript_security_graph_bridge.js')]),
    '.cjs': ('typescript_security_graph', ['node', str(ROOT/'ast_plugins/js/typescript_security_graph_bridge.js')]),
    '.ts': ('typescript_security_graph', ['node', str(ROOT/'ast_plugins/js/typescript_security_graph_bridge.js')]),
    '.tsx': ('typescript_security_graph', ['node', str(ROOT/'ast_plugins/js/typescript_security_graph_bridge.js')]),
    '.go': ('go_parser', ['go','run', str(ROOT/'ast_plugins/go/go_parser_bridge.go')]),
    '.php': ('php_parser', ['php', str(ROOT/'ast_plugins/php/php_parser_bridge.php')]),
    '.rb': ('ruby_ripper', ['ruby', str(ROOT/'ast_plugins/ruby/ripper_bridge.rb')]),
}
def iter_files(root: Path):
    for p in root.rglob('*'):
        if not p.is_file() or p.suffix.lower() not in LANG: continue
        if any(part in SKIP for part in p.parts): continue
        yield p

def run(cmd, file: Path):
    if not shutil.which(cmd[0]):
        return {'status':'missing','file':str(file),'plugin':cmd[0],'real_ast':False,'nodes':[],'edges':[],'error':'missing executable '+cmd[0]}
    try:
        r = subprocess.run(cmd+[str(file)], cwd=str(ROOT), text=True, capture_output=True, timeout=40)
        txt = r.stdout.strip() or r.stderr.strip()
        data = json.loads(txt)
        data.setdefault('file', str(file)); data.setdefault('nodes', []); data.setdefault('edges', [])
        if r.returncode != 0 and data.get('status') == 'ready': data['status']='failed'
        return data
    except Exception as e:
        return {'status':'failed','file':str(file),'plugin':cmd[0],'real_ast':False,'nodes':[],'edges':[],'error':str(e)}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('project', nargs='?', default=str(ROOT/'tests/fixtures/ast_project'))
    ap.add_argument('--out', default=str(ROOT/'outputs/current/ast_security_graph.json'))
    args=ap.parse_args(); project=Path(args.project).resolve()
    results=[]; nodes=[]; edges=[]
    for p in iter_files(project):
        plugin, cmd = LANG[p.suffix.lower()]
        res = run(cmd, p); res['selected_backend']=plugin; results.append(res)
        if res.get('status') == 'ready' and res.get('real_ast') is True:
            nodes.extend(res.get('nodes') or []); edges.extend(res.get('edges') or [])
    node_types=sorted({n.get('type') for n in nodes}); edge_types=sorted({e.get('type') for e in edges})
    required = {
        'has_real_ast_backend': any(r.get('status')=='ready' and r.get('real_ast') is True for r in results),
        'has_route_to_handler': 'ROUTE_TO_HANDLER' in edge_types,
        'has_api_call': 'api_call' in node_types,
        'has_param_or_source': bool({'parameter','source'} & set(node_types)),
        'has_sink': 'sink' in node_types,
        'has_auth_or_guard': bool({'guard','authn'} & set(node_types)),
    }
    status = 'promoted' if all(required.values()) else 'needs_review'
    graph = {
        'schema':'ast-security-graph',
        'project':str(project),
        'status':status,
        'policy':'Only nodes emitted by real AST backends can contribute to promoted AST evidence. Text fallback is not promoted.',
        'required_checks':required,
        'nodes':nodes,
        'edges':edges,
        'backend_results':results,
    }
    out=Path(args.out); out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(graph, ensure_ascii=False, indent=2)+"\n", encoding='utf-8')
    print(json.dumps({'status':status,'nodes':len(nodes),'edges':len(edges),'required_checks':required,'out':str(out)}, ensure_ascii=False, indent=2))
    return 0 if status == 'promoted' else 1
if __name__ == '__main__': raise SystemExit(main())

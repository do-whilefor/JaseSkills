#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    out=ROOT/'outputs/current/ast_semantic_selftest.json'
    graph=ROOT/'outputs/current/ast_security_graph.json'
    r=subprocess.run([sys.executable, str(ROOT/'scripts/ast_semantic_graph_builder.py'), str(ROOT/'tests/fixtures/ast_project'), '--out', str(graph)], cwd=str(ROOT), text=True, capture_output=True)
    data=json.loads(graph.read_text(encoding='utf-8')) if graph.exists() else {}
    node_types={n.get('type') for n in data.get('nodes',[])}; edge_types={e.get('type') for e in data.get('edges',[])}
    checks={
      'builder_exit_zero': r.returncode == 0,
      'real_typescript_ast': any(x.get('plugin')=='typescript_security_graph' and x.get('real_ast') is True and x.get('status')=='ready' for x in data.get('backend_results',[])),
      'real_python_ast': any(x.get('plugin')=='python_security_graph' and x.get('real_ast') is True and x.get('status')=='ready' for x in data.get('backend_results',[])),
      'route_to_handler': 'ROUTE_TO_HANDLER' in edge_types,
      'api_call_extracted': 'api_call' in node_types,
      'sink_extracted': 'sink' in node_types,
      'browser_state_extracted': bool({'browser_storage','message_boundary','service_worker_registration'} & node_types),
      'graphql_extracted': 'graphql_operation' in node_types,
    }
    result={'status':'pass' if all(checks.values()) else 'fail','checks':checks,'graph':str(graph),'stdout':r.stdout[-2000:],'stderr':r.stderr[-2000:]}
    out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['status']=='pass' else 1
if __name__=='__main__': raise SystemExit(main())

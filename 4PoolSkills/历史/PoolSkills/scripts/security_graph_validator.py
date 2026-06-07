#!/usr/bin/env python3
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main(path=None):
    p=Path(path) if path else ROOT/'outputs/security_graph.json'
    if not p.exists(): print(json.dumps({'status':'failed','error':'missing security_graph.json'})); return 2
    g=json.loads(p.read_text(encoding='utf-8'))
    types={n.get('type') for n in g.get('nodes',[])}; etypes={e.get('type') for e in g.get('edges',[])}
    missing_nodes=sorted({'route','handler'}-types); missing_edges=sorted({'ROUTE_TO_HANDLER'}-etypes)
    status='pass' if not missing_nodes and not missing_edges else 'degraded'
    out={'status':status,'node_types':sorted(types),'edge_types':sorted(etypes),'missing_required_node_types':missing_nodes,'missing_required_edge_types':missing_edges,'policy':'degraded graphs cannot confirm vulnerabilities'}
    (ROOT/'outputs/security_graph_validation.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(out,ensure_ascii=False,indent=2)); return 0 if status=='pass' else 1
if __name__=='__main__': raise SystemExit(main(sys.argv[1] if len(sys.argv)>1 else None))

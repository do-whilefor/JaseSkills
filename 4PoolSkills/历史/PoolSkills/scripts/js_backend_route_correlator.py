#!/usr/bin/env python3
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'outputs/js_deep_audit'; OUT.mkdir(parents=True, exist_ok=True)
js_path=Path(sys.argv[1]) if len(sys.argv)>1 else OUT/'bundle_module_map.json'; graph_path=Path(sys.argv[2]) if len(sys.argv)>2 else ROOT/'outputs/security_graph.json'
js=json.loads(js_path.read_text(encoding='utf-8')) if js_path.exists() else {'api_endpoints':[]}; graph=json.loads(graph_path.read_text(encoding='utf-8')) if graph_path.exists() else {'nodes':[]}
routes=[n for n in graph.get('nodes',[]) if n.get('type')=='route']; matches=[]; gaps=[]
for ep in js.get('api_endpoints',[]):
    m=[r for r in routes if ep == r.get('route') or ep.rstrip('/') == str(r.get('route','')).rstrip('/')]
    (matches if m else gaps).append({'endpoint':ep,'backend_routes':m,'status':'mapped' if m else 'unmapped_candidate'})
out={'status':'ok','matches':matches,'unmapped_js_endpoints':gaps,'policy':'unmapped JS endpoint is not a vulnerability without backend/dynamic evidence'}
(OUT/'backend_route_correlation.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps(out,ensure_ascii=False,indent=2))

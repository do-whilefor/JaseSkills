#!/usr/bin/env python3
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'outputs/chains'; OUT.mkdir(parents=True, exist_ok=True)
gp=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'outputs/security_graph.json'; g=json.loads(gp.read_text(encoding='utf-8')) if gp.exists() else {'nodes':[],'edges':[]}
nodes=g.get('nodes',[]); route_count=sum(1 for n in nodes if n.get('type')=='route'); guard_count=sum(1 for n in nodes if n.get('type') in ('guard','authn','authz','middleware')); sink_count=sum(1 for n in nodes if n.get('type')=='sink')
candidates=[]
if route_count and sink_count: candidates.append({'chain':'import/export-file-read-path-traversal','status':'candidate','reason':'route and sink co-exist; requires dataflow and dynamic evidence'})
if route_count and guard_count==0: candidates.append({'chain':'frontend-guard-backend-authz-gap','status':'candidate','reason':'routes without detected guards; requires dynamic role matrix'})
out={'status':'ok','route_count':route_count,'guard_count':guard_count,'sink_count':sink_count,'chain_candidates':candidates}
(OUT/'chain_query_results.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps(out,ensure_ascii=False,indent=2))

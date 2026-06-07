#!/usr/bin/env python3
import json, sys, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
project=sys.argv[1] if len(sys.argv)>1 else str(ROOT/'examples')
subprocess.run([sys.executable, str(ROOT/'scripts/semantic_ast_analyzer.py'), project], check=False)
graph=json.loads((ROOT/'outputs/security_graph.json').read_text(encoding='utf-8'))
routes=[n for n in graph.get('nodes',[]) if n.get('type')=='route']
out={'routes':routes,'source_graph':str(ROOT/'outputs/security_graph.json'),'status':'ok' if routes else 'degraded'}
(ROOT/'outputs/semantic_routes.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(out,ensure_ascii=False,indent=2))

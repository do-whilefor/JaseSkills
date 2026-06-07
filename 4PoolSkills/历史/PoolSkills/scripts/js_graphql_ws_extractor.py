#!/usr/bin/env python3
import json, re, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'outputs/js_deep_audit'; OUT.mkdir(parents=True, exist_ok=True)
p=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'benchmarks/01-express-nestjs/frontend/app.js'; s=p.read_text(encoding='utf-8',errors='ignore')
gql=sorted(set(re.findall(r'\b(query|mutation|subscription)\s+[A-Za-z0-9_]+', s))); ws=sorted(set(re.findall(r"new\s+WebSocket\(['\"]([^'\"]+)['\"]", s)))
out={'status':'ok','file':str(p),'graphql_operations':gql,'websocket_endpoints':ws}
(OUT/'graphql_ws_extraction.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps(out,ensure_ascii=False,indent=2))

#!/usr/bin/env python3
import json, re, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'outputs/js_deep_audit'; OUT.mkdir(parents=True, exist_ok=True)
p=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'benchmarks/01-express-nestjs/frontend/app.js'; s=p.read_text(encoding='utf-8',errors='ignore')
funcs=[{'name':m.group(1),'offset':m.start(),'status':'candidate','use':'May support Burp/Playwright request construction after manual review'} for m in re.finditer(r'function\s+([A-Za-z0-9_$]*(sign|hash|hmac|token|encrypt)[A-Za-z0-9_$]*)\s*\(', s, re.I)]
out={'status':'ok','file':str(p),'signature_function_candidates':funcs}
(OUT/'signature_functions.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps(out,ensure_ascii=False,indent=2))

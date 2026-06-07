#!/usr/bin/env python3
import json, re, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'outputs/js_deep_audit'; OUT.mkdir(parents=True, exist_ok=True)
p=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'benchmarks/01-express-nestjs/frontend/app.js'; s=p.read_text(encoding='utf-8',errors='ignore')
modules=[{'signal':pat,'status':'candidate'} for pat in [r'webpackJsonp',r'__webpack_require__',r'import\(',r'vite',r'next/static'] if re.search(pat,s)]
endpoints=sorted(set(re.findall(r"['\"](/api/[^'\"]+)['\"]", s)))
out={'status':'ok','file':str(p),'bundle_signals':modules,'api_endpoints':endpoints}
(OUT/'bundle_module_map.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps(out,ensure_ascii=False,indent=2))

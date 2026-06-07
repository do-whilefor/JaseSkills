#!/usr/bin/env python3
from __future__ import annotations
import json, hashlib, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
idx=ROOT/'raw_original_sources'/'RAW_ORIGINAL_SOURCES_INDEX.json'; kbidx=ROOT/'raw_original_kb_templates'/'ORIGINAL_KB_TEMPLATE_INVENTORY.json'; mapidx=ROOT/'raw_original_kb_templates'/'ORIGINAL_TO_RESEARCH_UNIT_MAPPING.json'; qidx=ROOT/'raw_original_kb_templates_quarantine'/'QUARANTINED_ORIGINAL_ITEMS_INDEX.json'
errors=[]; warnings=[]
for p,msg in [(idx,'missing raw index'),(kbidx,'missing kb inventory'),(mapidx,'missing mapping')]:
    if not p.exists(): errors.append(msg)
files=[]
if idx.exists():
    files=json.loads(idx.read_text(encoding='utf-8'))
    kb=[x for x in files if x.get('raw_kb_template_path')]
    if len(files)<50: errors.append(f'expanded active file count too low: {len(files)}')
    if len(kb)<20: errors.append(f'active kb/template/rule file count too low: {len(kb)}')
    for x in kb[:5000]:
        p=ROOT/x['raw_kb_template_path']
        if not p.exists(): errors.append('missing '+x['raw_kb_template_path']); continue
        h=hashlib.sha256(p.read_bytes()).hexdigest()
        if h!=x['sha256']:
            warnings.append('encoding-normalized hash differs for '+x['raw_kb_template_path'])
if mapidx.exists():
    mp=json.loads(mapidx.read_text(encoding='utf-8')); empty=[k for k,v in mp.items() if not v]
    if empty: errors.append('unmapped research units: '+','.join(empty))
qcount=0
if qidx.exists(): qcount=len(json.loads(qidx.read_text(encoding='utf-8')))
out={'status':'pass' if not errors else 'fail','errors':errors,'warnings':warnings[:20],'expanded_active_files':len(files),'active_kb_template_files':sum(1 for x in files if x.get('raw_kb_template_path')),'quarantined_items':qcount}
print(json.dumps(out,ensure_ascii=False,indent=2)); sys.exit(0 if not errors else 1)

#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, hashlib, re
from pathlib import Path
from _scope import redact_text

def sha_file(path):
    p=Path(path)
    if p.exists() and p.is_file(): return hashlib.sha256(p.read_bytes()).hexdigest()
    return hashlib.sha256(str(path).encode()).hexdigest()

def safe_summary(s): return redact_text(str(s or ''))[:500]

def build(candidates, scope, root):
    root=Path(root).resolve(); findings=[]
    for c in candidates.get('candidates',[]):
        ev=[]; seen=set()
        for i,e in enumerate((c.get('code_evidence') or []) + (c.get('js_evidence') or []) + (c.get('dynamic_evidence') or [])):
            fp=e.get('file') or e.get('path') or ''
            full=(root/fp).resolve() if fp else root
            if fp and not str(full).startswith(str(root)):
                continue
            kind='source_line' if e in (c.get('code_evidence') or []) else ('js_signal' if e in (c.get('js_evidence') or []) else 'runtime')
            key=(kind,fp,int(e.get('line') or 1),safe_summary(e.get('summary')))
            if key in seen: continue
            seen.add(key)
            ev.append({'id':f"ev-{c.get('id','candidate')}-{len(ev)}", 'kind':kind, 'path':fp, 'line':int(e.get('line') or 1), 'sha256':sha_file(full) if fp and full.exists() else None, 'summary':safe_summary(e.get('summary')), 'source':e.get('source','detector')})
        findings.append({'candidate_id':c.get('id','unknown'), 'candidate_type':c.get('type'), 'state':c.get('dynamic_state','STATIC_CANDIDATE'), 'status':c.get('status','needs_review'), 'evidence':ev, 'evidence_quality':{'has_code_evidence':any(x['kind']=='source_line' for x in ev),'has_js_evidence':any(x['kind']=='js_signal' for x in ev),'has_runtime_evidence':any(x['kind']=='runtime' for x in ev),'deduped_count':len(ev)}, 'policy':'no evidence item may contain unredacted secrets; static evidence cannot confirm vulnerability'})
    return {'schema_version':'evidence-manifest-v1','scope':scope,'findings':findings,'policy':'candidate evidence manifest; confirmed reporting requires dynamic runtime evidence and negative controls'}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--candidates',required=True); ap.add_argument('--root',default='.'); ap.add_argument('--out',required=True); ns=ap.parse_args()
    cand=json.loads(Path(ns.candidates).read_text(encoding='utf-8'))
    data=build(cand, cand.get('scope', ns.root), ns.root)
    Path(ns.out).parent.mkdir(parents=True, exist_ok=True); Path(ns.out).write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'ok':True,'findings':len(data['findings'])}, ensure_ascii=False))
if __name__=='__main__': main()

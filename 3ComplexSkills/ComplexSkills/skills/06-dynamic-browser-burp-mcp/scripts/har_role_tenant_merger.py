#!/usr/bin/env python3
"""Merge HAR files into a redacted role/tenant evidence ledger."""
from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path
SECRET=re.compile(r'(?i)(authorization|cookie|token|secret|api[_-]?key|password)')

def load(p): return json.loads(Path(p).read_text(encoding='utf-8', errors='ignore'))
def red(v): return '<redacted>' if v and SECRET.search(str(v)) else v

def entry_row(e, role, tenant):
    req=e.get('request') or {}; res=e.get('response') or {}
    url=req.get('url','')
    headers=[{'name':h.get('name'), 'value':red(h.get('value'))} for h in req.get('headers',[]) if not SECRET.search(h.get('name',''))]
    key=hashlib.sha256(json.dumps({'role':role,'tenant':tenant,'method':req.get('method'),'url':url,'status':res.get('status')}, sort_keys=True).encode()).hexdigest()[:16]
    return {'case_id':'HAR-'+key,'role':role,'tenant':tenant,'method':req.get('method'),'url_hash':hashlib.sha256(url.encode()).hexdigest(),'url_path':url.split('?',1)[0][-180:],'status':res.get('status'),'request_headers_redacted':headers,'response_mime':(res.get('content') or {}).get('mimeType'),'redacted':True,'non_destructive':True}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--har', action='append', required=True); ap.add_argument('--role', action='append'); ap.add_argument('--tenant', action='append'); ap.add_argument('--out')
    a=ap.parse_args(); rows=[]
    for i,h in enumerate(a.har):
        obj=load(h); role=(a.role or ['unknown'])[min(i, len(a.role or ['unknown'])-1)]; tenant=(a.tenant or ['unknown'])[min(i, len(a.tenant or ['unknown'])-1)]
        for e in ((obj.get('log') or {}).get('entries') or []): rows.append(entry_row(e, role, tenant))
    res={'schema_version':'har_role_tenant_merge_v1','executor':'har_role_tenant_merger.py','executed':True,'rows':rows,'row_count':len(rows),'promotion_policy':'HAR merge is supporting dynamic evidence only when paired with storageState/account context, negative controls and quality gate.'}
    text=json.dumps(res, ensure_ascii=False, indent=2)
    if a.out: Path(a.out).parent.mkdir(parents=True, exist_ok=True); Path(a.out).write_text(text+'\n', encoding='utf-8')
    print(text); return 0
if __name__=='__main__': raise SystemExit(main())

#!/usr/bin/env python3
"""C01-C05 access-control candidate detector.

Inputs normalized info-surface JSONL and emits needs_review candidates only.
It does not confirm vulnerabilities. Confirmation requires role/tenant replay evidence.
"""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path

ADMIN_RE=re.compile(r"admin|superuser|root|manage|settings|billing|export|impersonate",re.I)
ID_RE=re.compile(r"(^|[^a-z])(id|userId|accountId|orgId|tenantId|projectId|ownerId)([^a-z]|$)",re.I)
AUTH_RE=re.compile(r"auth|jwt|session|permission|role|guard|policy|csrf|bearer|cookie",re.I)
TENANT_RE=re.compile(r"tenant|org|workspace|accountId|projectId",re.I)

def load_jsonl(paths):
    for p in paths:
        with open(p,encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try: yield json.loads(line)
                    except json.JSONDecodeError: continue

def text_of(r):
    return ' '.join(str(r.get(k,'')) for k in ['endpoint','path','source_file','parameter','candidate_vulnerability','source_type'])

def detect(r):
    txt=text_of(r)
    endpoint=str(r.get('endpoint') or r.get('path') or '')
    auth=' '.join(map(str, r.get('auth_context') or [])) + ' ' + str(r.get('auth_context',''))
    tenant=' '.join(map(str, r.get('tenant_context') or [])) + ' ' + str(r.get('tenant_context',''))
    records=[]
    base={
        'source_file':r.get('source_file'), 'source_line':r.get('source_line') or r.get('line'),
        'endpoint':endpoint, 'method':r.get('method'), 'review_status':'needs_review',
        'evidence':{'source_record_type':r.get('type'), 'source_asset_id':r.get('asset_id')},
        'limitation':'candidate requires non-destructive role/tenant replay before reportable finding'
    }
    if ADMIN_RE.search(txt) and not AUTH_RE.search(auth):
        records.append({**base,'type':'c01_c05_access_control_candidate','candidate_vulnerability':'admin_or_privileged_endpoint_without_collected_auth_evidence','class_id':'C02/C05','confidence':0.48})
    if ID_RE.search(txt):
        records.append({**base,'type':'c01_c05_access_control_candidate','candidate_vulnerability':'idor_parameter_requires_ownership_check','class_id':'C03','confidence':0.50})
    if TENANT_RE.search(txt) or TENANT_RE.search(tenant):
        records.append({**base,'type':'c01_c05_access_control_candidate','candidate_vulnerability':'tenant_boundary_requires_cross_tenant_negative_replay','class_id':'C04','confidence':0.50})
    return records

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--input', action='append', required=True)
    ap.add_argument('-o','--out',default='-')
    args=ap.parse_args()
    out=[]
    for r in load_jsonl(args.input): out.extend(detect(r))
    data=''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in out)
    if args.out=='-': sys.stdout.write(data)
    else: Path(args.out).write_text(data,encoding='utf-8')
    print(f"wrote {len(out)} C01-C05 candidates", file=sys.stderr)
if __name__=='__main__': main()

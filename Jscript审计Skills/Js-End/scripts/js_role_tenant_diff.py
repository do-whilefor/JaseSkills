#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
from typing import Any

def load_ledger(d: Path):
    p=d/'js_asset_ledger.json'
    if not p.exists(): return None
    return json.loads(p.read_text(encoding='utf-8'))

def asset_set(ledger):
    return {a['path'] for a in ledger.get('assets',[]) if a.get('kind') in {'javascript','service_worker','manifest','sourcemap'}}

def evidence_values(ledger, kinds):
    return {e.get('value') for e in ledger.get('evidence',[]) if e.get('kind') in kinds and e.get('value')}

def main():
    ap=argparse.ArgumentParser(description='Compare multiple role/tenant JS ledgers for chunk/endpoint/GraphQL/WebSocket differences')
    ap.add_argument('--input', action='append', required=True, help='name=report_dir containing js_asset_ledger.json')
    ap.add_argument('--out', default='reports/js-top-tier')
    args=ap.parse_args()
    ledgers={}
    for item in args.input:
        if '=' not in item: raise SystemExit('--input must be name=dir')
        name, d = item.split('=',1)
        led=load_ledger(Path(d))
        if led is None: raise SystemExit(f'missing ledger in {d}')
        ledgers[name]=led
    names=list(ledgers)
    diffs=[]
    for i,a in enumerate(names):
        for b in names[i+1:]:
            aset=asset_set(ledgers[a]); bset=asset_set(ledgers[b])
            aeps=evidence_values(ledgers[a], {'endpoint_candidate','hidden_route_candidate','graphql_operation_candidate','websocket_candidate'})
            beps=evidence_values(ledgers[b], {'endpoint_candidate','hidden_route_candidate','graphql_operation_candidate','websocket_candidate'})
            diffs.append({'left':a,'right':b,'assets_only_left':sorted(aset-bset),'assets_only_right':sorted(bset-aset),'endpoints_only_left':sorted(aeps-beps),'endpoints_only_right':sorted(beps-aeps)})
    status='ready' if len(names)>=2 and any(d['assets_only_left'] or d['assets_only_right'] or d['endpoints_only_left'] or d['endpoints_only_right'] for d in diffs) else ('partial' if len(names)>=2 else 'missing')
    out=Path(args.out); out.mkdir(parents=True, exist_ok=True)
    result={'schema_version':'js-role-tenant-diff/v1','status':status,'reason':'ready means at least two role/tenant ledgers were compared and differences were found; still requires non-destructive backend authorization validation','diffs':diffs}
    (out/'js_role_tenant_diff.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'ok':True,'status':status,'pairs':len(diffs),'out':str(out/'js_role_tenant_diff.json')}, ensure_ascii=False, indent=2))
if __name__=='__main__': main()

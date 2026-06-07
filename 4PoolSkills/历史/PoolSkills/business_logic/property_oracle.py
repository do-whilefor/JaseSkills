#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

def _fail(name, reason, event=None): return {'invariant':name,'status':'failed','reason':reason,'event':event}
def _pass(name): return {'invariant':name,'status':'passed'}

def evaluate(spec: dict, events: list[dict]) -> dict:
    results=[]
    for inv in spec.get('invariants',[]):
        name=inv.get('name') or inv.get('type') or 'invariant'
        typ=inv.get('type')
        if typ == 'tenant_ownership':
            key=inv.get('tenant_key','tenant_id')
            owner=inv.get('owner_key','owner_tenant_id')
            bad=next((e for e in events if e.get(key) is not None and e.get(owner) is not None and e.get(key) != e.get(owner)), None)
            results.append(_fail(name,'tenant_mismatch',bad) if bad else _pass(name))
        elif typ == 'role_allowed':
            allowed=set(inv.get('allowed_roles') or [])
            bad=next((e for e in events if e.get('action')==inv.get('action') and e.get('role') not in allowed), None)
            results.append(_fail(name,'role_not_allowed',bad) if bad else _pass(name))
        elif typ == 'amount_non_negative':
            field=inv.get('field','amount')
            bad=next((e for e in events if isinstance(e.get(field),(int,float)) and e.get(field) < 0), None)
            results.append(_fail(name,'negative_amount',bad) if bad else _pass(name))
        elif typ == 'balance_monotonic_min':
            field=inv.get('field','balance')
            minimum=inv.get('minimum',0)
            bad=next((e for e in events if isinstance(e.get(field),(int,float)) and e.get(field) < minimum), None)
            results.append(_fail(name,'balance_below_minimum',bad) if bad else _pass(name))
        elif typ == 'state_transition':
            allowed={tuple(x) for x in inv.get('allowed_transitions',[])}
            bad=next((e for e in events if e.get('from') is not None and e.get('to') is not None and (e.get('from'),e.get('to')) not in allowed), None)
            results.append(_fail(name,'invalid_state_transition',bad) if bad else _pass(name))
        else:
            results.append({'invariant':name,'status':'unsupported','reason':'unknown_invariant_type'})
    status='passed' if results and all(r['status']=='passed' for r in results) else ('failed' if any(r['status']=='failed' for r in results) else 'needs_review')
    return {'schema_version':'business-property-oracle-v1','status':status,'results':results,'policy':'Property oracle evaluates local recorded events only; it does not confirm vulnerabilities without dynamic evidence and quality gate.'}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--spec',required=True); ap.add_argument('--events',required=True); ap.add_argument('--out',required=True); ns=ap.parse_args()
    data=evaluate(json.loads(Path(ns.spec).read_text(encoding='utf-8')), json.loads(Path(ns.events).read_text(encoding='utf-8')).get('events',[]))
    Path(ns.out).parent.mkdir(parents=True,exist_ok=True); Path(ns.out).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':data['status'],'checks':len(data['results'])},ensure_ascii=False)); sys.exit(0 if data['status']=='passed' else 1)
if __name__=='__main__': main()

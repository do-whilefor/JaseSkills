#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, hashlib
from pathlib import Path
from typing import Any
PROTOCOL_RULES={
  'graphql':['GRAPHQL','GQL'],
  'websocket':['WEBSOCKET','WS-'],
  'postmessage':['POSTMESSAGE','PM-']
}

def load(p: Path, default=None):
    try: return json.loads(p.read_text(encoding='utf-8'))
    except Exception: return default if default is not None else {}

def blob(x): return json.dumps(x, ensure_ascii=False).lower()

def hash_item(x): return hashlib.sha256(json.dumps(x, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:16]

def classify_finding(f):
    rid=str(f.get('rule_id','')).upper(); title=str(f.get('title','')).upper()
    for proto, sigs in PROTOCOL_RULES.items():
        if any(s in rid or s in title for s in sigs): return proto
    return ''

def main():
    ap=argparse.ArgumentParser(description='Bind GraphQL/WebSocket/postMessage detector findings to imported runtime evidence. Binding never confirms without ready runtime manifest and request/response/role-tenant evidence.')
    ap.add_argument('--detectors', required=True)
    ap.add_argument('--runtime-bundle', required=True)
    ap.add_argument('--authorization', default='')
    ap.add_argument('--out', default='reports/js-top-tier')
    args=ap.parse_args(); out=Path(args.out); out.mkdir(parents=True, exist_ok=True)
    det=load(Path(args.detectors),{}); run=load(Path(args.runtime_bundle),{}); auth=load(Path(args.authorization),{}) if args.authorization else {}
    runtime_ready=run.get('status')=='ready'
    protocol_ev=run.get('protocol_runtime_evidence',{}) or {}
    auth_ready=auth.get('status')=='ready'
    bindings=[]
    for f in det.get('findings',[]):
        proto=classify_finding(f)
        if not proto: continue
        fblob=blob(f)
        candidates=protocol_ev.get(proto,[]) if isinstance(protocol_ev,dict) else []
        matched=[]
        for ev in candidates:
            evblob=blob(ev)
            evidence_values=[]
            for e in f.get('evidence',[]):
                if not isinstance(e,dict):
                    continue
                for key in ('value','url','endpoint'):
                    value=str(e.get(key,'')).strip().lower()
                    if value:
                        evidence_values.append(value)
            if evidence_values and any(value in evblob for value in evidence_values):
                matched.append({'runtime_hash':hash_item(ev),'entry':ev})
        bound=bool(matched)
        status='runtime_bound' if bound and runtime_ready else ('partial' if bound else 'unbound')
        promotable=bool(status=='runtime_bound' and auth_ready and f.get('status')!='confirmed')
        bindings.append({'finding_id':f.get('finding_id'),'rule_id':f.get('rule_id'),'protocol':proto,'status':status,'runtime_ready':runtime_ready,'authorization_ready':auth_ready,'runtime_matches':matched[:20],'promotable_to_confirmed':False,'promotion_blockers':[] if promotable else [x for x,v in {'runtime_bundle_ready':runtime_ready,'runtime_match':bound,'authorization_ready':auth_ready,'security_impact_reviewed':False}.items() if not v]})
    status='ready' if bindings and all(b['status']=='runtime_bound' for b in bindings) and runtime_ready else ('partial' if bindings else 'missing')
    result={'schema_version':'js-runtime-detector-binding/v1','status':status,'bindings':bindings,'summary':{'bindings':len(bindings),'runtime_bound':sum(1 for b in bindings if b['status']=='runtime_bound'),'unbound':sum(1 for b in bindings if b['status']=='unbound'),'confirmed_promotions':0},'downgrade':'This binder records runtime correlation only. It deliberately does not promote to confirmed without security impact review.'}
    (out/'js_runtime_detector_binding.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'ok':True,'status':status,**result['summary'],'out':str(out/'js_runtime_detector_binding.json')}, ensure_ascii=False, indent=2))
if __name__=='__main__': main()

#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re, hashlib
from pathlib import Path
from typing import Any

def load(p:Path, default):
    try: return json.loads(p.read_text(encoding='utf-8'))
    except Exception: return default

def status_for(rule:dict[str,Any], evs:list[dict[str,Any]], manifest:dict[str,Any], scope_ok:bool)->tuple[str,list[str]]:
    blockers=[]
    if not scope_ok: blockers.append('scope guard missing or unauthorized')
    if manifest.get('status')!='ready': blockers.append('evidence manifest not ready')
    # Static graph evidence is allowed to create candidates only. Even a ready manifest must not
    # convert static-only matches to confirmed without an explicit non-static runtime graph.
    if manifest.get('static_only') is True:
        blockers.append('static-only manifest cannot promote findings')
    if not any(x.get('request') or x.get('response') for x in manifest.get('items',[]) if isinstance(x,dict)):
        blockers.append('request/response evidence missing')
    if any(k in rule['rule_id'] for k in ['IDOR','BFLA','TENANT','AUTHZ','GQL-IDOR','WS-AUTHZ']):
        if not any(('role' in json.dumps(x).lower() or 'tenant' in json.dumps(x).lower()) for x in manifest.get('items',[]) if isinstance(x,dict)):
            blockers.append('role/tenant replay evidence missing')
    if any(k in rule['rule_id'] for k in ['DOM-XSS','REFLECTED','STORED','TEMPLATE']):
        if not any(x.get('kind') in {'source_sink_path','dom_snapshot','screenshot'} for x in manifest.get('items',[]) if isinstance(x,dict)):
            blockers.append('DOM source-sink/runtime evidence missing')
    return ('confirmed' if not blockers and evs else ('candidate' if evs else 'needs_review')), blockers

def match_evidence(rule:dict[str,Any], graph:dict[str,Any], ledger:dict[str,Any]):
    signals=set(s.lower() for s in rule.get('signals',[]))
    ev=[]
    for source_name, items in [('semantic_graph', graph.get('evidence',[])), ('collector_ledger', ledger.get('evidence',[]))]:
        for item in items:
            blob=json.dumps(item, ensure_ascii=False).lower()
            if any(s and s in blob for s in signals):
                ev.append({'source':source_name,'file':item.get('file'),'line':item.get('line'),'kind':item.get('kind'),'value':item.get('value') or item.get('endpoint') or item.get('url'),'status':'candidate','hash':hashlib.sha256(blob.encode()).hexdigest()[:16]})
    return ev[:25]

def main():
    ap=argparse.ArgumentParser(description='Run detector registry against semantic graph and evidence ledger. Static evidence emits candidate/needs_review only.')
    ap.add_argument('--graph', required=True)
    ap.add_argument('--ledger')
    ap.add_argument('--manifest')
    ap.add_argument('--scope')
    ap.add_argument('--registry', default='data/js_detector_registry_v2.json')
    ap.add_argument('--out', default='reports/js-top-tier')
    args=ap.parse_args(); out=Path(args.out); out.mkdir(parents=True, exist_ok=True)
    graph=load(Path(args.graph),{})
    ledger=load(Path(args.ledger),{}) if args.ledger else {}
    manifest=load(Path(args.manifest),{}) if args.manifest else {}
    scope=load(Path(args.scope),{}) if args.scope else {}
    scope_ok=scope.get('authorized_use') is True and scope.get('non_destructive') is True and bool(scope.get('targets')) if scope else False
    reg=load(Path(args.registry),{'detectors':[]})
    findings=[]; detector_status=[]
    for rule in reg.get('detectors',[]):
        ev=match_evidence(rule, graph, ledger)
        manifest_for_status=dict(manifest)
        manifest_for_status['static_only']=graph.get('static_only', True)
        st, blockers=status_for(rule, ev, manifest_for_status, scope_ok)
        detector_status.append({'rule_id':rule['rule_id'],'title':rule['title'],'module':rule['module'],'status':'partial' if ev else 'needs_review','promotion':'blocked' if blockers else 'eligible','promotion_blockers':blockers[:10],'evidence_count':len(ev)})
        if ev:
            findings.append({'finding_id':f"REG-{len(findings)+1:04d}",'rule_id':rule['rule_id'],'title':rule['title'],'status':st,'evidence':ev,'promotion_blockers':blockers,'redaction_status':'redacted-or-no-secret','report_template':rule.get('report_template'),'false_positive_downgrade_rules':rule.get('false_positive_downgrade_rules',[]),'promotion_rule':rule.get('promotion_rule'),'static_only':graph.get('static_only', True)})
    result={'schema_version':'js-detector-registry-run/v1','ok':True,'scope_ok':scope_ok,'static_only':graph.get('static_only', True),'findings':findings,'detectors':detector_status,'summary':{'detectors':len(detector_status),'findings':len(findings),'confirmed':sum(1 for f in findings if f['status']=='confirmed'),'candidate':sum(1 for f in findings if f['status']=='candidate'),'needs_review':sum(1 for f in findings if f['status']=='needs_review')}}
    if graph.get('static_only', True) and result['summary']['confirmed']:
        result['ok']=False; result.setdefault('errors',[]).append('static-only graph produced confirmed finding')
    (out/'js_detector_registry_run.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'ok':result['ok'],'out':str(out/'js_detector_registry_run.json'), **result['summary']}, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result['ok'] else 1)
if __name__=='__main__': main()

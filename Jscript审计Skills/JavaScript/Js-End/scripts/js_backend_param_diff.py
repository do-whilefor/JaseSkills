#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re
from pathlib import Path
RISK=re.compile(r'(tenant|org|owner|user|role|admin|permission|price|quota|balance|plan|status|state|force|debug|dryRun|override|redirect|callback|url|path|file|template|command|include|expand|fields|filter|sort)', re.I)

def load(p:Path): return json.loads(p.read_text(encoding='utf-8'))
def uniq(xs):
    out=[]
    for x in xs:
        if x and x not in out: out.append(x)
    return out

def risk(xs): return [x for x in uniq(xs) if RISK.search(x)]

def main():
    ap=argparse.ArgumentParser(description='Compare frontend JS params with backend accepted field candidates')
    ap.add_argument('--api-model', required=True)
    ap.add_argument('--out', default='reports/js-top-tier')
    args=ap.parse_args(); out=Path(args.out); out.mkdir(parents=True, exist_ok=True)
    model=load(Path(args.api_model))
    frontend=uniq(model.get('frontend_field_summary',{}).get('fields',[]))
    traffic=uniq([p for vals in model.get('traffic_model',{}).get('observed_params',{}).values() for p in vals])
    backend_items=model.get('backend_model',{}).get('backend_fields',[])
    backend=uniq([x.get('field') for x in backend_items if x.get('field')])
    backend_only=uniq([f for f in backend if f not in frontend and f not in traffic])
    frontend_hidden=uniq([p for api in model.get('apis',[]) for p in api.get('hidden_param_candidates',[])])
    high=uniq(risk(backend_only)+risk(frontend_hidden)+risk(frontend)+risk(traffic))
    per_field=[]
    for f in backend_only:
        ev=[x for x in backend_items if x.get('field')==f][:20]
        per_field.append({'field':f,'status':'candidate-only','risk':'high' if RISK.search(f) else 'medium','backend_evidence':ev,'frontend_seen':f in frontend,'traffic_seen':f in traffic,'required_validation':['same endpoint with frontend params only vs extra field','normal user vs admin','tenant A vs tenant B','owned object vs unowned object'],'blocking_reason':'No backend acceptance response difference proven yet'})
    result={'schema_version':'js-backend-param-diff/v1','status':'partial' if backend_only or frontend_hidden else 'empty','frontend_sent_or_schema_fields':frontend,'traffic_observed_fields':traffic,'backend_accept_field_candidates':backend,'backend_only_fields':backend_only,'frontend_hidden_field_candidates':frontend_hidden,'high_risk_hidden_or_backend_only_fields':high,'field_findings':per_field,'decision':'needs-dynamic-validation' if backend_only or high else 'no-hidden-param-evidence','downgrade':'Do not report backend accepted extra params as verified until non-destructive request/response evidence exists'}
    (out/'js_backend_param_diff.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'ok':True,'out':str(out/'js_backend_param_diff.json'),'backend_only_fields':len(backend_only),'high_risk':len(high)}, ensure_ascii=False, indent=2))
if __name__=='__main__': main()

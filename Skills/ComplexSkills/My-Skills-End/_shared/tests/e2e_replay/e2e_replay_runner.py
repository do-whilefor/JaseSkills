#!/usr/bin/env python3
from __future__ import annotations
import importlib.util, json, os, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
INDEX=Path(__file__).with_name('e2e_replay_index.json')
def imp(path,name):
    spec=importlib.util.spec_from_file_location(name,path); mod=importlib.util.module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(mod); return mod
inv=imp(ROOT/'skills/02-project-intelligence/scripts/project_inventory_extractor.py','inv')
cg=imp(ROOT/'skills/03-code-knowledge-graph/scripts/advanced_code_graph_extractor.py','cg')
js=imp(ROOT/'skills/05-js-audit-runtime/scripts/advanced_js_runtime_extractor.py','js')
surf=imp(ROOT/'skills/04-attack-surface-mapping/scripts/attack_surface_builder.py','surf')
eng=imp(ROOT/'skills/07-vulnerability-hunting-engine/scripts/vulnerability_candidate_engine.py','eng')
def run_sample(s):
    root=ROOT/s['path']
    i=inv.extract(root)
    os.environ['SKIP_OPTIONAL_AST_PLUGIN']='1'
    c=cg.extract(root)
    os.environ.pop('SKIP_OPTIONAL_AST_PLUGIN',None)
    j=js.extract(root); a=surf.build(i,c,j,{}); v=eng.generate(c,j,a,i)
    templates=sorted({x.get('template_id') for x in v.get('candidates',[])})
    routes=sorted({(r.get('method','ANY')+' '+r.get('route','')).strip() for r in c.get('routes',[])})
    js_targets=sorted({str(x.get('target') or x.get('endpoint') or '') for x in j.get('api_clients',[]) if str(x.get('target') or x.get('endpoint') or '')})
    sink_types=sorted({x.get('sink_type') for x in c.get('sinks',[]) if x.get('sink_type')})
    ledger=a.get('role_object_tenant_ledger') or {}
    unres=len(ledger.get('high_risk_unresolved_routes') or [])
    density=round(v.get('candidate_count',0)/max(1,(len(routes)+len(j.get('api_clients',[])))),2)
    return {'id':s['id'],'routes':routes,'route_count':len(routes),'js_api_count':len(j.get('api_clients',[])),'js_api_targets':js_targets,'templates':templates,'candidate_count':v.get('candidate_count'),'candidate_density':density,'sink_types':sink_types,'graph_nodes':len(c.get('nodes',[])),'graph_edges':len(c.get('edges',[])),'role_object_tenant_unresolved_count':unres,'schemas':{'inventory':i.get('schema_version'),'code':c.get('schema_version'),'js':j.get('schema_version'),'surface':a.get('schema_version'),'engine':v.get('schema_version')},'source_map_reentry':(j.get('summary') or {}).get('source_map_reentry_count',0),'ast_symbol_nodes':(j.get('summary') or {}).get('ast_symbol_nodes',0),'errors':[]}
def compare(row,s):
    e=[]
    def eq(field, actual, expected):
        if actual != expected: e.append(f"{s['id']} {field} exact mismatch: expected {expected!r}, got {actual!r}")
    eq('candidate_count', row['candidate_count'], s.get('expected_exact_candidate_count'))
    eq('route_count', row['route_count'], s.get('expected_exact_route_count'))
    eq('routes', row['routes'], s.get('expected_exact_routes'))
    eq('js_api_count', row['js_api_count'], s.get('expected_exact_js_api_count'))
    eq('js_api_targets', row['js_api_targets'], s.get('expected_exact_js_api_targets'))
    eq('templates', row['templates'], s.get('expected_exact_templates'))
    forbidden=sorted(set(row['templates']).intersection(set(s.get('forbidden_templates') or [])))
    if forbidden: e.append(f"{s['id']} produced forbidden templates: {forbidden}")
    eq('sink_types', row['sink_types'], s.get('expected_exact_sink_types'))
    if row['graph_nodes'] < s.get('expected_graph_node_min',0): e.append(f"{s['id']} graph node regression: {row['graph_nodes']} < {s.get('expected_graph_node_min')}")
    if row['graph_edges'] < s.get('expected_graph_edge_min',0): e.append(f"{s['id']} graph edge regression: {row['graph_edges']} < {s.get('expected_graph_edge_min')}")
    eq('role_object_tenant_unresolved_count', row['role_object_tenant_unresolved_count'], s.get('expected_role_object_tenant_unresolved_count'))
    if row['candidate_density'] > s.get('candidate_density_max',999999): e.append(f"{s['id']} candidate density too high: {row['candidate_density']} > {s.get('candidate_density_max')}")
    if row['schemas'] != s.get('expected_schemas'): e.append(f"{s['id']} schema mismatch: expected {s.get('expected_schemas')}, got {row['schemas']}")
    row['errors']=e; return e
def run():
    idx=json.loads(INDEX.read_text(encoding='utf-8')); results=[]; errors=[]
    for s in idx.get('samples',[]):
        row=run_sample(s); errors.extend(compare(row,s)); results.append(row)
    return {'schema_version':'e2e_replay_result_v4.1_exact','passed':not errors,'sample_count':len(results),'results':results,'errors':errors,'anti_regression_assertions':['exact route set','exact JS API targets','exact template set','forbidden templates absent','exact candidate count','candidate density max','graph node/edge minimum','exact role-object-tenant unresolved count','exact schema versions']}
def main():
    r=run(); print(json.dumps(r,ensure_ascii=False,indent=2)); return 0 if r.get('passed') else 1
if __name__=='__main__': raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, sys, re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/benchmarks'; OUT.mkdir(parents=True, exist_ok=True)

def load_json(p, default=None):
    try: return json.loads(Path(p).read_text(encoding='utf-8'))
    except Exception: return default

def norm_route(x):
    if not x: return ''
    x='/' + str(x).strip().lstrip('/')
    x=re.sub(r'<(?:int:)?([A-Za-z_][A-Za-z0-9_]*)>', r'{\1}', x)
    x=re.sub(r':([A-Za-z_][A-Za-z0-9_]*)', r'{\1}', x)
    x=re.sub(r'\[([A-Za-z_][A-Za-z0-9_]*)\]', r'{\1}', x)
    return x.rstrip('/') or '/'

def graph_from_routes(attack):
    nodes=[]; edges=[]; seen=set()
    def add(n):
        k=(n.get('type'),n.get('id'))
        if k not in seen:
            seen.add(k); nodes.append(n)
    for r in attack.get('routes',[]):
        rid=f"{r.get('file')}:{r.get('method')} {r.get('route')}"
        hid=f"{r.get('file')}:handler:{r.get('handler_hint') or r.get('line')}"
        add({'id':rid,'type':'route','file':r.get('file'),'method':r.get('method'),'route':r.get('route'),'framework_hint':r.get('framework_hint'),'line':r.get('line')})
        add({'id':hid,'type':'handler','file':r.get('file'),'name':r.get('handler_hint') or 'framework_handler','line':r.get('line')})
        edges.append({'from':rid,'to':hid,'type':'ROUTE_TO_HANDLER'})
        for param in r.get('parameters') or []:
            pid=f'{rid}:param:{param}'
            add({'id':pid,'type':'parameter','file':r.get('file'),'name':param})
            edges.append({'from':rid,'to':pid,'type':'READS_PARAMETER'})
    nt={n.get('type') for n in nodes}; et={e.get('type') for e in edges}
    quality={'has_route':'route' in nt,'has_handler':'handler' in nt,'has_route_to_handler':'ROUTE_TO_HANDLER' in et,'status':'pass' if {'route','handler'}.issubset(nt) and 'ROUTE_TO_HANDLER' in et else 'degraded','confirmation_policy':'benchmark graph is route-discovery evidence only; no vulnerability confirmation'}
    return {'schema_version':'phase4-security-graph-v2','project':attack.get('project'),'nodes':nodes,'edges':edges,'quality':quality,'policy':'benchmark graph evidence is candidate-only'}

def assert_graph(graph, expected):
    nodes=graph.get('nodes',[]); edges=graph.get('edges',[])
    nt={n.get('type') for n in nodes}; et={e.get('type') for e in edges}
    fails=[]
    if 'route' not in nt: fails.append('missing_route_node')
    if 'handler' not in nt: fails.append('missing_handler_node')
    if 'ROUTE_TO_HANDLER' not in et: fails.append('missing_route_to_handler_edge')
    if not graph.get('quality') or graph['quality'].get('status')!='pass': fails.append('security_graph_quality_not_pass')
    er=expected.get('route')
    if er:
        expected_norm=norm_route(er)
        observed=[norm_route(n.get('route')) for n in nodes if n.get('type')=='route']
        if expected_norm not in observed: fails.append('expected_route_not_found:'+er)
    return fails

def assert_quality_file(q):
    fails=[]
    if not isinstance(q,dict): return ['quality_gate_not_object']
    if q.get('confirmed_allowed') is not False: fails.append('confirmed_allowed_must_be_false_for_static_benchmark')
    if 'dynamic_evidence' not in ''.join(q.get('required_missing',[])): fails.append('missing_dynamic_evidence_requirement')
    if 'negative_control' not in ''.join(q.get('required_missing',[])): fails.append('missing_negative_control_requirement')
    if q.get('expected_status') not in ['rejected_or_validation_blocked','needs_human_review','rejected']:
        fails.append('unexpected_quality_expected_status')
    return fails

results=[]; last_graph=None
for b in sorted((ROOT/'benchmarks').iterdir()):
    if not b.is_dir(): continue
    attack_path=OUT/(b.name+'_attack_surface.json')
    r=subprocess.run([sys.executable, str(ROOT/'scripts/route_extractor.py'), str(b), '--out', str(attack_path)], text=True, capture_output=True, timeout=30)
    attack=load_json(attack_path,{})
    graph=graph_from_routes(attack); last_graph=graph
    expected=load_json(b/'expected/evidence_manifest.json',{})
    q=load_json(b/'expected/quality_gate.json',{})
    graph_fails=assert_graph(graph, expected)
    q_fails=assert_quality_file(q)
    status='pass' if r.returncode==0 and not graph_fails and not q_fails else 'fail'
    results.append({'benchmark':b.name,'status':status,'route_extractor_returncode':r.returncode,'expected_route':expected.get('route'),'graph_assertions':graph_fails,'quality_assertions':q_fails,'route_count':len(attack.get('routes',[])),'node_count':len(graph.get('nodes',[])),'edge_count':len(graph.get('edges',[])),'stdout_summary':r.stdout[-500:],'stderr_summary':r.stderr[-500:]})
if last_graph:
    (ROOT/'outputs/security_graph.json').write_text(json.dumps(last_graph,ensure_ascii=False,indent=2),encoding='utf-8')
overall='pass' if results and all(x['status']=='pass' for x in results) else 'fail'
out={'schema_version':'benchmark-results-v4','status':overall,'benchmarks':results,'count':len(results),'policy':'returncode alone is insufficient; each benchmark asserts expected route, handler node, ROUTE_TO_HANDLER edge, and static-only quality policy'}
(OUT/'benchmark_results.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(out,ensure_ascii=False,indent=2))
sys.exit(0 if overall=='pass' else 2)

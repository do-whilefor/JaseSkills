#!/usr/bin/env python3
"""One-command local authorized audit pipeline.

Read-only source analysis plus planned dynamic proof ledgers. It does not attack third-party targets.
Confirmed claims remain blocked unless strict evidence manifests are supplied and pass gates.
"""
from __future__ import annotations
import argparse, json, subprocess, sys, os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
TRACE_LOG=None

def run(cmd: list[str], out: Path|None=None, allow_returncodes: tuple[int,...]=(0,)) -> dict:
    global TRACE_LOG
    if TRACE_LOG:
        TRACE_LOG.parent.mkdir(parents=True, exist_ok=True); TRACE_LOG.write_text((TRACE_LOG.read_text() if TRACE_LOG.exists() else '') + 'START ' + ' '.join(map(str,cmd)) + '\n', encoding='utf-8')
    cp=subprocess.run(cmd, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=180, env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
    base={'ok': cp.returncode in allow_returncodes, 'cmd': cmd, 'returncode': cp.returncode}
    if TRACE_LOG:
        TRACE_LOG.write_text((TRACE_LOG.read_text() if TRACE_LOG.exists() else '') + 'END rc=' + str(cp.returncode) + ' ' + ' '.join(map(str,cmd[:2])) + '\n', encoding='utf-8')
    if cp.returncode not in allow_returncodes:
        base.update({'stderr':cp.stderr[-1800:], 'stdout':cp.stdout[-1800:]}); return base
    src = out.read_text(encoding='utf-8') if out and out.exists() else cp.stdout
    try:
        obj=json.loads(src); base['json']=obj
        if isinstance(obj,dict) and obj.get('passed') is False and cmd and ('reverse_acceptance_gate.py' in ' '.join(map(str,cmd)) or 'performance_dedupe_noise_gate.py' in ' '.join(map(str,cmd))): base['ok']=False
        return base
    except Exception as exc:
        base.update({'stdout':cp.stdout[-1000:],'stderr':cp.stderr[-1000:],'parse_error':str(exc) if out else None}); return base

def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument('project_root'); ap.add_argument('--out-dir', default='_audit_outputs/pipeline'); ap.add_argument('--manifest-dir', action='append', default=[]); args=ap.parse_args()
    project=Path(args.project_root).resolve(); out=(ROOT/args.out_dir); out.mkdir(parents=True, exist_ok=True)
    global TRACE_LOG; TRACE_LOG=out/'PIPELINE_TRACE.log'
    if not project.exists() or not project.is_dir():
        print(json.dumps({'ok':False,'error':'project_root must be local existing directory','project_root':str(project)},ensure_ascii=False,indent=2)); return 2
    p={
      'inventory':out/'01_inventory.json','parser_readiness':out/'01b_parser_readiness.json','external_parsers':out/'01c_external_parsers.json','code_graph':out/'02_code_graph.json','authz_proof':out/'02b_authz_path_proof.json','dataflow':out/'02c_interprocedural_dataflow.json','js_audit':out/'03_js_audit.json','js_dual':out/'03b_js_dual_ast_sourcemap.json','surface':out/'04_attack_surface.json','parameter_diff':out/'04b_parameter_diff.json','tenant_binding':out/'04c_tenant_object_binding.json','canonical_candidates':out/'05_canonical_candidates.json','extended_candidates':out/'06_extended_candidates.json','perf_gate':out/'06b_performance_gate.json','replay_plan':out/'07_replay_plan.json','role_tenant_matrix':out/'09_role_tenant_matrix.json','playwright_replay':out/'09b_playwright_multirole_replay.json','graphql_replay':out/'09c_graphql_replay.json','websocket_replay':out/'09d_websocket_replay.json','manifest_index':out/'10_manifest_index.json','dashboard':out/'11_dashboard.html','final_guard':out/'12_final_claim_guard.json','reverse_acceptance':out/'13_reverse_acceptance_gate.json','summary':out/'PIPELINE_SUMMARY.json'}
    steps=[]
    steps.append(('inventory', run([sys.executable,'skills/02-project-intelligence/scripts/project_inventory_extractor.py',str(project),'--out',str(p['inventory'])], p['inventory'])))
    steps.append(('parser_readiness', run([sys.executable,'skills/03-code-knowledge-graph/scripts/parser_backends/parser_runtime_manager.py','--out',str(p['parser_readiness'])], p['parser_readiness'])))
    steps.append(('external_parsers', run([sys.executable,'skills/03-code-knowledge-graph/scripts/run_external_parser_plugins.py',str(project),'--out',str(p['external_parsers']),'--validate'], p['external_parsers'])))
    steps.append(('code_graph', run([sys.executable,'skills/03-code-knowledge-graph/scripts/advanced_code_graph_extractor.py',str(project),'--output',str(p['code_graph'])], p['code_graph'])))
    steps.append(('authz_proof', run([sys.executable,'skills/03-code-knowledge-graph/scripts/authz_path_consistency_proof.py','--code-graph',str(p['code_graph']),'--out',str(p['authz_proof']),'--validate'], p['authz_proof'])))
    steps.append(('dataflow', run([sys.executable,'skills/07-vulnerability-hunting-engine/scripts/interprocedural_dataflow_analyzer.py','--code-graph',str(p['code_graph']),'--out',str(p['dataflow']),'--validate'], p['dataflow'])))
    steps.append(('js_audit', run([sys.executable,'skills/05-js-audit-runtime/scripts/advanced_js_runtime_extractor.py',str(project),'--out',str(p['js_audit'])], p['js_audit'])))
    steps.append(('js_dual_ast_sourcemap', run([sys.executable,'skills/05-js-audit-runtime/scripts/js_dual_backend_ast_sourcemap.py',str(project),'--out',str(p['js_dual']),'--validate'], p['js_dual'])))
    steps.append(('surface', run([sys.executable,'skills/04-attack-surface-mapping/scripts/attack_surface_builder.py','--inventory',str(p['inventory']),'--code-graph',str(p['code_graph']),'--js-audit',str(p['js_audit']),'--out',str(p['surface'])], p['surface'])))
    steps.append(('parameter_diff', run([sys.executable,'skills/04-attack-surface-mapping/scripts/frontend_backend_parameter_diff.py','--code-graph',str(p['code_graph']),'--js-audit',str(p['js_audit']),'--out',str(p['parameter_diff'])], p['parameter_diff'])))
    steps.append(('tenant_binding', run([sys.executable,'skills/04-attack-surface-mapping/scripts/tenant_object_binding_inferer.py','--code-graph',str(p['code_graph']),'--out',str(p['tenant_binding']),'--validate'], p['tenant_binding'])))
    steps.append(('canonical_candidates', run([sys.executable,'skills/07-vulnerability-hunting-engine/scripts/vulnerability_candidate_engine.py','--inventory',str(p['inventory']),'--code-graph',str(p['code_graph']),'--js-audit',str(p['js_audit']),'--surface',str(p['surface']),'--out',str(p['canonical_candidates'])], p['canonical_candidates'])))
    steps.append(('extended_candidates', run([sys.executable,'skills/07-vulnerability-hunting-engine/scripts/extended_detector_engine.py','--inventory',str(p['inventory']),'--code-graph',str(p['code_graph']),'--js-audit',str(p['js_audit']),'--surface',str(p['surface']),'--out',str(p['extended_candidates']),'--validate'], p['extended_candidates'])))
    steps.append(('performance_gate', run([sys.executable,'tools/performance_dedupe_noise_gate.py','--candidates',str(p['extended_candidates']),'--out',str(p['perf_gate'])], p['perf_gate'])))
    steps.append(('replay_plan', run([sys.executable,'skills/07-vulnerability-hunting-engine/scripts/candidate_to_replay_plan.py','--candidates',str(p['extended_candidates']),'--out',str(p['replay_plan'])], p['replay_plan'])))
    steps.append(('role_tenant_matrix', run([sys.executable,'skills/06-dynamic-browser-burp-mcp/scripts/role_tenant_authz_matrix_builder.py','--surface',str(p['surface']),'--candidates',str(p['extended_candidates']),'--out',str(p['role_tenant_matrix'])], p['role_tenant_matrix'])))
    steps.append(('playwright_multirole_replay_plan', run([sys.executable,'skills/06-dynamic-browser-burp-mcp/scripts/playwright_multirole_replay.py','--matrix',str(p['role_tenant_matrix']),'--out',str(p['playwright_replay'])], p['playwright_replay'])))
    steps.append(('graphql_replay_plan', run([sys.executable,'skills/06-dynamic-browser-burp-mcp/scripts/graphql_resolver_replay.py','--code-graph',str(p['code_graph']),'--out',str(p['graphql_replay'])], p['graphql_replay'])))
    steps.append(('websocket_replay_plan', run([sys.executable,'skills/06-dynamic-browser-burp-mcp/scripts/websocket_message_authz_replay.py','--code-graph',str(p['code_graph']),'--out',str(p['websocket_replay'])], p['websocket_replay'])))
    manifest_dirs=args.manifest_dir or [str(out/'manifests')]
    cmd=[sys.executable,'_shared/dashboard/manifest_index_builder.py','--out',str(p['manifest_index'])]
    for d in manifest_dirs: cmd += ['--manifest-dir', d]
    steps.append(('manifest_index', run(cmd, p['manifest_index'])))
    steps.append(('dashboard_from_manifest_index', run([sys.executable,'_shared/dashboard/dashboard_from_manifest_index.py','--manifest-index',str(p['manifest_index']),'--out',str(p['dashboard'])])))
    steps.append(('final_claim_guard_block_check', run([sys.executable,'_shared/quality/final_claim_guard.py','--claim-level','confirmed','--role-tenant-matrix',str(p['role_tenant_matrix']),'--manifest-index',str(p['manifest_index']),'--out',str(p['final_guard'])], p['final_guard'], allow_returncodes=(0,1))))
    steps.append(('cleanup_runtime_cache', run([sys.executable,'tools/cleanup_runtime_cache.py'])))
    steps.append(('reverse_acceptance_gate', run([sys.executable,'tools/reverse_acceptance_gate.py','--detector-output',str(p['extended_candidates']),'--scan-output',str(out),'--manifest-dir',str(out/'manifests'),'--out',str(p['reverse_acceptance'])], p['reverse_acceptance'])))
    def get(step,key,default=0):
        for n,r in steps:
            if n==step and isinstance(r.get('json'),dict): return r['json'].get(key,default)
        return default
    summary={'schema_version':'authorized_pipeline_summary_v3','project_root':str(project),'out_dir':str(out),'passed':all(r.get('ok') for n,r in steps if n!='final_claim_guard_block_check'),'steps':[{'name':n,'ok':r.get('ok'),'cmd':' '.join(map(str,r.get('cmd',[]))),'error':r.get('stderr') or r.get('parse_error')} for n,r in steps],'outputs':{k:str(v) for k,v in p.items()},'counts':{'files':get('inventory','file_count'),'routes':get('code_graph','route_count'),'sinks':get('code_graph','sink_count'),'parameters':get('code_graph','parameter_count'),'dataflow_paths':get('dataflow','path_count'),'authz_proofs':get('authz_proof','proof_count'),'backend_only_parameters':get('parameter_diff','backend_only_count'),'tenant_object_bindings':get('tenant_binding','binding_count'),'extended_candidates':get('extended_candidates','candidate_count'),'parser_runtime_ready_count':get('parser_readiness','runtime_ready_count'),'js_ready_backends':get('js_dual_ast_sourcemap','ready_backend_count')},'claim_policy':'All candidate engines remain non-confirming. Confirmed requires strict manifest, dynamic execution, request/response summaries, role/tenant or tenant/object proof when applicable, second-pass redaction, manifest-index dashboard and quality gate.'}
    p['summary'].write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2)); return 0 if summary['passed'] else 1
if __name__=='__main__':
    rc = main()
    sys.stdout.flush(); sys.stderr.flush()
    os._exit(rc)

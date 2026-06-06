#!/usr/bin/env python3
from __future__ import annotations
import contextlib, io, json, runpy, sys, shutil, time, traceback
from pathlib import Path

root=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve()
fixture=root/'fixtures/js-top-tier-samples/app'
hidden_front=root/'fixtures/js-hidden-param-samples/frontend'
hidden_back=root/'fixtures/js-hidden-param-samples/backend'
hidden_har=root/'fixtures/js-hidden-param-samples/sample.har'
out=root/'tests/js-top-tier-last-run'
if out.exists(): shutil.rmtree(out)
out.mkdir(parents=True, exist_ok=True)
commands=[
    ['collect', root/'scripts/js_top_tier_collect.py', ['--root', str(fixture), '--out', str(out)]],
    ['analyze', root/'scripts/js_top_tier_analyze.py', ['--ledger', str(out/'js_asset_ledger.json'), '--out', str(out)]],
    ['api-model', root/'scripts/js_api_parameter_model.py', ['--root', str(hidden_front), '--backend-root', str(hidden_back), '--har', str(hidden_har), '--out', str(out)]],
    ['backend-diff', root/'scripts/js_backend_param_diff.py', ['--api-model', str(out/'js_api_parameter_model.json'), '--out', str(out)]],
    ['wrapper-resolver', root/'scripts/js_wrapper_resolver.py', ['--root', str(hidden_front), '--out', str(out)]],
    ['schema-alignment', root/'scripts/js_schema_alignment.py', ['--root', str(root/'fixtures/js-hidden-param-samples'), '--api-model', str(out/'js_api_parameter_model.json'), '--out', str(out)]],
    ['hidden-feature', root/'scripts/js_hidden_feature_extractor.py', ['--root', str(fixture), '--out', str(out)]],
    ['business-flows', root/'scripts/js_business_flow_template_generator.py', ['--out', str(out)]],
    ['sourcemap-reconstruct', root/'scripts/js_sourcemap_reconstructor.py', ['--root', str(fixture), '--out', str(out/'sourcemap-reconstructed')]],
    ['framework-build', root/'scripts/js_framework_build_parser.py', ['--root', str(fixture), '--out', str(out)]],
    ['service-worker-cache', root/'scripts/js_service_worker_cache_auditor.py', ['--root', str(fixture), '--out', str(out)]],
    ['cdn-history', root/'scripts/js_cdn_history_asset_enumerator.py', ['--ledger', str(out/'js_asset_ledger.json'), '--out', str(out)]],
    ['browser-plan', root/'scripts/js_browser_lazyload_replay_plan.py', ['--url', 'http://127.0.0.1:3000/', '--out', str(out)]],
    ['playwright-generate-spec', root/'scripts/js_playwright_safe_replay_executor.py', ['--plan', str(out/'js_browser_replay_plan.json'), '--generate-spec', '--out', str(out)]],
    ['runtime-bridge', root/'scripts/js_runtime_evidence_bridge.py', ['--evidence-root', str(fixture), '--out', str(out)]],
    ['evidence-manifest', root/'scripts/js_runtime_evidence_manifest.py', ['--evidence-root', str(fixture), '--out', str(out)]],
    ['graphql-ws-runtime', root/'scripts/js_graphql_ws_runtime_replay.py', ['--scenarios', str(root/'fixtures/runtime-replay/graphql-ws-scenarios.json'), '--out', str(out)]],
    ['oss-registry', root/'scripts/js_oss_replay_registry.py', ['--samples-root', str(root/'fixtures/oss-replay'), '--out', str(out)]],
    ['severe-map', root/'scripts/js_severe_js_candidate_mapper.py', ['--api-model', str(out/'js_api_parameter_model.json'), '--param-diff', str(out/'js_backend_param_diff.json'), '--out', str(out)]],
    ['report', root/'scripts/js_top_tier_report_generator.py', ['--report-dir', str(out)]],
    ['dashboard-drilldown', root/'scripts/js_evidence_dashboard_drilldown.py', ['--report-dir', str(out)]],
    ['quality-1', root/'scripts/js_top_tier_quality_gate.py', ['--report-dir', str(out)]],
    ['self-audit', root/'scripts/js_self_audit_matrix.py', ['--root', str(root), '--report-dir', str(out)]],
    ['quality-2', root/'scripts/js_top_tier_quality_gate.py', ['--report-dir', str(out)]],
]

def run_script(name: str, script: Path, argv: list[str]):
    old_argv=sys.argv[:]
    sys.argv=[str(script)] + argv
    stdout=io.StringIO(); stderr=io.StringIO(); rc=0; tb=''
    started=time.time()
    try:
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            try:
                runpy.run_path(str(script), run_name='__main__')
            except SystemExit as e:
                rc = int(e.code) if isinstance(e.code,int) else (0 if e.code is None else 1)
    except Exception:
        rc=1; tb=traceback.format_exc()
    finally:
        sys.argv=old_argv
    (out/f'{name}.stdout.txt').write_text(stdout.getvalue(), encoding='utf-8')
    (out/f'{name}.stderr.txt').write_text(stderr.getvalue()+tb, encoding='utf-8')
    return {'name':name,'script':str(script),'argv':argv,'returncode':rc,'elapsed_ms':round((time.time()-started)*1000,2),'stdout_tail':stdout.getvalue()[-2000:],'stderr_tail':(stderr.getvalue()+tb)[-2000:]}

results=[]; progress=out/'runner-progress.log'; progress.write_text('', encoding='utf-8')
for name,script,argv in commands:
    progress.write_text(progress.read_text(encoding='utf-8')+f'START {name}\n', encoding='utf-8')
    result=run_script(name, script, argv)
    results.append(result)
    progress.write_text(progress.read_text(encoding='utf-8')+f'END {name} rc={result["returncode"]} elapsed={result["elapsed_ms"]}\n', encoding='utf-8')
    if result['returncode'] != 0:
        break

def load(p):
    try: return json.loads(p.read_text(encoding='utf-8'))
    except Exception: return {}
ledger=load(out/'js_asset_ledger.json'); analysis=load(out/'js_analysis.json'); gate=load(out/'js_quality_gate.json')
api_model=load(out/'js_api_parameter_model.json'); diff=load(out/'js_backend_param_diff.json'); severe=load(out/'js_severe_candidate_map.json'); runtime=load(out/'js_runtime_evidence.json'); selfaudit=load(out/'js_self_audit_matrix.json')
checks={
 'collects_js': ledger.get('stats',{}).get('javascript_assets',0) >= 2,
 'collects_sourcemap': ledger.get('stats',{}).get('sourcemaps',0) >= 1,
 'finds_graphql_or_ws': any(e.get('kind') in {'graphql_operation_candidate','websocket_candidate'} for e in ledger.get('evidence',[])),
 'api_parameter_model_generated': api_model.get('schema_version') == 'js-api-parameter-model/v1' and api_model.get('api_count',0) >= 1,
 'backend_param_diff_generated': diff.get('schema_version') == 'js-backend-param-diff/v1',
 'severe_candidate_map_generated': severe.get('schema_version') == 'js-severe-candidate-map/v1',
 'browser_plan_generated_but_not_ready': load(out/'js_browser_replay_plan.json').get('status') == 'plan-only',
 'runtime_bridge_runs_without_fake_ready': runtime.get('schema_version') == 'js-runtime-evidence/v2' and runtime.get('status') != 'ready',
 'evidence_manifest_generated_but_not_ready': load(out/'js_evidence_manifest.json').get('schema_version') == 'js-evidence-manifest/v1' and load(out/'js_evidence_manifest.json').get('status') != 'ready',
 'wrapper_resolver_generated': load(out/'js_wrapper_resolution.json').get('schema_version') == 'js-wrapper-resolution/v1',
 'schema_alignment_generated': load(out/'js_schema_alignment.json').get('schema_version') == 'js-schema-alignment/v1',
 'sourcemap_reconstruction_generated': load(out/'js_sourcemap_reconstruction.json').get('schema_version') == 'js-sourcemap-reconstruction/v1',
 'framework_build_parser_generated': load(out/'js_framework_build_artifacts.json').get('schema_version') == 'js-framework-build-parser/v1',
 'service_worker_cache_audit_generated': load(out/'js_service_worker_cache_audit.json').get('schema_version') == 'js-service-worker-cache-audit/v1',
 'cdn_history_generated': load(out/'js_cdn_history_assets.json').get('schema_version') == 'js-cdn-history-enumeration/v1',
 'graphql_ws_runtime_generated': load(out/'js_graphql_ws_runtime_replay.json').get('schema_version') == 'js-graphql-ws-runtime-replay/v1',
 'oss_registry_generated_not_real': load(out/'js_oss_replay_registry.json').get('schema_version') == 'js-oss-replay-registry/v1' and load(out/'js_oss_replay_registry.json').get('real_oss_replay_count') == 0,
 'drilldown_dashboard_generated': (out/'js_evidence_drilldown_dashboard.html').exists(),
 'quality_gate_strict_downgrade': gate.get('decision') == 'not-top-tier' and gate.get('overall_score',100) <= 60,
 'self_audit_v3_blocks_missing_dynamic': selfaudit.get('schema_version') == 'js-self-audit-matrix/v3' and bool(selfaudit.get('must_fix_p0')), 
 'findings_not_promoted_without_dynamic': all(f.get('status') != 'ready' for f in analysis.get('findings',[])),
}
ok=all(r['returncode']==0 for r in results) and all(checks.values())
summary={'ok':ok,'real_oss_replay':False,'results':results,'checks':checks,'out':str(out),'quality_gate_decision':gate.get('decision'),'overall_score':gate.get('overall_score'),'self_audit_p0':selfaudit.get('must_fix_p0',[])}
(root/'tests/js-top-tier-fixture-test-result.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(summary, ensure_ascii=False, indent=2))
raise SystemExit(0 if ok else 1)

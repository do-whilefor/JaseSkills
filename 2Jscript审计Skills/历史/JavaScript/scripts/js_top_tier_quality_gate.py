#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
from typing import Any

def load(p: Path, default):
    try: return json.loads(p.read_text(encoding='utf-8'))
    except Exception: return default

def backend_ready(analysis: dict[str,Any]) -> bool:
    return analysis.get('semantic_status') == 'ready' and analysis.get('ast_success_count',0) > 0 and analysis.get('ast_error_count',0) == 0

def runtime_ready(runtime: dict[str,Any]) -> bool:
    req = runtime.get('requirements', {}) if isinstance(runtime, dict) else {}
    return runtime.get('status') == 'ready' and all(req.get(k) for k in ('har','trace','screenshots','request_response','role_tenant_mapping'))

def runtime_partial(runtime: dict[str,Any]) -> bool:
    return runtime.get('status') in {'partial','evidence-present'} or bool(runtime.get('items'))

def role_tenant_ready(rtdiff: dict[str,Any]) -> bool:
    return rtdiff.get('status') == 'ready' and bool(rtdiff.get('authorization_validation')) and any(d.get('authorization_result') for d in rtdiff.get('diffs',[]))

def backend_acceptance_ready(accept: dict[str,Any]) -> bool:
    return accept.get('status') == 'ready' and any(x.get('verdict') == 'accepted-and-impactful' for x in accept.get('probes',[]))

def hidden_param_matrix_ready(matrix: dict[str,Any]) -> bool:
    s=matrix.get('summary',{}) if isinstance(matrix,dict) else {}
    return matrix.get('status') == 'ready' and bool(s.get('positive')) and bool(s.get('negative')) and bool(s.get('blocked'))

def main():
    ap=argparse.ArgumentParser(description='Strict JS top-tier quality gate. Plans and regex candidates never count as ready evidence.')
    ap.add_argument('--report-dir', default='reports/js-top-tier')
    ap.add_argument('--strict', action='store_true', help='exit non-zero when decision is not promotable or blocking conditions exist')
    args=ap.parse_args()
    d=Path(args.report_dir); d.mkdir(parents=True, exist_ok=True)
    ledger=load(d/'js_asset_ledger.json', {})
    analysis=load(d/'js_analysis.json', {})
    findings=load(d/'js_findings.json', {'findings':[]}).get('findings',[])
    api_model=load(d/'js_api_parameter_model.json', {})
    param_diff=load(d/'js_backend_param_diff.json', {})
    browser_plan=load(d/'js_browser_replay_plan.json', {})
    severe_map=load(d/'js_severe_candidate_map.json', {})
    self_audit=load(d/'js_self_audit_matrix.json', {})
    evidence_manifest=load(d/'js_evidence_manifest.json', {})
    wrapper_resolution=load(d/'js_wrapper_resolution.json', {})
    schema_alignment=load(d/'js_schema_alignment.json', {})
    gql_ws_runtime=load(d/'js_graphql_ws_runtime_replay.json', {})
    oss_registry=load(d/'js_oss_replay_registry.json', {})
    env_check=load(d.parent/'env-check/js_env_check.json', {}) if (d.parent/'env-check/js_env_check.json').exists() else load(d/'js_env_check.json', {})
    runtime=load(d/'js_runtime_evidence.json', {})
    rtdiff=load(d/'js_role_tenant_diff.json', {})
    acceptance=load(d/'js_backend_acceptance_evidence.json', {})
    hidden_matrix=load(d/'js_hidden_param_acceptance_matrix.json', {})
    runtime_binding=load(d/'js_runtime_detector_binding.json', {})
    real_oss=load(d/'real-oss-replay/js_real_oss_replay_result.json', {})
    authorized_gate=load(d/'js_authorized_target_import_gate.json', {})
    playwright_exec=load(d/'playwright-probe/js_playwright_execution.json', {})
    stats=ledger.get('stats',{})
    caps=[]; blocking=[]

    js_collection=0
    if stats.get('javascript_assets',0) > 0: js_collection += 35
    if stats.get('sourcemaps',0) > 0: js_collection += 15
    if stats.get('manifests',0) > 0: js_collection += 10
    if stats.get('service_workers',0) > 0: js_collection += 10
    if any(e.get('kind') in {'graphql_operation_candidate','websocket_candidate'} for e in ledger.get('evidence',[])): js_collection += 10
    if runtime_ready(runtime): js_collection += 20
    else: caps.append('没有执行态 runtime 证据，动态 chunk / 浏览器缓存 / 懒加载覆盖不能计入最高档')

    js_semantic=80 if backend_ready(analysis) else (35 if analysis.get('semantic_status') == 'candidate-only' else 20)
    if not backend_ready(analysis):
        caps.append('AST backend 未产出无错误语义结果，语义审计不得 ready')
        blocking.append('AST backend not proven ready')

    if runtime_ready(runtime) and authorized_gate.get('status') == 'ready': dynamic=90
    elif runtime_ready(runtime): dynamic=55; caps.append('runtime artifact bundle ready 但不是非 fixture 授权目标导入，不能作为真实目标动态验证')
    elif runtime_partial(runtime): dynamic=25; caps.append('只有部分 HAR/trace/screenshot 证据，动态验证不能 promoted')
    elif browser_plan.get('schema_version') == 'js-browser-replay-plan/v1': dynamic=5; caps.append('只有浏览器 replay 计划，动态验证按 5 分处理')
    else: dynamic=0; caps.append('没有 Playwright/Burp/HAR 动态证据')

    if role_tenant_ready(rtdiff): role_tenant=85
    elif rtdiff.get('status') in {'partial','evidence-present'}: role_tenant=25; caps.append('存在多角色/多租户对比数据但无授权结果验证')
    else: role_tenant=0; caps.append('没有多角色/多租户 replay，严重漏洞能力阻断')

    if api_model.get('schema_version') == 'js-api-parameter-model/v1' and api_model.get('api_count',0) > 0:
        api_param=65
        if backend_ready(analysis): api_param += 10
        if runtime_ready(runtime): api_param += 10
    elif api_model.get('schema_version') == 'js-api-parameter-model/v1':
        api_param=35; caps.append('API 参数模型存在但未提取到 API')
    else:
        api_param=0; caps.append('缺少 API 参数模型')

    if backend_acceptance_ready(acceptance):
        backend_diff=85
    elif hidden_param_matrix_ready(hidden_matrix):
        backend_diff=75; caps.append('hidden param 已有 positive/negative/blocked acceptance matrix，但没有 accepted-and-impactful，不得确认漏洞')
    elif param_diff.get('schema_version') == 'js-backend-param-diff/v1':
        backend_diff=25; caps.append('前后端参数差异只有候选，没有后端接受性请求/响应证据')
        blocking.append('backend hidden-param acceptance matrix missing')
    else:
        backend_diff=0; caps.append('缺少前后端参数差异模型和 hidden-param acceptance matrix')

    if severe_map.get('schema_version') == 'js-severe-candidate-map/v1':
        if runtime_ready(runtime) and role_tenant_ready(rtdiff): severe_chain=75
        else:
            severe_chain=25; caps.append('严重漏洞只有候选映射，缺 runtime + role/tenant 证据')
            blocking.append('severe vulnerability chain not dynamically validated')
    else:
        severe_chain=0; caps.append('缺少严重漏洞候选映射')

    fixture_result=load(d.parent/'js-top-tier-fixture-test-result.json', {}) if (d.parent/'js-top-tier-fixture-test-result.json').exists() else load(d/'js-top-tier-fixture-test-result.json', {})
    tests=55 if fixture_result.get('ok') else 30
    if not fixture_result.get('real_oss_replay'):
        tests=min(tests,40); caps.append('fixture 不是真实 OSS replay，测试最高 40')

    required_finding_fields={'finding_id','rule_id','title','status','asset_path','evidence_path','backend','dynamic_validation','role_tenant_replay','report_section','reason'}
    field_ok=findings and all(required_finding_fields.issubset(set(f)) for f in findings)
    evidence=25 if field_ok else 10
    if runtime_ready(runtime): evidence += 35
    if role_tenant_ready(rtdiff): evidence += 20
    if backend_acceptance_ready(acceptance): evidence += 15
    if not runtime_ready(runtime): blocking.append('runtime evidence manifest missing or not ready')
    if authorized_gate.get('status') != 'ready':
        blocking.append('non-fixture authorized target runtime artifact import missing')
        caps.append('未导入用户真实授权目标的 HAR/trace/screenshot/DOM/console/role_tenant_matrix，真实目标动态验证阻断')
    if playwright_exec.get('status') == 'environment_blocked':
        caps.append('本环境 Playwright/Chromium 被策略阻断，执行录制不能计为 ready')
    if evidence_manifest.get('status') != 'ready':
        blocking.append('redacted evidence manifest missing or not ready')
        caps.append('缺 HAR/trace/screenshots/request-response/role-tenant 的 evidence manifest，动态证据链阻断')
    if not env_check.get('ready'):
        caps.append('一键安装/环境自检未 ready；AST/browser 依赖不能视为可用')
    if wrapper_resolution.get('schema_version') != 'js-wrapper-resolution/v1':
        caps.append('缺 wrapper resolver 产物，axios/fetch 封装可能漏报')
    if schema_alignment.get('schema_version') != 'js-schema-alignment/v1':
        caps.append('缺 schema 对齐产物，hidden param 可能漏报')
    if gql_ws_runtime.get('schema_version') != 'js-graphql-ws-runtime-replay/v1' and runtime_binding.get('schema_version') != 'js-runtime-detector-binding/v1':
        caps.append('缺 GraphQL/WebSocket/postMessage runtime binding 产物，相关漏洞不得 promoted')
    elif runtime_binding.get('status') != 'ready':
        caps.append('GraphQL/WebSocket/postMessage runtime binding 未 ready，相关 detector 不得 confirmed')
    real_oss_count=max(oss_registry.get('real_oss_replay_count',0), 1 if real_oss.get('status') in {'ready','environment_blocked'} else 0)
    if real_oss_count < 10:
        caps.append('真实 OSS replay 样本不足 10 个，泛化能力不能声称顶级')

    report_mapping=75 if (d/'js_top_tier_report.md').exists() and ((d/'js_evidence_drilldown_dashboard.html').exists() or (d/'js_top_tier_dashboard.html').exists()) else 30
    self_review=75 if self_audit.get('schema_version') == 'js-self-audit-matrix/v3' and not self_audit.get('must_fix_p0') else 30
    if self_audit.get('must_fix_p0'): blocking.extend([f"self-audit P0: {x}" for x in self_audit.get('must_fix_p0',[])[:10]])

    weights={'js_collection':0.10,'js_semantic_audit':0.14,'dynamic_validation':0.16,'role_tenant_replay':0.12,'api_parameter_model':0.10,'backend_param_diff':0.12,'severe_candidate_chain':0.10,'tests':0.06,'evidence_chain':0.06,'report_mapping':0.02,'self_review':0.02}
    scores={'js_collection':js_collection,'js_semantic_audit':js_semantic,'dynamic_validation':dynamic,'role_tenant_replay':role_tenant,'api_parameter_model':api_param,'backend_param_diff':backend_diff,'severe_candidate_chain':severe_chain,'tests':tests,'evidence_chain':evidence,'report_mapping':report_mapping,'self_review':self_review}
    overall=round(sum(scores[k]*weights[k] for k in weights),2)

    if any(f.get('status') == 'ready' and (f.get('dynamic_validation') in {'未动态验证','missing',''} or f.get('role_tenant_replay') in {'缺少 role/tenant replay','missing',''}) for f in findings):
        blocking.append('存在未动态验证或缺 role/tenant 却标 ready 的 finding')
        overall=min(overall,25)
    if authorized_gate.get('status') != 'ready': overall=min(overall,72)
    if not runtime_ready(runtime): overall=min(overall,55)
    if authorized_gate.get('status') != 'ready':
        blocking.append('non-fixture authorized target runtime artifact import missing')
        caps.append('未导入用户真实授权目标的 HAR/trace/screenshot/DOM/console/role_tenant_matrix，真实目标动态验证阻断')
    if playwright_exec.get('status') == 'environment_blocked':
        caps.append('本环境 Playwright/Chromium 被策略阻断，执行录制不能计为 ready')
    if evidence_manifest.get('status') != 'ready': overall=min(overall,55)
    if max(oss_registry.get('real_oss_replay_count',0), 1 if real_oss.get('status') in {'ready','environment_blocked'} else 0) < 10: overall=min(overall,70)
    if not role_tenant_ready(rtdiff): overall=min(overall,55)
    if not backend_ready(analysis): overall=min(overall,60)
    if not backend_acceptance_ready(acceptance) and not hidden_param_matrix_ready(hidden_matrix): overall=min(overall,60)
    decision='promotable' if overall >= 90 and not blocking else 'not-top-tier'
    gate={'schema_version':'js-top-tier-quality-gate/v4','overall_score':overall,'scores':scores,'caps':caps,'blocking':sorted(set(blocking)),'decision':decision,'ready_conditions':{'ast_backend_ready':backend_ready(analysis),'runtime_ready':runtime_ready(runtime),'role_tenant_ready':role_tenant_ready(rtdiff),'backend_acceptance_ready':backend_acceptance_ready(acceptance),'hidden_param_matrix_ready':hidden_param_matrix_ready(hidden_matrix),'runtime_detector_binding_ready':runtime_binding.get('status')=='ready','authorized_target_import_ready':authorized_gate.get('status')=='ready','playwright_execution_status':playwright_exec.get('status'),'real_oss_replay_count':max(oss_registry.get('real_oss_replay_count',0), 1 if real_oss.get('status') in {'ready','environment_blocked'} else 0)},'required_next_p0':['import_non_fixture_authorized_target_runtime_artifacts','execute_playwright_or_import_har_trace_screenshots_with_role_tenant_mapping','build_redacted_evidence_manifest','perform_role_tenant_replay_with_authorization_result','prove_backend_extra_param_acceptance_before_reporting','execute_graphql_websocket_runtime_replay','run_wrapper_resolver_and_schema_alignment','add_10_real_oss_replay_samples','generate_evidence_drilldown_dashboard','pass_one_click_env_check','complete_self_audit_matrix_v3']}
    (d/'js_quality_gate.json').write_text(json.dumps(gate, ensure_ascii=False, indent=2), encoding='utf-8')
    md=['# JS Top Tier Quality Gate','',f"Decision: `{decision}`",f"Overall score: `{overall}/100`",'', '## Scores']
    md += [f'- {k}: {v}' for k,v in scores.items()]
    md += ['', '## Ready Conditions'] + [f'- {k}: {v}' for k,v in gate['ready_conditions'].items()]
    md += ['', '## Caps'] + [f'- {c}' for c in caps]
    md += ['', '## Blocking'] + ([f'- {b}' for b in sorted(set(blocking))] if blocking else ['- none'])
    (d/'js_quality_gate_report.md').write_text('\n'.join(md)+'\n', encoding='utf-8')
    ok_for_mode = decision == 'promotable' and not blocking
    print(json.dumps({'ok': (ok_for_mode if args.strict else True), 'decision': decision, 'overall_score': overall, 'strict': args.strict, 'blocking_count': len(sorted(set(blocking))), 'out': str(d/'js_quality_gate.json')}, ensure_ascii=False, indent=2))
    if args.strict and not ok_for_mode:
        raise SystemExit(1)
if __name__ == '__main__': main()

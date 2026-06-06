#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
from typing import Any

CHECKS=[
 ('skill_files_complete','检查每个 Skill 文件','custom'),
 ('static_js_collection','静态 JS 收集','json:js_asset_ledger.json:stats.javascript_assets:gt0'),
 ('sourcemap_reconstruction','sourcemap 完整还原','json:js_sourcemap_reconstruction.json:schema_version:eq:js-sourcemap-reconstruction/v1'),
 ('framework_build_parser','Next/Nuxt/Vite/Webpack 构建产物解析','json:js_framework_build_artifacts.json:schema_version:eq:js-framework-build-parser/v1'),
 ('service_worker_cache','service worker cache 候选/运行 dump','json:js_service_worker_cache_audit.json:schema_version:eq:js-service-worker-cache-audit/v1'),
 ('cdn_history_assets','CDN 历史资产候选枚举','json:js_cdn_history_assets.json:schema_version:eq:js-cdn-history-enumeration/v1'),
 ('wrapper_resolver','axios/fetch wrapper resolver','json:js_wrapper_resolution.json:schema_version:eq:js-wrapper-resolution/v1'),
 ('schema_alignment','OpenAPI/Postman/zod/yup/joi/DTO/model 对齐','json:js_schema_alignment.json:schema_version:eq:js-schema-alignment/v1'),
 ('hidden_feature_signals','i18n/feature flag/analytics/route meta 隐藏功能提取','json:js_hidden_feature_signals.json:schema_version:eq:js-hidden-feature-extraction/v1'),
 ('business_flow_templates','OAuth/SSO/支付/审批/成员权限等专项模板','json:js_business_flow_templates.json:schema_version:eq:js-business-flow-templates/v1'),
 ('dynamic_chunk_lazyload','动态 chunk / 懒加载触发','runtime_ready'),
 ('real_browser_interaction','真实浏览器交互执行证据','runtime_ready'),
 ('runtime_evidence_manifest','HAR/trace/screenshots/request-response evidence manifest','evidence_manifest_ready'),
 ('login_roles_tenants','登录态/多角色/多租户','role_tenant_ready'),
 ('har_burp_runtime','HAR/Burp/trace runtime evidence','runtime_ready'),
 ('api_parameter_model','API 与参数逆向建模','json:js_api_parameter_model.json:api_count:gt0'),
 ('backend_param_diff','前后端参数差异候选','json:js_backend_param_diff.json:schema_version:eq:js-backend-param-diff/v1'),
 ('backend_acceptance','后端接受性请求/响应证据','backend_acceptance_ready'),
 ('graphql_ws_runtime','GraphQL/WebSocket runtime replay','json:js_graphql_ws_runtime_replay.json:schema_version:eq:js-graphql-ws-runtime-replay/v1'),
 ('severe_candidate_map','严重漏洞候选映射','json:js_severe_candidate_map.json:schema_version:eq:js-severe-candidate-map/v1'),
 ('oss_replay_samples','真实 OSS replay 样本','oss_replay_ready'),
 ('env_check','一键安装和环境自检','env_check_ready'),
 ('quality_gate','质量门槛','json:js_quality_gate.json:schema_version:prefix:js-top-tier-quality-gate/'),
 ('report_dashboard','证据链 drill-down dashboard','file:js_evidence_drilldown_dashboard.html'),
]
P0={'dynamic_chunk_lazyload','real_browser_interaction','runtime_evidence_manifest','login_roles_tenants','har_burp_runtime','backend_acceptance','graphql_ws_runtime','oss_replay_samples','env_check','quality_gate','report_dashboard'}

def load(p: Path, default=None):
    try: return json.loads(p.read_text(encoding='utf-8'))
    except Exception: return default if default is not None else {}

def dotted(obj: dict[str,Any], path: str):
    cur=obj
    for part in path.split('.'):
        if not isinstance(cur,dict): return None
        cur=cur.get(part)
    return cur

def runtime_ready(rd: Path):
    runtime=load(rd/'js_runtime_evidence.json', {})
    req=runtime.get('requirements', {})
    ready=runtime.get('status') == 'ready' and all(req.get(k) for k in ('har','trace','screenshots','request_response','role_tenant_mapping'))
    return ready, [str(rd/'js_runtime_evidence.json')] if runtime else [], [] if ready else ['missing executed HAR+trace+screenshots+request_response+role_tenant_mapping']

def evidence_manifest_ready(rd: Path):
    ev=load(rd/'js_evidence_manifest.json', {})
    req=ev.get('runtime_requirements', {})
    ready=ev.get('status') == 'ready' and all(req.get(k) for k in ('har','trace','screenshots','request_response','role_tenant_mapping'))
    return ready, [str(rd/'js_evidence_manifest.json')] if ev else [], [] if ready else ['missing redacted evidence manifest with all runtime requirements']

def role_tenant_ready(rd: Path):
    rt=load(rd/'js_role_tenant_diff.json', {})
    ready=rt.get('status') == 'ready' and bool(rt.get('authorization_validation')) and any(d.get('authorization_result') for d in rt.get('diffs',[]))
    return ready, [str(rd/'js_role_tenant_diff.json')] if rt else [], [] if ready else ['missing role/tenant authorization result']

def backend_acceptance_ready(rd: Path):
    ev=load(rd/'js_backend_acceptance_evidence.json', {})
    ready=ev.get('status') == 'ready' and any(x.get('verdict') == 'accepted-and-impactful' for x in ev.get('probes',[]))
    return ready, [str(rd/'js_backend_acceptance_evidence.json')] if ev else [], [] if ready else ['missing non-destructive request/response proving backend acceptance and impact']

def oss_replay_ready(rd: Path):
    ev=load(rd/'js_oss_replay_registry.json', {})
    ready=ev.get('real_oss_replay_count',0) >= 10
    return ready, [str(rd/'js_oss_replay_registry.json')] if ev else [], [] if ready else [f"real_oss_replay_count={ev.get('real_oss_replay_count','missing')}; need >=10"]

def env_check_ready(rd: Path):
    ev=load(rd/'../env-check/js_env_check.json', {}) if (rd/'../env-check/js_env_check.json').exists() else load(rd/'js_env_check.json', {})
    ready=bool(ev.get('ready'))
    return ready, [str((rd/'../env-check/js_env_check.json').resolve())] if ev else [], [] if ready else ['environment check not ready or missing']

def eval_check(root: Path, rd: Path, spec: str):
    if spec == 'custom':
        dirs=[p for p in root.glob('[0-9][0-9]-*') if p.is_dir()]
        missing=[str(p.relative_to(root)) for p in dirs if not (p/'SKILL.md').exists()]
        return bool(dirs) and not missing, [str((p/'SKILL.md').relative_to(root)) for p in dirs[:80] if (p/'SKILL.md').exists()], missing
    if spec == 'runtime_ready': return runtime_ready(rd)
    if spec == 'evidence_manifest_ready': return evidence_manifest_ready(rd)
    if spec == 'role_tenant_ready': return role_tenant_ready(rd)
    if spec == 'backend_acceptance_ready': return backend_acceptance_ready(rd)
    if spec == 'oss_replay_ready': return oss_replay_ready(rd)
    if spec == 'env_check_ready': return env_check_ready(rd)
    if spec.startswith('file:'):
        q=rd/spec.split(':',1)[1]
        return q.exists(), [str(q)] if q.exists() else [], [] if q.exists() else [str(q)]
    if spec.startswith('json:'):
        parts=spec.split(':')
        file, key, op = parts[1], parts[2], parts[3]
        expected=parts[4] if len(parts)>4 else None
        q=rd/file; obj=load(q,{})
        value=dotted(obj,key)
        ok=False
        if op=='gt0': ok=isinstance(value,(int,float)) and value>0
        elif op=='eq': ok=value==expected
        elif op=='prefix': ok=isinstance(value,str) and value.startswith(expected)
        return ok, [str(q)] if q.exists() else [], [] if ok else [f'{q}:{key} failed {op} {expected or ""}; actual={value!r}']
    return False, [], [f'unknown check spec: {spec}']

def main():
    ap=argparse.ArgumentParser(description='Evidence-first self-audit v3. Plan-only files never satisfy runtime capability.')
    ap.add_argument('--root', default='.')
    ap.add_argument('--report-dir', default='reports/js-top-tier')
    args=ap.parse_args(); root=Path(args.root).resolve(); rd=Path(args.report_dir).resolve(); rd.mkdir(parents=True, exist_ok=True)
    rows=[]; p0=[]
    for cid,title,spec in CHECKS:
        ok, ev, missing = eval_check(root, rd, spec)
        status='verified-evidence' if ok else 'missing-or-unverified'
        if not ok and cid in P0: p0.append(cid)
        rows.append({'check_id':cid,'title':title,'status':status,'evidence':ev,'missing':missing,'downgrade':'' if ok else '未满足证据条件，不能 promoted/ready'})
    result={'schema_version':'js-self-audit-matrix/v3','status':'blocked' if p0 else 'evidence-present','checks':rows,'must_fix_p0':p0,'verdict':'not-top-tier-until-p0-fixed' if p0 else 'evidence-chain-present-but-findings-still-need-case-by-case-validation','non_negotiable_rule':'plan-only browser replay, regex candidates, README claims, templates, schemas, and sample registries without generated evidence never count as ready capability'}
    (rd/'js_self_audit_matrix.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    md=['# JS Self Audit Matrix v3','',f"Verdict: `{result['verdict']}`",'', '| check | status | evidence / missing |', '| --- | --- | --- |']
    for r in rows:
        msg='; '.join(r['evidence']) if r['evidence'] else '; '.join(r['missing'])
        md.append(f"| {r['title']} | {r['status']} | {msg} |")
    md += ['', '## P0', *([f'- {x}' for x in p0] if p0 else ['- none'])]
    (rd/'js_self_audit_matrix.md').write_text('\n'.join(md)+'\n', encoding='utf-8')
    print(json.dumps({'ok':True,'out':str(rd/'js_self_audit_matrix.json'),'verdict':result['verdict'],'p0':p0}, ensure_ascii=False, indent=2))
if __name__=='__main__': main()

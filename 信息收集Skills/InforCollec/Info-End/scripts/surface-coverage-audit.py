#!/usr/bin/env python3
"""Audit whether information-collection coverage is backed by files/scripts/tests.

This is a package self-audit helper. It does not scan targets; it checks the
Skill package itself and optional JSONL evidence produced by the inventory tools.
"""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path

DIMENSIONS=[
('project_structure','项目目录结构与模块边界',['scripts/code-surface-inventory.py','scripts/codegraph-builder.py'],['tests/test_code_surface_inventory.py','tests/test_codegraph_builder.py'],['dependency_or_deployment_manifest','data_asset']),
('language_detection','编程语言识别',['scripts/code-surface-inventory.py','scripts/codegraph-builder.py'],['tests/test_code_surface_inventory.py'],['language','extension']),
('framework_detection','框架识别',['scripts/code-surface-inventory.py','scripts/config-dependency-inventory.py'],['tests/test_config_dependency_inventory.py'],['framework','dependency_entry']),
('route_detection','路由识别',['scripts/code-surface-inventory.py','scripts/route-artifact-extract.py'],['tests/test_code_surface_inventory.py'],['http_route','route']),
('api_entry_detection','API 入口识别',['scripts/code-surface-inventory.py','scripts/api-spec-inventory.py'],['tests/test_api_spec_inventory.py'],['openapi_path_operation','url_or_path_hidden_candidate']),
('codegraph_relations','controller/handler/service/model/middleware 关系识别',['scripts/codegraph-builder.py'],['tests/test_codegraph_builder.py'],['node','edge']),
('auth_entry','认证入口识别',['scripts/code-surface-inventory.py','scripts/hidden-info-miner.py'],['tests/test_hidden_info_miner.py'],['auth_cors_cookie_oauth_hint']),
('authorization_logic','鉴权逻辑识别',['scripts/code-surface-inventory.py','scripts/source-sink-dataflow.py'],['tests/test_source_sink_dataflow.py'],['auth_context']),
('role_model','角色模型识别',['scripts/hidden-info-miner.py','scripts/playwright-har-role-matrix.mjs'],['tests/test_role_matrix_contract.py'],['test_seed_default_account_or_role']),
('tenant_boundary','多租户边界识别',['scripts/source-sink-dataflow.py','scripts/hidden-info-miner.py'],['tests/test_source_sink_dataflow.py'],['tenant']),
('parameter_source','参数来源识别',['scripts/code-surface-inventory.py','scripts/js-asset-audit.py'],['tests/test_js_asset_audit.py'],['parameter']),
('sensitive_params','敏感参数识别',['scripts/hidden-info-miner.py','scripts/config-dependency-inventory.py'],['tests/test_hidden_info_miner.py'],['secret_name_or_credential_key']),
('file_upload','文件上传入口识别',['scripts/code-surface-inventory.py','scripts/source-sink-dataflow.py'],['tests/test_source_sink_dataflow.py'],['upload']),
('file_read','文件读取入口识别',['scripts/source-sink-dataflow.py'],['tests/test_source_sink_dataflow.py'],['arbitrary_file_access_candidate']),
('file_write','文件写入入口识别',['scripts/source-sink-dataflow.py'],['tests/test_source_sink_dataflow.py'],['file_read_write']),
('ssrf','SSRF URL/webhook/callback/proxy/fetch/request 入口识别',['scripts/source-sink-dataflow.py','scripts/hidden-info-miner.py'],['tests/test_source_sink_dataflow.py'],['ssrf_candidate','domain_or_callback_url_hint']),
('command_execution','命令执行入口识别',['scripts/source-sink-dataflow.py'],['tests/test_source_sink_dataflow.py'],['command_injection_candidate']),
('template_rendering','模板渲染入口识别',['scripts/source-sink-dataflow.py'],['tests/test_source_sink_dataflow.py'],['template_injection_candidate']),
('sql_nosql_orm','SQL/NoSQL/ORM 查询入口识别',['scripts/source-sink-dataflow.py'],['tests/test_source_sink_dataflow.py'],['sql_injection_candidate','nosql_injection_candidate']),
('graphql','GraphQL schema/resolver/introspection/operation 信息识别',['scripts/api-spec-inventory.py','scripts/graphql-nondestructive-probe.sh'],['tests/test_api_spec_inventory.py'],['graphql_operation','graphql_schema_type']),
('ws_sse_rpc_grpc','WebSocket/SSE/RPC/gRPC 入口识别',['scripts/api-spec-inventory.py','scripts/ws-readonly-capture.mjs','scripts/hidden-info-miner.py'],['tests/test_ws_capture_contract.py','tests/test_api_spec_inventory.py'],['websocket_event_name','grpc_rpc_method']),
('admin','管理后台入口识别',['scripts/code-surface-inventory.py','scripts/hidden-info-miner.py'],['tests/test_hidden_info_miner.py'],['admin']),
('debug','调试接口识别',['scripts/code-surface-inventory.py','scripts/hidden-info-miner.py'],['tests/test_hidden_info_miner.py'],['debug']),
('health','健康检查接口识别',['scripts/code-surface-inventory.py','scripts/exposure-probe-safe.sh'],['tests/test_code_surface_inventory.py'],['health']),
('docs_interfaces','文档接口 Swagger/OpenAPI/Redoc/Postman 识别',['scripts/api-spec-inventory.py','scripts/code-surface-inventory.py'],['tests/test_api_spec_inventory.py'],['openapi_path_operation','postman_request']),
('cicd','CI/CD 配置识别',['scripts/hidden-info-miner.py','scripts/config-dependency-inventory.py'],['tests/test_hidden_info_miner.py'],['cicd_deployment_or_secret_name_hint']),
('deployment_iac','Docker/Compose/Kubernetes/Helm/Terraform/Ansible 部署信息识别',['scripts/deployment-readonly-inventory.sh','scripts/hidden-info-miner.py'],['tests/test_hidden_info_miner.py'],['container_iac_internal_service_hint']),
('env_refs','环境变量引用识别',['scripts/config-dependency-inventory.py','scripts/hidden-info-miner.py'],['tests/test_config_dependency_inventory.py'],['environment_variant_config']),
('secrets','secrets/token/key/credential 风险线索识别',['scripts/redact-sensitive.py','scripts/hidden-info-miner.py'],['tests/test_hidden_info_miner.py'],['secret_name_or_credential_key']),
('third_party','第三方服务识别',['scripts/config-dependency-inventory.py','scripts/hidden-info-miner.py'],['tests/test_hidden_info_miner.py'],['cloud_or_third_party_service_hint']),
('domains_cors_oauth','域名/子域/回调域/CORS/OAuth redirect_uri 识别',['scripts/hidden-info-miner.py','scripts/config-dependency-inventory.py'],['tests/test_hidden_info_miner.py'],['domain_or_callback_url_hint','auth_cors_cookie_oauth_hint']),
('security_headers_auth_config','CSP/CORS/cookie/session/JWT/OAuth/SAML/OIDC 配置识别',['scripts/hidden-info-miner.py','scripts/config-dependency-inventory.py'],['tests/test_hidden_info_miner.py'],['auth_cors_cookie_oauth_hint']),
('logging_monitoring','日志/审计/监控/analytics/Sentry/Datadog/Grafana/Prometheus 识别',['scripts/hidden-info-miner.py'],['tests/test_hidden_info_miner.py'],['cloud_or_third_party_service_hint']),
('frontend_hidden','前端路由/接口/隐藏页面/feature flag/实验功能识别',['scripts/js-asset-audit.py','scripts/hidden-info-miner.py'],['tests/test_js_asset_audit.py','tests/test_hidden_info_miner.py'],['feature_flag_or_experiment','manifest_path_or_asset']),
('js_artifacts','JS bundle/chunk/source map/service worker/manifest/build artifact 识别',['scripts/js-asset-audit.py','scripts/js-manifest-expander.py','scripts/hidden-info-miner.py'],['tests/test_js_asset_audit.py','tests/test_js_manifest_expander.py'],['source_map_reference','service_worker_cache_or_route_hint']),
('mobile_desktop_electron','移动端/桌面端/Electron/浏览器插件信息识别',['scripts/js-asset-audit.py','scripts/package-artifact-readonly-inventory.py'],['tests/test_js_asset_audit.py'],['electron','mobile']),
('tests_fixtures','测试文件/fixture/mock/seed/demo account/example config 识别',['scripts/hidden-info-miner.py'],['tests/test_hidden_info_miner.py'],['test_seed_default_account_or_role']),
('backup_legacy_temp','备份文件/旧接口/废弃接口/迁移脚本/临时文件识别',['scripts/package-artifact-readonly-inventory.py','scripts/hidden-info-miner.py'],['tests/test_hidden_info_miner.py'],['deprecated','migration']),
('dependency_risk','依赖漏洞信息与危险依赖配置识别',['scripts/config-dependency-inventory.py'],['tests/test_config_dependency_inventory.py'],['dependency_entry']),
('attack_surface_graph','攻击面知识图谱生成能力',['scripts/codegraph-builder.py','scripts/shadow-ledger-diff.py'],['tests/test_codegraph_builder.py'],['nodes','edges'])]

def read_jsonl(paths):
    rows=[]
    for p in paths:
        pp=Path(p)
        if not pp.exists(): continue
        for line in pp.read_text(encoding='utf-8',errors='ignore').splitlines():
            try: rows.append(json.loads(line))
            except Exception: pass
    return rows

def main():
    ap=argparse.ArgumentParser(description='Check package coverage bindings and optional evidence rows.')
    ap.add_argument('--root', default='.')
    ap.add_argument('--jsonl', action='append', default=[], help='Optional inventory JSONL output to inspect')
    ap.add_argument('--out', default='-')
    args=ap.parse_args()
    root=Path(args.root).resolve()
    rows=read_jsonl(args.jsonl)
    blob='\n'.join(json.dumps(r,ensure_ascii=False) for r in rows).lower()
    results=[]
    for key,label,scripts,tests,signals in DIMENSIONS:
        script_ok=[s for s in scripts if (root/s).exists()]
        test_ok=[t for t in tests if (root/t).exists()]
        signal_ok=[sig for sig in signals if sig.lower() in blob]
        if script_ok and test_ok and (not rows or signal_ok): status='implemented' if rows else 'unverifiable'
        elif script_ok and (test_ok or signal_ok): status='partial'
        elif script_ok: status='partial'
        else: status='missing'
        results.append({'dimension':key,'label':label,'status':status,'evidence_files':script_ok,'tests':test_ok,'signals_found':signal_ok,'failure_scenario':'No runtime/dynamic evidence or missing signal keeps this at candidate/unverifiable level.' if status!='implemented' else 'Still requires authorized runtime validation before finding promotion.','required_fix':'Add script/test/fixture/output binding or run inventory tools and feed JSONL evidence.' if status!='implemented' else 'Keep QG and role/tenant validation gates.'})
    report={'schema_version':'surface-coverage-audit.v1','root':str(root),'jsonl_inputs':args.jsonl,'summary':{s:sum(1 for r in results if r['status']==s) for s in ['implemented','partial','missing','unverifiable']},'results':results}
    text=json.dumps(report,ensure_ascii=False,indent=2)
    if args.out=='-': print(text)
    else: Path(args.out).write_text(text,encoding='utf-8')
    return 0 if report['summary']['missing']==0 else 1
if __name__=='__main__':
    raise SystemExit(main())

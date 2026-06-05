# SOURCE_SENTENCE_TO_SKILL_RULE

Purpose: sentence/rule level traceability map used by selftest and dashboard.

| Source requirement | Enforced file/rule | Test/quality hook |
|---|---|---|
| 多语言 AST 插件体系必须真实落地，不得把 manual/optional 误报为 ready | `skills/03-code-knowledge-graph/scripts/parser_plugins/PARSER_PLUGIN_REGISTRY.json`, `advanced_code_graph_extractor.py` | `parser_backends.statuses[*].ready`, graph provenance claim policy |
| security graph 必须符合 schema | `_shared/security_graph/SECURITY_GRAPH_SCHEMA.json`, `advanced_code_graph_extractor.py` | graph emits `schema_version=security_graph_v3`, `metadata`, `nodes`, `edges`, `provenance` |
| sourcemap 必须重新进入 JS extractor | `skills/05-js-audit-runtime/scripts/advanced_js_runtime_extractor.py` | `source_map_reentry_count > 0` when `sourcesContent` exists |
| JS wrapper resolver 必须覆盖 axios instance/interceptor/GraphQL persisted query | `advanced_js_runtime_extractor.py` | `api_wrappers`, `interceptors`, `graphql.persisted_hash`, `wrapper_resolutions` |
| 动态验证必须有本机浏览器/HAR/截图/角色矩阵闭环 | `skills/06-dynamic-browser-burp-mcp/scripts/playwright_local_capture.py` | `capture_result_v2`, artifact hash, optional screenshot status |
| GraphQL/Webhook/OAuth/CORS 研究单元必须完整 | `_shared/vulnerability_research_units/C17-graphql-access-control`, `_shared/vulnerability_research_units/C18-webhook-signature-bypass`, `_shared/vulnerability_research_units/C20-oauth-sso-callback-redirect`, `_shared/vulnerability_research_units/C21-cors-high-risk` | static/dynamic/FP/framework/test/report files exist |
| 依赖分析必须含版本、锁文件、reachability、构建脚本风险 | `project_inventory_extractor.py` | `dependency_semantics`, `lockfile_version_reachability`, `build_script_risks` |
| 配置分析必须含框架语义 | `project_inventory_extractor.py` | `config_semantics` |
| IDOR/租户隔离必须有角色-对象-租户账本 | `attack_surface_builder.py` | `role_object_tenant_ledger` |
| E2E replay 必须能发现 extractor 退化 | `_shared/tests/e2e_replay/e2e_replay_runner.py` | exact minimum route/API/template/schema assertions |
| Manifest 与 live selftest 不得冲突 | `SYSTEM_MANIFEST.json`, `SELFTEST_RESULT.json` | regenerated after live selftest |
| capability 文档不得把脚本存在等同能力证明 | `_shared/capabilities/CAPABILITY_PROOF_MATRIX.md` | runtime probe/proof fields required |
| Burp 端口开放不得等同 Burp ready | `_shared/tools/tool_health_check.py` | status `degraded/manual_required` until API/CA/context verified |
| dashboard fixture 态不得误认为真实运行态 | `_shared/dashboard/dashboard_generator.py`, `dashboard_data_schema.json` | explicit `data_source` and `fixture_mode` fields |

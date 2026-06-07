# 能力矩阵

| 能力 | 当前状态 | 证据路径 | 边界 |
|---|---|---|---|
| 真实 AST 图谱 | promoted | scripts/ast_semantic_graph_builder.py; ast_plugins/python/python_security_graph_bridge.py; ast_plugins/js/typescript_security_graph_bridge.js; outputs/current/ast_semantic_selftest.json | Python 与 JS/TS 已有真实 AST fixture 证明；其他语言按本机 bridge 运行结果降级 |
| 浏览器动态验证引擎 | promoted_engine_only | scripts/browser_role_tenant_matrix_replay.py; outputs/current/browser_matrix/evidence_manifest_v4_dynamic.json | 证明引擎可执行；目标项目漏洞确认仍需目标运行证据 |
| 多角色/多租户矩阵 | promoted_engine_only | config/role_tenant_matrix.example.json; outputs/current/browser_matrix/matrix_result.json | fixture 中验证跨租户与 admin 负向控制；目标项目需配置真实账号 |
| JS 资产与端点收集 | promoted_candidate_only | tools/js_asset_extractor.py; outputs/current/selftest_js_assets.json | 不能单独证明后端接受或漏洞存在 |
| 38 类严重漏洞 detector | needs_review | scripts/detectors/registry.json; tests/fixtures/severe_vuln_matrix | 只产出候选风险；confirmed 需 source-sink-dataflow 与动态证据 |
| 报告确认 | blocked_without_target_runtime_evidence | tools/quality_gate.py; schemas/EVIDENCE_MANIFEST_SCHEMA.json | 没有目标证据不得 confirmed |

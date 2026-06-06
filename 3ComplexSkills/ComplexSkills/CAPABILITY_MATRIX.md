# Capability Matrix

| 能力 | 声明位置 | 实现文件 | 测试证据 | 运行证据 | 判定 | 问题 |
|---|---|---|---|---|---|---|
| 信息收集 | SKILL.md; skills/02-project-intelligence/SKILL.md | skills/02-project-intelligence/scripts/project_inventory_extractor.py | _shared/tests/e2e_replay/e2e_replay_runner.py | e2e replay passed locally | IMPLEMENTED | 仍以文件/关键词为主，非完整多语言语义理解 |
| 资产识别 | skills/04-attack-surface-mapping/SKILL.md | skills/04-attack-surface-mapping/scripts/attack_surface_builder.py | _shared/tests/e2e_replay/e2e_replay_runner.py | surface ledger generated in e2e | IMPLEMENTED | 依赖上游 extractor 质量 |
| 技术栈识别 | skills/02-project-intelligence/SKILL.md | project_inventory_extractor.py | e2e samples | local compile/json checks passed | PARTIAL | 未证明真实大型项目覆盖率 |
| 框架识别 | skills/02-project-intelligence/SKILL.md | project_inventory_extractor.py | 10 e2e samples | e2e passed | PARTIAL | 主要样本驱动，复杂框架仍需人工复核 |
| 路由提取 | skills/03-code-knowledge-graph/SKILL.md | advanced_code_graph_extractor.py; tools/route_extractor.py | tests/fixtures/local_minimal | tools/selftest.py passes | IMPLEMENTED | 新增根工具标记为 regex_candidate_not_ast |
| API 提取 | skills/05-js-audit-runtime/SKILL.md | advanced_js_runtime_extractor.py; tools/js_asset_extractor.py | tests/fixtures/local_minimal | tools/selftest.py passes | IMPLEMENTED | 复杂 wrapper 仍需 runtime/AST |
| 参数提取 | skills/03-code-knowledge-graph/SKILL.md | advanced_code_graph_extractor.py | e2e replay | e2e passed | PARTIAL | 跨文件 DTO/泛型未充分证明 |
| JS 文件收集 | skills/05-js-audit-runtime/SKILL.md | advanced_js_runtime_extractor.py; tools/js_asset_extractor.py | local fixture | tools/selftest.py passes | IMPLEMENTED | CDN/远程抓取不默认执行 |
| JS chunk 识别 | skills/05-js-audit-runtime/SKILL.md | js_deep_semantic_graph.py; advanced_js_runtime_extractor.py | e2e/selftest | selftest passed | PARTIAL | chunk lineage 有样本，真实构建产物仍需扩大 replay |
| sourcemap 识别 | skills/05-js-audit-runtime/SKILL.md | advanced_js_runtime_extractor.py; tools/js_asset_extractor.py | fixture sourcemap | adversarial smoke found source map | IMPLEMENTED | source map 还原深度仍有限 |
| service worker 识别 | skills/05-js-audit-runtime/SKILL.md | tools/js_asset_extractor.py | local fixture | tools/selftest.py passes | PARTIAL | 缓存泄露验证需动态证据 |
| GraphQL 端点识别 | skills/05-js-audit-runtime/SKILL.md | js_deep_semantic_graph.py; tools/js_asset_extractor.py | fixture | selftest passes | IMPLEMENTED | resolver auth 仍需后端图谱 |
| WebSocket 识别 | skills/05-js-audit-runtime/SKILL.md | tools/js_asset_extractor.py | fixture | selftest passes | PARTIAL | 未做协议级动态 replay |
| Electron/extension/mobile webview 线索 | _shared/reverse_judgement/js_rules | advanced_js_runtime_extractor.py | coverage matrices | not fully runtime-validated | PARTIAL | 多为线索规则 |
| 前端敏感信息识别 | skills/05-js-audit-runtime/SKILL.md | tools/js_asset_extractor.py | fixture | selftest passes | PARTIAL | 只报告 secret-like 线索，不确认泄露 |
| 后端代码结构分析 | skills/03-code-knowledge-graph/SKILL.md | advanced_code_graph_extractor.py | 10 e2e samples | e2e passed | PARTIAL | Java/PHP/Rust parser runtime 当前未 promoted |
| 配置文件分析 | skills/02-project-intelligence/SKILL.md | project_inventory_extractor.py | e2e samples | e2e passed | PARTIAL | 语义校验不足 |
| 依赖分析 | skills/02-project-intelligence/SKILL.md | project_inventory_extractor.py | e2e samples | e2e passed | PARTIAL | 非 SCA，不等于漏洞确认 |
| 权限模型分析 | skills/03-code-knowledge-graph/SKILL.md; skills/07-vulnerability-hunting-engine/SKILL.md | candidate engine + detectors | fixtures/replay | candidate replay passed | PARTIAL | 多角色矩阵仍依赖动态账号 |
| 多角色访问差异分析 | skills/06-dynamic-browser-burp-mcp/SKILL.md; _shared/tests/high_risk_replay | dynamic scripts | high_risk_replay_runner.py | 28 cases passed | PARTIAL | 真实浏览器 runtime 当前 blocked |
| 多租户隔离分析 | C04 templates/detectors | detectors/C04; high risk replay | C04 fixture classes | passed | PARTIAL | 需真实 tenant replay 才能 confirmed |
| source-sink 数据流分析 | skills/07-vulnerability-hunting-engine detector spec | vulnerability_candidate_engine.py | candidate replay | passed | PARTIAL | 仍是候选引擎，不是完整 interprocedural taint |
| 动态验证 | skills/06-dynamic-browser-burp-mcp/SKILL.md | playwright/capture scripts | playwright_runtime_manager.py | Playwright browser missing | PARTIAL | 浏览器未安装，不能声称 ready |
| 证据保存 | _shared/evidence schemas; skills/06-dynamic-browser-burp-mcp/scripts | evidence_capture_bridge.py; tools/evidence_builder.py | fixtures/selftest | selftest passes | IMPLEMENTED | 动态 request/response 需真实采集 |
| 报告生成 | _shared/reporting; reports/templates | REPORT_FROM_MANIFEST.py; root template | template index fixtures | json parse passed | PARTIAL | 报告必须由 quality gate 放行 |
| 质量门 | _shared/quality; tools/quality_gate.py | shared quality gate; root tool | positive/negative fixtures | adversarial replay passed | IMPLEMENTED | 根工具为补充 gate |
| replay | _shared/tests/e2e_replay; oss_replay | runner scripts | 10 e2e; 35 oss adapters | e2e passed; oss manual_required | PARTIAL | OSS 适配器未绑定本机 checkout |
| dashboard | _shared/dashboard; dashboard/ | dashboard_generator.py; dashboard/index.html | generator smoke | not all runtime linked | PARTIAL | 静态链路面板，不等同实时运行态 |
| human review queue | _shared/review_queue; REVIEW_QUEUE.md | review_queue.py | schema json parse | exists | PARTIAL | 需要实际项目填充 |
| AI 幻觉控制 | SKILL.md; quality gates | quality_gate scripts; docs | adversarial harness | passed | IMPLEMENTED | 仍需人工复核 claim-only 项 |


## Anti-lazy JS and real browser proof gate

The user-requested lazy-loading and browser-interaction requirements are preserved in `_shared/requirements/USER_REQUESTED_LAZY_BROWSER_REQUIREMENTS.md`. For frontend or dynamic-validation tasks, route through these additional hard gates before final reporting:

1. `skills/05-js-audit-runtime/scripts/lazy_js_asset_discovery.py` must produce a lazy JS asset ledger for dynamic import, lazy routes, chunks, source maps, service workers, build manifests, API clients, GraphQL and WebSocket/SSE signals.
2. `skills/06-dynamic-browser-burp-mcp/scripts/browser_interaction_coverage_matrix.py` must produce a browser interaction matrix for click, scroll, input, hover, menu, tab, modal, search, pagination, deep-route, error-page, role and tenant coverage.
3. `_shared/quality/anti_lazy_browser_proof_gate.py` blocks any claim of complete JS coverage or dynamic validation when the ledger or matrix is missing.
4. If browser runtime is unavailable, output `runtime_missing`; do not claim browser validation completed.
5. Candidate JS or browser evidence still requires evidence manifest validation, negative control and quality gate before `confirmed`.

Operational commands:

```powershell
python skills/05-js-audit-runtime/scripts/lazy_js_asset_discovery.py C:\path\to\local-project --out _shared/runs/lazy_js_asset_ledger.json
python skills/06-dynamic-browser-burp-mcp/scripts/browser_interaction_coverage_matrix.py --capture-json _shared/runs/playwright_local_capture_result.json --out _shared/runs/browser_interaction_coverage.json
python _shared/quality/anti_lazy_browser_proof_gate.py --lazy-ledger _shared/runs/lazy_js_asset_ledger.json --browser-matrix _shared/runs/browser_interaction_coverage.json
```

| 扩展 40 类 detector | 用户粘贴需求 | skills/07-vulnerability-hunting-engine/detectors/extended_40/*.json; extended_detector_engine.py | tools/authorized_audit_pipeline.py | selftest + pipeline smoke | IMPLEMENTED_AS_CANDIDATE_ENGINE | 仅候选/复核，不确认漏洞 |
| 一键本地流水线 | README.md | tools/authorized_audit_pipeline.py | tests/fixtures/local_minimal | pipeline smoke | IMPLEMENTED | 不进行外部探测，不执行 destructive validation |

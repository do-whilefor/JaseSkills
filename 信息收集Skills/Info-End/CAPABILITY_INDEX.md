# 信息暴露面审计 Skills 能力索引

必须先从 `00-master-info-exposure-orchestrator` 开始。除非用户明确要求单项能力，不要直接从子 Skill 开始。

| Skill / 文件 | 用途 | 何时使用 | 输出状态 |
|---|---|---|---|
| `00-master-info-exposure-orchestrator` | 总控调度、任务分类、三档路径、跨 Skill 交接 | 任意执行型信息暴露面审计开始 | 调度记录 |
| `01-scope-runtime-intake` | 根目录、运行方式、端口、Base URL、账号角色、禁止范围 | 审计前置 | 输入确认 |
| `02-runtime-entry-enumeration` | 本机运行态入口、端口、服务、文档、health、metrics | 有 Base URL 或端口 | 入口候选 |
| `03-static-route-artifact-mining` | 源码、路由、JS、配置、依赖、部署、包产物候选 | 需要从代码/文件找候选 | 静态候选 |
| `04-dynamic-exposure-validation` | HTTP/协议非破坏动态验证 | 有候选 URL/端口/协议入口 | 动态证据 |
| `05-role-diff-browser-storage` | 角色差异、cookie、localStorage、sessionStorage、IndexedDB、Cache Storage | 有授权账号或浏览器状态 | 角色/浏览器证据 |
| `06-artifact-cache-container-edge-cases` | 偏门补漏、二轮反思、容器、缓存、错误面、文档影子 | 第一轮后或专家路径 | 新增候选/反思 |
| `07-evidence-reporting-quality-gate` | 脱敏、QG、不可报告、报告 | 交付前 | 报告/阶段报告 |
| `08-skill-adversarial-audit-regression` | Skills 自审、触发路由压测、反幻觉、回归测试 | 审查或维护 Skills 包 | 审查结果/修复任务 |

## 核心硬规则

- 静态候选不是发现。
- 工具输出不是结论。
- 无动态证据不输出确定结论。
- 无账号不输出角色差异。
- 敏感信息必须脱敏。
- 文档、模板、矩阵、示例不等于实现。
- parser/backend/runtime 不可用时，必须降级输出。

## 能力绑定

| 能力 | 文件 | 当前实现等级 | 限制 |
|---|---|---|---|
| JS 资产候选采集 | `scripts/js-asset-audit.py`, `detectors/js_audit_coverage.yaml`, `tests/test_js_asset_audit.py` | 候选级实现 | 不是完整 AST/dataflow；需 parser backend 和动态验证 |
| JS endpoint 候选 | `scripts/js-ast-endpoint-extractor.mjs`, `tests/test_js_ast_endpoint_extractor.py`, `tests/test_js_ast_strict_mode.py` | 有 AST walk；backend 缺失时显式 lexical fallback | 不等于完整 Babel/TS 数据流 |
| 代码暴露面采集 | `scripts/code-surface-inventory.py`, `scripts/codegraph-builder.py`, `tests/test_code_surface_inventory.py`, `tests/test_codegraph_builder.py` | Python AST + 多语言 lexical graph | 不执行项目代码，不证明漏洞 |
| 配置与依赖采集 | `scripts/config-dependency-inventory.py`, `tests/test_config_dependency_inventory.py` | 本地文件候选采集 | 不联网查 CVE，不执行依赖脚本 |
| 前端 manifest / service worker 展开 | `scripts/js-manifest-expander.py`, `tests/test_js_manifest_expander.py` | 本地工件级实现 | 不下载 CDN 历史版本，不恢复远端 sourcemap |
| 信息面归一化 | `schemas/info-surface.schema.json`, `scripts/info-surface-normalizer.py`, `tests/test_info_surface_normalizer.py` | 统一字段与候选路由 | 不是确认漏洞 detector |
| source/sink 候选 | `scripts/source-sink-dataflow.py`, `tests/test_source_sink_dataflow.py` | 窗口级候选；全部 `needs_review` | 不能宣传为确认漏洞 |
| C01-C05 访问控制候选 | `detectors/c01_c05_access_control.py` | 候选 detector | 无 role/tenant replay 时不能 promoted |
| C06-C30 高危入口候选 | `detectors/c06_c30_high_impact_candidates.py`, `tests/test_c06_c30_detector.py` | 高危入口路由；默认 needs_review | 不是完整 AST/source-sink detector |
| Parser backend readiness | `scripts/parser-backend-check.py` | 可用性检查 | 不安装依赖，不代表完整 parser ready |
| Runtime readiness | `scripts/runtime-readiness-check.py` | 本地依赖/文件/URL 检查 | 不启动服务，不探测外部目标 |
| 角色/租户运行态契约 | `scripts/playwright-har-role-matrix.mjs`, `schemas/runtime-evidence.schema.json`, `tests/test_role_matrix_contract.py` | 无 Playwright 时输出 contract-only | 不等于 HAR 已采集 |
| WebSocket 只读契约 | `scripts/ws-readonly-capture.mjs`, `tests/test_ws_capture_contract.py` | 安全输出契约 | 不等于 WS 权限绕过验证 |
| Evidence Manifest | `scripts/report-to-manifest.py`, `schemas/evidence-manifest.schema.json` | 证据索引 | 不自动确认 finding |
| JSONL 质量门 | `scripts/qg-jsonl-score.py`, `schemas/finding-evidence-chain.schema.json`, `tests/test_qg_jsonl_score.py`, `tests/test_qg_manifest_linkage.py` | 字段与 manifest linkage 门禁 | 不替代人工复核 |
| 模板索引 | `manifests/template_index.json`, `tests/test_all_templates_indexed.py` | 全模板索引 | 模板不等于实现 |
| 知识索引与人工复核 | `manifests/knowledge_index.json`, `knowledge/`, `human_review/human_review_queue.jsonl` | 知识库保留与复核入口 | conflict/needs_review 不自动 promoted |
| Dashboard | `dashboard/dashboard_generator.py` | 读取 selftest 产物生成摘要 | 不是漏洞确认面板 |
| 发布清理 | `scripts/clean-release-artifacts.sh`, `tests/test_release_cleaner.py` | 清除缓存和陈旧 selftest | 不得删除 `knowledge/`、`templates/` |

## 关键文档

- `docs/task-router.md`
- `docs/trigger-routing.md`
- `docs/execution-paths.md`
- `docs/tooling-contract.md`
- `docs/quality-gates.md`
- `docs/evidence-manifest-runbook.md`
- `docs/anti-hallucination-rules.md`
- `docs/failure-case-library.md`
- `docs/fidelity-matrix.md`
- `docs/mirror-rule-map.md`

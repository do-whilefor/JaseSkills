# 15-js-top-tier-collection-analysis-audit

## 定位

本 Skill 负责把 JS 收集、JS 分析、JS 安全审计提升为可执行、可验收、可降级追责的工程链路。它不是报告美化层，也不是简单关键词扫描层。它必须产出资产账本、解析状态、候选证据、语义证据、动态证据需求、质量门槛和报告映射。

## 触发条件

当任务包含以下意图时触发：

- 顶级 JS 收集、JS 资产发现、chunk/source map/manifest/service worker/worker/GraphQL/WebSocket 收集。
- JS 分析、JS 审计、Source Map 反混淆、endpoint/router/wrapper/auth/tenant 分析。
- DOM XSS、postMessage、prototype pollution、GraphQL hidden mutation、WebSocket authz、OAuth/JWT、Electron、Extension、WebView、WASM、供应链等严重 JS 漏洞候选发现。
- 要求证明 ready/partial/doc-only/candidate-only/fake-ready/missing 的证据状态。

## 禁止条件

- 未提供授权边界、项目源码、HAR、HTML 或 JS 样本时，禁止输出 verified 漏洞。
- 只用 regex/grep 的结果必须标记为 `candidate-only`，禁止称为 AST 审计。
- 未运行 Playwright/Burp/HAR 证据桥时，必须标记为 `未动态验证`。
- 缺少多角色/多租户 replay 时，必须标记为 `缺少 role/tenant replay`。
- 缺少 schema/report mapping/quality gate 时，必须标记为 `证据链不闭环`。
- 禁止删除 knowledge、templates、既有 SKILL.md 或漏洞模板。

## 输入

- 本地源码目录、解包后的前端构建目录、JS 文件目录。
- HTML、HAR、asset-manifest、build-manifest、routes-manifest、vite manifest、precache manifest、service worker、source map。
- 可选：Playwright trace、Burp sitemap/HAR、多角色/多租户录制目录。

## 输出

默认输出到 `reports/js-top-tier/`：

- `js_asset_ledger.json`：JS 资产、来源、hash、mime、大小、manifest、source map、worker、runtime chunk、证据路径。
- `js_analysis.json`：backend 状态、AST/候选解析结果、router/endpoint/wrapper/auth/tenant/source-sink 信息。
- `js_findings.json`：严重漏洞候选，按 ready/partial/doc-only/candidate-only/fake-ready/missing 降级。
- `js_quality_gate.json`：质量门槛、惩罚规则、缺口清单、不可交付原因。
- `js_top_tier_report.md`：可读报告，所有未证实项必须显式降级。

## 执行步骤

1. 建立授权边界和输入来源账本。
2. 运行 `scripts/js_top_tier_collect.py --root <target> --out reports/js-top-tier` 收集 HTML/script/manifest/source map/service worker/worker/WASM/GraphQL/WebSocket/postMessage/storage 等资产。
3. 运行 `scripts/js_top_tier_analyze.py --ledger reports/js-top-tier/js_asset_ledger.json --out reports/js-top-tier` 分析 JS。若 `@babel/parser`、`typescript`、`tree-sitter` 不存在，必须输出 backend_status 为 missing，并将相关结论降级。
4. 运行 `scripts/js_top_tier_quality_gate.py --report-dir reports/js-top-tier` 计算质量门槛。
5. 必须运行 `scripts/run_js_top_tier_fixture_tests.py <skill-root>` 做 fixture 回归。
6. 若存在动态证据目录，再把 Playwright/Burp/HAR/trace 截图和请求响应映射到 evidence manifest；否则所有动态验证项必须为未动态验证。

## 工具依赖

基础可执行依赖：Python 3.10+。

可选语义级依赖：Node.js、`@babel/parser`、`@babel/traverse`、`typescript`、`tree-sitter`、`tree-sitter-javascript`、Playwright、Burp/HAR 输入。缺失时不能标记 ready。

## 证据要求

每条 finding 至少包含：`finding_id`、`status`、`asset_path`、`evidence_path`、`line`、`rule_id`、`backend`、`source`、`sink`、`dynamic_validation`、`report_section`。没有这些字段时不得进入 verified 报告。

## 质量门槛

- 没有真实 AST backend：JS 语义审计最高为 40%。
- 没有 Source Map 解析：JS 收集最高为 70%。
- 没有 Playwright/Burp/HAR 动态证据：动态验证最高为 30%。
- 没有多角色/多租户 replay：严重漏洞发现最高为 60%。
- 没有 positive/negative/blocked/needs_review 样本：测试最高为 40%。
- 任何 fake-ready 均必须在报告中阻断 promoted。

## 与其他 Skill 交接

- 前置：`00-js-master-dispatcher`、`01-js-scope-evidence-quality-gate`。
- 结构图谱交接：`02-js-structure-runtime-graph`。
- source-sink/authz 交接：`03-js-source-sink-authz-graph`。
- 构建暴露交接：`05-js-frontend-build-exposure`。
- 候选漏洞交接：`06-js-high-risk-candidate-hunter`。
- 动态验证交接：`07-js-dynamic-validator`。
- 证据门槛交接：`08-js-evidence-manifest-gate`。
- 最终追责：`14-js-skills-evidence-court`。

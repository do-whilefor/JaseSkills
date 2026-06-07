# Extreme Reverse Judgement and Evaluation Standard v4.2

生成时间：2026-06-05T06:12:08.099359+00:00

本文件是对上一轮评估与修复声明的反向审判层。结论：上一轮评估不应被视为最终证明；只有当 `_shared/reverse_judgement/extreme_reverse_audit.py`、`_shared/selftest/verify_system_integrity.py`、E2E replay、quality gate 与 23 类模板回放全部通过时，才能称为本机授权范围内的可执行评估体系。

## A. 原评估总判定

1. 原评估是否合格：部分合格。合格部分是识别了 schema、dynamic、E2E、parser、JS、ledger、taint、renderer 等高风险缺陷。不合格部分是很多结论没有逐项落到文件、规则、模板、脚本、测试输入、预期输出和质量门槛。
2. 合格部分：已推动 `EVIDENCE_MANIFEST_SCHEMA.v4.1.json`、`quality_gate_v4_1.py`、`playwright_local_capture.py`、`advanced_js_runtime_extractor.py`、`e2e_replay_runner.py`、`REPORT_FROM_MANIFEST.py` 进入可执行链路。
3. 不合格部分：原评估本身缺少强制 traceability schema，未逐项覆盖全部信息收集点、JS 审计点、23 类漏洞和 AI 幻觉/误报/漏报风险。
4. 最大风险：评估报告可能再次把“存在文件”误判为“能力已证明”。
5. 是否可能漏报高危：可能，尤其是 worker/queue/cron/CLI、sourcemap、旧 chunk、tenant ledger、GraphQL/RPC/gRPC、Electron/extension/小程序和 legacy route。
6. 是否可能产生 AI 幻觉：可能，尤其是 scanner-only、tool unavailable、generic renderer、知识库过期、prompt injection 未 taint 的场景。
7. 是否可能无法落地执行：可能，除非 `extreme_reverse_audit.py` 与 selftest 都作为发布前 gate。

## B. 不合格评估项清单

完整机器可校验清单位于 `_shared/reverse_judgement/evaluation_claim_traceability.json`。每项包含问题编号、具体文件路径、具体问题位置、原始证据、影响能力、修复文件、规则变更、模板变更、脚本变更、测试输入、预期输出、失败判断标准、质量门槛和优先级。

## C. 新增遗漏问题清单

新增遗漏问题被拆分为四个矩阵：

- `_shared/reverse_judgement/information_collection_coverage_matrix.json`
- `_shared/reverse_judgement/js_audit_coverage_matrix.json`
- `_shared/reverse_judgement/ai_hallucination_controls.json`
- `_shared/reverse_judgement/false_negative_controls.json`
- `_shared/reverse_judgement/false_positive_controls.json`

P0 规则：任一 P0 信息源、JS 审计点或 23 类漏洞模板没有负责 skill、规则文件、测试文件、manifest 字段和 quality gate，即评估失败。

## D. 23 类严重漏洞逐类复核表

机器可校验版本位于 `_shared/reverse_judgement/vulnerability_coverage_matrix_23.json`。每类漏洞必须包含触发条件、非触发条件、静态证据、动态证据、非破坏性边界、影响证明、误报排除、最低证据门槛、报告模板、测试样例、失败处理、与信息收集/JS/代码图谱/evidence manifest/quality gate 的联动。

## E. 信息收集逐项复核表

机器可校验版本位于 `_shared/reverse_judgement/information_collection_coverage_matrix.json`。覆盖 42 个信息源，包括常规项目结构、语言、框架、依赖、配置、环境变量、路由、API schema、认证、授权、租户、数据库、ORM、migration/seed/fixture、默认账号、Docker/Kubernetes/CI/CD，以及 i18n、埋点、feature flag、sourcemap、旧 chunk、Storybook/MSW/E2E、middleware 顺序、legacy/mobile/Electron/extension 等偏门来源。

## F. JS 审计逐项复核表

机器可校验版本位于 `_shared/reverse_judgement/js_audit_coverage_matrix.json`。覆盖 44 个 JS 收集、分析、审计点。每个点都必须进入 parser 要求、输出字段、候选漏洞联动、manifest 字段、测试样例、quality gate 和 report section。

## G. Skills 包结构修订建议

推荐目录结构：

```text
SKILL.md
CLAUDE.md
README_SYSTEM.md
skills/01-authorized-maximum-orchestrator/
skills/02-project-intelligence/
skills/03-code-knowledge-graph/
skills/04-attack-surface-mapping/
skills/05-js-audit-runtime/
skills/06-dynamic-browser-burp-mcp/
skills/07-vulnerability-hunting-engine/
skills/08-evidence-quality-gate/
skills/09-reporting-disclosure/
skills/10-regression-selftest-dashboard/
_shared/evidence/
_shared/quality/
_shared/vulnerability_templates/canonical_23/
_shared/vulnerability_research_units/
_shared/reverse_judgement/
_shared/tests/extreme_reverse_audit/
_shared/tests/e2e_replay/
_shared/dashboard/
_shared/review_queue/
```

新增强制层：`_shared/reverse_judgement/`。该层负责评估结果保真度，不替代漏洞发现链路。

## H. 最终结论

刚刚的评估不能单独视为世界顶级标准。修复后，最低通过门槛为：

1. `_shared/reverse_judgement/extreme_reverse_audit.py` 通过。
2. `_shared/selftest/verify_system_integrity.py` 通过。
3. E2E exact replay 10/10 通过。
4. 23 类 canonical fixtures 92/92 通过 v4.1 schema 和 semantic replay。
5. confirmed 报告必须通过 `quality_gate_v4_1.py`，且模板专用 renderer、taint review、dynamic negative control 和 artifact hash 均满足。
6. parser、Burp、Playwright、MCP 未 runtime ready 时只能 degraded/manual_required，禁止 promoted。

本机授权边界：所有测试、采集、回放、验证仅限本机授权项目、fixtures、localhost 和 file://。禁止第三方真实目标探测，禁止把候选点当 confirmed 漏洞。

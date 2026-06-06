# 13-js-skills-second-pass-reverse-auditor

## 职责边界

对上一轮 JS 安全审计 Skills 评估结果做二次反向审查。目标不是继续美化结论，而是检查原评估是否有文件证据、测试证据、真实实现、动态验证、role/tenant replay、report/quality/dashboard 闭环。该 Skill 只审查 Skills 包和评估结论本身，不对未授权目标执行扫描或攻击。

## 必须触发

当用户要求：

- 反向审查刚刚的 Skills 评估。
- 检查是否有 AI 幻觉、虚高评分、证据不足。
- 反查 JS 收集、JS 审计、严重 JS 漏洞链是否真正覆盖。
- 不删除知识库和漏洞模板、不削弱原有 Skills 能力，并输出新压缩包。
- 检查 doc-only、fake-ready、candidate-only、未动态验证、缺 role/tenant replay、测试不足。

## 禁止触发

- 用户只是要求普通 JS 语法解释、组件开发、样式修复、算法题。
- 用户要求对未授权第三方目标进行真实攻击。
- 用户要求把缺证据的候选漏洞写成 verified。
- 用户要求删除原有知识库、漏洞模板或降低已有 Skills 能力。

## 输入

- Skills 包根目录或压缩包。
- 上一轮评估产物，例如 `tests/last-extreme-review.json`、`tests/last-extreme-review.md`。
- 本 Skill 的二次反查矩阵：
  - `data/second_pass_original_conclusion_checks.json`
  - `data/second_pass_js_collection_points.json`
  - `data/second_pass_js_audit_capabilities.json`
  - `data/second_pass_severe_js_chains.json`
  - `data/second_pass_unconventional_js_audit_points.json`
  - `data/second_pass_score_rules.json`

## 输出

- `tests/last-second-pass-review.json`
- `tests/last-second-pass-review.md`
- 修正后的总分。
- 修正后的 P0/P1/P2 修复清单。
- 文件级覆盖表。
- JS 收集覆盖反查表。
- JS 审计语义保真反查表。
- 严重 JS 漏洞链反查表。
- 偏门/冷门/剑走偏锋审计点补充表。

## 执行步骤

1. 清点所有文件、目录、`SKILL.md`、`scripts`、`schemas`、`templates`、`tests`、`fixtures`、`knowledge`、`data`。
2. 读取上一轮 `last-extreme-review` 结果，提取原分数和核心结论。
3. 对每条原结论检查文件证据、测试证据、是否可能幻觉、修正后结论。
4. 对 30 个 JS 收集点逐条判定：原评估是否覆盖、是否有真实采集脚本、是否漏评。
5. 对 20 个 JS 审计能力逐条判定：是否把关键词/文档误判成语义审计。
6. 对 25 个严重 JS 漏洞链逐条判定：是否有 detector、动态验证、证据模板、多角色/多租户 replay。
7. 对所有重要文件/目录做覆盖率反查，列出未被原评估引用或可能遗漏的位置。
8. 重新评分。没有真实 parser backend 时，JS AST/语义审计强制低分；没有 Playwright/Burp/HAR bridge 时，动态验证强制低分；没有 detector 时，严重漏洞发现强制低分。
9. 输出可执行 P0/P1/P2 修复项，每项必须包含修改文件、新增文件、新增测试、命令、验收标准、失败回滚、不删除知识库和模板的保真要求。
10. 输出最终二次反审报告和 JSON 结果。

## 质量门槛

- 没有文件证据，必须写 `未证实`。
- 只有文档，必须写 `doc-only`。
- 只有 grep/regex/关键词，必须写 `candidate-only，不是语义审计`。
- 没有真实浏览器/Burp/HAR 请求响应证据，必须写 `未动态验证`。
- 没有双账号、多角色、多租户回放，必须写 `缺少 role/tenant replay`。
- 没有正负阻断复核样本，必须写 `测试不足`。
- 没有 schema 校验，必须写 `证据不可强校验`。
- 没有 report mapping，必须写 `无法闭环到报告`。
- 没有 quality gate，必须写 `无法量化质量`。
- 不允许把 `README`、`TODO`、模板、fixture、工具名出现当成 runtime ready。

## 工具依赖

- Python 3。
- `scripts/second_pass_reverse_audit.py`。
- `scripts/verify_second_pass_assets.py`。
- 可选：`scripts/extreme_skills_review.py` 的上一轮结果。

## 证据要求

每个二次反查结论至少绑定一种证据：文件路径、脚本名、函数名、schema 字段、模板名、测试用例、fixture、dashboard 字段、manifest 字段或命令输出。

## 失败处理

- 如果上一轮评估结果不存在，仍可从包内静态文件生成二次审查报告，但必须标记 `原分数未读取`。
- 如果 parser/runtime/detector 不存在，不得伪造；必须降级为 `doc-only`、`missing` 或 `未证实`。
- 如果新增二次反查资产不完整，`verify_second_pass_assets.py` 必须失败。

## 与其他 Skill 的交接

- 入口由 `00-js-master-dispatcher` 触发。
- 授权与证据规则继承 `01-js-scope-evidence-quality-gate`。
- 评分与证据输出交给 `08-js-evidence-manifest-gate`。
- 反向审查结果可交给 `09-js-reverse-review-chain-audit` 和 `10-js-final-report` 汇总。
- 不替代 `12-js-skills-extreme-reviewer`，而是在其结果上进行更严格的二次反查。

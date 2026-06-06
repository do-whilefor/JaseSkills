# 14-js-skills-evidence-court

## 定位

本 Skill 是第三层终极反向审判、证据法庭、失职追责 Skill。它不负责证明前两轮评估正确，只负责把所有未被文件、脚本、schema、fixture、manifest、dashboard、report mapping 或命令输出证明的结论降级为未证实、doc-only、candidate-only、fake-ready、missing、conflict、测试不足、证据不可强校验、无法闭环到报告或无法动态验证。

## 触发条件

当任务包含以下意图时必须触发：

- 终极反向审判、证据法庭、失职追责。
- 审判刚才评估、追责幻觉、反查伪 ready。
- JS 收集漏报事故模拟。
- JS 审计伪能力拆穿。
- 严重 JS 漏洞漏报清算。
- Skills 包工程验尸。
- 失败惩罚规则重新评分。
- 不可辩解 P0 清单。

## 禁止条件

- 禁止把计划当实现。
- 禁止把脚本存在当可执行闭环。
- 禁止把 fixture 存在当真实 replay。
- 禁止把模板存在当漏洞发现。
- 禁止把知识库存在当知识已接入。
- 禁止把 regex 候选当 AST / CFG / DFG / source-sink 审计。
- 禁止把静态候选当动态验证。
- 禁止无文件证据时使用 ready、已实现、已覆盖、闭环。
- 禁止删除原有 knowledge、templates、fixtures、docs 中的漏洞模板与知识库。

## 输入

- 当前 Skills 包根目录。
- 前两轮评估产物：`tests/last-extreme-review.*`、`tests/last-second-pass-review.*`。
- 数据矩阵：`data/final_court_*.json`。
- 当前脚本、schema、templates、fixtures、docs、knowledge、tests。

## 输出

- `tests/last-final-evidence-court.json`
- `tests/last-final-evidence-court.md`
- 表格化审判结果：原结论审判、20 起 JS 收集漏报事故、伪能力拆穿、30 类严重漏洞漏报、高危工程验尸、失败惩罚评分、不可辩解 P0、7 天修复计划。

## 执行步骤

1. 扫描包内所有文件，建立文件证据索引。
2. 对前两轮关键结论逐条检查文件证据、测试证据、运行链路证据。
3. 对 JS 收集漏报事故进行缺失能力归因。
4. 对 JS 审计能力执行伪能力拆穿，强制区分 doc-only、candidate-only、fake-ready、missing。
5. 对严重漏洞链执行动态验证、manifest、report mapping、样本矩阵检查。
6. 对工程结构执行验尸：孤立脚本、未引用模板、未调用 schema、缺 dashboard、缺 report generator、缺 runtime availability check。
7. 按失败惩罚规则重算分数，不能因文档完整给实现分。
8. 生成不可辩解 P0 清单和 7 天修复计划。
9. 输出 JSON 与 Markdown，供后续人工验收。

## 工具依赖

- Python 3 标准库。
- 不依赖外部网络。
- 不要求 Babel / TypeScript Compiler API / tree-sitter / Playwright / Burp 已安装；若未发现真实 backend 或 bridge，必须降级为 missing / fake-ready。

## 证据要求

每个结论必须至少绑定以下一种证据：文件路径、脚本名、函数名、schema 字段、模板名、测试用例名、fixture 名、manifest 字段、dashboard 字段、命令输出。没有证据必须写未证实。

## 失败处理

- 找不到前两轮评估产物：标记为证据不足，不中断。
- 找不到 runtime backend：相关能力降级为 missing，不中断。
- 找不到测试样本：相关能力标记测试不足。
- 找不到 report mapping：相关能力标记无法闭环到报告。
- 找不到 schema 校验调用：相关证据链标记证据不可强校验。

## 质量门槛

- 输出必须包含至少 20 起 JS 收集漏报事故。
- 输出必须包含至少 10 条伪能力拆穿。
- 输出必须包含至少 30 类严重 JS 漏洞漏报清算。
- 输出必须包含失败惩罚评分。
- 输出必须包含不可辩解 P0。
- 没有真实 AST backend 时，JS 审计分不得超过该项 40%。
- 没有 Playwright/Burp/HAR 证据时，动态验证分不得超过该项 30%。
- 没有 role/tenant replay 时，严重漏洞发现分不得超过该项 60%。

## 与其他 Skill 的交接

- 前置：`12-js-skills-extreme-reviewer`、`13-js-skills-second-pass-reverse-auditor`。
- 证据门禁：`08-js-evidence-manifest-gate`。
- 报告输出：`10-js-final-report`，但必须标注未动态验证、测试不足和无法闭环项。

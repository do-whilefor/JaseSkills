# Skill Quality Tests

这些测试用于判断 `local-injection-verify` 是否把 TXT 做成可执行 Skill，而不是摘要、空壳或幻觉扩展。

## 测试 1：是否漏掉 TXT 关键内容

步骤：打开 `SKILL.md`，检查授权本地环境、测试数据库、测试目录、测试账号、测试租户、无害 marker、动态验证、confirmed/candidate/blocked/false positive/needs manual review、证据链、二阶、隐藏参数、非 HTTP 入口、反向审判是否存在。

通过标准：

- [ ] 以上关键词和规则均存在。
- [ ] 每个规则都有执行步骤或质量门禁。
- [ ] 没有只用一句话概括原 TXT。

## 测试 2：是否把摘要当复刻

步骤：对比 `source/original-txt.txt`、`SKILL.md`、`templates/output-template.md`、`checklists/final-review.md`。

通过标准：

- [ ] 项目运行画像、暴露面矩阵、动态验证计划、动态验证结果、二阶结果、隐藏参数、封装风险、候选清单、confirmed 清单、修复建议、回归测试、反查修正版报告都在模板中出现。
- [ ] 禁止事项进入不适用范围、质量门禁或失败处理。
- [ ] 反查问题进入 final-review checklist。

## 测试 3：是否加入无关内容

通过标准：

- [ ] 没有公网攻击、真实目标扫描、破坏性 payload、MITM、真实敏感数据读取。
- [ ] 没有引入与注入类动态验证无关的独立目标。
- [ ] 工程化补强只用于编号、证据、门禁、模板、追溯和测试。

## 测试 4：是否命名过长或空泛

通过标准：

- [ ] 目录名为 `local-injection-verify`。
- [ ] 名称体现“本地授权注入动态验证”。
- [ ] 未使用 `best-skill`、`final-skill`、`advanced-skill`、`audit-skill`、`new-skill`。

## 测试 5：是否目录臃肿

通过标准：

- [ ] 只包含 `templates`、`checklists`、`examples`、`tests`、`source`、`mappings`。
- [ ] 不存在 `rules`、`workflows`、`schemas`、`fixtures` 等无依据目录。
- [ ] 不存在空目录、空文件、装饰性 manifest。

## 测试 6：是否没有输入输出定义

通过标准：

- [ ] 输入包含项目路径、启动命令/本地地址、测试数据库/回滚、账号/角色/租户、日志、测试目录、任务/队列/CLI 触发方式。
- [ ] 输出包含原 TXT 要求的 0-13 章节。
- [ ] 缺失输入有 blocked/candidate/needs manual review 处理。

## 测试 7：是否没有质量门禁

通过标准：

- [ ] `checklists/quality-gate.md` 覆盖授权、画像、输入面、sink、动态证据、结论分级、二阶/隐藏参数/冷门路径、修复回归、追溯。
- [ ] 每条检查项使用 `- [ ]` 格式。

## 测试 8：是否没有失败处理

通过标准：

- [ ] 无项目路径、无法启动、无测试库、无账号、无日志、人工触发、证据安全处理、越界风险均有处理方式。
- [ ] 失败场景明确禁止输出 confirmed。

## 测试 9：是否没有 TXT 映射

通过标准：

- [ ] `mappings/txt-skill-map.md` 包含 TXT 原文位置/标题、原文关键内容、当前 Skill 位置、是否完整复刻、是否失真、是否遗漏、修复动作。
- [ ] 覆盖动态验证负责人和反向审判官两段。
- [ ] 覆盖模板、清单、示例、测试的来源或补强原因。

## 测试 10：是否把工程化补强伪装成原文

通过标准：

- [ ] ID、证据编号、脱敏、追溯目录、测试方式标注为工程化补强。
- [ ] 原文复刻内容只对应 TXT 中已有要求。
- [ ] 新增字段不被描述为 TXT 原文。

## 测试 11：是否能防止“没有动态证据的 confirmed”

步骤：构造只有代码路径、没有请求/日志/marker/负向对照的候选点。

通过标准：

- [ ] 结论为 candidate 或 blocked。
- [ ] 报告列出缺失证据。
- [ ] confirmed 清单不包含该项。

## 测试 12：是否覆盖非 SQL 注入

通过标准：

- [ ] 模板、命令、表达式、搜索 DSL、GraphQL、Header/CRLF、JSONPath/JMESPath、Regex、Import/Export、二阶路径都有检查位置或未发现状态字段。
- [ ] 没有把 SQL 注入作为唯一检查对象。

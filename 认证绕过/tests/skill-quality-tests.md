# Skill Quality Tests

这些测试用于检查 `local-auth-gate-audit` 是否退化成摘要、空壳、幻觉扩展或不可验收说明书。

## 测试 1：是否重新读取输入材料

检查对象：

```text
原始 TXT
local-auth-gate-audit/SKILL.md
local-auth-gate-audit/README.md
local-auth-gate-audit/templates/output-template.md
local-auth-gate-audit/checklists/quality-gate.md
local-auth-gate-audit/checklists/final-review.md
local-auth-gate-audit/examples/basic-example.md
local-auth-gate-audit/examples/full-example.md
local-auth-gate-audit/tests/skill-quality-tests.md
```

通过标准：

- [ ] 每个文件均已读取。
- [ ] 未读取文件被标记为“未验证，不得宣称已通过”。
- [ ] 不能用文件名推断文件内容。
- [ ] 不能把旧版本结论当作本次审查结论。

失败处理：读取缺失文件；仍无法读取时把该文件从通过项中移除。

## 测试 2：是否漏掉 TXT 关键内容

检查方法：读取 `SKILL.md`、`templates/output-template.md`、`checklists/*.md`，逐项查找。

通过标准：

- [ ] 包含本地授权范围。
- [ ] 包含禁止公网、第三方真实系统、真实用户数据。
- [ ] 包含禁止中间人、嗅探、证书劫持、流量劫持、钓鱼、社工。
- [ ] 包含禁止破坏性操作、DoS、压力测试。
- [ ] 包含测试账号、测试租户、测试角色、测试资源。
- [ ] 包含写操作可回滚。
- [ ] 包含 candidate 与 confirmed 区分。
- [ ] 包含项目画像、环境准备、动态验证、小众路径、证据标准、自动化、报告、反幻觉。
- [ ] 包含误报追责。
- [ ] 包含 30 类非常规测试。
- [ ] 包含最终验收 8 问。

失败处理：缺一项即修改 SKILL.md 或模板，不允许只在 README 中说明。

## 测试 3：是否把摘要当复刻

检查方法：随机抽取 TXT 中的阶段、矩阵字段、证据字段、30 类测试项，对照 Skill 文件是否转成执行规则。

通过标准：

- [ ] 暴露面矩阵 11 个字段完整。
- [ ] confirmed 的 15 类证据字段完整。
- [ ] 30 类非常规测试均有测试入口、账号、正向、反向、请求构造、预期、实际、证据、结论、修复建议字段。
- [ ] 正向与反向测试规则可直接执行。
- [ ] blocked、candidate、false_positive、needs_review 均有判定条件。
- [ ] 没有只写“进行认证审计”或“输出报告”。

失败处理：把缺失字段补入 `SKILL.md` 和 `templates/output-template.md`。

## 测试 4：是否加入无关内容

检查方法：查找与 TXT 边界冲突或超出本地授权范围的内容。

失败模式：

- [ ] 要求公网扫描。
- [ ] 要求访问第三方真实系统。
- [ ] 要求真实用户数据。
- [ ] 要求中间人、嗅探、证书劫持、流量劫持、钓鱼、社工。
- [ ] 要求 DoS、压力测试、破坏性写入。
- [ ] 宣称无需动态请求即可 confirmed。
- [ ] 宣称自动发现全部缺陷。

通过标准：以上均不存在。

失败处理：删除冲突内容，改成 blocked 或本地无害验证。

## 测试 5：是否命名过长或空泛

检查对象：目录名和文件名。

通过标准：

- [ ] 主目录为 `local-auth-gate-audit`。
- [ ] 目录名使用小写英文和短横线。
- [ ] 目录名能对应本地授权认证门禁动态验证。
- [ ] 不含 best、final、new、advanced、ultimate、skill-only。
- [ ] 文件名不含 copy、new、final 等低质量标记。
- [ ] 文件名简洁且能看出作用。

失败处理：重命名并更新所有引用。

## 测试 6：是否目录臃肿

通过标准：

- [ ] 只保留 1 个主 Skill。
- [ ] 只保留 `templates/`、`checklists/`、`examples/`、`tests/`。
- [ ] 未增加无来源的 rules、workflows、schemas、fixtures 目录。
- [ ] 不存在空目录。
- [ ] 不存在空文件。
- [ ] 不存在重复文件。

失败处理：能合并就合并，能删除就删除。

## 测试 7：是否没有输入输出定义

通过标准：

- [ ] `SKILL.md` 有输入要求表。
- [ ] `SKILL.md` 有输出要求。
- [ ] `output-template.md` 有运行清单、暴露面矩阵、账号矩阵、replay_results、findings 模板。
- [ ] 缺失输入有失败处理。

失败处理：补齐输入、输出、失败处理字段。

## 测试 8：是否没有质量门禁

通过标准：

- [ ] 有 Skill 交付门禁。
- [ ] 有范围门禁。
- [ ] 有动态环境门禁。
- [ ] 有正反验证门禁。
- [ ] 有小众路径门禁。
- [ ] 有 confirmed 门禁。
- [ ] 有 candidate 门禁。
- [ ] 有 blocked 门禁。
- [ ] 有 false_positive 门禁。
- [ ] 有报告门禁。

失败处理：补齐到 `SKILL.md` 和 `checklists/quality-gate.md`。

## 测试 9：是否没有失败处理

通过标准：

- [ ] 未找到启动命令时输出最小补齐方案。
- [ ] 服务无法启动时写入 blocked。
- [ ] 无测试账号时生成 seed 草案并标记 blocked/candidate。
- [ ] 无测试数据库时不执行写操作。
- [ ] Playwright 不可用时使用替代动态请求工具。
- [ ] 无法保存 HAR/trace 时保存替代证据。
- [ ] 反向样本 200 时检查响应内容、权限效果、DB/log。
- [ ] 反向样本 403 时继续检查其他方法、路径、content-type。
- [ ] 写操作不可回滚时不执行。
- [ ] 目标超出授权范围时停止。

失败处理：补齐 `SKILL.md` 失败处理表。

## 测试 10：是否没有 TXT 映射

通过标准：

- [ ] `SKILL.md` 包含 TXT 到 Skill 映射说明。
- [ ] 映射表覆盖开头角色、严格边界、任务目标、八个阶段、误报追责、30 类测试、最终验收。
- [ ] 映射表区分原文复刻和工程化补强。
- [ ] 映射表不是只写“全文”。

失败处理：补齐逐项映射。

## 测试 11：是否把工程化补强伪装成原文

检查方法：查找新增内容是否标明为工程化补强。

通过标准：

- [ ] `run-manifest.json` 标记为工程化补强。
- [ ] Skill 交付门禁标记为工程化补强。
- [ ] examples 和 tests 标记为工程化补强。
- [ ] 未把新增目录结构说成 TXT 原文要求。

失败处理：改写来源标记。

## 测试 12：是否示例脱离 TXT

通过标准：

- [ ] 示例限定本地授权项目。
- [ ] 示例使用测试数据库和测试账号。
- [ ] 示例包含正向与反向样本。
- [ ] 示例没有公网或真实用户数据。
- [ ] 示例中 confirmed 有动态证据字段。
- [ ] 示例中证据不足项被降级为 candidate 或 blocked。

失败处理：重写示例。

## 测试 13：是否测试无法发现真实问题

通过标准：

- [ ] 测试能发现漏复刻。
- [ ] 测试能发现摘要化。
- [ ] 测试能发现无关扩展。
- [ ] 测试能发现命名失败。
- [ ] 测试能发现目录臃肿。
- [ ] 测试能发现缺输入输出。
- [ ] 测试能发现缺质量门禁。
- [ ] 测试能发现缺失败处理。
- [ ] 测试能发现缺 TXT 映射。
- [ ] 测试能发现工程化补强伪装成原文。

失败处理：补充对应测试项。

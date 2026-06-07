# skill-quality-tests

本测试用于验收 `cmd-exec-risk-replay` 是否把 TXT 复刻成可执行 Claude Skill，而不是摘要、空壳或无证据报告模板。

## 1. TXT 关键内容覆盖测试

- [ ] `SKILL.md` 保留“只允许分析和验证当前本地授权项目”。
- [ ] `SKILL.md` 保留“只允许本地测试环境、测试数据库、测试目录”。
- [ ] `SKILL.md` 保留禁止公网敏感地址、内网敏感地址、云元数据地址。
- [ ] `SKILL.md` 保留禁止反弹 shell、下载执行、持久化、提权、横向移动、凭据读取、删库、删文件、业务破坏、DoS、DDoS、资源耗尽。
- [ ] `SKILL.md` 保留无害 marker 级证明。
- [ ] `SKILL.md` 保留“只有静态路径、没有动态证据，只能 candidate”。
- [ ] `SKILL.md` 保留忽略 MITM、网络劫持、证书绕过。
- [ ] `SKILL.md` 保留初始化工作：语言、框架、入口、启动方式、路由、认证、权限模型。
- [ ] `SKILL.md` 保留 sink 清单。
- [ ] `SKILL.md` 保留 source 清单。
- [ ] `SKILL.md` 保留 source → transform → sink 数据流图。
- [ ] `SKILL.md` 保留八类重点挖掘方向。
- [ ] `templates/output-template.md` 保留 replay plan 十项字段。
- [ ] `checklists/final-review.md` 保留第二轮反思 15 项。
- [ ] `checklists/final-review.md` 保留第三轮偏门补充 10 项。
- [ ] `checklists/final-review.md` 保留 confirmed 反向审判 15 项。

失败判定：任一项缺失，判定为漏复刻。

## 2. 摘要伪装测试

- [ ] 没有只写“分析项目风险”而不写分析对象、来源、输出、判断标准、失败处理。
- [ ] 没有只写“验证漏洞”而不写验证对象、步骤、证据、通过标准、失败处理。
- [ ] 没有只写“输出报告”而不写字段、格式、结论等级、证据字段、禁止下结论场景。
- [ ] 没有只说“可能存在命令执行”而不写 source、sink、replay plan。
- [ ] 没有只给“过滤输入”一类泛泛修复项。

失败判定：任一失败形态出现，判定为把摘要当复刻。

## 3. 无关内容测试

- [ ] 没有加入未授权目标流程。
- [ ] 没有加入公网目标验证流程。
- [ ] 没有加入社工、钓鱼、凭据攻击、MITM、网络劫持、证书绕过作为主任务。
- [ ] 没有加入反弹 shell、下载执行、持久化、提权、横向移动。
- [ ] 没有加入规避检测或绕过安全产品内容。
- [ ] 没有把与命令执行无关的漏洞分类作为主任务。

失败判定：存在无关主任务或危险扩展时，判定为不合格。

## 4. 命名测试

- [ ] 目录名为 `cmd-exec-risk-replay`。
- [ ] 目录名能看出“命令执行风险”和“replay 验证”。
- [ ] 目录名使用小写英文和短横线。
- [ ] 目录名没有 `best`、`final`、`new`、`advanced`、`ultimate`、`skill-only`。
- [ ] 文件名简短且能看出用途。
- [ ] 没有 `README-final.md`、`new-template.md`、`copy.md` 这类低质量命名。

失败判定：命名不能对应 TXT 核心主题时，判定为命名失败。

## 5. 目录臃肿测试

- [ ] 只有 1 个主 Skill。
- [ ] 没有多个做同一件事的 Skills。
- [ ] 没有不能独立运行的 Skills。
- [ ] 只包含必要目录：`templates`、`checklists`、`examples`、`tests`。
- [ ] 没有空目录。
- [ ] 没有空文件。
- [ ] 每个文件都有明确调用价值。

失败判定：出现无作用目录、空文件、重复 Skill 时，判定为目录臃肿。

## 6. 输入输出定义测试

- [ ] `SKILL.md` 定义输入字段。
- [ ] `SKILL.md` 定义缺少输入时的处理。
- [ ] `SKILL.md` 定义输出结构。
- [ ] `templates/output-template.md` 可直接填写。
- [ ] `templates/output-template.md` 包含证据字段。
- [ ] `templates/output-template.md` 包含五类结论等级。
- [ ] `templates/output-template.md` 包含未完成验证及原因。

失败判定：缺少输入、输出或失败处理时，判定为不可执行。

## 7. 质量门禁测试

- [ ] `checklists/quality-gate.md` 包含边界门禁。
- [ ] `checklists/quality-gate.md` 包含输入门禁。
- [ ] `checklists/quality-gate.md` 包含项目理解门禁。
- [ ] `checklists/quality-gate.md` 包含 source 门禁。
- [ ] `checklists/quality-gate.md` 包含 sink 门禁。
- [ ] `checklists/quality-gate.md` 包含数据流门禁。
- [ ] `checklists/quality-gate.md` 包含 replay plan 门禁。
- [ ] `checklists/quality-gate.md` 包含动态验证门禁。
- [ ] `checklists/quality-gate.md` 包含结论门禁。
- [ ] `checklists/quality-gate.md` 包含输出门禁。

失败判定：没有可勾选门禁时，判定为验收失败。

## 8. 失败处理测试

- [ ] 项目路径缺失时停止。
- [ ] 授权范围缺失时停止。
- [ ] 测试环境无法启动时标为 `needs_environment`。
- [ ] marker 目录不可写时不执行动态验证。
- [ ] 只有静态路径时最高为 `candidate`。
- [ ] 字符串回显时不得 `confirmed`。
- [ ] 权限或 allowlist 阻断时标为 `blocked`。
- [ ] 环境不足时明确不能下结论。
- [ ] 缺少负向验证时降级。
- [ ] 缺少两类交叉证据时降级。

失败判定：失败处理不明确时，判定为不可落地。

## 9. TXT 映射测试

- [ ] `SKILL.md` 包含 TXT 到 Skill 映射表。
- [ ] 映射表列出原文位置/标题。
- [ ] 映射表列出 Skill 文件。
- [ ] 映射表说明转化方式。
- [ ] 映射表区分原文复刻和工程化补强。
- [ ] 映射表没有把新增内容伪装成 TXT 原文。

失败判定：缺少映射表或映射不可追溯，判定为复刻失败。

## 10. 工程化补强边界测试

- [ ] 编号规则标记为工程化补强。
- [ ] 输入 YAML 标记为工程化补强。
- [ ] 文件组织方式标记为工程化补强。
- [ ] 两类交叉证据规则标记为工程化补强。
- [ ] 工程化补强没有写成 TXT 原文要求。

失败判定：工程化补强伪装成原文，判定为不可信。

## 11. confirmed 证据测试

- [ ] 每个 confirmed 有动态验证成功。
- [ ] 每个 confirmed 有至少两类交叉证据。
- [ ] 每个 confirmed 有负向验证。
- [ ] 每个 confirmed 证明 source 到 sink 真实可达。
- [ ] 每个 confirmed 没有使用编造的命令输出、日志、截图、HAR、trace。
- [ ] 每个 confirmed 通过最终反向审判。
- [ ] 证据不足的项已降级。

失败判定：任何证据不足的 confirmed 都是交付失败。

## 12. 最终验收结论

```text
通过条件：
1. 上述 11 组测试全部通过。
2. Skill 数量为 1。
3. 文件都可直接使用。
4. 模板可直接填写。
5. checklist 可直接勾选。
6. examples 能说明合格和不合格输出。
7. tests 能发现漏复刻、摘要化、空壳化、无证据 confirmed、无映射、无失败处理、工程化补强伪装成原文。
```

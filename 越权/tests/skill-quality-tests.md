# Skill 质量测试

本文件用于检查 Skill 是否退化为摘要、空壳、幻觉扩展或不可验收说明书。

## 测试 1：是否漏掉 TXT 关键内容

检查对象：`SKILL.md`、`templates/output-template.md`

步骤：

1. 搜索关键词：水平越权、垂直越权、多租户、IDOR、BOLA、BFLA、GraphQL、WebSocket、异步任务、Webhook、状态机、旧 session、缓存、confirmed、candidate、blocked、false_positive、needs_review。
2. 检查是否包含第一阶段到第七阶段、误报追责、50 项非常规测试。
3. 检查越权暴露面矩阵 16 个字段是否完整。

通过标准：关键词、阶段和矩阵字段全部存在。失败时补回对应原文规则。

## 测试 2：是否把摘要当复刻

检查对象：`SKILL.md`

步骤：

1. 查找只有概括没有动作的句子。
2. 检查每个阶段是否包含执行动作、输出文件、通过标准、失败处理。
3. 检查 confirmed、candidate、blocked、false_positive、needs_review 是否有明确判定条件。

通过标准：每个阶段都能直接执行；没有只写概念的段落。失败时重写为动作表或清单。

## 测试 3：是否加入无关或越界内容

检查对象：全部文件

步骤：

1. 搜索公网扫描、第三方攻击、真实用户数据、压力测试、爆破、删除数据库、修改生产逻辑制造漏洞。
2. 检查命令是否限定本地 URL、回环地址、容器网络名或授权测试地址。
3. 检查是否加入与越权动态验证无关的主任务。

通过标准：无越界命令，无无关主任务。失败时删除或移入不适用范围。

## 测试 4：是否把工程化补强伪装成原文

检查对象：`SKILL.md`、`README.md`、`templates/output-template.md`

步骤：

1. 搜索 `AUTHZ-YYYYMMDD-NNN`、`evidence/_index.md`、工程化补强。
2. 检查这些内容是否被标为工程化补强。
3. 检查映射表是否说明它们不是 TXT 原文要求。

通过标准：新增内容有来源标记，不列为 TXT confirmed 必要条件。失败时改写映射表和相关章节。

## 测试 5：命名是否失败

检查对象：目录名和文件名

步骤：

1. 目录名必须为 `authz-bypass-dynamic-audit` 或同等简洁主题名。
2. 检查是否包含 best、final、new、advanced、ultimate、skill-only。
3. 检查是否使用小写英文和短横线。
4. 检查是否存在 README-final.md、new-template.md、copy.md。

通过标准：命名简洁且对应“越权动态验证”。失败时重命名并更新引用。

## 测试 6：目录是否臃肿或空壳

检查对象：目录结构

步骤：

1. 只允许主文件和 templates、checklists、examples、tests。
2. 检查是否存在空目录。
3. 检查每个文件是否有实际字段、清单、示例或测试步骤。

通过标准：不存在空目录、空文件、重复文件。失败时删除或合并。

## 测试 7：是否缺输入输出定义

检查对象：`SKILL.md`

步骤：

1. 输入要求必须包含 TXT、项目路径、授权边界、启动命令、数据库初始化、测试账号、测试资源、本地 base URL、测试工具。
2. 输出要求必须包含最终 13 部分。
3. evidence 目录必须包含 TXT 原文要求的文件。

通过标准：输入、输出、证据文件完整。失败时补齐表格。

## 测试 8：是否缺质量门禁

检查对象：`SKILL.md`、`checklists/quality-gate.md`

步骤：

1. 检查是否包含未读取 TXT 不得生成。
2. 检查是否包含未建立映射表不得通过。
3. 检查是否包含未区分原文复刻和工程化补强不得通过。
4. 检查是否包含未提供模板、checklist、examples、tests 不得通过。
5. 检查是否包含空壳文件不得通过。
6. 检查 confirmed 门槛是否包含动态请求、正反样本、异常成功、证据文件、复现步骤。

通过标准：门禁完整且能触发降级或修复。失败时补门禁。

## 测试 9：是否缺失败处理

检查对象：`SKILL.md`

步骤：

1. 检查失败处理表是否包含 TXT 未读取、授权边界不明、项目不能启动、数据库不能初始化、账号不能创建、资源不能创建、只有静态可疑代码、动态请求成功但无敏感数据、动态证明访问被拒绝、confirmed 证据缺失。
2. 检查每种失败是否映射到 blocked、candidate、needs_review 或 false_positive。
3. 检查每种失败是否有处理动作。

通过标准：所有失败路径可执行。失败时补失败处理表。

## 测试 10：是否缺 TXT 映射

检查对象：`SKILL.md`

步骤：

1. 检查“TXT 到 Skill 映射说明”是否存在。
2. 检查映射表字段是否包含 TXT 原文位置、Skill 文件、转化方式、原文复刻/工程化补强、备注。
3. 检查每个 TXT 关键标题是否有对应位置。

通过标准：映射表能追溯原文。失败时补表。

## 测试 11：SKILL.md 是否能直接被 Claude 使用

检查对象：`SKILL.md`

模拟输入：

```text
项目路径：C:\work\demo
授权范围：仅本机
要求：先做暴露面矩阵
```

检查：

1. Claude 是否会先确认授权边界。
2. Claude 是否会读取项目结构。
3. Claude 是否会生成 authz_surface_matrix.md。
4. Claude 是否不会直接输出 confirmed。
5. Claude 是否要求动态证据后才分级。

通过标准：输出路径和下一步明确。失败时重写核心工作流。

## 测试 12：examples 是否贴近 TXT

检查对象：`examples/basic-example.md`、`examples/full-example.md`

步骤：

1. 示例必须使用本地授权环境。
2. 示例必须包含正反对照。
3. 示例必须展示 confirmed、candidate、false_positive、blocked 的区别。
4. 示例必须包含证据文件路径。
5. 示例不得把示例漏洞当作目标项目真实漏洞。

通过标准：示例可复制到模板中使用，且不产生越界测试。失败时重写示例。

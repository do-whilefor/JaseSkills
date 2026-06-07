# cmd-exec-risk-replay

`cmd-exec-risk-replay` 是从 `命令执行提示词转skills.txt` 复刻出的单一 Claude Skill。它的目标是：在本地授权开源项目中，对命令执行类风险做 source → transform → sink 追踪，并用无害 marker 进行动态验证；证据不足时必须降级。

## Skill 数量

保留 1 个主 Skill。TXT 的内容虽然包含边界、初始化、挖掘方向、动态验证、报告、反思、偏门补挖、confirmed 复核，但它们属于同一条命令执行风险验证工作流。拆成多个 Skill 会产生重复规则和调用混乱。

## 目录结构

```text
cmd-exec-risk-replay/
  SKILL.md
  README.md
  templates/
    output-template.md
  checklists/
    quality-gate.md
    final-review.md
  examples/
    basic-example.md
    full-example.md
  tests/
    skill-quality-tests.md
```

## 文件作用

| 文件 | 作用 |
|---|---|
| `SKILL.md` | Claude 调用 Skill 时的核心规则，包含适用范围、边界、输入输出、工作流、质量门禁、幻觉控制、失败处理、TXT 映射 |
| `templates/output-template.md` | 最终报告模板，约束字段、证据、结论等级、未完成验证原因 |
| `checklists/quality-gate.md` | 执行前、执行中、输出前的硬门禁 |
| `checklists/final-review.md` | 第二轮反思、第三轮补挖、confirmed 反向审判 |
| `examples/basic-example.md` | 最小调用与最小合格输出示例 |
| `examples/full-example.md` | 完整报告骨架示例 |
| `tests/skill-quality-tests.md` | 验收 Skill 是否漏复刻、摘要化、空壳化、幻觉扩展、命名失败、缺少门禁 |

## Claude 调用示例

```text
使用 cmd-exec-risk-replay Skill。
项目路径：C:\path\to\authorized-project
授权范围：仅限该本地项目和测试环境。
测试目录：./security-lab/
marker 目录：./security-lab/markers/
证据目录：./security-lab/evidence/
角色/租户：user/admin，tenant-a/tenant-b。
要求：只允许无害 marker 级验证；没有动态证据不得 confirmed；输出时使用 templates/output-template.md。
```

## Windows PowerShell 落地命令

```powershell
$Zip = ".\cmd-exec-risk-replay.zip"
$Dest = "$env:USERPROFILE\.claude\skills"
New-Item -ItemType Directory -Force -Path $Dest | Out-Null
Expand-Archive -Path $Zip -DestinationPath $Dest -Force
Get-ChildItem -Recurse "$Dest\cmd-exec-risk-replay"
```

为项目创建证据目录：

```powershell
$ProjectRoot = "C:\path\to\authorized-project"
New-Item -ItemType Directory -Force -Path "$ProjectRoot\security-lab\markers" | Out-Null
New-Item -ItemType Directory -Force -Path "$ProjectRoot\security-lab\evidence" | Out-Null
```

## 使用限制

只允许本地授权项目、测试环境、测试数据库、测试目录。禁止公网敏感地址、内网敏感地址、云元数据地址，禁止真实密钥和真实用户数据，禁止破坏性动作。所有 confirmed 必须有无害动态证据和负向验证。

## 验收方式

按 `tests/skill-quality-tests.md` 执行验收。任一关键项失败，压缩包不得交付。
